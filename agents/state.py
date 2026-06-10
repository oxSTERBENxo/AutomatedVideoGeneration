from typing import Any, Optional
from typing_extensions import TypedDict


class VideoState(TypedDict, total=False):
    topic: str
    run_id: str

    script_raw: str
    story_title: str
    story_slug: str
    active_script: str
    part_number: int
    script_hook: str
    script_body: str
    script_outro: str
    estimated_duration_sec: float

    audio_path: str
    audio_duration_sec: float

    transcript_segments: list[dict[str, Any]]
    caption_chunks: list[dict[str, Any]]
    srt_path: str
    ass_path: str

    background_video_path: str
    background_start_sec: float

    final_video_path: str

    error: Optional[str]
    status: str
