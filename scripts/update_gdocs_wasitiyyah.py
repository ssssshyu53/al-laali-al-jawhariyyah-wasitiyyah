#!/usr/bin/env python3
"""
Creates (or updates in-place) two formatted RTL Google Docs for:
«اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ» by Shaykh Ahmad al-Jawhari:
  1. Verbatim Complete Edition (النسخة الحرفية الكاملة) from `book_engine/book_data.json`
  2. Edited Classical Arabic Edition (النسخة المحررة) from `book_engine/book_data_edited.json`
"""
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS_PATH = os.path.join(REPO_ROOT, "book_engine", "gdocs_ids.json")

YT_PLAYLIST = "https://youtube.com/playlist?list=PLjR2AWKLjP8T5pQ1SMr83qnNpgd4donq2"
GH_REPO = "https://github.com/ssssshyu53/al-laali-al-jawhariyyah-wasitiyyah"

to_arab_digits_map = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def to_ar(n: int) -> str:
    return str(n).translate(to_arab_digits_map)


def html_para_to_runs(p_html: str):
    pattern = re.compile(r'(<strong>.*?</strong>|<span class="ayah(?:-ref)?">.*?</span>)', flags=re.S)
    parts = pattern.split(p_html)
    runs = []
    for part in parts:
        if not part:
            continue
        is_bold = False
        color = "#202124"
        font_sz = 11.5
        txt = part
        if part.startswith("<strong>") and part.endswith("</strong>"):
            is_bold = True
            color = "#96267e"
            txt = part[len("<strong>"):-len("</strong>")]
        elif part.startswith('<span class="ayah">') and part.endswith("</span>"):
            is_bold = True
            color = "#111111"
            txt = part[len('<span class="ayah">'):-len("</span>")]
        elif part.startswith('<span class="ayah-ref">') and part.endswith("</span>"):
            is_bold = False
            color = "#5F6368"
            font_sz = 8.8
            txt = part[len('<span class="ayah-ref">'):-len("</span>")]
        txt = re.sub(r"<[^>]+>", "", txt)
        txt = (
            txt.replace("&quot;", '"')
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )
        if txt:
            runs.append({
                "text": txt,
                "bold": is_bold,
                "italic": False,
                "font_family": "Amiri",
                "font_size": font_sz,
                "text_color": color,
            })
    if not runs:
        runs.append({
            "text": " ",
            "bold": False,
            "italic": False,
            "font_family": "Amiri",
            "font_size": 11.5,
            "text_color": "#202124",
        })
    return runs


def build_header_ops(title_main: str, subtitle_line: str, method_desc: str, glossary_source: str):
    return [
        {
            "op": "set-default-style",
            "font_family": "Amiri",
            "font_size": 11.5,
            "text_color": "#202124",
            "line_spacing": 115,
            "space_above": 2,
            "space_below": 3,
        },
        {
            "op": "append",
            "text": "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ",
            "font_family": "Amiri",
            "font_size": 20,
            "bold": True,
            "alignment": "CENTER",
            "text_color": "#96267e",
        },
        {
            "op": "heading",
            "level": "TITLE",
            "text": title_main,
            "font_family": "Amiri",
            "font_size": 24,
            "bold": True,
            "alignment": "CENTER",
            "text_color": "#96267e",
            "space_above": 4,
            "space_below": 4,
        },
        {
            "op": "append",
            "text": subtitle_line,
            "font_family": "Amiri",
            "font_size": 13,
            "bold": True,
            "alignment": "CENTER",
            "text_color": "#202124",
        },
        {
            "op": "append",
            "text": "لِفَضِيلَةِ الشَّيْخِ أَحْمَدَ الْجَوْهَرِيِّ عَبْدِ الْجَوَادِ (حَفِظَهُ اللهُ تَعَالَى وَنَفَعَ بِعِلْمِهِ)",
            "font_family": "Amiri",
            "font_size": 13,
            "bold": True,
            "alignment": "CENTER",
            "text_color": "#96267e",
        },
        {
            "op": "append",
            "text": "وَالْمَتْنُ لِشَيْخِ الإِسْلَامِ تَقِيِّ الدِّينِ أَحْمَدَ بْنِ عَبْدِ الحَلِيمِ بْنِ تَيْمِيَّةَ الحَرَّانِيِّ (٦٦١ – ٧٢٨ هـ)",
            "font_family": "Amiri",
            "font_size": 11.5,
            "bold": False,
            "alignment": "CENTER",
            "text_color": "#3C4043",
        },
        {
            "op": "rich-text",
            "font_family": "Amiri",
            "font_size": 10.5,
            "alignment": "CENTER",
            "text_color": "#202124",
            "paragraph_bg_color": "#FAF7EF",
            "runs": [
                {"text": method_desc + "\n"},
                {"text": "مَنْهَجُ الْحَوَاشِي وَغَرِيبِ الْمَتْنِ: ", "bold": True, "text_color": "#96267e"},
                {"text": glossary_source + "\n"},
                {"text": "المصدر الصوتي: ", "bold": True},
                {"text": "سلسلة دروس شرح العقيدة الواسطية (يوتيوب — ١٠ لقاءات + مجلس الإسماع)", "text_color": "#1a73e8", "url": YT_PLAYLIST},
                {"text": "  •  "},
                {"text": "مستودع الكتاب والملفات (GitHub)", "text_color": "#1a73e8", "url": GH_REPO},
            ],
        },
        {"op": "horizontal-rule"},
    ]


