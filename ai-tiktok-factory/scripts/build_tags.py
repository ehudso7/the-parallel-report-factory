import subprocess
from pathlib import Path

from src.config import get_settings
from src.tts import synthesize_speech_bytes

TAGS = {
    "TAG_open":   "Broadcasting from an alternate timeline.",
    "TAG_close":  "Which timeline are we in?",
    "TAG_break":  "Developing.",
    "TAG_warn":   "Signal interference detected.",
}

OUT_DIR = Path("audio/pack_v1/tags")

def mp3_to_wav(mp3_path: str, wav_path: str):
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, "-ar", "48000", "-ac", "2", wav_path],
        check=True
    )

def main():
    s = get_settings()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, text in TAGS.items():
        audio_bytes, provider = synthesize_speech_bytes(
            eleven_api_key=s.ELEVENLABS_API_KEY,
            eleven_voice_id=s.ELEVENLABS_VOICE_ID,
            eleven_model_id=s.ELEVENLABS_MODEL_ID,
            eleven_output_format=s.ELEVENLABS_OUTPUT_FORMAT,
            openai_api_key=s.OPENAI_API_KEY,
            text=text,
        )

        mp3_path = OUT_DIR / f"{name}.mp3"
        wav_path = OUT_DIR / f"{name}.wav"

        with open(mp3_path, "wb") as f:
            f.write(audio_bytes)

        mp3_to_wav(str(mp3_path), str(wav_path))
        print(f"{name}: generated via {provider} -> {wav_path}")

    print("DONE. Tags written to audio/pack_v1/tags/*.wav")

if __name__ == "__main__":
    main()
