import logging
import re
import uuid

from agents.state import VideoState

from services.metadata_writer import write_metadata
import agents.script_agent as script_agent
import agents.voiceover_agent as voiceover_agent
import agents.caption_agent as caption_agent
import agents.visual_selection_agent as visual_selection_agent
import agents.video_editor_agent as video_editor_agent

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:60] or "story"


def build_part_intro(title: str, part_number: int) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = title.rstrip(".!?:;")

    if not title:
        title = "Reddit Story"

    return f"{title}, part {part_number}."


def add_part_intro(part_text: str, title: str, part_number: int) -> str:
    intro = build_part_intro(title, part_number)
    clean_part = part_text.strip()

    if clean_part.lower().startswith(intro.lower()):
        return clean_part

    return f"{intro}\n\n{clean_part}"


def run_step(agent_module, state: VideoState, name: str) -> VideoState:
    logger.info(f"Running {name}...")

    try:
        return agent_module.run(state)

    except Exception as e:
        logger.exception(f"{name} failed")

        return {
            **state,
            "error": str(e),
            "status": f"{name}_error"
        }


def run_pipeline(topic="") -> VideoState:
    run_id = str(uuid.uuid4())[:8]
    story_slug = slugify(topic)

    state: VideoState = {
        "topic": topic,
        "run_id": run_id,
        "story_slug": story_slug,
        "status": "starting",
    }

    state = run_step(script_agent, state, "script")

    if state.get("error"):
        return state

    story_title = state.get("story_title") or topic or "Reddit Story"
    story_slug = slugify(story_title)
    state = {
        **state,
        "story_title": story_title,
        "story_slug": story_slug,
    }

    final_video_paths = []

    for part_number in [1, 2, 3]:
        part_key = f"part{part_number}"
        part_text = state.get(part_key, "").strip()

        if not part_text:
            logger.warning(f"Skipping part {part_number}: empty text")
            continue

        part_state: VideoState = {
            **state,
            "active_script": add_part_intro(part_text, story_title, part_number),
            "part_number": part_number,
            "output_video_name": f"{story_slug}_part_{part_number}.mp4",
            "status": f"part_{part_number}_starting",
        }

        logger.info(f"========== RENDERING PART {part_number} ==========")

        part_state = run_step(voiceover_agent, part_state, "voice")
        if part_state.get("error"):
            return part_state

        part_state = run_step(caption_agent, part_state, "captions")
        if part_state.get("error"):
            return part_state

        part_state = run_step(visual_selection_agent, part_state, "visuals")
        if part_state.get("error"):
            return part_state

        part_state = run_step(video_editor_agent, part_state, "editor")
        part_state = write_metadata(part_state)
        if part_state.get("error"):
            return part_state

        final_video_paths.append(part_state.get("final_video_path"))

    return {
        **state,
        "final_video_paths": final_video_paths,
        "status": "done",
    }
