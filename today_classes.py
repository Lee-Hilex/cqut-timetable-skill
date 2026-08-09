# -*- coding: utf-8 -*-
"""
课表查询工具 v1.2.0
根据当前日期(或指定日期)计算周次,列出当天的课。

新增(v1.2.0): 大节概念(1-2节→第1大节)、自定义课程(custom_courses.json)、
            单日卡片布局、单周七列×五行网格、多教师省略号

用法:
  python today_classes.py                 # 今天有什么课
  python today_classes.py --date 2026-09-14   # 指定日期
  python today_classes.py --week 3 --day 2    # 第3周周二(1=周一)
  python today_classes.py --week 3              # 第3周全周课表(网格)
  python today_classes.py --week 3 --day 2       # 第3周周二(1=周一,日卡片)
  python today_classes.py --config config.json
  python today_classes.py --schedule schedule_2026_1.json
  python today_classes.py --list                 # 列出全部课程(按星期)

自定义课程: 在脚本同目录创建 custom_courses.json,格式见 README。

校区说明: config.json 的 campus 字段为 huaxi(花溪) 或 liangjiang(两江),
          class_time 为按校区分组的作息时间表。首次使用会交互询问校区。
"""
import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEEKDAY_CN = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
CAMPUS_CN = {'huaxi': '花溪校区', 'liangjiang': '两江校区'}

# 兼容旧配置: 若 class_time 是数组(非 dict),按花溪处理
DEFAULT_CAMPUS = 'huaxi'

# 大节标签: 两个小节组成一个大节,一天最多五个大节
BIG_SECTION_LABELS = {1: '1-2节', 2: '3-4节', 3: '5-6节', 4: '7-8节', 5: '9-10节'}


def load_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def disp_width(s):
    """计算字符串显示宽度(中文等全角字符按 2 计)"""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w


def pad(s, width):
    """按显示宽度左对齐补齐"""
    return s + ' ' * max(0, width - disp_width(s))


def ensure_campus(cfg, config_path):
    """确保 config 有 campus 字段;没有则交互询问并写回。返回 (cfg, campus)"""
    ct = cfg.get('class_time')
    if isinstance(ct, dict):
        campus = cfg.get('campus') or DEFAULT_CAMPUS
        if campus not in ct:
            campus = DEFAULT_CAMPUS
        return cfg, campus

    # 旧格式: 数组作息表 → 询问校区并升级配置
    print('检测到旧版配置(作息表为单一数组)。请选择你的校区:')
    print('  1) 花溪校区 (8:20 开始, 11 节)')
    print('  2) 两江校区 (8:30 开始, 10 节)')
    choice = input('请输入 1 或 2 [默认 1]: ').strip().replace('\ufeff','').replace('\x00','')
    campus = 'liangjiang' if choice == '2' else DEFAULT_CAMPUS

    cfg['campus'] = campus
    # 提供双校区作息表
    huaxi = [
        ['08:20', '09:05'], ['09:15', '10:00'], ['10:20', '11:05'],
        ['11:15', '12:00'], ['14:00', '14:45'], ['14:55', '15:40'],
        ['16:00', '16:45'], ['16:55', '17:40'], ['19:00', '19:45'],
        ['19:55', '20:40'], ['20:50', '21:35'],
    ]
    liangjiang = [
        ['08:30', '09:15'], ['09:25', '10:10'], ['10:30', '11:15'],
        ['11:25', '12:10'], ['14:20', '15:05'], ['15:15', '16:00'],
        ['16:20', '17:05'], ['17:15', '18:00'], ['19:00', '19:45'],
        ['19:50', '20:35'],
    ]
    cfg['class_time'] = {'huaxi': huaxi, 'liangjiang': liangjiang}

    # 写回(若文件可写)
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f'✅ 已选择 {CAMPUS_CN[campus]},配置已写入 {config_path}')
    except OSError:
        print(f'⚠️ 无法写回 {config_path},本次使用 {CAMPUS_CN[campus]}')
    return cfg, campus


