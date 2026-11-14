#!/usr/bin/env python3
"""
Validate edited Wasitiyyah lessons (L01-L10) against clean_lessons structure, Quranic ayahs,
L02-L10 opening-intro removal, L01-L09 closing-farewell removal, L01 intro & L10
closing preservation, and >= 92% verbatim Shaykh word retention (no summarizing/paraphrasing).
"""
import os
import re
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VIDEO_OPENING_RX = re.compile(
    r'أعوذ بالله السميع العليم|فمرحب[اً]? بكم أيها (?:الإخوة|الأحبة)|وكنا قد (?:وقفنا|وصلنا) عند'
)
VIDEO_CLOSING_RX = re.compile(
    r'لقاءنا القادم|لقائنا القادم|نقف هنا إن شاء الله|نبدأ منه بمشيئة الله|غدًا بمشيئة الله|وصل[ّ]? اللهم على نبينا محمد|وصلى الله على نبينا محمد، والحمد لله'
)
LATIN_RX = re.compile(r'[A-Za-z]')


def parse_units(path):
    txt = open(path, encoding='utf-8').read()
    parts = re.split(r'^@@UNIT\s*$', txt, flags=re.M)[1:]
    out = []
    for p in parts:
        m = re.search(r'@@SHARH\s*\n(.*)', p, flags=re.S)
        hdr = p[:m.start()] if m else p
        sharh = m.group(1).strip() if m else ''
        meta = {}
        for k in ['TOC_BOOK', 'TOC_FASL', 'HEADING', 'FASL_END']:
            mm = re.search(rf'^{k}:(.*)$', hdr, flags=re.M)
            meta[k] = mm.group(1).strip() if mm else ''
        mm = re.search(r'^MATN:(.*?)(?=^FASL_END:)', hdr, flags=re.M | re.S)
        meta['MATN'] = mm.group(1).strip() if mm else ''
        out.append((meta, sharh))
    return out


def check_lesson(lnum):
    c_path = os.path.join(_REPO, 'clean_lessons', f'L{lnum:02d}.txt')
    e_path = os.path.join(_REPO, 'edited_lessons', f'L{lnum:02d}.txt')
    if not os.path.exists(e_path):
        return False, f"L{lnum:02d}: MISSING {e_path}"

    cu = parse_units(c_path)
    eu = parse_units(e_path)

    if len(cu) != len(eu):
        return False, f"L{lnum:02d}: unit count mismatch {len(eu)} != {len(cu)}"

    errors = []
    tot_c_words = 0
    tot_e_words = 0
    for idx, ((cm, cs), (em, es)) in enumerate(zip(cu, eu), 1):
        for k in ['TOC_BOOK', 'TOC_FASL', 'HEADING', 'MATN', 'FASL_END']:
            if cm[k] != em[k]:
                errors.append(f"U{idx:02d} {k} mismatch")
        if not es:
            errors.append(f"U{idx:02d} empty SHARH")
        c_ayah_set = set(re.findall(r'﴿[^﴾]+﴾', cs))
        e_ayah_set = set(re.findall(r'﴿[^﴾]+﴾', es))
        missing_ay = {a for a in (c_ayah_set - e_ayah_set) if not any(a[1:-1] in ea for ea in e_ayah_set)}
        extra_ay = e_ayah_set - c_ayah_set
        if missing_ay or extra_ay:
            errors.append(f"U{idx:02d} Ayah set mismatch: missing={missing_ay} extra={extra_ay}")
        if LATIN_RX.search(es):
            errors.append(f"U{idx:02d} Latin chars found")
        for forb in ['الدكتور', 'د. أحمد', 'دار ابن حزم', 'أبي شجاع', 'تيسير الانتفاع', 'الدرر الجوهرية على متن العقيدة الطحاوية']:
            if forb in es:
                errors.append(f"U{idx:02d} forbidden term: {forb}")
        tot_c_words += len(cs.split())
        tot_e_words += len(es.split())

    u1_sharh = eu[0][1]
    if lnum != 1:
        hits_open = VIDEO_OPENING_RX.findall(u1_sharh[:600])
        if hits_open:
            errors.append(f"U01 leftover video intro: {hits_open}")

    ul_sharh = eu[-1][1]
    if lnum != 10:
        hits_close = VIDEO_CLOSING_RX.findall(ul_sharh[-400:])
        if hits_close:
            errors.append(f"U{len(eu):02d} leftover video closing: {hits_close}")

    ratio = tot_e_words / max(1, tot_c_words)
    if ratio < 0.92:
        errors.append(f"Word retention too low ({ratio:.2%}: {tot_e_words}/{tot_c_words}) - unwanted deletion/summarization")
    if errors:
        return False, f"L{lnum:02d} FAIL ({tot_e_words}/{tot_c_words}, {ratio:.1%}): " + " | ".join(errors)
    return True, f"L{lnum:02d} PASS ({len(eu)} units, {tot_e_words}/{tot_c_words} words = {ratio:.1%})"


def main():
    nums = [int(a.lstrip('L')) for a in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 11))
    ok_all = True
    for n in nums:
        ok, msg = check_lesson(n)
        print(msg)
        if not ok:
            ok_all = False
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
