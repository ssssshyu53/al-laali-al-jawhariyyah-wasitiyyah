#!/usr/bin/env python3
import argparse
import json
import os
import re

_PARSER = argparse.ArgumentParser()
_PARSER.add_argument('--mode', choices=('verbatim', 'edited'), default='verbatim')
_ARGS, _ = _PARSER.parse_known_args()
IS_EDITED = (_ARGS.mode == 'edited')

_ENG = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_ENG)
out_dir = os.path.join(_REPO, 'اللَّآلِئُ_الجَوْهَرِيَّةُ_عَلَى_مَتْنِ_العَقِيدَةِ_الوَاسِطِيَّةِ_النسخة_المحررة' if IS_EDITED else 'اللَّآلِئُ_الجَوْهَرِيَّةُ_عَلَى_مَتْنِ_العَقِيدَةِ_الوَاسِطِيَّةِ')
os.makedirs(out_dir, exist_ok=True)

EDIGITS = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')

def to_e(n):
    return str(n).translate(EDIGITS)

LESSON_SPECS = [
    (1, '01_الدرس_الأول_مقدمة_الواسطية_وفرقة_أهل_السنة_والإيمان_بالأسماء_والصفات.md', 'اللقاء الأول: مقدمة العقيدة الواسطية، والفرقة الناجية، وأصل الإيمان بالأسماء والصفات', 'مقدمة الواسطية وأصل الأسماء والصفات'),
    (2, '02_الدرس_الثاني_سورة_الإخلاص_وآية_الكرسي_ونفي_التمثيل_والعلم_والحكمة.md', 'اللقاء الثاني: سورة الإخلاص، وآية الكرسي، والأسماء والصفات، والعلم والحكمة', 'الإخلاص وآية الكرسي والعلم والحكمة'),
    (3, '03_الدرس_الثالث_الصفات_الذاتية_والفعلية_والقدرة_والسمع_والبصر_والمشيئة_والمحبة_والرحمة.md', 'اللقاء الثالث: الصفات الذاتية والفعلية، والقدرة والقوة، والسمع والبصر، والمشيئة والمحبة والرحمة', 'القدرة والسمع والبصر والمشيئة والمحبة'),
    (4, '04_الدرس_الرابع_صفات_الرضا_والغضب_والمجيء_والوجه_واليدين_والعين_والمكر_والعزة.md', 'اللقاء الرابع: صفات الرضا والغضب، والإتيان والمجيء، والوجه واليدين والعينين، والسمع والبصر، والمكر والعزة', 'الرضا والغضب والمجيء والوجه واليدين والعزة'),
    (5, '05_الدرس_الخامس_التنزيه_الإجمالي_والمفصل_والاستواء_على_العرش_والعلو.md', 'اللقاء الخامس: التنزيه الإجمالي والمفصل، نفي المثيل والشريك والولد، والاستواء على العرش، وعلو الله تعالى', 'التنزيه والاستواء على العرش والعلو'),
    (6, '06_الدرس_السادس_المعية_العامة_والخاصة_وصفة_الكلام_وتنزيل_القرآن_والرؤية.md', 'اللقاء السادس: المعية العامة والخاصة، وإثبات صفة الكلام، وتنزيل القرآن غير مخلوق، والرؤية، وإثبات الصفات بالسنة', 'المعية والكلام والقرآن والرؤية'),
    (7, '07_الدرس_السابع_أحاديث_الصفات_ووسطية_أهل_السنة_والجماعة.md', 'اللقاء السابع: أحاديث الصفات من السنة النبوية، وخاتمة فصل الأسماء والصفات، ومقدمة وسطية أهل السنة والجماعة', 'أحاديث الصفات ومقدمة الوسطية'),
    (8, '08_الدرس_الثامن_وسطية_أهل_السنة_والرؤية_وفتنة_القبر_والموازين_والحساب.md', 'اللقاء الثامن: وسطية أهل السنة في فرق الأمة، والعلو والمعية والقرب، والقرآن كلام الله، والرؤية، وفتنة القبر والبعث والموازين والدواوين', 'وسطية أهل السنة والرؤية والقبر والميزان'),
    (9, '09_الدرس_التاسع_الحوض_والصراط_والشفاعات_والقدر_وحقيقة_الإيمان_وأهل_الكبائر.md', 'اللقاء التاسع: الحوض والصراط والقنطرة، والشفاعات الثلاث، والإيمان بالقدر بدرجتيه، وحقيقة الإيمان وحكم أهل الكبائر', 'الحوض والصراط والشفاعات والقدر والإيمان'),
    (10, '10_الدرس_العاشر_حقوق_الصحابة_وأهل_البيت_وكرامات_الأولياء_ومنهج_أهل_السنة_والخاتمة.md', 'اللقاء العاشر: حقوق الصحابة ومراتبهم، وأهل البيت وأمهات المؤمنين، وكرامات الأولياء، واتباع الآثار والإجماع، ومكارم الأخلاق وخاتمة المتن', 'الصحابة وأهل البيت والكرامات والأخلاق'),
]