def ensure_semester_start(cfg, config_path, schedule=None):
    """确保 config 有 semester_start(开学日期,第一周第一天,可能不是周一)。
    首次使用或无课时交互询问;有 schedule 时用其学期信息辅助提示。
    返回 semester_start 字符串(YYYY-MM-DD)。
    """
    current = str(cfg.get('semester_start') or '').strip()
    # 校验格式
    valid = False
    if current:
        try:
            datetime.date.fromisoformat(current)
            valid = True
        except ValueError:
            valid = False

    if valid:
        return current

    print('\n请确认本学期开学日期(第一周的第一天,不一定是周一):')
    if schedule:
        print(f'  (当前课表: {schedule.get("schoolYear")} 学年第{schedule.get("schoolTerm")}学期)')
    print('  例如 2026-09-07,回车跳过则用 2026-09-01')
    ans = input('  开学日期 [YYYY-MM-DD]: ').strip()
    # 只保留数字和连字符,过滤 BOM/控制字符/零宽字符(PowerShell 管道易带)
    ans = re.sub(r'[^0-9\-]', '', ans).strip('-')
    if not ans:
        ans = '2026-09-01'
    try:
        d = datetime.date.fromisoformat(ans)
    except ValueError:
        print(f'⚠️ 日期格式无效({ans}),使用默认 2026-09-01')
        d = datetime.date.fromisoformat('2026-09-01')
    ans = d.isoformat()

    cfg['semester_start'] = ans
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f'✅ 开学日期 {ans} 已写入 {config_path}')
    except OSError:
        print(f'⚠️ 无法写回 {config_path},本次使用 {ans}')
    return ans


