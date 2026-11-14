#!/usr/bin/env python3
import json
import os
import subprocess

BASE = "/home/antigravity/wasitiyyah"
AUDIO_DIR = os.path.join(BASE, "audio_cache")
SUB_DIR = os.path.join(BASE, "subtitles_raw")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SUB_DIR, exist_ok=True)

info = json.load(open(os.path.join(BASE, "playlist_info.json"), encoding="utf-8"))
YTDLP = "/home/antigravity/.venv/bin/yt-dlp"

for idx, entry in enumerate(info["entries"], 1):
    vid = entry["id"]
    url = f"https://www.youtube.com/watch?v={vid}"
    out_m4a = os.path.join(AUDIO_DIR, f"lesson_{idx:02d}.m4a")
    if os.path.exists(out_m4a) and os.path.getsize(out_m4a) > 1_000_000:
        print(f"[{idx:02d}] Already exists: {out_m4a} ({os.path.getsize(out_m4a)} bytes)", flush=True)
    else:
        print(f"[{idx:02d}] Downloading audio {vid} -> {out_m4a}...", flush=True)
        cmd = [
            YTDLP, "-x", "--audio-format", "m4a", "--audio-quality", "0",
            "-o", os.path.join(AUDIO_DIR, f"lesson_{idx:02d}.%(ext)s"),
            url,
        ]
        subprocess.run(cmd, check=True)
        print(f"[{idx:02d}] Done audio: {os.path.getsize(out_m4a)} bytes", flush=True)

    # Try auto-subs as supplementary reference (non-fatal)
    sub_tpl = os.path.join(SUB_DIR, f"lesson_{idx:02d}.%(ext)s")
    subprocess.run(
        [YTDLP, "--skip-download", "--write-auto-subs", "--sub-lang", "ar", "-o", sub_tpl, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

print("ALL_DOWNLOADS_COMPLETE", flush=True)
