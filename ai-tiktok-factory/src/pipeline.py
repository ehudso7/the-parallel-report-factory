import os
from datetime import datetime
from src.config import get_settings
from src.openai_gen import generate_script, generate_anchor_image
from src.tts import synthesize_speech_bytes
from src.hedra_client import HedraClient
from src.audio_mix import mix_audio_ffmpeg, mux_audio_video_ffmpeg

def run(topic_hint: str = "BREAKING: a timeline where AI runs city hall"):
    s = get_settings()
    os.makedirs(s.OUT_DIR, exist_ok=True)

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    script_path = os.path.join(s.OUT_DIR, f"script_{stamp}.txt")
    image_path = os.path.join(s.OUT_DIR, f"anchor_{stamp}.png")

    voice_mp3_path = os.path.join(s.OUT_DIR, f"voice_{stamp}.mp3")

    raw_video_path = os.path.join(s.OUT_DIR, f"video_raw_{stamp}.mp4")
    mix_audio_path = os.path.join(s.OUT_DIR, f"audio_mix_{stamp}.wav")
    final_video_path = os.path.join(s.OUT_DIR, f"video_final_{stamp}.mp4")

    # 1) Script
    script = generate_script(s.OPENAI_API_KEY, topic_hint)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    # 2) Anchor image
    img_prompt = (
        "Photorealistic news anchor portrait, front-facing, neutral expression, "
        "modern newsroom background, soft key light, high detail, 9:16 framing, "
        "looks like a real TV segment, no text on screen."
    )
    generate_anchor_image(s.OPENAI_API_KEY, img_prompt, image_path)

    # 3) Voice (ElevenLabs primary, OpenAI fallback)
    voice_bytes, provider = synthesize_speech_bytes(
        eleven_api_key=s.ELEVENLABS_API_KEY,
        eleven_voice_id=s.ELEVENLABS_VOICE_ID,
        eleven_model_id=s.ELEVENLABS_MODEL_ID,
        eleven_output_format=s.ELEVENLABS_OUTPUT_FORMAT,
        openai_api_key=s.OPENAI_API_KEY,
        text=script,
    )
    with open(voice_mp3_path, "wb") as f:
        f.write(voice_bytes)

    # 4) Hedra: upload assets + generate raw talking video
    hedra = HedraClient(api_key=s.HEDRA_API_KEY, base_url=s.HEDRA_BASE_URL)
    model_id = hedra.pick_model_id(["character-3", "hedra character-3"])

    img_asset = hedra.create_asset(name=os.path.basename(image_path), asset_type="image")
    aud_asset = hedra.create_asset(name=os.path.basename(voice_mp3_path), asset_type="audio")

    hedra.upload_asset(img_asset["id"], image_path)
    hedra.upload_asset(aud_asset["id"], voice_mp3_path)

    gen = hedra.generate_video(
        ai_model_id=model_id,
        start_keyframe_id=img_asset["id"],
        audio_id=aud_asset["id"],
        duration_ms=s.VIDEO_DURATION_MS,
        aspect_ratio=s.ASPECT_RATIO,
        resolution=s.RESOLUTION,
    )

    gen_id = gen["id"]
    url = hedra.wait_for_video_url(gen_id)
    hedra.download_file(url, raw_video_path)

    # 5) Mix theme + sfx + tags + loudness normalization
    duration_sec = s.VIDEO_DURATION_MS / 1000.0
    mix_audio_ffmpeg(
        voice_path=voice_mp3_path,
        out_audio_path=mix_audio_path,
        duration_sec=duration_sec
    )

    # 6) Mux final audio into video
    mux_audio_video_ffmpeg(
        video_in=raw_video_path,
        audio_in=mix_audio_path,
        video_out=final_video_path
    )

    return {
        "script_path": script_path,
        "image_path": image_path,
        "voice_mp3_path": voice_mp3_path,
        "raw_video_path": raw_video_path,
        "final_video_path": final_video_path,
        "generation_id": gen_id,
        "video_url": url,
        "tts_provider": provider,
    }
