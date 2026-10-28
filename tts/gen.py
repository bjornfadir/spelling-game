import json, re, subprocess, sys, os, base64
import numpy as np, onnxruntime as rt, scipy.io.wavfile as wavfile

D = os.path.dirname(os.path.abspath(__file__))
import shutil
ESP = os.environ.get("ESPEAK_NG") or (os.path.join(D, "esp/bin/espeak-ng") if os.path.exists(os.path.join(D, "esp/bin/espeak-ng")) else shutil.which("espeak-ng"))
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
LANG = "en-us" if VOICE.startswith("a") else "en-gb"
vocab = json.load(open(os.path.join(D, "kokoro-onnx/src/kokoro_onnx/config.json")))["vocab"]
voices = np.load(os.path.join(D, "voices.bin"))
sess = rt.InferenceSession(os.path.join(D, "kokoro.onnx"), providers=["CPUExecutionProvider"])
in_names = {i.name: i.type for i in sess.get_inputs()}
tok_name = "input_ids" if "input_ids" in in_names else "tokens"
speed_int = "int" in in_names["speed"]

def ipa(text):
    # phonemize each clause with espeak, keep punctuation between clauses
    out = []
    for part in re.findall(r"[^.,!?]+|[.,!?]", text):
        if part in ".,!?":
            out.append(part); continue
        if not part.strip(): continue
        p = subprocess.run([ESP, "-q", "--ipa", "-v", LANG, part.strip()], capture_output=True, text=True).stdout
        out.append(" " + " ".join(p.split()))
    s = "".join(out).strip()
    return "".join(c for c in s if c in vocab)

def synth(text, speed=0.85):
    ph = ipa(text)
    toks = [vocab[c] for c in ph]
    style = voices[VOICE][len(toks)]
    feed = {tok_name: np.array([[0, *toks, 0]], dtype=np.int64),
            "style": np.asarray(style, dtype=np.float32).reshape(1, -1),
            "speed": np.array([1 if speed_int else speed], dtype=np.int32 if speed_int else np.float32)}
    audio = sess.run(None, feed)[0].squeeze()
    # trim leading/trailing near-silence, keep a short pad
    idx = np.where(np.abs(audio) > 0.01)[0]
    if len(idx): audio = audio[max(0, idx[0]-1200): idx[-1]+2400]
    return ph, audio

clips = json.load(open(os.path.join(D, "clips.json")))
outdir = os.path.join(D, "out_" + VOICE); os.makedirs(outdir, exist_ok=True)
result = {}
for key, (text, speed) in clips.items():
    ph, a = synth(text, speed)
    wav = os.path.join(outdir, key + ".wav"); mp3 = os.path.join(outdir, key + ".mp3")
    wavfile.write(wav, 24000, (np.clip(a, -1, 1) * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "48k", mp3], check=True)
    result[key] = "data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode()
    print(f"{key:14s} {len(a)/24000:4.1f}s  {ph}")
json.dump(result, open(os.path.join(D, f"audio_{VOICE}.json"), "w"))
print("total KB", sum(len(v) for v in result.values()) // 1024)
