import subprocess
from pathlib import Path

def mix_audio_ffmpeg(
    *,
    voice_path: str,
    out_audio_path: str,
    pack_dir: str = "audio/pack_v1",
    duration_sec: float = 15.0,
):
    pack = Path(pack_dir)
    mus = pack / "music"
    sfx = pack / "sfx"
    tags = pack / "tags"

    logo  = str(mus / "MUS_logo_01.wav")
    intro = str(mus / "MUS_intro_01.wav")
    bed   = str(mus / "MUS_bed_loop_01.wav")
    outro = str(mus / "MUS_outro_01.wav")

    whoosh = str(sfx / "SFX_whoosh_short_01.wav")
    hit    = str(sfx / "SFX_hit_hard_01.wav")

    tag_open  = str(tags / "TAG_open.wav")
    tag_close = str(tags / "TAG_close.wav")

    bed_vol = 0.16
    logo_vol = 0.80
    intro_vol = 0.55
    outro_vol = 0.55
    whoosh_vol = 0.55
    hit_vol = 0.60
    tag_vol = 1.00

    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-i", logo,
        "-i", intro,
        "-i", bed,
        "-i", outro,
        "-i", whoosh,
        "-i", hit,
        "-i", tag_open,
        "-i", tag_close,
        "-filter_complex",
        f"""
        [0:a]atrim=0:{duration_sec},asetpts=N/SR/TB,volume=1.00[voice];

        [1:a]atrim=0:{duration_sec},asetpts=N/SR/TB,volume={logo_vol}[logo];
        [2:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=800|800,volume={intro_vol}[intro];
        [3:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=800|800,volume={bed_vol}[bed];

        [4:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=14200|14200,volume={outro_vol}[outro];

        [5:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=2000|2000,volume={whoosh_vol}[whoosh];
        [6:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=7500|7500,volume={hit_vol}[hit];

        # Spoken tags:
        [7:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=800|800,volume={tag_vol}[tagopen];
        [8:a]atrim=0:{duration_sec},asetpts=N/SR/TB,adelay=13800|13800,volume={tag_vol}[tagclose];

        # Duck the bed under voice+tags (sidechain)
        [bed][voice]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=250[bedduck1];
        [bedduck1][tagopen]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=250[bedduck2];
        [bedduck2][tagclose]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=250[bedduck];

        # Mix everything
        [voice][logo][intro][bedduck][outro][whoosh][hit][tagopen][tagclose]amix=inputs=9:normalize=0[mix];

        # Normalize loudness for social
        [mix]loudnorm=I=-14:TP=-1.0:LRA=11[out]
        """.strip(),
        "-map", "[out]",
        "-ac", "2",
        "-ar", "48000",
        out_audio_path
    ]
    subprocess.run(cmd, check=True)

def mux_audio_video_ffmpeg(*, video_in: str, audio_in: str, video_out: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_in,
        "-i", audio_in,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        video_out
    ]
    subprocess.run(cmd, check=True)
