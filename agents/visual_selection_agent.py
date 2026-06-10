import logging
import random
import subprocess
import json
from pathlib import Path

from config import settings
from agents.state import VideoState

logger = logging.getLogger(__name__)


def _video_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return 0.0

    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        if stream.get("duration"):
            return float(stream["duration"])

    return 0.0


def run(state: VideoState) -> VideoState:
    folder = settings.ROOT_DIR / "assets" / "minecraft_gameplay"
    videos = list(folder.glob("*.mp4"))

    if not videos:
        return {
            **state,
            "error": f"No .mp4 videos found in {folder}",
            "status": "visual_error",
        }

    chosen = random.choice(videos)
    video_duration = _video_duration(chosen)
    audio_duration = state.get("audio_duration_sec", settings.TARGET_DURATION_SEC)

    max_start = max(0, video_duration - audio_duration - 2)
    start = random.uniform(0, max_start) if max_start > 0 else 0

    logger.info(f"[VisualAgent] Chosen background: {chosen.name}")

    return {
        **state,
        "background_video_path": str(chosen),
        "background_start_sec": round(start, 2),
        "status": "visuals_selected",
    }