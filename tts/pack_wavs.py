"""Pack a folder of <key>.wav clips into audio_<name>.json (48 kbps mono MP3 data URIs).

  uv run --with imageio-ffmpeg python3 pack_wavs.py out_adam adam

Uses the ffmpeg binary bundled with imageio-ffmpeg, so no system ffmpeg is needed.
Trims leading/trailing silence, keeping a short pad, like gen.py does for Kokoro.
"""
import base64, json, pathlib, subprocess, sys, tempfile
import imageio_ffmpeg

src, name = pathlib.Path(sys.argv[1]), sys.argv[2]
ff = imageio_ffmpeg.get_ffmpeg_exe()
here = pathlib.Path(__file__).parent
keys = json.load(open(here / "clips.json"))
trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse")
result, missing = {}, []
with tempfile.TemporaryDirectory() as tmp:
    for k in keys:
        wav = src / f"{k}.wav"
        if not wav.exists():
            missing.append(k); continue
        mp3 = pathlib.Path(tmp) / f"{k}.mp3"
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(wav), "-af", trim,
                        "-ac", "1", "-b:a", "48k", str(mp3)], check=True)
        result[k] = "data:audio/mpeg;base64," + base64.b64encode(mp3.read_bytes()).decode()
(here / f"audio_{name}.json").write_text(json.dumps(result))
print(f"audio_{name}.json: {len(result)} clips, {sum(map(len, result.values()))//1024} KB")
if missing: print("MISSING (game will skip these silently):", ", ".join(missing))
