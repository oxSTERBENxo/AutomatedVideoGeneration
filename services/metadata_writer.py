from pathlib import Path

from config import settings


def make_hook(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        return lines[0][:180]

    words = text.split()
    return " ".join(words[:22])


def make_description(story_title: str, part_number: int, hook: str) -> str:
    return f"""{story_title} | Part {part_number}

HOOK:
{hook}

DESCRIPTION:
POV: {hook}

Part {part_number} 😬

#redditstories #storytime #aita #relationshipdrama #minecraft #shorts #tiktokstory #part{part_number} #fyp
"""


def write_metadata(state: dict) -> dict:
    video_path = state.get("final_video_path")
    active_script = state.get("active_script", "")
    story_title = state.get("story_title", "Reddit Story")
    part_number = state.get("part_number", 1)

    if not video_path:
        return state

    video_path = Path(video_path)

    hook = make_hook(active_script)
    content = make_description(
        story_title=story_title,
        part_number=part_number,
        hook=hook
    )

    txt_path = settings.VIDEOS_DIR / f"{video_path.stem}.txt"

    txt_path.write_text(content, encoding="utf-8")

    return {
        **state,
        "description_path": str(txt_path),
        "hook": hook,
    }