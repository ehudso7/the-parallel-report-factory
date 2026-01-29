# AI TikTok Factory (Parallel Timeline News)

Generates a TikTok-ready vertical MP4 daily:
1) Writes a short fictional "alternate timeline news" script (OpenAI)
2) Generates an anchor image (OpenAI)
3) Generates narration (ElevenLabs primary; OpenAI fallback)
4) Animates a talking-head video (Hedra Character-3)
5) Mixes brand audio (theme + SFX + spoken tags + ducking + loudnorm)
6) Saves outputs to `/out` and uploads GitHub Actions artifacts

## Setup

### Required Secrets / Env Vars
- OPENAI_API_KEY
- HEDRA_API_KEY
- ELEVENLABS_API_KEY (primary TTS)

Optional:
- ELEVENLABS_VOICE_ID (if unset, first available voice is auto-selected and cached)

### Local Run
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="..."
export HEDRA_API_KEY="..."
export ELEVENLABS_API_KEY="..."
# optional:
export ELEVENLABS_VOICE_ID="..."

# 1) Generate tag WAV files:
python scripts/build_tags.py

# 2) Ensure you placed audio pack WAVs:
# audio/pack_v1/music/{MUS_logo_01.wav,MUS_intro_01.wav,MUS_bed_loop_01.wav,MUS_outro_01.wav}
# audio/pack_v1/sfx/{SFX_whoosh_short_01.wav,SFX_hit_hard_01.wav}

# 3) Run:
python scripts/run_once.py
```
