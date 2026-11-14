#!/usr/bin/env python3
"""
Expands every {S:A} / {S:A1-A2} / {S:A[:B]:partial:phrase} tag in
matn_wasitiyyah_template.txt using exact Uthmani Rasm from quran_uthmani.json
and appends [السورة: الآية].
"""
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quran_helper import QuranIndex, SURAH_NAMES, to_eastern, norm_uthmani_for_imlaei_match, norm_quran

BASE = "/home/antigravity/wasitiyyah"

def strip_qmarks(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("۞", "").replace("۩", "")).strip()

def norm_skeleton(s: str) -> str:
    s = norm_quran(s)
    s = s.replace("ءا", "ا").replace("ء", "")
    # Remove dagger alefs and medial alefs/waws used in Uthmani orthography (لكنه, سموت, صلوة, ائك)
    s = re.sub(r"(?<!\b)[اوي]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def extract_partial_uthmani(full_uthmani: str, phrase: str) -> str:
    p_clean = phrase.replace("*", " ")
    p_toks = [t for t in norm_uthmani_for_imlaei_match(p_clean).split() if t]
    p_skel = " ".join(norm_skeleton(p_clean).split())
    u_words = strip_qmarks(full_uthmani).split()
    word_map = []
    for i, w in enumerate(u_words):
        nt = norm_uthmani_for_imlaei_match(w)
        if nt:
            word_map.append((i, nt, norm_skeleton(w)))

    norm_list = [x[1] for x in word_map]
    skel_list = [x[2] for x in word_map]
    p_str = " ".join(p_toks)
    for start in range(len(word_map)):
        acc = ""
        acc_sk = ""
        for end in range(start, len(word_map)):
            acc = (acc + " " + norm_list[end]).strip()
            acc_sk = (acc_sk + " " + skel_list[end]).strip()
            if acc == p_str or norm_quran(acc) == norm_quran(p_str) or acc_sk == p_skel:
                i0 = word_map[start][0]
                i1 = word_map[end][0]
                out_slice = u_words[i0:i1 + 1]
                while out_slice and not norm_uthmani_for_imlaei_match(out_slice[-1]):
                    out_slice.pop()
                return " ".join(out_slice)
            if len(acc_sk) > len(p_skel) + 12:
                break
    p_compact = p_skel.replace(" ", "")
    for start in range(len(word_map)):
        acc = ""
        for end in range(start, len(word_map)):
            acc += skel_list[end]
            if acc == p_compact:
                i0 = word_map[start][0]
                i1 = word_map[end][0]
                return " ".join(u_words[i0:i1 + 1])
            if len(acc) > len(p_compact) + 8:
                break
    raise ValueError(f"Could not locate partial '{phrase}' inside '{full_uthmani}'")

def main():
    qi = QuranIndex()
    tpl = open(os.path.join(BASE, "matn_wasitiyyah_template.txt"), encoding="utf-8").read()

    def repl(m):
        tag = m.group(1)
        parts = tag.split(":", 3)
        snum = int(parts[0])
        arange = parts[1]
        if "-" in arange:
            a1, a2 = [int(x) for x in arange.split("-")]
        else:
            a1 = a2 = int(arange)

        full_uth = " ".join(strip_qmarks(qi.surahs[snum][i - 1]["uthmani"]) for i in range(a1, a2 + 1))
        if len(parts) >= 4 and parts[2] == "partial":
            phrase = parts[3]
            uth_text = extract_partial_uthmani(full_uth, phrase)
        else:
            uth_text = full_uth

        if a2 > a1:
            ref = f"[{SURAH_NAMES[snum]}: {to_eastern(a1)}-{to_eastern(a2)}]"
        else:
            ref = f"[{SURAH_NAMES[snum]}: {to_eastern(a1)}]"
        return f"﴿{uth_text}﴾ {ref}"

    expanded = re.sub(r"\{([0-9]+:[0-9\-]+(?::partial:[^\}]+)?)\}", repl, tpl)
    out_path = os.path.join(BASE, "matn_wasitiyyah_uthmani.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(expanded)
    ayah_count = len(re.findall(r"﴿[^﴾]+﴾", expanded))
    print(f"Expanded {ayah_count} Uthmani ayahs in {out_path}")

if __name__ == "__main__":
    main()