json_name = 'book_data_edited.json' if IS_EDITED else 'book_data.json'
json_path = os.path.join(_ENG, json_name)
if not os.path.exists(json_path):
    print(f"File not found: {json_path}")
    exit(0)

book_json = json.load(open(json_path, encoding='utf-8'))
lessons_data = {l['lesson_num']: l for l in book_json.get('lessons', [])}
units_by_lesson = {}
for u in book_json.get('units', []):
    lnum = u['lesson_num']
    if lnum not in units_by_lesson:
        units_by_lesson[lnum] = []
    units_by_lesson[lnum].append(u)

full_volume_lines = [
    f"# {book_json.get('title', 'اللَّآلِئُ الجَوْهَرِيَّةُ عَلَى مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ')}",
    f"## {book_json.get('subtitle', 'شَرْحُ مَتْنِ العَقِيدَةِ الوَاسِطِيَّةِ لِشَيْخِ الإِسْلَامِ ابْنِ تَيْمِيَّةَ')}",
    "",
    f"**المتن:** {book_json.get('author_matn', '')}  ",
    f"**الشرح:** {book_json.get('author_sharh', '')}  ",
    f"**النسخة:** {'النسخة المحررة المهذبة (بكلام الشيخ بلفظه دون اختصار مع الاقتصار على مقدمة اللقاء الأول وخاتمة الأخير وتهذيب التكرار المتتابع)' if IS_EDITED else 'النسخة الحرفية الكاملة كما ألقيت'}  ",
    "",
    "---",
    "",
]

for lnum, fname, full_title, short_title in LESSON_SPECS:
    if lnum not in units_by_lesson:
        continue
    u_list = units_by_lesson[lnum]
    pinfo = lessons_data.get(lnum, {})
    disp_title = full_title.replace('اللقاء ', 'المحاضرة رقم ') if IS_EDITED else full_title
    
    lesson_md = []
    lesson_md.append(f"# {disp_title}")
    lesson_md.append("")
    if pinfo.get('url'):
        lesson_md.append(f"> 🔗 **رابط المحاضرة الأصلية:** [{pinfo.get('url')}]({pinfo.get('url')}) — المدة: {pinfo.get('duration_min', 0)} دقيقة ({to_e(pinfo.get('duration_min', 0))} د)")
        lesson_md.append("")
    lesson_md.append("---")
    lesson_md.append("")

    for u in u_list:
        if u.get('heading'):
            lesson_md.append(f"## {u['heading']}")
            lesson_md.append("")
        
        if u.get('matn_raw'):
            lesson_md.append("> ### [ مَتْنُ العَقِيدَةِ الوَاسِطِيَّةِ ]")
            for ml in u['matn_raw'].splitlines():
                if ml.strip():
                    lesson_md.append(f"> **{ml.strip()}**")
            lesson_md.append("")
            lesson_md.append("---")
            lesson_md.append("")

        for p_html in u.get('sharh_paras_html', []):
            p_text = re.sub(r'<span class="ayah(?:-ref)?">([^<]+)</span>', r'\1', p_html)
            p_text = re.sub(r'<strong>([^<]+)</strong>', r'**\1**', p_text)
            p_text = re.sub(r'<[^>]+>', '', p_text)
            lesson_md.append(p_text.strip())
            lesson_md.append("")

        if u.get('glosses'):
            lesson_md.append("")
            lesson_md.append("##### الحواشي ومعاني المفردات:")
            for g in u['glosses']:
                lesson_md.append(f"- **{g['term']}**: {g['gloss']}")
            lesson_md.append("")

        lesson_md.append("")

    file_path = os.path.join(out_dir, fname)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lesson_md).strip() + '\n')
    print(f"Saved: {file_path}")

    full_volume_lines.extend(lesson_md)
    full_volume_lines.append("")
    full_volume_lines.append("---")
    full_volume_lines.append("")

vol_name = 'اللَّآلِئُ_الجَوْهَرِيَّةُ_عَلَى_مَتْنِ_العَقِيدَةِ_الوَاسِطِيَّةِ_النسخة_المحررة.md' if IS_EDITED else 'اللَّآلِئُ_الجَوْهَرِيَّةُ_عَلَى_مَتْنِ_العَقِيدَةِ_الوَاسِطِيَّةِ.md'
vol_path = os.path.join(out_dir, vol_name)
with open(vol_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(full_volume_lines).strip() + '\n')
print(f"Saved Full Volume Markdown: {vol_path}")
