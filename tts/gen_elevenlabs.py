"""Render clips.json with ElevenLabs -> tts/audio_<name>.json (MP3 data URIs, ready for build.py)

  python3 gen_elevenlabs.py <voice_id> <name> [--only w_beak,l_a] [--speed 0.9]
  python3 ../build.py <name>

The API key comes from $ELEVENLABS_API_KEY or ~/.config/elevenlabs/api_key (chmod 600,
outside the repo; never commit it). The current key is restricted to text-to-speech,
so it cannot list voices or read the quota: pick voice ids from the ElevenLabs voice library.
Each clip is cached as out_el_<name>/<key>.mp3, so re-runs only spend characters on
clips that are missing (delete one .mp3 to re-render it). The whole list is ~1,400 characters.
Stdlib only, no ffmpeg needed: ElevenLabs returns MP3 directly.
"""
import argparse, base64, json, os, pathlib, time, urllib.error, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("voice_id"); ap.add_argument("name")
ap.add_argument("--model", default="eleven_multilingual_v2")
ap.add_argument("--speed", type=float, default=0.9, help="0.7-1.2; a little slower helps a young second-language learner")
ap.add_argument("--only", help="comma-separated clip keys to render (for auditioning voices)")
a = ap.parse_args()

key = os.environ.get("ELEVENLABS_API_KEY") or pathlib.Path("~/.config/elevenlabs/api_key").expanduser().read_text().strip()
here = pathlib.Path(__file__).parent
clips = json.load(open(here / "clips.json"))
out = here / f"out_el_{a.name}"; out.mkdir(exist_ok=True)

def tts(text):
    body = json.dumps({"text": text, "model_id": a.model,
                       "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "speed": a.speed}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{a.voice_id}?output_format=mp3_44100_64", body,
        {"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code == 429 and attempt < 2: time.sleep(5); continue
            raise SystemExit(f"ElevenLabs {e.code}: {msg}")

only = set(a.only.split(",")) if a.only else None
for k, (text, _speed) in clips.items():
    if only and k not in only: continue
    mp3 = out / f"{k}.mp3"
    if mp3.exists(): continue
    # Letter names: the capital letter reads as its name ("B."); Kokoro's phonetic spellings ("bee") don't help here
    if k.startswith("l_"): text = k[2:].upper() + "."
    mp3.write_bytes(tts(text)); print(f"{k:12s} {text}", flush=True)

if not only:
    missing = [k for k in clips if not (out / f"{k}.mp3").exists()]
    if missing: raise SystemExit("missing: " + ", ".join(missing))
    result = {k: "data:audio/mpeg;base64," + base64.b64encode((out / f"{k}.mp3").read_bytes()).decode() for k in clips}
    (here / f"audio_{a.name}.json").write_text(json.dumps(result))
    print(f"audio_{a.name}.json: {len(result)} clips, {sum(map(len, result.values()))//1024} KB")
