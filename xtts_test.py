from TTS.api import TTS

from config import settings

device = settings.XTTS_DEVICE
if device == "auto":
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
tts.tts_to_file(
    text="Last night... I heard knocking... from inside my wall.",
    speaker_wav="assets/voices/narrator.wav",
    language="en",
    file_path="output/audio/xtts_test.wav"
)

print("DONE: output/audio/xtts_test.wav")