def parse_weeks(week_str):
    """解析周次字符串,返回包含的周集合。
    支持: "2-6周" / "4-6周,9-12周,14-18周" / "15-19周(单)" / "10-16周(双)" / "11周"
    """
    weeks = set()
    if not week_str:
        return weeks
    for part in re.split(r'[,，]', week_str):
        part = part.strip()
        odd = '单' in part
        even = '双' in part
        m = re.search(r'(\d+)\s*[-—~至]\s*(\d+)', part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            rng = range(a, b + 1)
        else:
            m2 = re.search(r'\d+', part)
            if not m2:
                continue
            rng = [int(m2.group(0))]
        for w in rng:
            if odd and w % 2 == 0:
                continue
            if even and w % 2 == 1:
                continue
            weeks.add(w)
    return weeks


def get_week(today, semester_start):
    """计算今天是第几周。

    semester_start 是开学日期(第一周第一天,可能是周中)。
    周次按自然周对齐: 开学日所在自然周(周一起)为第 1 周。
    这样第一周可能不完整(如周三开学,则第 1 周只有周三~周日)。
    开学前返回 0。
    """
    start = datetime.date.fromisoformat(semester_start)
    if today < start:
        return 0  # 还没开学
    # 第一周的周一(开学日所在自然周的周一)
    first_monday = start - datetime.timedelta(days=start.weekday())
    delta = (today - first_monday).days
    return delta // 7 + 1


def parse_session(course_section):
    """解析节次,返回起始节和结束节,如 '3-4节' -> (3, 4)"""
    m = re.search(r'(\d+)\s*[-—~至]\s*(\d+)', course_section or '')
    if m:
        return int(m.group(1)), int(m.group(2))
    m2 = re.search(r'\d+', course_section or '')
    if m2:
        return int(m2.group(0)), int(m2.group(0))
    return 0, 0


def section_to_big(s, e):
    """将节次范围映射为大节编号(1-5)。
    1-2节→1, 3-4节→2, 5-6节→3, 7-8节→4, 9+→5
    """
    if not s:
        return 0
    avg = (s + e) // 2
    if avg <= 2:
        return 1
    if avg <= 4:
        return 2
    if avg <= 6:
        return 3
    if avg <= 8:
        return 4
    return 5


def truncate_teacher(teacher_str):
    """多个教师(逗号/顿号分隔)时只显示第一个,后跟 …"""
    if not teacher_str:
        return ''
    teachers = [t.strip() for t in re.split(r'[,，、]', teacher_str) if t.strip()]
    return teachers[0] if len(teachers) <= 1 else teachers[0] + '…'


def bold_md(s):
    """Markdown 加粗: 非空内容包 **,空内容原样返回"""
    return f'**{s}**' if s else ''


def plain_width(s):
    """计算显示宽度,但忽略 Markdown 加粗符号(**),用于对齐计算"""
    return disp_width(s.replace('**', ''))


def load_custom_courses():
    """加载 custom_courses.json(脚本同目录),返回课程列表或 []"""
    custom_path = os.path.join(BASE_DIR, 'custom_courses.json')
    if not os.path.exists(custom_path):
        return []
    try:
        courses = load_json(custom_path)
        return courses if isinstance(courses, list) else []
    except Exception:
        return []


def get_class_time(cfg, campus, start_session, end_session=None):
    """根据校区+节次范围查上课时间段,返回如 '08:20-09:05'"""
    ct = cfg.get('class_time')
    if isinstance(ct, dict):
        times = ct.get(campus) or []
    else:
        times = ct or []
    if 1 <= start_session <= len(times):
        start = times[start_session - 1][0]
        if end_session and 1 <= end_session <= len(times):
            end = times[end_session - 1][1]
        else:
            end = times[start_session - 1][1]
        return f'{start}-{end}'
    return '?'


def query(cfg, campus, schedule, week, day, custom=None):
    """查询第 week 周星期 day(1-7) 的课程(含自定义课程),按节次排序"""
    results = []
    # 教务课表
    for c in schedule.get('courses', []):
        try:
            wd = int(c.get('weekday'))
        except (TypeError, ValueError):
            continue
        if wd != day:
            continue
        weeks = parse_weeks(c.get('courseWeek'))
        if week in weeks:
            s, e = parse_session(c.get('courseSection'))
            results.append({
                'course': c.get('courseTitle'),
                'teacher': c.get('teacher'),
                'sessions': c.get('courseSection'),
                'sessionStart': s, 'sessionEnd': e,
                'big': section_to_big(s, e),
                'time': get_class_time(cfg, campus, s, e),
                'weeks': c.get('courseWeek'),
                'room': c.get('courseRoom'),
                'campus': c.get('campus'),
                'credit': c.get('credit'),
                'courseId': c.get('courseId'),
                'courseTitle': c.get('courseTitle'),
            })
    # 自定义课程
    for c in (custom or []):
        try:
            wd = int(c.get('weekday'))
        except (TypeError, ValueError):
            continue
        if wd != day:
            continue
        wks = parse_weeks(c.get('weeks'))
        if week not in wks:
            continue
        s, e = parse_session(c.get('sessions'))
        title = c.get('title', '')
        results.append({
            'course': title,
            'teacher': c.get('teacher', ''),
            'sessions': c.get('sessions', ''),
            'sessionStart': s, 'sessionEnd': e,
            'big': section_to_big(s, e),
            'time': get_class_time(cfg, campus, s, e),
            'weeks': c.get('weeks', ''),
            'room': c.get('room', ''),
            'campus': campus,
            'credit': c.get('credit'),
            'courseId': 'custom_' + title,
            'courseTitle': title,
            'custom': True,
        })
    results.sort(key=lambda x: x['sessionStart'])
    return results


def _course_key(c):
    """课程去重键: 优先 courseId, fallback 为 courseTitle"""
    return c.get('courseId', '') or c.get('courseTitle', '')


def total_credit(schedule, custom=None):
    """学期总学分(按课程去重求和,含自定义课程)"""
    seen = set()
    total = 0.0
    for c in schedule.get('courses', []):
        kid = _course_key(c)
        if kid and kid not in seen:
            seen.add(kid)
            try:
                total += float(c.get('credit') or 0)
            except (TypeError, ValueError):
                pass
    for c in (custom or []):
        kid = 'custom_' + c.get('title', '')
        if kid and kid not in seen:
            seen.add(kid)
            try:
                total += float(c.get('credit') or 0)
            except (TypeError, ValueError):
                pass
    return total


def day_credit_sum(results):
    """当日学分(去重)"""
    seen = set()
    total = 0.0
    for r in results:
        kid = _course_key(r)
        if kid and kid not in seen:
            seen.add(kid)
            try:
                total += float(r.get('credit') or 0)
            except (TypeError, ValueError):
                pass
    return total


def _schedule_max_week(schedule, custom=None):
    """课表最大周次(含自定义)"""
    mw = 0
    for c in schedule.get('courses', []):
        w = parse_weeks(c.get('courseWeek'))
        if w:
            mw = max(mw, max(w))
    for c in (custom or []):
        w = parse_weeks(c.get('weeks'))
        if w:
            mw = max(mw, max(w))
    return mw


# ── 单日卡片布局(纵向堆叠) ──────────────────────────────────

def fmt_day_cards_md(week, day, results, today, schedule, campus, ttl):
    """单日 markdown 表格: 三列(节次+时间 / 课程 / 教室),教室加粗,紧凑"""
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    date_str = f" ({today.isoformat()})" if today else ''
    campus_name = CAMPUS_CN.get(campus, '')
    lines = [f'📚 {term} · 第{week}周 {WEEKDAY_CN[day - 1]}{date_str}']

    if not results:
        hint = ''
        mw = _schedule_max_week(schedule)
        if week > mw > 0:
            hint = f'\n💡 当前第{week}周已超过课表最大第{mw}周,学期可能已结束'
        lines.append(f'🟢 {campus_name} 今天没有课,可以休息!{hint}')
        return '\n'.join(lines)

    bigs = sorted(set(r['big'] for r in results))
    big_count = len(bigs)
    small_count = len(results)
    lines.append(f'🏫 {campus_name} · 共 {big_count} 大节（{small_count} 小节）')
    lines.append('')

    # markdown 表格: 节次+时间 / 课程 / 教室
    lines.append('| 节次 | 课程 | 教室 |')
    lines.append('|---|---|---|')
    for r in results:
        label = BIG_SECTION_LABELS.get(r['big'], f'大节{r["big"]}')
        lines.append(f'| {label} {r["time"]} | {str(r["course"] or "")} | {bold_md(str(r["room"] or ""))} |')

    dc = day_credit_sum(results)
    if ttl > 0:
        pct = dc / ttl * 100
        lines.append(f'\n🎓 今日学分 {dc:g} / 学期总学分 {ttl:g} ({pct:.1f}%)')
    return '\n'.join(lines)


def fmt_day_cards(week, day, results, today, schedule, campus, ttl):
    """三行一列×n: 每大节一张卡片,纵向堆叠;每卡片三行(课程名/教室/教师)"""
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    date_str = f" ({today.isoformat()})" if today else ''
    campus_name = CAMPUS_CN.get(campus, '')
    header = f'📚 {term} · 第{week}周 {WEEKDAY_CN[day - 1]}{date_str}'
    lines = [header]

    if not results:
        hint = ''
        mw = _schedule_max_week(schedule)
        if week > mw > 0:
            hint = f'\n💡 当前第{week}周已超过课表最大第{mw}周,学期可能已结束'
        lines.append(f'🟢 {campus_name} 今天没有课,可以休息!{hint}')
        return '\n'.join(lines)

    # 大节/小节计数
    bigs = sorted(set(r['big'] for r in results))
    big_count = len(bigs)
    small_count = len(results)
    lines.append(f'🏫 {campus_name} · 共 {big_count} 大节（{small_count} 小节）')
    lines.append('')

    # 计算卡片宽度
    max_w = 4
    for r in results:
        for field in ['course', 'room']:
            w = disp_width(str(r.get(field, '') or ''))
            if w > max_w:
                max_w = w
        w = disp_width(truncate_teacher(r.get('teacher', '')))
        if w > max_w:
            max_w = w
        w = disp_width(f"{BIG_SECTION_LABELS.get(r['big'], '')}  {r['time']}")
        if w > max_w:
            max_w = w
    card_width = max_w + 6  # padding + borders

    sep_top = '┌' + '─' * (card_width - 2) + '┐'
    sep_mid = '├' + '─' * (card_width - 2) + '┤'
    sep_bot = '└' + '─' * (card_width - 2) + '┘'

    # 按大节分组,同一大节内可能有多门课(罕见)
    by_big = {}
    for r in results:
        by_big.setdefault(r['big'], []).append(r)

    first = True
    for b in sorted(by_big):
        entries = by_big[b]
        label = BIG_SECTION_LABELS.get(b, f'大节{b}')
        # 大节分隔
        if first:
            lines.append(sep_top)
            first = False
        else:
            lines.append(sep_mid)

        for j, r in enumerate(entries):
            if j > 0:
                lines.append('│' + ' ' * (card_width - 2) + '│')  # 同大节内课程间空行
            # 标题行: 大节标签 + 时间
            title_line = f"  {label}  {r['time']}"
            lines.append('│' + pad(title_line, card_width - 2) + '│')
            # 课程名
            lines.append('│' + pad('  ' + str(r['course'] or ''), card_width - 2) + '│')
            # 教室
            lines.append('│' + pad('  ' + str(r['room'] or ''), card_width - 2) + '│')
            # 教师(多个时截断)
            lines.append('│' + pad('  ' + truncate_teacher(r.get('teacher', '')), card_width - 2) + '│')

    lines.append(sep_bot)
    lines.append('')

    # 学分统计
    dc = day_credit_sum(results)
    if ttl > 0:
        pct = dc / ttl * 100
        lines.append(f'🎓 今日学分 {dc:g} / 学期总学分 {ttl:g} ({pct:.1f}%)')
    return '\n'.join(lines)


# ── 单周网格布局(七列×五行) ──────────────────────────────────

def fmt_week_grid_md(week, results_by_day, schedule, campus, ttl):
    """单周 markdown 表格: 七列(周一~周日),每大节一行,格内"课程 / **教室**",节次列带时间段。紧凑,不用 <br>(raw HTML 会被转义)"""
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    campus_name = CAMPUS_CN.get(campus, '')
    lines = [f'📅 {term} · 第{week}周课表', f'🏫 {campus_name}', '']

    # 构建 5×7 网格: 每格一行文本 "课程 / **教室**"; 记录每个大节的时间段
    grid = [['' for _ in range(7)] for _ in range(5)]
    big_times = {}
    for day in range(1, 8):
        for r in results_by_day.get(day, []):
            b = r['big']
            if 1 <= b <= 5:
                big_times.setdefault(b, r.get('time', ''))
                entry = f"{str(r['course'] or '')} / {bold_md(str(r['room'] or ''))}".strip(' /')
                if grid[b - 1][day - 1]:
                    grid[b - 1][day - 1] += ' / ' + entry
                else:
                    grid[b - 1][day - 1] = entry

    # markdown 表格: 每大节一行
    headers = ['节次'] + WEEKDAY_CN[:7]
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('|' + '---|' * 8)
    for bi in range(5):
        label = BIG_SECTION_LABELS.get(bi + 1, '')
        t = big_times.get(bi + 1, '')
        label_cell = f'{label} {t}'.strip()
        cells = [label_cell] + [grid[bi][di] for di in range(7)]
        lines.append('| ' + ' | '.join(cells) + ' |')

    # 统计
    big_set = set()
    small_count = 0
    for day in range(1, 8):
        for r in results_by_day.get(day, []):
            big_set.add((day, r['big']))
            small_count += 1
    lines.append(f'\n📊 本周共 {len(big_set)} 大节（{small_count} 小节）')
    if ttl > 0:
        lines.append(f'🎓 学期总学分: {ttl:g}')
    return '\n'.join(lines)


def fmt_week_grid(week, results_by_day, schedule, campus, ttl):
    """七列(周一~周日)×五行(五大节)网格,每格三行(课程/教室/教师)"""
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    campus_name = CAMPUS_CN.get(campus, '')
    lines = [f'📅 {term} · 第{week}周课表', f'🏫 {campus_name}', '']

    # 构建 5×7 网格内容
    grid = [[[] for _ in range(7)] for _ in range(5)]
    for day in range(1, 8):
        for r in results_by_day.get(day, []):
            b = r['big']
            if 1 <= b <= 5 and not grid[b - 1][day - 1]:
                grid[b - 1][day - 1] = [
                    str(r['course'] or ''),
                    bold_md(str(r['room'] or '')),
                    truncate_teacher(r.get('teacher', '')),
                ]
            elif 1 <= b <= 5 and grid[b - 1][day - 1]:
                # 同大节第二门课: 追加到已有格(罕见)
                cell = grid[b - 1][day - 1]
                cell[0] += '/' + str(r['course'] or '')
                room = str(r['room'] or '')
                if room and not room in cell[1].replace('**', ''):
                    cell[1] = bold_md(cell[1].replace('**', '') + '/' + room)

    # 计算列宽
    label_width = 6
    day_widths = [8] * 7
    for bi in range(5):
        for di in range(7):
            cell = grid[bi][di]
            for line in cell:
                w = plain_width(line)
                if w > day_widths[di]:
                    day_widths[di] = w
    day_widths = [max(w, 8) for w in day_widths]
    col_widths = [label_width] + day_widths

    def _row(cells):
        return '│' + '│'.join(pad(c, w) for c, w in zip(cells, col_widths)) + '│'

    # 表头行
    sep_top = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    lines.append(sep_top)
    lines.append(_row([''] + WEEKDAY_CN[:7]))

    # 五大节
    for bi in range(5):
        sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
        if bi > 0:
            lines.append(sep)
        label = BIG_SECTION_LABELS.get(bi + 1, '')
        for sub in range(3):  # 课程名/教室/教师
            cells = [label if sub == 0 else '']
            for di in range(7):
                cell = grid[bi][di]
                cells.append(cell[sub] if len(cell) > sub else '')
            lines.append(_row(cells))

    sep_bot = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    lines.append(sep_bot)

    # 统计
    big_set = set()
    small_count = 0
    for day in range(1, 8):
        for r in results_by_day.get(day, []):
            big_set.add((day, r['big']))
            small_count += 1
    lines.append(f'\n📊 本周共 {len(big_set)} 大节（{small_count} 小节）')
    if ttl > 0:
        lines.append(f'🎓 学期总学分: {ttl:g}')
    return '\n'.join(lines)


# ── 旧格式(保留 --list 使用) ──────────────────────────────────

def render_table(rows, campus):
    """渲染美观的表格(考虑中英文宽度对齐)"""
    if not rows:
        return None
    headers = ['时间', '节次', '课程', '教师', '学分', '地点']
    cols = ['time', 'sessions', 'course', 'teacher', 'credit', 'room']
    widths = [disp_width(h) for h in headers]
    for r in rows:
        for i, c in enumerate(cols):
            widths[i] = max(widths[i], disp_width(str(r[c] or '')))
    widths = [min(w, 28) for w in widths]

    sep = '┌' + '┬'.join('─' * (w + 2) for w in widths) + '┐'
    hdr = '│' + '│'.join(' ' + pad(h, w) + ' ' for h, w in zip(headers, widths)) + '│'
    div = '├' + '┼'.join('─' * (w + 2) for w in widths) + '┤'
    foot = '└' + '┴'.join('─' * (w + 2) for w in widths) + '┘'

    lines = [sep, hdr, div]
    for r in rows:
        cells = []
        for i, c in enumerate(cols):
            v = str(r[c] or '')
            if disp_width(v) > widths[i]:
                while disp_width(v) > widths[i] - 1 and len(v) > 1:
                    v = v[:-1]
                v = v + '…'
            cells.append(' ' + pad(v, widths[i]) + ' ')
        lines.append('│' + '│'.join(cells) + '│')
    lines.append(foot)
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=os.path.join(BASE_DIR, 'config.json'))
    ap.add_argument('--schedule', default=None, help='课表 JSON 文件')
    ap.add_argument('--date', default=None, help='YYYY-MM-DD,默认今天')
    ap.add_argument('--week', type=int, default=None, help='第几周')
    ap.add_argument('--day', type=int, default=None, help='星期几 1-7')
    ap.add_argument('--list', action='store_true', help='列出全部课程(旧表格格式)')
    ap.add_argument('--markdown', action='store_true',
                    help='输出 markdown 表格(供 Agent 原样展示;终端默认 ASCII)')
    args = ap.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f'错误: 找不到配置文件 {config_path}')
        sys.exit(1)
    cfg = load_json(config_path)
    cfg, campus = ensure_campus(cfg, config_path)

    sched_path = args.schedule
    if not sched_path:
        cands = sorted([f for f in os.listdir(BASE_DIR)
                        if f.startswith('schedule_') and f.endswith('.json')])
        if cands:
            sched_path = os.path.join(BASE_DIR, cands[-1])
    schedule = None
    if sched_path and os.path.exists(sched_path):
        schedule = load_json(sched_path)
    else:
        print('错误: 找不到课表文件(schedule_*.json)。请先运行 '
              'fetch_schedule_browser.py 抓取课表,或用 --schedule 指定。')
        sys.exit(1)

    # 开学日期
    semester_start = ensure_semester_start(cfg, config_path, schedule)
    # 自定义课程
    custom = load_custom_courses()
    ttl = total_credit(schedule, custom)

    # ── --list: 旧横向表格(全部课程) ──
    if args.list:
        print(f'📚 全部课程 ({schedule.get("name")} {schedule.get("className")} '
              f'{schedule.get("major")} · {schedule.get("schoolYear")} 学年第'
              f'{schedule.get("schoolTerm")}学期)')

        if custom:
            print(f'📝 含 {len(custom)} 门自定义课程')

        for d in range(1, 8):
            rows = [c for c in schedule.get('courses', [])
                    if str(c.get('weekday')) == str(d)]
            for cc in custom:
                if str(cc.get('weekday')) == str(d):
                    rows.append({
                        'courseTitle': cc.get('title'),
                        'teacher': cc.get('teacher', ''),
                        'courseSection': cc.get('sessions', ''),
                        'courseWeek': cc.get('weeks', ''),
                        'courseRoom': cc.get('room', ''),
                        'campus': campus,
                        'credit': cc.get('credit'),
                    })
            if not rows:
                continue
            print(f'\n📅 {WEEKDAY_CN[d - 1]}:')
            recs = []
            for c in sorted(rows, key=lambda x: parse_session(x.get('courseSection', ''))[0]):
                s, e = parse_session(c.get('courseSection', ''))
                recs.append({
                    'time': get_class_time(cfg, campus, s, e),
                    'sessions': c.get('courseSection', ''),
                    'course': c.get('courseTitle'),
                    'teacher': c.get('teacher'),
                    'credit': c.get('credit'),
                    'room': (f"{c.get('campus')} " if c.get('campus') else '') + (c.get('courseRoom') or ''),
                })
            print(render_table(recs, campus))
        if ttl > 0:
            print(f'\n🎓 学期总学分: {ttl:g}')
        return

    # ── 计算目标日期/周次 ──
    week_mode = False  # True = 整周网格, False = 单日卡片
    if args.day and not args.week:
        print('错误: --day 需要配合 --week 一起使用。例如 --week 3 --day 2')
        sys.exit(1)
    if args.week and args.day:
        week, day = args.week, args.day
        today = None
    elif args.week:
        week = args.week
        today = None
        week_mode = True
    elif args.date:
        today = datetime.date.fromisoformat(args.date)
        week = get_week(today, semester_start)
        day = today.isoweekday()
    else:
        today = datetime.date.today()
        week = get_week(today, semester_start)
        day = today.isoweekday()

    if week <= 0:
        start = datetime.date.fromisoformat(semester_start)
        print(f'📅 还没开学(学期开始: {start}),当前周次为 0')
        print('课程从开学后第 1 周开始。')
        return

    # ── 整周网格模式 ──
    if week_mode:
        results_by_day = {}
        for d in range(1, 8):
            results_by_day[d] = query(cfg, campus, schedule, week, d, custom)
        if args.markdown:
            print(fmt_week_grid_md(week, results_by_day, schedule, campus, ttl))
        else:
            print(fmt_week_grid(week, results_by_day, schedule, campus, ttl))
        return

    # ── 单日卡片模式 ──
    results = query(cfg, campus, schedule, week, day, custom)
    if args.markdown:
        print(fmt_day_cards_md(week, day, results, today, schedule, campus, ttl))
    else:
        print(fmt_day_cards(week, day, results, today, schedule, campus, ttl))


if __name__ == '__main__':
    main()
