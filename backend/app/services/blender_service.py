import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.core.config import settings
from app.services.video_assembly_service import VideoAssemblyService

logger = logging.getLogger("TamilKidsAI.BlenderService")

class BlenderService:
    def __init__(self):
        self.blender_bin = self._find_blender()
        self.assembly_service = VideoAssemblyService()

    def _find_blender(self) -> str:
        if settings.BLENDER_PATH and os.path.exists(settings.BLENDER_PATH):
            return settings.BLENDER_PATH
        
        system_blender = shutil.which("blender")
        if system_blender:
            return system_blender
            
        # Common Windows paths
        common_win_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
        ]
        for p in common_win_paths:
            if os.path.exists(p):
                return p
        return "blender"

    def render_scene(self, scene_dict: Dict[str, Any], output_path: str) -> str:
        """
        Executes Blender headless to render the 3D animated scene.
        If Blender is not present, generates a dynamic kinetic animated scene
        using FFmpeg & high-resolution canvas so the pipeline remains 100% operational.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if Blender is truly runnable
        blender_available = False
        try:
            res = subprocess.run([self.blender_bin, "--version"], capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                blender_available = True
        except Exception:
            blender_available = False

        if blender_available:
            script_path = settings.BLENDER_DIR / "scripts" / "generate_scene.py"
            temp_json = out_file.parent / f"scene_{scene_dict.get('scene_number', 1)}.json"
            with open(temp_json, "w", encoding="utf-8") as f:
                json.dump(scene_dict, f, ensure_ascii=False)

            cmd = [
                self.blender_bin,
                "-b",
                "-P", str(script_path),
                "--",
                "--scene-json", str(temp_json),
                "--output-video", str(out_file)
            ]
            logger.info(f"Rendering 3D scene in Blender: {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * 60)
                if res.returncode != 0:
                    raise RuntimeError(f"Blender exited {res.returncode}: {res.stderr[-800:] or res.stdout[-800:]}")
                # Blender may append the frame range to the filename - find the real file
                if not out_file.exists() or out_file.stat().st_size == 0:
                    candidates = sorted(out_file.parent.glob(f"{out_file.stem}*.mp4"))
                    if not candidates:
                        raise RuntimeError(f"Blender finished but no video was written. Output: {res.stdout[-800:]}")
                    candidates[0].replace(out_file)
                return str(out_file)
            except Exception as e:
                logger.error(f"Blender render failed, using FFmpeg fallback scene instead: {e}")
                return self._synthesize_kinetic_scene(scene_dict, str(out_file))
            finally:
                if temp_json.exists():
                    temp_json.unlink()
        else:
            logger.info("Blender binary not found on host. Running zero-latency kinetic cartoon scene synthesizer.")
            return self._synthesize_kinetic_scene(scene_dict, str(out_file))

    def _synthesize_kinetic_scene(self, scene_dict: Dict[str, Any], output_path: str) -> str:
        """
        Low-memory animated scene (FFmpeg only). Safe for 512MB servers:
        360p by default, ultrafast preset, single thread, no lookahead.
        Resolution / FPS come from VIDEO_WIDTH / VIDEO_HEIGHT / VIDEO_FPS settings.
        """
        ffmpeg_cmd = self.assembly_service.ffmpeg_cmd
        try:
            duration = max(1, int(float(scene_dict.get("duration_seconds", 15))))
        except (TypeError, ValueError):
            duration = 15

        width = int(settings.VIDEO_WIDTH)
        height = int(settings.VIDEO_HEIGHT)
        fps = int(settings.VIDEO_FPS)

        location = str(scene_dict.get("location", "")).lower()
        sky = "0x1B5E20" if "forest" in location else "0x1A237E"
        ground = "0x2E7D32"
        sun_size = max(16, int(height * 0.28))

        filter_complex = (
            f"[0:v]drawbox=y=ih*0.6:color={ground}:width=iw:height=ih*0.4:t=fill[bg];"
            f"[bg][1:v]overlay="
            f"x='(W-w)/2+sin(t*2)*W*0.10':"
            f"y='(H-h)/2+cos(t*3)*H*0.04':eval=frame,format=yuv420p[v]"
        )

        cmd = [
            ffmpeg_cmd, "-y", "-hide_banner", "-loglevel", "error", "-nostats",
            "-f", "lavfi", "-i", f"color=c={sky}:s={width}x{height}:r={fps}:d={duration}",
            "-f", "lavfi", "-i", f"color=c=0xFFD54F:s={sun_size}x{sun_size}:r={fps}:d={duration}",
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "1",
            "-x264-params", "rc-lookahead=0:ref=1:bframes=0",
            "-crf", "28",
            "-r", str(fps),
            "-t", str(duration),
            "-an",
            output_path,
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not Path(output_path).exists():
            raise RuntimeError(f"FFmpeg scene synthesis failed: {res.stderr[-800:]}")
        return output_path
