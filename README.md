# ASL Fingerspelling Trainer

A browser-based flashcard tool for practising **receptive fingerspelling** — reading words spelled out in the American Sign Language manual alphabet. A word appears as a sequence of handshapes; you reveal the written spelling and hear it spoken aloud, then the next word appears.

This is the **hosted / installable** build. It loads fast, works fully offline after the first visit, and can be installed to a phone or desktop home screen as a Progressive Web App (PWA).

> There is also a single-file version (everything, including audio, embedded in one `.html`) that needs no server and can be emailed. This repo is the split version, tuned for hosting on GitHub Pages.

---

## Contents

```
index.html             The app: UI, logic, and the embedded Gallaudet font
audio/                 2,094 spoken clips, one MP3 per word (audio/CAT.mp3, ...)
sw.js                  Service worker: offline caching of the app + audio
manifest.webmanifest   PWA manifest (name, icons, colours) for installability
icons/                 App icons (192, 512, maskable, apple-touch)
generate_audio.py      Script that regenerates every clip (documented pipeline)
wordlist.txt           The 2,094 words + names, one per line (input to the script)
.nojekyll              Tells GitHub Pages to serve files as-is (no Jekyll)
README.md              This file
```

---

## Features

- **2,094 words and names** across three selectable banks (1,618 words, 488 names, combined 2,094)
- **Neural speech** — each word is spoken on reveal by a modern text-to-speech voice, not the browser's robotic built-in synthesis
- **Length filter** — practise short (3–4), medium (5–6), or long (7+) words, or all
- **Adjustable pace** — the revealed answer stays up for 0.6s, 1s, or 2s before the next card
- **Audio on/off** toggle
- **No repeats** until the current pool is exhausted (shuffled-bag randomisation)
- **Aggressive preloading** — the next clip is loaded before you reveal, and the whole bank is prefetched in the background so playback never lags
- **Installable and offline** — add it to your home screen and it works with no connection

---

## Using it

- A word appears in fingerspelling handshapes.
- Press **Click, Space, or Enter** to reveal the written word — it is spoken once at the same moment.
- After the answer time, it advances automatically to a new random word.
- Press the **Right arrow** to skip the current word without revealing it.

| Control | Options | Effect |
|---|---|---|
| **Bank** | Words / Names / Both | Which pool words are drawn from |
| **Length** | All / 3–4 / 5–6 / 7+ | Filter by number of letters |
| **Answer time** | 0.6s / 1s / 2s | How long the revealed answer stays up |
| **Audio** | On / Off | Whether the word is spoken on reveal |

**Tip:** *Both* is the hardest mode — with names mixed into ordinary vocabulary you can't guess a word from its first few letters, which is much closer to real-world fingerspelling.

The small note in the bottom bar (`caching audio …`) shows the background prefetch progress; it changes to `ready offline` once every clip is cached, then disappears.

---

## Hosting on GitHub Pages

1. Put these files at the **root** of a repository (or in a `/docs` folder).
2. In the repo, go to **Settings → Pages** and set the source to your branch (root or `/docs`).
3. Open the published URL, e.g. `https://<user>.github.io/<repo>/`.

That's it — no build step. Notes:

- **All paths are relative**, so the app, its service worker, and audio all work correctly under the `/<repo>/` subpath that project sites use. Don't rewrite them to absolute paths.
- **`.nojekyll` is included.** GitHub Pages runs Jekyll by default, which ignores files and folders beginning with an underscore; this file disables that and avoids surprises.
- **HTTPS is automatic**, which is required for service workers and PWA install — both work out of the box on Pages.
- The service worker is registered from `sw.js` at the repo root, so its scope covers the whole app.

### The font is embedded on purpose

The Gallaudet handshape font is baked into `index.html` as a data URI, so there is **no external font request**. Keep it that way — don't point it at a third-party URL, which could go down, change, or block hotlinking and would silently break the handshapes. (If you'd rather not inline it, commit the `.ttf` into the repo and reference it with a *relative* path — but never an external one.)

---

## How it works

**Handshapes.** The fingerspelling is drawn with the **Gallaudet** TrueType font (David Rakowski, 1991), which maps each keyboard letter A–Z to a picture of the corresponding ASL handshape. Typing `CAT` in this font displays the handshapes for C‑A‑T.

**Speech.** The audio was generated with **Kokoro**, a modern StyleTTS2-based neural TTS model, using its `af_heart` voice. Each of the 2,094 clips is a small mono MP3 (32 kbps), silence-trimmed and loudness-matched. They live in `audio/` and are played by URL on reveal. See `generate_audio.py` to rebuild them.

**Preloading & offline.** On load, the app registers a service worker that precaches the shell (HTML, font, icons, manifest). When a word is shown, its clip is preloaded so revealing plays instantly; meanwhile a concurrency-limited background task prefetches the entire bank. The service worker serves audio **cache-first**, so once a clip has been fetched it plays instantly and works with no connection. After the prefetch finishes, the whole tool is available offline.

**Randomisation.** A "shuffled bag": the active pool is shuffled and drawn down to the end before reshuffling, so you never see the same word twice in a row and every word comes up once per cycle.

---

## Rebuilding or changing the audio

The clips are produced by `generate_audio.py`. Common changes:

- **Different voice:** `VOICE=am_michael python generate_audio.py` (delete `audio/` first, or set `FORCE=1`).
- **More/other words:** edit `wordlist.txt` (one uppercase word per line) and run the script; existing clips are skipped, so only new words are generated.
- **Different quality/size:** adjust `BITRATE` (e.g. `BITRATE=48k`).

The script's header lists the exact dependencies and where to download the Kokoro model files. It is resumable — interrupting and re-running continues where it left off.

If you change `index.html`, `sw.js`, or the icons, bump `CACHE_VERSION` in `sw.js` so returning visitors pick up the new shell.

---

## Credits & licensing

- **Gallaudet font** — created by David Rakowski (1991), distributed free for personal and educational use; hosted by Dr. Bill Vicars at [Lifeprint.com](https://www.lifeprint.com), who asks users to consider a donation to a charity of their choice. Publishing this tool embeds (redistributes) the font, so please keep the attribution and confirm the terms cover redistribution. This is not legal advice.
- **Kokoro TTS** — the Kokoro-82M model ([hexgrad/kokoro](https://github.com/hexgrad/kokoro), used via [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)) is Apache 2.0 licensed; generated audio is free to use, including commercially.
- Word lists and interface code are yours to use and modify freely.

---

*This tool teaches the receptive skill of recognising fingerspelled words. It is a practice aid, not a substitute for learning ASL with a qualified instructor or the Deaf community.*
