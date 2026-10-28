"""Render clips.json with Adam's self-hosted VoiceStudio -> out_<name>/<key>.wav

Runs ON odin-cloud (the API listens on 127.0.0.1:3900 and the API key stays in
~/voicestudio-local/.env there; never copy it off the box). Stdlib only.
Resumable: clips that already have a .wav are skipped, so it can be re-run after
a crash, or after deleting single .wav files to re-render them.

  python3 gen_voicestudio.py clips.json out_pocket --engine pockettts --letters-as-caps
  python3 gen_voicestudio.py clips.json out_adam --engine voxcpm2 --profile c05a9ebc --seed 7

PocketTTS with no profile uses its built-in English voice "alba" and renders in
roughly real time on odin-cloud. VoxCPM2 with a cloned profile is ~50x slower.

Then copy out_adam/ back and run pack_wavs.py to make audio_<name>.json.
"""
import argparse, json, os, pathlib, time, urllib.request, uuid

ap = argparse.ArgumentParser()
ap.add_argument("clips"); ap.add_argument("outdir")
ap.add_argument("--profile", help="voice profile id, e.g. c05a9ebc = Adam (voiceover); omit for the engine's preset voice")
ap.add_argument("--engine", default="pockettts")
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--cfg", type=float, default=2.5)
ap.add_argument("--only", help="comma-separated clip keys to render")
ap.add_argument("--letters-as-caps", action="store_true",
                help="speak l_<x> clips as the capital letter (\"B.\") instead of the phonetic spelling tuned for Kokoro")
ap.add_argument("--api", default="http://127.0.0.1:3900")
a = ap.parse_args()

env = pathlib.Path("~/voicestudio-local/.env").expanduser().read_text()
key = next(l.split("=", 1)[1].strip() for l in env.splitlines() if l.startswith("OMNIVOICE_API_KEY="))

def generate(text, speed):
    fields = {"text": text, "engine": a.engine, "seed": str(a.seed),
              "guidance_scale": str(a.cfg), "language": "English", "speed": str(speed)}
    if a.profile: fields["profile_id"] = a.profile
    b = uuid.uuid4().hex
    body = "".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n' for k, v in fields.items())
    body = (body + f"--{b}--\r\n").encode()
    req = urllib.request.Request(a.api + "/generate", body, {
        "Authorization": "Bearer " + key, "Content-Type": "multipart/form-data; boundary=" + b})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return r.read()

clips = json.load(open(a.clips))
only = set(a.only.split(",")) if a.only else None
out = pathlib.Path(a.outdir); out.mkdir(exist_ok=True)
todo = [k for k in clips if (not only or k in only) and not (out / f"{k}.wav").exists()]
print(f"{len(todo)} to render", flush=True)
for n, k in enumerate(todo, 1):
    text, speed = clips[k]
    if a.letters_as_caps and k.startswith("l_"): text = k[2:].upper() + "."
    # Kokoro needed slowed speech (0.8-0.9); VoxCPM2 sounds natural at 1.0
    t = time.time(); wav = generate(text, 1.0)
    (out / f"{k}.wav.part").write_bytes(wav); os.replace(out / f"{k}.wav.part", out / f"{k}.wav")
    print(f"[{n}/{len(todo)}] {k:12s} {time.time()-t:5.0f}s  {text}", flush=True)
