from pydantic import BaseModel
import os


class Settings(BaseModel):
    # OpenAI (fallback + script + image)
    OPENAI_API_KEY: str | None = None

    # Hedra
    HEDRA_API_KEY: str
    HEDRA_BASE_URL: str = "https://api.hedra.com/web-app/public"

    # ElevenLabs (primary)
    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_VOICE_ID: str | None = None
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    ELEVENLABS_OUTPUT_FORMAT: str = "mp3_44100_128"

    # Output
    OUT_DIR: str = "out"
    VIDEO_DURATION_MS: int = 15000
    ASPECT_RATIO: str = "9:16"
    RESOLUTION: str = "720p"


def get_settings() -> Settings:
    # Hedra required
    if not os.getenv("HEDRA_API_KEY"):
        raise RuntimeError("Missing env var: HEDRA_API_KEY")

    # In practice we need OpenAI for script+image, so fail loud if missing.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Missing env var: OPENAI_API_KEY (required for script + image).")

    # At least one TTS provider must exist
    if not os.getenv("ELEVENLABS_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Missing TTS creds: set ELEVENLABS_API_KEY (primary) and/or OPENAI_API_KEY (fallback).")

    return Settings(
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        HEDRA_API_KEY=os.environ["HEDRA_API_KEY"],
        HEDRA_BASE_URL=os.getenv("HEDRA_BASE_URL", "https://api.hedra.com/web-app/public"),

        ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY"),
        ELEVENLABS_VOICE_ID=os.getenv("ELEVENLABS_VOICE_ID"),
        ELEVENLABS_MODEL_ID=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        ELEVENLABS_OUTPUT_FORMAT=os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),

        OUT_DIR=os.getenv("OUT_DIR", "out"),
        VIDEO_DURATION_MS=int(os.getenv("VIDEO_DURATION_MS", "15000")),
        ASPECT_RATIO=os.getenv("ASPECT_RATIO", "9:16"),
        RESOLUTION=os.getenv("RESOLUTION", "720p"),
    )
