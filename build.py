"""Inject the generated voice clips into src/game.html -> dist/index.html."""
import json, pathlib
root = pathlib.Path(__file__).parent
voice = "af_heart"
clips = json.loads((root / f"tts/audio_{voice}.json").read_text())
html = (root / "src/game.html").read_text()
assert "__CLIPS__" in html
out = html.replace("__CLIPS__", json.dumps(clips), 1)
(root / "dist").mkdir(exist_ok=True)
(root / "dist/index.html").write_text(out)
print(f"dist/index.html: {len(out)//1024} KB, {len(clips)} clips")
