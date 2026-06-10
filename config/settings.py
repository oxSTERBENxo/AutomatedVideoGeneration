import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", 1080))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", 1920))
TARGET_DURATION_SEC = int(os.getenv("TARGET_DURATION_SEC", 45))

BACKGROUND_VIDEO_PATH = ROOT_DIR / os.getenv(
    "BACKGROUND_VIDEO_PATH",
    "assets/minecraft_gameplay/gameplay.mp4"
)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
XTTS_DEVICE = os.getenv("XTTS_DEVICE", "cuda").strip().lower()
CAPTION_MAX_WORDS = int(os.getenv("CAPTION_MAX_WORDS", 3))
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", 72))
CAPTION_STROKE_WIDTH = int(os.getenv("CAPTION_STROKE_WIDTH", 4))


OUTPUT_DIR = ROOT_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
CAPTIONS_DIR = OUTPUT_DIR / "captions"
VIDEOS_DIR = OUTPUT_DIR / "videos"

for folder in [AUDIO_DIR, CAPTIONS_DIR, VIDEOS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
