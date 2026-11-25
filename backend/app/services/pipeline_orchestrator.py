import os
import traceback
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.all_models import Topic, Story, Script, VideoJob, GeneratedVideo, YouTubeUpload, ErrorLog
from app.services.ai_story_generator import AIStoryGeneratorService
from app.services.tamil_tts_service import TamilTTSService
from app.services.blender_service import BlenderService
from app.services.video_assembly_service import VideoAssemblyService
from app.services.youtube_service import YouTubeService

logger = logging.getLogger("TamilKidsAI.Pipeline")

class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.story_gen = AIStoryGeneratorService()
        self.tts_service = TamilTTSService()
        self.blender_service = BlenderService()
        self.assembly_service = VideoAssemblyService()
        self.youtube_service = YouTubeService()

    def run_daily_pipeline(self, topic_id: Optional[int] = None) -> VideoJob:
        """
        Executes the full automated video generation pipeline from scratch.
        """
        # Step 1: Topic selection
        if topic_id:
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
        else:
            topic = self.story_gen.generate_daily_topic(self.db)

        # Step 2: Story generation
        story = self.story_gen.generate_full_story(topic, self.db)

        # Step 3: Script & Scene planning
        script = self.story_gen.generate_scene_script(story, self.db)

        # Step 4: Create Job tracking record
        job = VideoJob(
            story_id=story.id,
            stage="tts_generating",
            progress=10,
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return self.run_job(job.id)

    def run_job(self, job_id: int) -> Optional[VideoJob]:
        """
        Runs production stages for an existing job. Used by the API background task
        and the render worker. Always records failures (status, message, traceback).
        """
        job = self.db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            logger.error(f"Job #{job_id} not found")
            return None
        try:
            if not job.story or not job.story.script:
                raise RuntimeError("Job has no story/script - scene planning did not complete")
            job.status = "in_progress"
            job.started_at = job.started_at or datetime.now(timezone.utc)
            self.db.commit()
            self._execute_production_stages(job, job.story, job.story.script)
        except Exception as e:
            self.db.rollback()
            failed_stage = job.stage
            error_trace = traceback.format_exc()
            logger.error(f"Pipeline job #{job_id} failed at stage '{failed_stage}': {e}\n{error_trace}")
            job.status = "failed"
            job.stage = "failed"
            job.error_message = f"[{failed_stage}] {e}"[:2000]
            self.db.add(ErrorLog(
                job_id=job.id, level="ERROR", stage=failed_stage,
                message=str(e), stack_trace=error_trace
            ))
            self.db.commit()
        return job

    def _execute_production_stages(self, job: VideoJob, story: Story, script: Script):
        work_dir = settings.TEMP_DIR / f"job_{job.id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------
        # STAGE 1: Tamil Voice & Subtitles Generation
        # ---------------------------------------------------------
        job.stage = "tts_generating"
        job.progress = 20
        self.db.commit()

        audio_path = str(work_dir / "narration.mp3")
        srt_path = str(work_dir / "subtitles.srt")
        
        self.tts_service.generate_sync(
            text=story.full_story_tamil,
            output_audio_path=audio_path,
            output_srt_path=srt_path
        )

        # ---------------------------------------------------------
        # STAGE 2: 3D Scene Production & Animation
        # ---------------------------------------------------------
        job.stage = "scenes_rendering"
        job.progress = 40
        self.db.commit()

        scene_clips = []
        scenes_data = script.scenes or []
        if not scenes_data:
            raise RuntimeError("Script has no scenes to render")
        for idx, sc in enumerate(scenes_data):
            scene_out_path = str(work_dir / f"scene_{idx + 1}.mp4")
            rendered_clip = self.blender_service.render_scene(sc, scene_out_path)
            scene_clips.append(rendered_clip)
            # Update incremental progress
            job.progress = 40 + int((idx + 1) / max(len(scenes_data), 1) * 30)
            self.db.commit()

        # ---------------------------------------------------------
        # STAGE 3: Video & Audio Assembly (FFmpeg)
        # ---------------------------------------------------------
        job.stage = "assembling"
        job.progress = 75
        self.db.commit()

        final_video_name = f"tamil_kids_story_{story.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        final_video_path = str(settings.OUTPUT_DIR / final_video_name)

        validation = self.assembly_service.assemble_final_video(
            scene_video_paths=scene_clips,
            narration_audio_path=audio_path,
            output_video_path=final_video_path,
            srt_subtitle_path=srt_path
        )

        if not validation.get("valid"):
            raise RuntimeError(f"Final video validation failed: {validation.get('error')}")

        # ---------------------------------------------------------
        # STAGE 4: Thumbnail Creation
        # ---------------------------------------------------------
        job.stage = "thumbnailing"
        job.progress = 85
        self.db.commit()

        thumb_name = f"thumb_{story.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        final_thumb_path = str(settings.THUMBNAIL_DIR / thumb_name)
        
        self.assembly_service.generate_youtube_thumbnail(
            title_tamil=story.title_tamil,
            category=story.topic.category if story.topic else "நீதிக் கதை",
            background_image_path=None,
            output_thumbnail_path=final_thumb_path
        )

        # Save Generated Video Record
        gen_video = GeneratedVideo(
            job_id=job.id,
            video_path=final_video_path,
            thumbnail_path=final_thumb_path,
            srt_path=srt_path,
            audio_path=audio_path,
            duration_seconds=validation.get("duration", 600.0),
            resolution=validation.get("resolution", "1920x1080"),
            fps=validation.get("fps", 24),
            file_size_mb=validation.get("size_mb", 0.0),
            is_validated=True,
            validation_report=validation
        )
        self.db.add(gen_video)
        self.db.commit()

        # ---------------------------------------------------------
        # STAGE 5: Publishing / YouTube Upload Check
        # ---------------------------------------------------------
        job.stage = "ready_to_upload"
        job.progress = 90
        self.db.commit()

        # Check safety switch
        auto_pub = settings.AUTO_PUBLISH_ENABLED
        manual_approval = settings.REQUIRE_MANUAL_APPROVAL

        youtube_record = YouTubeUpload(
            video_id=gen_video.id,
            title=f"{story.title_tamil} | Tamil Kids Stories | 3D Cartoon",
            description=(
                f"{story.title_tamil}\n\n"
                f"நீதி: {story.moral_tamil}\n\n"
                f"அன்பு குழந்தைகளுக்கான இனிமையான 3D கார்ட்டூன் நீதிக் கதை.\n\n"
                f"#TamilKidsStories #MoralStories #TamilCartoons #KidsStoriesTamil"
            ),
            tags=["Tamil Kids Stories", "Moral Stories", "Tamil Cartoons", "Tamil Fairy Tales"],
            privacy_status=settings.YOUTUBE_PRIVACY_STATUS,
            made_for_kids=True,
            upload_status="pending"
        )
        self.db.add(youtube_record)
        self.db.commit()

        if auto_pub and not manual_approval:
            job.stage = "uploading"
            job.progress = 95
            self.db.commit()

            upload_result = self.youtube_service.upload_video(
                video_path=final_video_path,
                title=youtube_record.title,
                description=youtube_record.description,
                tags=youtube_record.tags,
                thumbnail_path=final_thumb_path,
                privacy_status=youtube_record.privacy_status,
                made_for_kids=True
            )

            if upload_result.get("success"):
                youtube_record.youtube_video_id = upload_result.get("video_id")
                youtube_record.upload_status = "uploaded"
                youtube_record.uploaded_at = datetime.now(timezone.utc)
            else:
                youtube_record.upload_status = "failed"
                youtube_record.error_message = upload_result.get("error")

        job.stage = "completed"
        job.progress = 100
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(f"Pipeline job #{job.id} completed successfully.")
