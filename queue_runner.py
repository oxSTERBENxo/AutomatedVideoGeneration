import time
from pathlib import Path

from pipeline import run_pipeline

QUEUE_FILE = Path("queue.txt")
DONE_FILE = Path("queue_done.txt")
FAILED_FILE = Path("queue_failed.txt")
STOP_FILE = Path("stop.txt")


def load_queue():
    if not QUEUE_FILE.exists():
        return []

    lines = QUEUE_FILE.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def save_queue(items):
    QUEUE_FILE.write_text("\n".join(items), encoding="utf-8")


def append_line(path: Path, text: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def stop_requested():
    return STOP_FILE.exists()


def main():
    print("Queue runner started.")
    print("To stop after the current story finishes, create a file named stop.txt")
    print("To continue later, delete stop.txt and run this again.\n")

    while True:
        queue = load_queue()

        if not queue:
            print("Queue empty. Done.")
            break

        if stop_requested():
            print("Stop requested. No new story will start.")
            break

        topic = queue[0]
        print(f"\n===== STARTING: {topic} =====\n")

        try:
            state = run_pipeline(topic=topic)

            if state.get("error"):
                raise RuntimeError(state["error"])

            append_line(DONE_FILE, topic)
            print(f"\n===== DONE: {topic} =====\n")

            # Remove only after successful full story render
            queue = load_queue()
            if queue and queue[0] == topic:
                save_queue(queue[1:])

        except Exception as e:
            append_line(FAILED_FILE, f"{topic} | ERROR: {e}")
            print(f"\n===== FAILED: {topic} =====")
            print(e)

            # Remove failed item too, so queue doesn't get stuck forever
            queue = load_queue()
            if queue and queue[0] == topic:
                save_queue(queue[1:])

        if stop_requested():
            print("Stop requested. Finished current story, stopping now.")
            break

        time.sleep(2)


if __name__ == "__main__":
    main()