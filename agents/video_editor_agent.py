import logging
import subprocess
import uuid
from pathlib import Path

from config import settings
from agents.state import VideoState

logger = logging.getLogger(__name__)


def run(state: VideoState) -> VideoState:
    audio_path = state.get("audio_path")
    ass_path = state.get("ass_path")
    bg_path = state.get("background_video_path")
    bg_start = state.get("background_start_sec", 0)
    duration = state.get("audio_duration_sec", settings.TARGET_DURATION_SEC)

    if not audio_path or not Path(audio_path).exists():
        raise FileNotFoundError("Missing audio file.")

    if not ass_path or not Path(ass_path).exists():
        raise FileNotFoundError("Missing caption .ass file.")

    if not bg_path or not Path(bg_path).exists():
        raise FileNotFoundError("Missing background video.")

    run_id = state.get("run_id", str(uuid.uuid4())[:8])
    output_name = state.get("output_video_name", f"{run_id}_final.mp4")

    out_path = settings.VIDEOS_DIR / output_name

    clip_duration = duration + 0.5

    safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

    vf = (
        f"scale=-2:{settings.VIDEO_HEIGHT},"
        f"crop={settings.VIDEO_WIDTH}:{settings.VIDEO_HEIGHT},"
        f"subtitles='{safe_ass_path}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(bg_start),
        "-i", bg_path,
        "-i", audio_path,
        "-t", str(clip_duration),
        "-vf", vf,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]

    logger.info(f"[VideoEditor] Rendering final video: {output_name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return {
        **state,
        "final_video_path": str(out_path),
        "status": "video_done",
    }