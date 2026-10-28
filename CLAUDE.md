# Long ee & ea Quest — spelling game (handoff)

A browser spelling game Adam built for his daughter (9, in Israel; English is a second language) to learn the 10 words on her spelling test. This file is the handoff so Claude Code can continue the project.

Live version (claude.ai artifact, private to Adam): https://claude.ai/artifact/HMZuhNj75BjmPoLAujcqki

## The words

All 10 words have the long **e** sound, split into two spelling teams:

| ee team | ea team |
|---|---|
| feet, deep, sleep, week, bleed | beak, east, steam, seal, peas |

Each word has an emoji, an example sentence and a memory trick. They live in the `WORDS` array in `src/game.html`.

## Files

```
spelling-game/
  CLAUDE.md            this file
  src/game.html        the game source (edit this). Holds a __CLIPS__ placeholder for the audio
  build.py             puts tts/audio_af_heart.json into the placeholder and writes dist/index.html
  dist/index.html      the built, self-contained game (~884 KB, audio embedded). Don't edit by hand
  tts/mkclips.py       defines every spoken line -> tts/clips.json
  tts/clips.json       clip key -> [text, speed]
  tts/gen.py           renders clips.json with Kokoro TTS -> tts/audio_<voice>.json (base64 MP3 data URIs)
  tts/audio_af_heart.json   the current 60 generated clips
```

`src/game.html` carries its own doctype, charset and viewport tags so it also works on hosts other than claude.ai.

Workflow: edit `src/game.html`, then run `python3 build.py`, then open `dist/index.html` in a browser. The game is a single self-contained file with no server and no network access needed. Fonts (Baloo 2, Andika) come from Google Fonts and fall back to system fonts when offline.

## How the game works

Plain HTML, CSS and vanilla JS in one file. No framework and no build step beyond `build.py`.

**Modes** (tabs at the top):
1. **📖 Learn** — the main teaching flow. A start screen shows the ee team and ea team with a ✅ for each learned word. Each word then goes through 4 steps (`lesson(i, step)`):
   1. Look — big word with the vowel pair coloured, the sentence and the memory trick, read aloud.
   2. Spell — letter boxes light up one at a time as each letter name is spoken (`l_<letter>` clips).
   3. Cover & write — the word is hidden and she types it from memory.
   4. Check — her letters are compared with the word's, marked green or red. A correct answer marks the word learned (`localStorage` key `ee-learned`) and earns a star. A wrong one offers "Look again" or "Try writing again".
2. **🔤 ee or ea?** — "f _ _ t": pick ee or ea.
3. **🧩 Unscramble** — tap jumbled letter tiles in order (with Undo).
4. **✏️ Spelling Test** — hear the word and type it. Wrong letters are highlighted.

Rounds are the 10 words shuffled, with a progress bar. The end screen shows the score, the missed words to practise, and a button to the next mode (ee/ea → unscramble → test). Stars are saved in `localStorage` key `ee-stars`, with +5 for a perfect round.

**Design:** teal (`--sea`) marks the ee team and yellow (`--sun`) marks the ea team, consistently everywhere. Yellow text is too faint on white (2:1), so ea-team *text* uses `--sun-ink` (dark amber); `--sun` stays for fills and borders. Text on teal uses `--on-sea`. Light and dark themes are defined through CSS tokens on `:root`. Layout is tablet- and phone-first with big tap targets. Andika is used for the letters because it was designed for early readers.

## Audio / voice

Audio is **pre-generated**, not live TTS. This is because:
- The claude.ai artifact sandbox blocks network calls to other hosts, so a live TTS API can't be called from the page.
- Browser `speechSynthesis` sounded poor and differed between devices.

Clips were made with **Kokoro v1.0** (ONNX), voice **`af_heart`** (US English, female, its best-rated voice), at speeds 0.8–0.9. Phonemes come from **espeak-ng** (`--ipa`, `en-us`). The clips are encoded as 48 kbps mono MP3 and embedded as data URIs in `<script type="application/json" id="clips">`.