def build_unit_ops(units_slice):
    ops = [
        {
            "op": "set-default-style",
            "font_family": "Amiri",
            "font_size": 11.5,
            "text_color": "#202124",
            "line_spacing": 115,
            "space_above": 2,
            "space_below": 3,
        }
    ]
    for u in units_slice:
        if u.get("is_preface"):
            preface_title = u.get("toc_fasl") or "مُقَدِّمَةُ الْكِتَابِ"
            ops.append({
                "op": "heading",
                "level": "2",
                "text": preface_title,
                "font_family": "Amiri",
                "font_size": 16,
                "bold": True,
                "alignment": "CENTER",
                "text_color": "#96267e",
                "space_above": 12,
                "space_below": 4,
            })
            if u.get("lesson_note"):
                ops.append({
                    "op": "append",
                    "text": f"(*) {u['lesson_note']}",
                    "font_family": "Amiri",
                    "font_size": 10,
                    "italic": True,
                    "alignment": "CENTER",
                    "text_color": "#5F6368",
                })
            for p_html in u["sharh_paras_html"]:
                runs = html_para_to_runs(p_html)
                ops.append({
                    "op": "rich-text",
                    "font_family": "Amiri",
                    "font_size": 11.5,
                    "text_color": "#202124",
                    "alignment": "JUSTIFIED",
                    "indent_first_line": 18,
                    "runs": runs,
                })
            ops.append({
                "op": "append",
                "text": "✽      ✽      ✽",
                "font_family": "Amiri",
                "font_size": 12,
                "bold": True,
                "alignment": "CENTER",
                "text_color": "#96267e",
            })
            continue

        if u.get("toc_book"):
            ops.append({
                "op": "heading",
                "level": "1",
                "text": u["toc_book"],
                "font_family": "Amiri",
                "font_size": 18,
                "bold": True,
                "alignment": "CENTER",
                "text_color": "#96267e",
                "space_above": 14,
                "space_below": 4,
            })
        if u.get("toc_fasl"):
            ops.append({
                "op": "heading",
                "level": "2",
                "text": u["toc_fasl"],
                "font_family": "Amiri",
                "font_size": 14.5,
                "bold": True,
                "alignment": "CENTER",
                "text_color": "#96267e",
                "space_above": 10,
                "space_below": 3,
            })
        if u.get("lesson_note"):
            ops.append({
                "op": "append",
                "text": f"(*) {u['lesson_note']}",
                "font_family": "Amiri",
                "font_size": 10,
                "italic": True,
                "alignment": "CENTER",
                "text_color": "#5F6368",
            })

        glosses = u.get("glosses") or []
        for m_line in u["matn_lines"]:
            clean_m = (
                m_line.replace("&quot;", '"')
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
            ).strip()
            if not clean_m:
                continue
            is_dots = all(ch == "." for ch in clean_m) and len(clean_m) >= 5
            is_basmalah = "بِسْمِ اللَّهِ الرَّحْمَ" in clean_m and len(clean_m) <= 45
            if is_dots:
                ops.append({
                    "op": "append",
                    "text": clean_m,
                    "font_family": "Amiri",
                    "font_size": 12,
                    "bold": True,
                    "alignment": "CENTER",
                    "paragraph_bg_color": "#FAF7EF",
                    "text_color": "#96267e",
                })
            else:
                ops.append({
                    "op": "append",
                    "text": clean_m,
                    "font_family": "Amiri",
                    "font_size": 14 if is_basmalah else 13.5,
                    "bold": True,
                    "alignment": "CENTER" if is_basmalah else "JUSTIFIED",
                    "indent_first_line": 0 if is_basmalah else 18,
                    "paragraph_bg_color": "#FAF7EF",
                    "text_color": "#96267e",
                })

        ops.append({"op": "horizontal-rule"})

        for p_html in u["sharh_paras_html"]:
            runs = html_para_to_runs(p_html)
            ops.append({
                "op": "rich-text",
                "font_family": "Amiri",
                "font_size": 11.5,
                "text_color": "#202124",
                "alignment": "JUSTIFIED",
                "indent_first_line": 18,
                "runs": runs,
            })

        if glosses:
            gloss_runs = [{"text": "غَرِيبُ الْمَتْنِ:  ", "bold": True, "text_color": "#96267e"}]
            for gi, gl in enumerate(glosses, 1):
                gloss_runs.append({
                    "text": f"({to_ar(gi)}) {gl['gloss']}",
                    "bold": False,
                    "text_color": "#3C4043",
                })
                if gi < len(glosses):
                    gloss_runs.append({"text": "\n"})
            ops.append({
                "op": "rich-text",
                "font_family": "Amiri",
                "font_size": 10,
                "text_color": "#3C4043",
                "alignment": "JUSTIFIED",
                "paragraph_bg_color": "#F8F9FA",
                "runs": gloss_runs,
            })

        ops.append({
            "op": "append",
            "text": "✽      ✽      ✽",
            "font_family": "Amiri",
            "font_size": 11.5,
            "bold": True,
            "alignment": "CENTER",
            "text_color": "#96267e",
        })
    return ops


