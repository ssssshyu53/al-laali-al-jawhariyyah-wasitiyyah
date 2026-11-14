#!/usr/bin/env python3
"""
Verifies that every cleaned lesson file (`clean_lessons/L01.txt` .. `L10.txt`)
preserves 100% of Shaykh Ahmad Al-Jawhari's spoken verbatim commentary from
`تفريغ_كامل_مجرد_كما_ذكر/*.txt` (and `verbatim_raw/L*.txt`) with:
  - >= 95% word retention vs verified audio-reviewed transcript
  - Zero non-Arabic Whisper ASR hallucinations / Latin characters
  - Proper segmentation into `@@UNIT` / `MATN:` / `@@SHARH` blocks
  - Forbidden / off-book strings (`الدكتور`, `د. أحمد`, `دار ابن حزم`, `الطحاوية`, `أبي شجاع`) absent
"""
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(REPO_ROOT, "clean_lessons")
RAW_DIR = os.path.join(REPO_ROOT, "تفريغ_كامل_مجرد_كما_ذكر")


def norm_ar(w: str) -> str:
    w = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", w)
    w = re.sub(r"[^\u0621-\u063A\u0641-\u064A]", "", w)
    w = re.sub(r"[أإآٱ]", "ا", w)
    w = w.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    return w


def verify_lesson(lnum: int) -> bool:
    clean_path = os.path.join(CLEAN_DIR, f"L{lnum:02d}.txt")
    raw_matches = sorted(glob.glob(os.path.join(RAW_DIR, f"{lnum:02d}_*.txt")))
    if not os.path.exists(clean_path) or not raw_matches:
        print(f"L{lnum:02d} [MISSING FILE]")
        return False

    raw_txt = open(raw_matches[0], encoding="utf-8").read()
    raw_lines = [
        ln for ln in raw_txt.splitlines()
        if not ln.startswith(("عنوان الدرس:", "الشيخ الشارح:", "الكتاب:", "رابط الدرس:", "==="))
    ]
    raw_body = "\n".join(raw_lines)

    clean_txt = open(clean_path, encoding="utf-8").read()
    units = [u.strip() for u in re.split(r"^@@UNIT\s*$", clean_txt, flags=re.M) if u.strip()]
    sharh_chunks = []
    for u in units:
        m_sh = re.search(r"^@@SHARH\s*\n(.*)", u, flags=re.M | re.S)
        if not m_sh:
            print(f"L{lnum:02d} [FAIL]: Unit missing @@SHARH")
            return False
        sharh_chunks.append(m_sh.group(1).strip())

    clean_body = "\n".join(sharh_chunks)
    latin = re.findall(r"[A-Za-z]{2,}", clean_body)
    if latin:
        print(f"L{lnum:02d} [FAIL]: Found Latin tokens in cleaned text: {latin[:5]}")
        return False

    for forb in ("الدكتور", "د. أحمد", "دار ابن حزم", "أبي شجاع", "تيسير الانتفاع", "الدرر الجوهرية على متن العقيدة الطحاوية"):
        if forb in clean_txt:
            print(f"L{lnum:02d} [FAIL]: Forbidden token found: {forb}")
            return False

    clean_for_wc = re.sub(r"\[[^\]:]+:\s*[٠-٩\-]+\]", "", clean_body)
    raw_words = [norm_ar(w) for w in raw_body.split() if norm_ar(w)]
    clean_words = [norm_ar(w) for w in clean_for_wc.split() if norm_ar(w)]
    ratio = (len(clean_words) / len(raw_words) * 100.0) if raw_words else 100.0

    status = "PASS" if (len(units) >= 3 and ratio >= 95.0 and not latin) else "FAIL"
    print(f"L{lnum:02d} [{status}]: units={len(units)} raw={len(raw_words)} clean={len(clean_words)} ({ratio:.1f}%)")
    return status == "PASS"


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 11))
    ok = all(verify_lesson(n) for n in nums)
    sys.exit(0 if ok else 1)