Clip keys (from `mkclips.py`):
- `w_<word>` — the word; `s_<word>` — its sentence; `t_<word>` — its memory trick read aloud
- `l_a, l_b, l_d, l_e, l_f, l_k, l_l, l_m, l_p, l_s, l_t, l_w` — letter names (only the letters these words use)
- `intro`, `p0`–`p3` (praise), `perfect`, `almost`, `done10`, `score0`–`score9`

All audio goes through one shared `<audio>` element (iOS blocks fresh `Audio()` objects played outside a tap). Every screen change calls `hush()`, which stops speech and cancels delayed auto-play queued with `later()`. In JS, `say(key | [keys])` plays clips in order, and `sayChain(keys, onEach(i), done)` adds a callback per clip (used to light up letters). A new call cancels the one already playing. A missing key is skipped silently.

### Regenerating audio (e.g. new words or a different voice)

`gen.py` deliberately avoids the `kokoro-onnx` package's phonemizer dependency. It only needs `numpy`, `onnxruntime`, `scipy`, `ffmpeg` and an `espeak-ng` binary. Put these next to `gen.py` in `tts/`:
- `kokoro.onnx` and `voices.bin` from https://github.com/thewh1teagle/kokoro-onnx/releases (tag `model-files-v1.0`: `kokoro-v1.0.onnx`, `voices-v1.0.bin`)
- the vocab file: `git clone --depth 1 https://github.com/thewh1teagle/kokoro-onnx` (it reads `kokoro-onnx/src/kokoro_onnx/config.json`)
- espeak-ng: `apt install espeak-ng` / `brew install espeak-ng`, or set `ESPEAK_NG=/path/to/espeak-ng`

Then run:
```
cd tts && python3 mkclips.py && python3 gen.py af_heart && cd .. && python3 build.py
```
`gen.py` prints the IPA for every clip, so check it for mispronunciations. Letter names are written phonetically in `mkclips.py` (for example `"f": "ef"`, `"a": "A"`), because a bare letter can be read as its sound instead of its name ("ay" came out as "eye"). Other voices: `bf_emma` / `bf_isabella` (British; `gen.py` switches espeak to `en-gb` automatically for `b*` voices), `af_bella`, and others. If you change the voice, update the filename in `build.py`.

Adam also has his own voice engine at `https://odin-cloud.tail177352.ts.net/`, on his Tailscale network. It was not reachable from the claude.ai sandbox and its API is unknown. To use it instead, have it render the same `clips.json` keys to MP3, write `tts/audio_<name>.json` in the same `{key: "data:audio/mpeg;base64,..."}` format, and point `build.py` at that file.

## Adding next week's words

1. Edit `WORDS` in `src/game.html`, giving each word `w`, `e` (emoji), `s` (sentence with `___`), `t` (trick HTML with `<u>` around the vowel pair) and `ts` (the spoken trick).
2. Mirror the same words, sentences and tricks in `tts/mkclips.py`, and add any new letters to `L`.
3. Regenerate the audio, then build.
4. The game assumes every word contains `ee` or `ea` (`vowel()`, the team columns, and the ee-or-ea mode). A list with other spelling patterns (ai/ay, oa/ow, …) needs `vowel()` and the ee/ea mode generalised to a per-week pattern pair, and the team colours relabelled.

## Ideas not done yet

- Support several word lists (one per week) with a picker, keeping progress per list.
- A parent view showing which words were missed most often across sessions.
- Spaced review: bring missed words back sooner in later rounds.
- On-screen letter keyboard for the typing steps (right now it relies on the device keyboard).
- Hebrew translations or hints for each word, if helpful.

## Constraints if it is republished as a claude.ai artifact

The page must be one self-contained HTML file: scripts only from cdnjs, jsDelivr, unpkg or the Tailwind CDN, styles only from Google Fonts, no fetch to other hosts, and no `alert` or `confirm`. Audio plays only after a tap, which the flows already guarantee. Keep the page under 16 MB.
