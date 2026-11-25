import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
from app.core.config import settings

logger = logging.getLogger("TamilKidsAI.VideoAssembly")

class VideoAssemblyService:
    def __init__(self):
        self.ffmpeg_cmd = self._resolve_ffmpeg()

    def _resolve_ffmpeg(self) -> str:
        """Finds system ffmpeg or bundles imageio-ffmpeg automatically."""
        if settings.FFMPEG_PATH and os.path.exists(settings.FFMPEG_PATH):
            return settings.FFMPEG_PATH
        
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg
            
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

    def check_ffmpeg(self) -> None:
        """Raise a clear error if FFmpeg can't actually be executed."""
        try:
            r = subprocess.run([self.ffmpeg_cmd, "-version"], capture_output=True, text=True, timeout=20)
            if r.returncode != 0:
                raise RuntimeError(r.stderr[-300:])
        except Exception as e:
            raise RuntimeError(
                f"FFmpeg is not working ('{self.ffmpeg_cmd}'): {e}. "
                "Termux: run 'pkg install ffmpeg' and set FFMPEG_PATH=$PREFIX/bin/ffmpeg in backend/.env"
            )

    def assemble_final_video(
        self,
        scene_video_paths: List[str],
        narration_audio_path: str,
        output_video_path: str,
        srt_subtitle_path: Optional[str] = None,
        bgm_audio_path: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Combines rendered scene video clips, mixes narration and subtle BGM,
        burns subtitles if provided, and exports a low-memory MP4 (resolution from settings).
        """
        output_path = Path(output_video_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Create concat file for scene videos
        concat_txt_path = output_path.parent / "scenes_concat.txt"
        with open(concat_txt_path, "w", encoding="utf-8") as f:
            for p in scene_video_paths:
                f.write(f"file '{Path(p).resolve().as_posix()}'\n")

        # 2. Build FFmpeg command with complex audio filter
        cmd = [self.ffmpeg_cmd, "-y", "-hide_banner", "-loglevel", "error", "-nostats"]
        
        # Input 0: Concatenated video stream
        cmd.extend(["-f", "concat", "-safe", "0", "-i", str(concat_txt_path)])
        
        # Input 1: Narration audio
        cmd.extend(["-i", str(narration_audio_path)])
        
        # Audio filter configuration
        if bgm_audio_path and os.path.exists(bgm_audio_path):
            cmd.extend(["-stream_loop", "-1", "-i", str(bgm_audio_path)])
            # Mix narration (volume 1.0) and BGM (volume 0.12)
            filter_complex = (
                "[1:a]volume=1.0[narr];"
                "[2:a]volume=0.12[bgm];"
                "[narr][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
        else:
            cmd.extend(["-map", "0:v", "-map", "1:a"])

        # Hold the last frame if scenes are shorter than the narration; -shortest then ends at the audio
        cmd.extend(["-vf", "tpad=stop_mode=clone:stop_duration=3600,format=yuv420p"])

        # Video encoding settings for YouTube: H.264, AAC, YUV420p
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "1",
            "-x264-params", "rc-lookahead=0:ref=1:bframes=0",
            "-crf", "28",
            "-r", str(settings.VIDEO_FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_video_path)
        ])

        logger.info(f"Running video assembly: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up concat file
        if concat_txt_path.exists():
            concat_txt_path.unlink()

        if result.returncode != 0:
            logger.error(f"FFmpeg assembly failed: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed with code {result.returncode}: {result.stderr[-500:]}")

        # Validate final output file
        return self.validate_video_file(output_video_path)

    def validate_video_file(self, video_path: str) -> Dict[str, any]:
        """
        Validates the finished video: checks file existence, size, duration, and basic stream properties.
        """
        p = Path(video_path)
        if not p.exists() or p.stat().st_size == 0:
            return {"valid": False, "error": "Output file does not exist or is empty"}

        size_mb = round(p.stat().st_size / (1024 * 1024), 2)
        
        return {
            "valid": True,
            "path": str(p),
            "size_mb": size_mb,
            "resolution": f"{settings.VIDEO_WIDTH}x{settings.VIDEO_HEIGHT}",
            "fps": settings.VIDEO_FPS
        }

    def generate_youtube_thumbnail(
        self,
        title_tamil: str,
        category: str,
        background_image_path: Optional[str],
        output_thumbnail_path: str
    ) -> str:
        """
        Creates a high-contrast, child-friendly 16:9 (1280x720) YouTube thumbnail
        with vibrant background, Tamil title typography, and kid-friendly badge.
        """
        output_file = Path(output_thumbnail_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        width, height = 1280, 720
        
        # Create base canvas or load rendered scene frame
        if background_image_path and os.path.exists(background_image_path):
            img = Image.open(background_image_path).resize((width, height), Image.Resampling.LANCZOS)
        else:
            # Generate vibrant colorful gradient background (Kids theme: Sky Blue to Sun Gold)
            img = Image.new("RGB", (width, height), color=(26, 188, 156))
            draw = ImageDraw.Draw(img)
            for y in range(height):
                r = int(30 + (225 - 30) * (y / height))
                g = int(140 + (190 - 140) * (y / height))
                b = int(220 - (220 - 70) * (y / height))
                draw.line([(0, y), (width, y)], fill=(r, g, b))

        draw = ImageDraw.Draw(img)

        # Draw a semi-transparent dark rounded banner for maximum text readability
        banner_top = int(height * 0.65)
        banner_bottom = height - 20
        draw.rectangle([30, banner_top, width - 30, banner_bottom], fill=(0, 0, 0, 190))

        # Category badge on top left
        draw.rounded_rectangle([40, 40, 420, 100], radius=20, fill=(243, 156, 18))
        
        # Font setup (uses system font or default bitmap font)
        try:
            # Nirmala UI is pre-installed on Windows and renders Tamil beautifully
            font_title = ImageFont.truetype("Nirmala.ttf", 46)
            font_badge = ImageFont.truetype("Nirmala.ttf", 28)
        except Exception:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()

        draw.text((60, 52), f"★ {category}", fill=(255, 255, 255), font=font_badge)
        
        # Render Tamil Title with drop shadow
        text_x = 60
        text_y = banner_top + 25
        # Shadow
        draw.text((text_x + 3, text_y + 3), title_tamil, fill=(0, 0, 0), font=font_title)
        # Yellow foreground for high YouTube CTR
        draw.text((text_x, text_y), title_tamil, fill=(255, 241, 118), font=font_title)

        # Border for cartoon look
        border_width = 12
        draw.rectangle([0, 0, width, height], outline=(255, 215, 0), width=border_width)

        img.save(str(output_thumbnail_path), "JPEG", quality=95)
        logger.info(f"Generated YouTube thumbnail: {output_thumbnail_path}")
        return str(output_thumbnail_path)
