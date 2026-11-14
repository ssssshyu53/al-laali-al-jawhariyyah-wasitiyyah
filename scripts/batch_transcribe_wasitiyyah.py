#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
from faster_whisper import WhisperModel

BASE = "/home/antigravity/wasitiyyah"
INFO = json.load(open(os.path.join(BASE, "playlist_info.json"), encoding="utf-8"))
AUDIO_DIR = os.path.join(BASE, "audio_cache")
TEMP_DIR = os.path.join(BASE, "temp_chunks")
PARTS_DIR = os.path.join(BASE, "raw_parts")
OUT_DIR = os.path.join(BASE, "raw_transcripts")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PARTS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

PROMPT = (
    "شرح متن العقيدة الواسطية لشيخ الإسلام ابن تيمية، لفضيلة الشيخ أحمد الجوهري عبد الجواد، "
    "اعتقاد الفرقة الناجية المنصورة أهل السنة والجماعة، الأسماء والصفات، الإيمان بالقدر، "
    "الصحابة وآل البيت، الخوارج والمعتزلة والجهمية والأشاعرة والمرجئة والقدرية والرافضة."
)

CHUNK_LEN = 12 * 60  # 12 minutes per chunk

def is_audio_ready(lnum: int) -> bool:
    m4a = os.path.join(AUDIO_DIR, f"lesson_{lnum:02d}.m4a")
    webm = os.path.join(AUDIO_DIR, f"lesson_{lnum:02d}.webm")
    part = os.path.join(AUDIO_DIR, f"lesson_{lnum:02d}.m4a.part")
    return os.path.exists(m4a) and os.path.getsize(m4a) > 1_000_000 and not os.path.exists(webm) and not os.path.exists(part)

def main():
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 12))
    print(f"Loading Whisper 'small' model on CPU int8 for lessons {nums}...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
    print("Model loaded.", flush=True)

    for lnum in nums:
        entry = INFO["entries"][lnum - 1]
        total_sec = int(entry["duration"])
        audio_file = os.path.join(AUDIO_DIR, f"lesson_{lnum:02d}.m4a")

        # Wait up to 300s if currently finishing download/remux
        waited = 0
        while not is_audio_ready(lnum) and waited < 300:
            time.sleep(5)
            waited += 5
        if not is_audio_ready(lnum):
            print(f"[SKIP] Audio not ready: {audio_file}", flush=True)
            continue

        chunks = []
        st = 0
        c_idx = 1
        while st < total_sec:
            dur = min(CHUNK_LEN, total_sec - st)
            chunks.append((c_idx, st, dur))
            st += dur
            c_idx += 1

        final_txt = os.path.join(OUT_DIR, f"lesson_{lnum:02d}.txt")
        print(f"\n=== Lesson {lnum:02d} ({entry['title']}): {len(chunks)} chunks, {total_sec}s ===", flush=True)
        part_files = []
        for c_idx, st, dur in chunks:
            chunk_audio = os.path.join(TEMP_DIR, f"l{lnum:02d}_c{c_idx:02d}.m4a")
            chunk_txt = os.path.join(PARTS_DIR, f"l{lnum:02d}_c{c_idx:02d}.txt")
            part_files.append((c_idx, st, chunk_txt))

            st_str = f"{st//3600:02d}:{(st%3600)//60:02d}:{st%60:02d}"
            dur_str = f"{dur//3600:02d}:{(dur%3600)//60:02d}:{dur%60:02d}"

            if not os.path.exists(chunk_audio) or os.path.getsize(chunk_audio) < 50_000:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", st_str, "-t", dur_str, "-i", audio_file, "-vn", "-c", "copy", chunk_audio],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )

            if os.path.exists(chunk_txt) and os.path.getsize(chunk_txt) > 500:
                print(f"  Chunk l{lnum:02d}_c{c_idx:02d} already done, skipping ASR.", flush=True)
                continue

            t0 = time.time()
            print(f"  Transcribing l{lnum:02d}_c{c_idx:02d} ({st_str} +{dur_str})...", flush=True)
            segments, _ = model.transcribe(chunk_audio, language="ar", initial_prompt=PROMPT, beam_size=1)
            cnt = 0
            with open(chunk_txt, "w", encoding="utf-8") as f:
                for s in segments:
                    f.write(f"[{s.start:.1f} - {s.end:.1f}] {s.text.strip()}\n")
                    cnt += 1
            elapsed = time.time() - t0
            print(f"  -> {cnt} segs in {elapsed:.1f}s", flush=True)

        all_lines = []
        for c_idx, st, p_txt in part_files:
            with open(p_txt, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[") and " - " in line:
                        be = line.find("]")
                        tp = line[1:be]
                        tx = line[be + 1:].strip()
                        try:
                            ss, es = tp.split(" - ")
                            all_lines.append(f"[{float(ss)+st:.1f} - {float(es)+st:.1f}] {tx}")
                        except Exception:
                            all_lines.append(line)
                    else:
                        all_lines.append(line)
        with open(final_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(all_lines) + "\n")
        print(f">>> SAVED {final_txt} ({len(all_lines)} segments)", flush=True)

    print("BATCH_TRANSCRIBE_DONE", flush=True)

if __name__ == "__main__":
    main()
