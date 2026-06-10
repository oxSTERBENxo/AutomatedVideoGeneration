import argparse
import logging
import sys

from pipeline import run_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--topic",
        "-t",
        default="",
        help="Story topic"
    )

    args = parser.parse_args()

    print("\n🎬 VIDEO FACTORY STARTING...\n")

    try:
        result = run_pipeline(args.topic)

    except Exception as e:
        logging.exception("Pipeline crashed")
        return 1

    print("\n──────── RESULT ────────\n")

    for k, v in result.items():
        if k not in ["script_raw", "caption_chunks", "transcript_segments"]:
            print(f"{k}: {v}")

    if result.get("final_video_path"):
        print("\n✅ FINAL VIDEO CREATED:")
        print(result["final_video_path"])

    if result.get("error"):
        print("\n❌ ERROR:")
        print(result["error"])

    return 0


if __name__ == "__main__":
    sys.exit(main())