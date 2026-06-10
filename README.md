## Technologies and Architecture

The project is implemented in Python and follows a modular multi-agent architecture, where individual agents handle script generation, voice synthesis, caption creation, visual selection, and final video assembly.

Script generation is powered by a locally hosted Large Language Model through Ollama, allowing the system to run without relying entirely on paid cloud APIs. Voiceovers are generated using XTTS v2 (Coqui TTS), which supports voice cloning from short reference audio samples. Video processing, audio handling, subtitle rendering, and final video assembly are performed using FFmpeg and related Python tools.

The project also includes a queue-based processing system for batch video generation, allowing multiple topics to be processed automatically. Long-running generation jobs can be safely paused and resumed through a graceful shutdown mechanism.

## Running the Project

Install the dependencies and ensure Ollama and FFmpeg are available on your system.

```bash
pip install -r requirements.txt
```

Run a single video generation:

```bash
python main.py
```

Run batch processing:

```bash
python queue_runner.py
```

To stop batch processing after the current video finishes:

```powershell
New-Item stop.txt
```

To resume processing:

```powershell
Remove-Item stop.txt
python queue_runner.py
```
