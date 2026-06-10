import logging
import re
import requests

from config import settings
from agents.state import VideoState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a viral Reddit-style storyteller for TikTok, YouTube Shorts, and Reels.

You write highly believable first-person stories inspired by:
- r/AmITheAsshole
- r/Confession
- r/TrueOffMyChest
- r/LetsNotMeet
- r/RelationshipAdvice

The stories should feel like real people casually telling strange, awkward, emotional, creepy, dramatic, or suspicious experiences online.

The writing MUST sound human.

It should feel like:
- a Reddit post
- a voice message to a friend
- someone casually explaining what happened
- a story retold for TikTok

NOT like:
- a novel
- a screenplay
- a movie trailer
- AI-generated horror prose

Do NOT:
- use markdown
- use bold
- put titles inside the story parts
- explain the story
- use flowery descriptions
- use poetic language
- overdescribe emotions
- sound cinematic
- sound philosophical

Avoid phrases like:
- little did I know
- my blood ran cold
- an eerie feeling
- nightmare
- haunting
- it changed my life forever
- I felt a chill down my spine

The hook is the most important part.

The first 1-2 sentences must instantly create curiosity, tension, suspicion, awkwardness, danger, or drama.

Style:
- short paragraphs
- modern casual English
- believable dialogue
- realistic details
- internet storytelling vibe
- TikTok pacing
- cliffhanger ending

Return only the requested title and narration fields.
"""


def call_ollama(prompt: str) -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.75,
            "num_predict": 2600
        }
    }

    response = requests.post(settings.OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()


def clean_script(text: str) -> str:
    text = text.strip()

    text = re.sub(r"(?i)^script:\s*", "", text)
    text = text.replace("HOOK:", "")
    text = text.replace("BODY:", "")
    text = text.replace("OUTRO:", "")

    text = text.replace("**", "")
    text = text.replace("*", "")

    text = re.sub(r"(?i)this opening is designed.*", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)the suspense builds.*", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"(?i)^title:\s*", "", title)
    title = title.replace("**", "").replace("*", "")
    title = title.strip(" \t\r\n\"'")
    title = re.sub(r"\s+", " ", title)
    return title


def split_title_and_story(script: str, topic: str = ""):
    match = re.search(r"(?im)^\s*TITLE\s*:\s*(.+?)\s*$", script)

    if match:
        title = clean_title(match.group(1))
        story = script[:match.start()] + script[match.end():]
        return title, story.strip()

    topic_title = clean_title(topic)

    if topic_title:
        return topic_title, script

    first_sentence = re.split(r"(?<=[.!?])\s+", script.strip(), maxsplit=1)[0]
    return clean_title(first_sentence), script


def split_story_parts(script: str):
    parts = re.split(r"(?i)\bPART\s*\d+\s*:", script)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]

    # fallback if model does not follow format
    words = script.split()
    third = max(1, len(words) // 3)

    part1 = " ".join(words[:third])
    part2 = " ".join(words[third:third * 2])
    part3 = " ".join(words[third * 2:])

    return part1, part2, part3

def detect_narrator_gender(script: str) -> str:
    text = script.lower()

    female_patterns = [
        "my boyfriend",
        "my husband",
        "his mom",
        "his girlfriend",
        "my ex boyfriend",
        "my ex-husband",
    ]

    male_patterns = [
        "my girlfriend",
        "my wife",
        "her boyfriend",
        "her husband",
        "my ex girlfriend",
        "my ex-wife",
    ]

    female_score = sum(p in text for p in female_patterns)
    male_score = sum(p in text for p in male_patterns)

    if female_score > male_score:
        return "female"

    return "male"

def run(state: VideoState) -> VideoState:
    topic = state.get("topic", "")

    user_prompt = f"""
{SYSTEM_PROMPT}

Topic: {topic}

Write a 3-part first-person Reddit-style story series.

STRICT OUTPUT FORMAT:

TITLE:
[short Reddit-style title for the story]

PART 1:
[story text only]

PART 2:
[story text only]

PART 3:
[story text only]

Rules:
- Do not use markdown.
- Do not use bold.
- Only write one title in the TITLE field.
- The title must match the actual story.
- If the topic is already a good Reddit-style title, use it.
- Do not explain your writing.
- Do not include analysis.
- Do not include "This opening is designed".
- Do not include "To be continued".
- Do not write labels such as "Cliffhanger" or "Ending"; the narration must contain only the story.
- Each part must be 350-500 words.
- Each part must end on an unresolved story moment that makes the viewer want the next part.
- PART 1 must start with the strongest possible hook.
- The story does not have to be horror.
- It can be creepy, dramatic, suspicious, emotional, or socially awkward.
- Make it sound like a real Reddit story someone would comment on.
- Do not rush the story.
- Slowly build tension and details before reveals.
- Include realistic conversations.
- Include small awkward details.
- Include pauses, uncertainty, and reactions.
- Let scenes play out naturally before reveals.
- Do not summarize important moments.
- Write moment-by-moment instead of summarizing events.
- Do not end parts too quickly.
"""

    logger.info(f"[ScriptAgent] Generating script with Ollama model={settings.OLLAMA_MODEL}")

    raw = call_ollama(user_prompt)
    script = clean_script(raw)
    story_title, script = split_title_and_story(script, topic)

    part1, part2, part3 = split_story_parts(script)

    print("\n========== GENERATED STORY ==========\n")
    print(script)
    print("\n========== PART 1 ==========\n")
    print(part1)
    print("\n========== PART 2 ==========\n")
    print(part2)
    print("\n========== PART 3 ==========\n")
    print(part3)
    print("\n=====================================\n")

    word_count = len(script.split())
    estimated_duration = round(word_count / 2.5, 1)

    return {
        **state,
        "script_raw": script,
        "story_title": story_title,
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "script_hook": part1.split("\n")[0] if part1 else "",
        "script_body": part2,
        "script_outro": part3,
        "estimated_duration_sec": estimated_duration,
        "status": "scripted",
        "narrator_gender": detect_narrator_gender(script),
    }
