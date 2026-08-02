#!/usr/bin/env python3
"""
generate_audio.py
=================
Regenerates every spoken clip used by the ASL Fingerspelling Trainer.

Each word in `wordlist.txt` is synthesised with Kokoro (a modern, StyleTTS2-based
neural text-to-speech model), trimmed, loudness-normalised, and encoded as a small
mono MP3 written to `audio/<WORD>.mp3`. The web app plays these files by URL.

This is the exact pipeline used to build the shipped audio, provided so you can
rebuild it, change the voice, or extend the word list.

--------------------------------------------------------------------------------
Requirements
--------------------------------------------------------------------------------
1. Python 3.9+ and ffmpeg on your PATH (ffmpeg must be built with libmp3lame):
       # macOS:    brew install ffmpeg
       # Debian:   sudo apt-get install ffmpeg
2. Python packages:
       pip install kokoro-onnx soundfile numpy
3. The Kokoro model files (downloaded once):
       kokoro-v1.0.fp16.onnx   (~170 MB)
       voices-v1.0.bin         (~27 MB)
   From the kokoro-onnx releases:
       https://github.com/thewh1teagle/kokoro-onnx/releases
   Place them next to this script, or point MODEL_PATH / VOICES_PATH below at them.

--------------------------------------------------------------------------------
Usage
--------------------------------------------------------------------------------
    python generate_audio.py

Options via environment variables:
    VOICE=af_heart      # Kokoro voice (e.g. af_heart, af_bella, am_michael, bf_emma)
    BITRATE=32k         # MP3 bitrate (mono). 32k is clear for single words.
    WORDLIST=wordlist.txt
    OUT=audio
    FORCE=0             # set to 1 to re-render clips that already exist

Already-generated clips are skipped, so the script is resumable if interrupted.
"""

import os
import sys
import glob
import time
import subprocess

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
VOICE       = os.environ.get("VOICE", "af_heart")
BITRATE     = os.environ.get("BITRATE", "32k")
WORDLIST    = os.environ.get("WORDLIST", "wordlist.txt")
OUT         = os.environ.get("OUT", "audio")
FORCE       = os.environ.get("FORCE", "0") == "1"
MODEL_PATH  = os.environ.get("MODEL_PATH", "kokoro-v1.0.fp16.onnx")
VOICES_PATH = os.environ.get("VOICES_PATH", "voices-v1.0.bin")

TRIM_DB     = -40.0   # silence gate, relative to each clip's peak
TRIM_PAD_MS = 30      # keep this much padding around the speech
PEAK        = 0.891   # normalise peak to ~ -1 dBFS for consistent loudness


def trim_silence(x, sr, thresh_db=TRIM_DB, pad_ms=TRIM_PAD_MS):
    """Trim leading/trailing near-silence, keeping a little padding."""
    env = np.abs(x)
    peak = np.max(env)
    if peak == 0:
        return x
    thr = (10 ** (thresh_db / 20.0)) * peak
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    pad = int(sr * pad_ms / 1000.0)
    start = max(0, idx[0] - pad)
    end = min(len(x), idx[-1] + pad)
    return x[start:end]


def encode_mp3(wav_path, mp3_path, bitrate):
    """Encode a WAV to mono MP3 at the given bitrate via ffmpeg."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path,
         "-c:a", "libmp3lame", "-b:a", bitrate, "-ac", "1", mp3_path],
        capture_output=True, check=True,
    )


def main():
    for path, label in [(MODEL_PATH, "model"), (VOICES_PATH, "voices")]:
        if not os.path.exists(path):
            sys.exit(f"Missing {label} file: {path}\n"
                     f"Download it from the kokoro-onnx releases (see the header of this script).")
    if not os.path.exists(WORDLIST):
        sys.exit(f"Missing word list: {WORDLIST}")

    os.makedirs(OUT, exist_ok=True)
    words = [w.strip() for w in open(WORDLIST) if w.strip()]

    done = {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(OUT, "*.mp3"))}
    todo = words if FORCE else [w for w in words if w not in done]

    print(f"words: {len(words)} | already done: {len(done)} | to generate: {len(todo)}")
    print(f"voice: {VOICE} | bitrate: {BITRATE} | output: {OUT}/")
    if not todo:
        print("Nothing to do.")
        return

    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
    tmp_wav = os.path.join(OUT, "_tmp.wav")

    t0 = time.time()
    made = 0
    for w in todo:
        try:
            # Feed the word title-cased ("Cat", not "CAT") so the model reads it
            # as a word rather than spelling out capital letters.
            samples, sr = kokoro.create(w.capitalize(), voice=VOICE, speed=1.0, lang="en-us")
            if samples.ndim > 1:
                samples = samples.mean(axis=1)
            samples = trim_silence(samples, sr)
            peak = np.max(np.abs(samples))
            if peak > 0:
                samples = samples / peak * PEAK
            sf.write(tmp_wav, samples, sr)
            encode_mp3(tmp_wav, os.path.join(OUT, f"{w}.mp3"), BITRATE)
            made += 1
            if made % 25 == 0:
                rate = made / (time.time() - t0)
                eta = (len(todo) - made) / rate / 60 if rate else 0
                print(f"  {made}/{len(todo)}  {w:<14} {rate:.2f}/s  eta {eta:.1f} min")
        except Exception as exc:  # keep going; one bad word shouldn't stop the run
            print(f"  ERROR {w}: {exc!r}")

    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)
    print(f"Done: generated {made} clips in {(time.time() - t0) / 60:.1f} min.")


if __name__ == "__main__":
    main()
