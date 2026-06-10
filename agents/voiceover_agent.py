import logging
import subprocess
import json
import uuid
import re
import hashlib
from pathlib import Path

from TTS.api import TTS

from config import settings
from agents.state import VideoState

logger = logging.getLogger(__name__)

_tts_model = None


def get_tts_model():
    global _tts_model

    if _tts_model is None:
        logger.info("[XTTS] Loading model...")
        _tts_model = TTS(
            "tts_models/multilingual/multi-dataset/xtts_v2"
        ).to("cuda")

    return _tts_model


def get_duration(path: Path) -> float:
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
        duration = stream.get("duration")
        if duration:
            return float(duration)

    return 0.0


def prepare_script_for_tts(script: str, part_number: int) -> str:
    script = script.strip()

    script = script.replace("**", "")
    script = script.replace("*", "")
    script = script.replace("---", "")

    script = re.sub(r"(?im)^\s*part\s*(one|two|three|1|2|3)\s*:?\s*", "", script)
    script = re.sub(r"(?im)^\s*chapter\s*(one|two|three|1|2|3)\s*:?\s*", "", script)
    script = re.sub(r"(?im)^\s*(cliffhanger|ending)\s*[.!?:-]*\s*$", "", script)
    script = re.sub(r"(?im)^\s*(cliffhanger|ending)\s*:\s*", "", script)

    first_sentence_split = re.split(r'(?<=[.!?])\s+', script, maxsplit=1)

    if len(first_sentence_split) > 1:
        first_sentence = first_sentence_split[0].strip()
        rest = first_sentence_split[1].strip()

        script = (
            f"{first_sentence}\n\n"
            f"Part {part_number}.\n\n"
            f"{rest}"
        )
    else:
        script = f"{script}\n\n"

    script = script.replace(". ", ".\n\n")
    script = script.replace("? ", "?\n\n")
    script = script.replace("! ", "!\n\n")

    return script.strip()


def choose_speaker_path(state: VideoState) -> Path:
    narrator_gender = state.get("narrator_gender", "male").lower()

    voices_dir = settings.ROOT_DIR / "assets" / "voices"

    if narrator_gender == "female":
        speaker_path = voices_dir / "female.wav"
    else:
        male_path = voices_dir / "narrator.wav"
        fallback_path = voices_dir / "narrator.wav"
        speaker_path = male_path if male_path.exists() else fallback_path

    if not speaker_path.exists():
        raise FileNotFoundError(
            f"Missing narrator voice sample: {speaker_path}\n"
            "Expected one of:\n"
            "- assets/voices/female.wav\n"
            "- assets/voices/narrator.wav\n"
            "- assets/voices/narrator.wav"
        )

    return speaker_path


def run(state: VideoState) -> VideoState:
    script = state.get("active_script", "")

    if not script:
        script = state.get("part1", "")

    if not script:
        script = state.get("script_raw", "")

    if not script:
        raise ValueError("No script found for voiceover.")

    run_id = state.get("run_id", str(uuid.uuid4())[:8])
    part_number = state.get("part_number", 1)
    story_slug = state.get("story_slug", run_id)

    prepared_script = prepare_script_for_tts(script, part_number)
    speaker_path = choose_speaker_path(state)

    narrator_gender = state.get("narrator_gender", "male").lower()
    script_hash = hashlib.sha1(
        f"{prepared_script}|{speaker_path.name}".encode("utf-8")
    ).hexdigest()[:8]

    out_path = settings.AUDIO_DIR / (
        f"{story_slug}_part_{part_number}_{narrator_gender}_{script_hash}_voiceover.wav"
    )

    if out_path.exists() and out_path.stat().st_size > 0:
        logger.info(f"[VoiceoverAgent] Using cached voiceover: {out_path.name}")
        duration = get_duration(out_path)

        return {
            **state,
            "audio_path": str(out_path),
            "audio_duration_sec": duration,
            "active_script": script,
            "speaker_path": str(speaker_path),
            "status": "voiceover_cached",
        }

    logger.info(
        f"[VoiceoverAgent] Generating XTTS voiceover for part {part_number} "
        f"using {speaker_path.name}..."
    )

    tts = get_tts_model()

    tts.tts_to_file(
        text=prepared_script,
        speaker_wav=str(speaker_path),
        language="en",
        file_path=str(out_path)
    )

    duration = get_duration(out_path)

    return {
        **state,
        "audio_path": str(out_path),
        "audio_duration_sec": duration,
        "active_script": script,
        "speaker_path": str(speaker_path),
        "status": "voiceover_done",
    }