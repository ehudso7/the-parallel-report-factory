import base64
from openai import OpenAI


def build_script(topic_hint: str) -> str:
    return f"""
You are writing a TikTok script as a fictional news anchor from an alternate timeline.

Topic hint: {topic_hint}

Rules:
- 15 seconds spoken max (about 35-45 words).
- Punchy, vivid, no filler.
- Ends with a question that sparks comments.
- No hate, no harassment, no real-person defamation.

Return ONLY the script text.
""".strip()


def generate_script(openai_api_key: str, topic_hint: str) -> str:
    client = OpenAI(api_key=openai_api_key)
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=build_script(topic_hint),
    )
    return resp.output_text.strip()


def generate_anchor_image(openai_api_key: str, prompt: str, out_path: str) -> None:
    client = OpenAI(api_key=openai_api_key)
    img = client.images.generate(
        model="gpt-image-1-mini",
        prompt=prompt,
        size="1024x1536",
        quality="low",
    )
    b64 = img.data[0].b64_json
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
