import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

from faster_whisper import WhisperModel

from config import settings
from agents.state import VideoState

logger = logging.getLogger(__name__)


def srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunk_words(words: List[Dict[str, Any]], max_words=1):
    chunks = []

    i = 0
    while i < len(words):
        batch = words[i:i + max_words]

        text = " ".join(w["word"].strip() for w in batch)
        start = batch[0]["start"]
        end = batch[-1]["end"]

        if end - start < 0.25:
            end = start + 0.25

        chunks.append({
            "text": text,
            "start": start,
            "end": end
        })

        i += max_words

    return chunks


def write_srt(chunks, path: Path):
    lines = []

    for idx, chunk in enumerate(chunks, 1):
        lines.append(str(idx))
        lines.append(f"{srt_time(chunk['start'])} --> {srt_time(chunk['end'])}")
        lines.append(chunk["text"])
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_ass(chunks, path: Path):
    header = f"""
[Script Info]
ScriptType: v4.00+
PlayResX: {settings.VIDEO_WIDTH}
PlayResY: {settings.VIDEO_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding

Style: TikTok,Impact,{settings.CAPTION_FONT_SIZE},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,{settings.CAPTION_STROKE_WIDTH},2,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]

    for chunk in chunks:
        clean_text = chunk["text"].replace("{", "").replace("}", "").upper()

        # pop animation: starts bigger, quickly shrinks to normal
        animated_text = (
            r"{\fad(40,40)\fscx135\fscy135\t(0,120,\fscx100\fscy100)}"
            + clean_text
        )

        lines.append(
            f"Dialogue: 0,{ass_time(chunk['start'])},{ass_time(chunk['end'])},TikTok,,0,0,0,,{animated_text}"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def run(state: VideoState) -> VideoState:
    audio_path = state.get("audio_path")

    if not audio_path:
        raise ValueError("No audio file found.")

    logger.info("[CaptionAgent] Loading Whisper model...")
    model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")

    logger.info("[CaptionAgent] Transcribing audio...")
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language="en"
    )

    words = []

    for seg in segments:
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end
                })

    chunks = chunk_words(words, max_words=1)

    run_id = state.get("run_id", str(uuid.uuid4())[:8])

    srt_path = settings.CAPTIONS_DIR / f"{run_id}.srt"
    ass_path = settings.CAPTIONS_DIR / f"{run_id}.ass"

    write_srt(chunks, srt_path)
    write_ass(chunks, ass_path)

    logger.info(f"[CaptionAgent] Generated {len(chunks)} caption chunks.")

    return {
        **state,
        "transcript_segments": words,
        "caption_chunks": chunks,
        "srt_path": str(srt_path),
        "ass_path": str(ass_path),
        "status": "captions_done",
    }