def run_cmd(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{res.stderr or res.stdout}")
    return res.stdout


def create_doc(title: str) -> str:
    out = run_cmd(["gdocs", "mutate", "create", "--title", title, "--pageless=false", "--json"])
    info = json.loads(out)
    doc_id = info.get("documentId") or info.get("id")
    if not doc_id:
        raise RuntimeError(f"Unexpected create JSON output: {out}")
    return doc_id


def run_batch(doc_id: str, ops, replace_all: bool, label: str):
    tmp_path = f"/tmp/gdoc_ops_{doc_id}_{'rep' if replace_all else 'app'}.json"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(ops, f, ensure_ascii=False)
    cmd = ["gdocs", "mutate", "batch", doc_id, "-f", tmp_path]
    if replace_all:
        cmd.append("--replace-all")
    print(f"  [{label}] {len(ops)} ops (replace_all={replace_all}) -> {doc_id} ...", flush=True)
    run_cmd(cmd)


def apply_rtl_to_entire_doc(doc_id: str):
    out = run_cmd(["gdocs", "readonly", "dump-body", doc_id])
    body = json.loads(out)
    content = body.get("content", [])
    end_idx = content[-1].get("endIndex", 2) - 1 if content else 2
    if end_idx <= 1:
        return
    rtl_ops = [
        {
            "op": "raw",
            "raw_request": {
                "updateParagraphStyle": {
                    "range": {"startIndex": 1, "endIndex": end_idx},
                    "paragraphStyle": {"direction": "RIGHT_TO_LEFT"},
                    "fields": "direction",
                }
            },
        }
    ]
    run_batch(doc_id, rtl_ops, replace_all=False, label=f"RTL (1..{end_idx})")


def sync_edition(doc_id: str, data_file: str, title_main: str, subtitle_line: str, method_desc: str):
    with open(os.path.join(REPO_ROOT, "book_engine", data_file), encoding="utf-8") as f:
        data = json.load(f)
    units = data["units"]
    glossary_source = data.get("glossary_source", "")

    u_part1 = [u for u in units if u["lesson_num"] <= 3]
    u_part2 = [u for u in units if 4 <= u["lesson_num"] <= 7]
    u_part3 = [u for u in units if u["lesson_num"] >= 8]

    ops1 = build_header_ops(title_main, subtitle_line, method_desc, glossary_source) + build_unit_ops(u_part1)
    run_batch(doc_id, ops1, replace_all=True, label=f"{data_file} L01-L03")
    if u_part2:
        run_batch(doc_id, build_unit_ops(u_part2), replace_all=False, label=f"{data_file} L04-L07")
    if u_part3:
        run_batch(doc_id, build_unit_ops(u_part3), replace_all=False, label=f"{data_file} L08-L10")
    apply_rtl_to_entire_doc(doc_id)

    url = run_cmd(["gdocs", "readonly", "get-url", doc_id]).strip()
    return url


def main():
    ids = {}
    if os.path.exists(IDS_PATH):
        with open(IDS_PATH, encoding="utf-8") as f:
            ids = json.load(f)

    if not ids.get("verbatim_doc_id"):
        print("Creating Google Doc for Verbatim Edition...", flush=True)
        ids["verbatim_doc_id"] = create_doc(
            "اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ — النُّسْخَةُ الحَرْفِيَّةُ الكَامِلَةُ"
        )
    if not ids.get("edited_doc_id"):
        print("Creating Google Doc for Edited Edition...", flush=True)
        ids["edited_doc_id"] = create_doc(
            "اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ — النُّسْخَةُ المُحَرَّرَةُ"
        )

    with open(IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)

    print("Syncing Verbatim Edition...", flush=True)
    url_verb = sync_edition(
        ids["verbatim_doc_id"],
        "book_data.json",
        "اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ",
        "( شَرْحُ مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ لِشَيْخِ الإِسْلَامِ ابْنِ تَيْمِيَّةَ ) — التَّفْرِيغُ الحَرْفِيُّ الكَامِلُ (١٠ لِقَاءَاتٍ)",
        "تفريغ حرفي كامل مراجع صوتيا دون حذف أو اختصار (المتن مضبوطا بالشكل في الأعلى مفصولا بخط أفقي عن الشرح أسفله).",
    )
    ids["verbatim_url"] = url_verb

    print("Syncing Edited Classical Arabic Edition...", flush=True)
    url_edit = sync_edition(
        ids["edited_doc_id"],
        "book_data_edited.json",
        "اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ — النُّسْخَةُ المُحَرَّرَةُ",
        "( شَرْحُ مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ لِشَيْخِ الإِسْلَامِ ابْنِ تَيْمِيَّةَ ) — تَفْرِيغٌ مُحَرَّرٌ مُهَذَّبٌ لِمُحَاضَرَاتِ الشَّيْخِ (١٠ مُحَاضَرَاتٍ)",
        "تفريغ محرر مهذب لمحاضرات الشيخ في شرح متن العقيدة الواسطية بإثبات كلامه كاملا بلفظه دون تبديل أو اختصار مع الاقتصار على مقدمة اللقاء الأول وخاتمة الأخير وتهذيب التكرار اللفظي المتتابع.",
    )
    ids["edited_url"] = url_edit

    with open(IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)

    print("\nDONE:")
    print(f"  Verbatim: {url_verb}")
    print(f"  Edited:   {url_edit}")


if __name__ == "__main__":
    main()
