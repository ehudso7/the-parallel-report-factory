import os
import json
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

ELEVEN_BASE = "https://api.elevenlabs.io/v1"

class TTSError(RuntimeError):
    pass

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=12))
def _eleven_list_voices(api_key: str) -> dict:
    r = requests.get(
        f"{ELEVEN_BASE}/voices",
        headers={"xi-api-key": api_key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def _cache_path() -> str:
    return os.path.join(".cache", "eleven_voice.json")

def resolve_eleven_voice_id(api_key: str, preferred_voice_id: str | None) -> str:
    if preferred_voice_id:
        return preferred_voice_id

    os.makedirs(".cache", exist_ok=True)

    cp = _cache_path()
    if os.path.exists(cp):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("voice_id"):
                return data["voice_id"]
        except Exception:
            pass

    voices = _eleven_list_voices(api_key)
    vlist = voices.get("voices") or []
    if not vlist:
        raise TTSError("ElevenLabs returned no voices for this account/key.")

    voice_id = vlist[0].get("voice_id") or vlist[0].get("id")
    if not voice_id:
        raise TTSError(f"Could not parse voice_id from ElevenLabs voices response: {vlist[0]}")

    with open(cp, "w", encoding="utf-8") as f:
        json.dump({"voice_id": voice_id, "note": "Auto-selected first available voice."}, f)

    return voice_id

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def eleven_tts_to_bytes(
    *,
    api_key: str,
    voice_id: str,
    text: str,
    model_id: str,
    output_format: str,
) -> bytes:
    url = f"{ELEVEN_BASE}/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.7,
            "style": 0.1,
            "use_speaker_boost": True,
        },
    }

    r = requests.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        params={"output_format": output_format},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.content

def openai_tts_to_bytes(*, openai_api_key: str, text: str, voice: str = "alloy") -> bytes:
    client = OpenAI(api_key=openai_api_key)
    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        format="mp3",
        input=text,
    )
    return audio.read()

def synthesize_speech_bytes(
    *,
    eleven_api_key: str | None,
    eleven_voice_id: str | None,
    eleven_model_id: str,
    eleven_output_format: str,
    openai_api_key: str | None,
    text: str,
) -> tuple[bytes, str]:
    if eleven_api_key:
        try:
            vid = resolve_eleven_voice_id(eleven_api_key, eleven_voice_id)
            b = eleven_tts_to_bytes(
                api_key=eleven_api_key,
                voice_id=vid,
                text=text,
                model_id=eleven_model_id,
                output_format=eleven_output_format,
            )
            return b, "elevenlabs"
        except Exception as e:
            last_err = str(e)
    else:
        last_err = "ELEVENLABS_API_KEY not set"

    if openai_api_key:
        try:
            b = openai_tts_to_bytes(openai_api_key=openai_api_key, text=text)
            return b, "openai_fallback"
        except Exception as e:
            raise TTSError(f"Both TTS providers failed. ElevenLabs error: {last_err}. OpenAI error: {e}") from e

    raise TTSError(f"TTS failed: ElevenLabs error: {last_err}. OpenAI fallback not configured.")
