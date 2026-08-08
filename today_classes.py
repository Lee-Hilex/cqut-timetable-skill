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
"""
import argparse
import calendar
import datetime
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEEKDAY_CN = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def get_class_time(cfg, start_session):
    """根据起始节次查上课时间(如第3节 -> 10:00)"""
    times = cfg.get('class_time') or []
    if 1 <= start_session <= len(times):
        return times[start_session - 1][0]
    return '?'


def query(cfg, schedule, week, day):
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
                'time': get_class_time(cfg, s),
                'weeks': c.get('courseWeek'),
                'room': c.get('courseRoom'),
                'campus': c.get('campus'),
            })
    results.sort(key=lambda x: x['sessionStart'])
    return results


def fmt_result(week, day, results, today, schedule):
    lines = []
    term = f"{schedule.get('schoolYear')} 学年第{schedule.get('schoolTerm')}学期"
    lines.append(f'📚 {term} 课表 · 第{week}周 {WEEKDAY_CN[day-1]}'
                 f'({today.isoformat() if today else ""})')
    if not results:
        lines.append('🟢 今天没有课,可以休息!')
        return '\n'.join(lines)
    lines.append(f'共 {len(results)} 门课:')
    for r in results:
        loc = f"{r['campus']} {r['room']}".strip()
        lines.append(f'  {r["time"]} {r["sessions"]} | {r["course"]}'
                     f' | {r["teacher"]} | {loc}')
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

    cfg = load_json(args.config)
    semester_start = cfg.get('semester_start')
    if not semester_start:
        print('错误: config.json 缺少 semester_start(学期第一周周一日期)')
        sys.exit(1)

    sched_path = args.schedule
    if not sched_path:
        # 自动找最新课表文件
        cands = sorted([f for f in os.listdir(BASE_DIR)
                        if f.startswith('schedule_') and f.endswith('.json')])
        if cands:
            sched_path = os.path.join(BASE_DIR, cands[-1])
    if not sched_path or not os.path.exists(sched_path):
        print(f'错误: 找不到课表文件(schedule_*.json)。请先运行 '
              f'fetch_schedule_browser.py 抓取课表,或用 --schedule 指定。')
        sys.exit(1)
    schedule = load_json(sched_path)

    if args.list:
        print(f'📚 全部课程 ({schedule.get("name")} {schedule.get("className")} '
              f'{schedule.get("major")} · {schedule.get("schoolYear")} 学年第'
              f'{schedule.get("schoolTerm")}学期)')
        for d in range(1, 8):
            results = query(cfg, schedule, 99, d)  # week=99 不匹配任何周,只用于分组
            # 直接按天分组
            rows = [c for c in schedule.get('courses', []) if str(c.get('weekday')) == str(d)]
            if rows:
                print(f'\n{WEEKDAY_CN[d-1]}:')
                for c in sorted(rows, key=lambda x: parse_session(x.get('courseSection'))[0]):
                    s, e = parse_session(c.get('courseSection'))
                    print(f'  {get_class_time(cfg, s)} {c.get("courseSection")} | '
                          f'{c.get("courseTitle")} | {c.get("teacher")} | '
                          f'{c.get("campus")} {c.get("courseRoom")} | {c.get("courseWeek")}')
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

    results = query(cfg, schedule, week, day)
    print(fmt_result(week, day, results, today, schedule))


if __name__ == '__main__':
    main()
