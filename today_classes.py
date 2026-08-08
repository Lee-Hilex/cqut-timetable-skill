# -*- coding: utf-8 -*-
"""
课表查询工具: 根据当前日期(或指定日期)计算周次,列出当天的课。

用法:
  python today_classes.py                 # 今天有什么课
  python today_classes.py --date 2026-09-14   # 指定日期
  python today_classes.py --week 3 --day 2    # 第3周周二(1=周一)
  python today_classes.py --config config.json
  python today_classes.py --schedule schedule_2026_1.json
  python today_classes.py --list              # 列出全部课程(按星期)

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

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEEKDAY_CN = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
CAMPUS_CN = {'huaxi': '花溪校区', 'liangjiang': '两江校区'}

# 兼容旧配置: 若 class_time 是数组(非 dict),按花溪处理
DEFAULT_CAMPUS = 'huaxi'


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
    choice = input('请输入 1 或 2 [默认 1]: ').strip()
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
    """计算今天是第几周(从学期第一周周一算起)"""
    start = datetime.date.fromisoformat(semester_start)
    delta = (today - start).days
    if delta < 0:
        return 0  # 还没开学
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


def get_class_time(cfg, campus, start_session):
    """根据校区+起始节次查上课时间"""
    ct = cfg.get('class_time')
    if isinstance(ct, dict):
        times = ct.get(campus) or []
    else:
        times = ct or []
    if 1 <= start_session <= len(times):
        return times[start_session - 1][0]
    return '?'


def query(cfg, campus, schedule, week, day):
    """查询第 week 周星期 day(1-7) 的课程,按节次排序"""
    results = []
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
                'sessionStart': s,
                'sessionEnd': e,
                'time': get_class_time(cfg, campus, s),
                'weeks': c.get('courseWeek'),
                'room': c.get('courseRoom'),
                'campus': c.get('campus'),
            })
    results.sort(key=lambda x: x['sessionStart'])
    return results


def render_table(rows, campus):
    """渲染美观的表格(考虑中英文宽度对齐)"""
    if not rows:
        return None
    headers = ['时间', '节次', '课程', '教师', '地点']
    cols = ['time', 'sessions', 'course', 'teacher', 'room']
    # 计算每列最大宽度
    widths = [disp_width(h) for h in headers]
    for r in rows:
        for i, c in enumerate(cols):
            widths[i] = max(widths[i], disp_width(str(r[c] or '')))
    # 上限
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
            if len(v) > 28:
                v = v[:27] + '…'
            cells.append(' ' + pad(v, widths[i]) + ' ')
        lines.append('│' + '│'.join(cells) + '│')
    lines.append(foot)
    return '\n'.join(lines)


def fmt_result(week, day, results, today, schedule, campus):
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    date_str = f"({today.isoformat()})" if today else ''
    header = f'📚 {term} · 第{week}周 {WEEKDAY_CN[day-1]} {date_str}'
    campus_name = CAMPUS_CN.get(campus, '')
    table = render_table(results, campus)
    if not table:
        return f'{header}\n🟢 {campus_name} 今天没有课,可以休息!'
    lines = [header, table]
    if campus_name:
        lines.append(f'🏫 {campus_name} · 共 {len(results)} 门课')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=os.path.join(BASE_DIR, 'config.json'))
    ap.add_argument('--schedule', default=None, help='课表 JSON 文件')
    ap.add_argument('--date', default=None, help='YYYY-MM-DD,默认今天')
    ap.add_argument('--week', type=int, default=None, help='第几周')
    ap.add_argument('--day', type=int, default=None, help='星期几 1-7')
    ap.add_argument('--list', action='store_true', help='列出全部课程')
    args = ap.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f'错误: 找不到配置文件 {config_path}')
        sys.exit(1)
    cfg = load_json(config_path)
    cfg, campus = ensure_campus(cfg, config_path)
    semester_start = cfg.get('semester_start')
    if not semester_start:
        print('错误: config.json 缺少 semester_start(学期第一周周一日期)')
        sys.exit(1)

    sched_path = args.schedule
    if not sched_path:
        cands = sorted([f for f in os.listdir(BASE_DIR)
                        if f.startswith('schedule_') and f.endswith('.json')])
        if cands:
            sched_path = os.path.join(BASE_DIR, cands[-1])
    if not sched_path or not os.path.exists(sched_path):
        print('错误: 找不到课表文件(schedule_*.json)。请先运行 '
              'fetch_schedule_browser.py 抓取课表,或用 --schedule 指定。')
        sys.exit(1)
    schedule = load_json(sched_path)

    if args.list:
        print(f'📚 全部课程 ({schedule.get("name")} {schedule.get("className")} '
              f'{schedule.get("major")} · {schedule.get("schoolYear")} 学年第'
              f'{schedule.get("schoolTerm")}学期)')
        for d in range(1, 8):
            rows = [c for c in schedule.get('courses', [])
                    if str(c.get('weekday')) == str(d)]
            if not rows:
                continue
            print(f'\n📅 {WEEKDAY_CN[d-1]}:')
            recs = []
            for c in sorted(rows, key=lambda x: parse_session(x.get('courseSection'))[0]):
                s, e = parse_session(c.get('courseSection'))
                recs.append({
                    'time': get_class_time(cfg, campus, s),
                    'sessions': c.get('courseSection'),
                    'course': c.get('courseTitle'),
                    'teacher': c.get('teacher'),
                    'room': f"{c.get('campus')} {c.get('courseRoom')}",
                })
            print(render_table(recs, campus))
        return

    # 计算目标日期/周次
    if args.week and args.day:
        week, day = args.week, args.day
        today = None
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

    results = query(cfg, campus, schedule, week, day)
    print(fmt_result(week, day, results, today, schedule, campus))


if __name__ == '__main__':
    main()
