<!-- markdownlint-disable -->

<div align="right">

<a href="README.md">🇨🇳 简体中文</a> | **<a href="README.en.md">🇬🇧 English</a>**

</div>

<div align="center">

# 🎓 cqut-timetable-skill

CQUT class schedule query Skill — ask "what classes do I have today" and get schedule, weeks, credits instantly<br>
Powered by Python + Playwright (real browser to bypass SSO / RS-WAF)

[Issues](https://github.com/Lee-Hilex/cqut-timetable-skill/issues) · [Changelog](https://github.com/Lee-Hilex/cqut-timetable-skill/releases) <br>
[Quick Start](#quick-start) · [How It Works](#-how-it-works) · [Disclaimer](#-disclaimer)

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/Lee-Hilex/cqut-timetable-skill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Stars](https://img.shields.io/github/stars/Lee-Hilex/cqut-timetable-skill?color=ffcb47&labelColor=black)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Playwright](https://img.shields.io/badge/Playwright-v1-%232EAD33)
![Zero Deps](https://img.shields.io/badge/Query-Zero_Deps-brightgreen)

</div>

<!-- markdownlint-restore -->

---

## Why cqut-timetable-skill

Tired of opening the academic portal, typing your student ID and password, and fighting CAPTCHAs and WAF blocks just to check your schedule? This Skill automates the whole pipeline — **login → fetch schedule → calculate week → answer** — so you can just ask "what classes do I have today" and get an instant answer.

- **Tailored for CQUT**: Zhengfang academic system + UIS unified authentication + RS-WAF, one pipeline to rule them all
- **Conversational queries**: install as a Skill and just talk to your Agent; it figures out the current week, today's classes, and time slots automatically
- **Zero-dependency queries**: fetch once, query locally forever — no login, no network, no extra dependencies

> ⚠️ Other universities using "Zhengfang academic system + unified authentication" can adapt `fetch_schedule_browser.py`'s SSO flow for their own setup.

## Features

- **🔐 Auto login & fetch** — Playwright real browser handles UIS unified authentication, RS-WAF, and SSO ticket exchange to grab your entire semester schedule in one shot

  ```text
  $ python fetch_schedule_browser.py --year 2026 --term 1
  ① Logging into unified auth (student ID 1251*****25)...
  ② Obtaining SSO ticket, entering academic system...
  ③ Fetching 2026 Fall semester schedule...
  ✅ Success: John Doe / Applied Chemistry / 15 courses → schedule_2026_1.json
  ```

- **📅 Smart querying** — auto-calculates the current academic week; ask "today / tomorrow / week X day Y" with credit stats

  ```text
  $ python today_classes.py --date 2026-09-18
  📚 2026-2027 AY Semester 1 · Week 3 Friday (2026-09-18)
  🏫 Huaxi Campus · 2 big sections (2 sub-sessions)

  ┌──────────────────────┐
  │  1-2   08:20-10:00   │
  │  Physical Chemistry  │
  │  1-0516              │
  │  Zhou W…             │
  ├──────────────────────┤
  │  5-6   14:00-15:40   │
  │  Organic Chemistry   │
  │  3-0405              │
  │  Zhou D…             │
  └──────────────────────┘

  🎓 Today: 6.5 credits / Total: 18.75 (34.7%)
  ```

- **🗓️ Week grid view** — `--week 3` shows a 7-column (Mon–Sun) × 5-row (big sections) grid, with course/room/teacher at a glance

  ```text
  $ python today_classes.py --week 3
  📅 2026-2027 AY Semester 1 · Week 3
  ┌──────┬────────┬────────┬────────┬────────┬────────┬──────┬──────┐
  │      │  Mon   │  Tue   │  Wed   │  Thu   │  Fri   │  Sat  │  Sun  │
  │ 1-2  │        │Socialism│OrgChem │        │PhyChem │        │      │
  │      │        │1-0708  │3-0603  │        │1-0516  │        │      │
  │      │        │Hu CX   │Zhou D… │        │Zhou W… │        │      │
  ├──────┼────────┼────────┼────────┼────────┼────────┼──────┼──────┤
  …(5 big-section rows total)
  📊 This week: 11 big sections (11 sub-sessions)
  ```

- **✏️ Custom courses (v1.2.0)** — add self-study, electives, etc. in `custom_courses.json`; auto-merged into schedule on query

  ```json
  [{"title":"Self-study","teacher":"N/A","weekday":3,"weeks":"2-16w","sessions":"7-8","room":"Library 301","credit":0}]
  ```

- **🎯 Big-section counting (v1.2.0)** — consecutive sessions form "big sections" (1-2→1st, 3-4→2nd, … 5 total); "how many classes" answers in big sections (+ sub-sessions)
- **👥 Teacher truncation (v1.2.0)** — multiple teachers (e.g. `Zhou W, Hu X`) shown as first name + `…`
- **🔄 Odd/even & multi-range weeks** — correctly parses `15-19w(odd)`, `10-16w(even)`, `4-6w,9-12w,14-18w`
- **⏱️ Partial first week** — semester starting mid-week is handled correctly with natural week alignment
- **⏰ Time range display** — time column shows full range (e.g. `10:20-12:00`) with start-to-end for multi-session blocks, not just start time
- **🏫 Dual campus schedules** — Huaxi (11 periods from 8:20) & Liangjiang (10 periods from 8:30), selected on first use
- **🛡️ Privacy-first** — credentials stay in local `config.json` (.gitignored), never sent to any third party
- **🧰 Auto dependency handling** — `check_deps.py` auto-detects and installs missing dependencies

## Use Cases

- Heading out in the morning: ask "what classes do I have today" — how many, when, which room, all at a glance
- Want a full view: "list everything this semester, total credits" — one command shows it all
- New semester: re-run the fetch script once and never log into the portal again

## 📥 Download & Install

| Method | Instructions |
|--------|-------------|
| **Zip (recommended)** | [cqut-timetable-skill-1.2.0.zip](dist/cqut-timetable-skill-1.2.0.zip) — unzip and use; contains all 11 files |
| **GitHub Releases** | Download source archives from the [Releases page](https://github.com/Lee-Hilex/cqut-timetable-skill/releases) |
| **Git clone** | `git clone git@github.com:Lee-Hilex/cqut-timetable-skill.git` |

## Quick Start

### 1. Environment check (auto-detects & installs deps)

This project ships with `check_deps.py` — it auto-checks your environment and installs any missing dependencies:

```bash
# Check environment (tells you exactly what's missing)
python check_deps.py

# Auto-download and install missing deps (playwright + Chromium)
python check_deps.py --install
```

| Function | Dependency | Notes |
|----------|-----------|-------|
| Query `today_classes.py` | **Zero** | Pure Python stdlib, works out of the box |
| Fetch `fetch_schedule_browser.py` | `playwright` + Chromium | `check_deps.py --install` auto-runs `pip install playwright` + `playwright install chromium` |

### 2. Configuration

```bash
cp config.example.json config.json
```

Edit `config.json` with your student ID and password:

```json
{
  "sid": "your_student_id",
  "pwd": "your_password",
  "campus": "huaxi",
  "semester_start": "2026-09-02",
  "class_time": {
    "huaxi": [
      ["08:20", "09:05"],
      ["09:15", "10:00"],
      ["10:20", "11:05"],
      ["11:15", "12:00"],
      ["14:00", "14:45"],
      ["14:55", "15:40"],
      ["16:00", "16:45"],
      ["16:55", "17:40"],
      ["19:00", "19:45"],
      ["19:55", "20:40"],
      ["20:50", "21:35"]
    ],
    "liangjiang": [
      ["08:30", "09:15"],
      ["09:25", "10:10"],
      ["10:30", "11:15"],
      ["11:25", "12:10"],
      ["14:20", "15:05"],
      ["15:15", "16:00"],
      ["16:20", "17:05"],
      ["17:15", "18:00"],
      ["19:00", "19:45"],
      ["19:50", "20:35"]
    ]
  }
}
```

| Field | Description |
|---|---|
| `sid` / `pwd` | Unified identity authentication credentials (same as uis.cqut.edu.cn) |
| `campus` | Campus: `huaxi` or `liangjiang`, determines bell schedule |
| `semester_start` | First day of semester (may be mid-week; recommended to fill manually, e.g. `2026-09-02`) |
| `class_time` | Bell schedule per campus (Huaxi: 11 periods from 8:20 / Liangjiang: 10 periods from 8:30) |

> 🔒 `config.json` is gitignored — your credentials never enter version control.
>
> 💡 On first use (or with legacy single-schedule config), `today_classes.py` will prompt you to pick a campus and upgrade the config — no manual `class_time` editing needed.
>
> 📅 Fill in `semester_start` manually (e.g. `2026-09-02`, the first day of semester; the Monday of that week is auto-aligned as Week 1 Monday). Leaving it blank triggers auto-detection during fetching, but **pre-semester detections may be inaccurate** — detected results will ask for manual confirmation; you can also enter it interactively during queries.

### 3. Fetch your schedule

```bash
python fetch_schedule_browser.py --year 2026 --term 1
# --term 1 = Fall, 2 = Spring
```

On success:
- Generates `schedule_2026_1.json` (contains name / student ID / courses / teachers / rooms / weeks / weekdays / credits)
- If `config.json` has no `semester_start`, the script attempts auto-detection: writes directly when the semester has started; prompts for manual confirmation pre-semester (returned week numbers may be inaccurate before classes begin) — you can also enter it interactively during queries later

### 4. Query your schedule

```bash
# What classes today?
python today_classes.py

# Specific date
python today_classes.py --date 2026-09-23

# Week 15, Thursday
python today_classes.py --week 15 --day 4

# List all courses
python today_classes.py --list
```

## 🤖 As a Skill (Reasonix / Agent)

Copy this directory to your Agent's skills directory, or in Reasonix:

```
/install-skill <path-to-this-directory>
```

> 🤖 **Install guide**: after installing this Skill, the Agent runs `check_deps.py` on first use to check the environment; missing dependencies are auto-downloaded (see Environment Check above). The query feature has zero dependencies and works immediately.

Then just talk:

> **You**: What classes do I have today?
>
> **Agent**:
> 📚 2026-2027 AY Semester 1 · Week 3 Wednesday
> ┌─────────────┬───────┬───────────┬────────┬───────┬─────────┐
> │ Time        │ Sess  │ Course    │ Teacher│ Credit│ Room    │
> ├─────────────┼───────┼───────────┼────────┼───────┼─────────┤
> │ 10:20-12:00 │ 3-4   │ Sample B  │ Mr. Li │ 2     │ 2-0202  │
> └─────────────┴───────┴───────────┴────────┴───────┴─────────┘
> 🏫 Huaxi Campus · 1 course
> 🎓 Today: 2 credits / Total: 7.5 (26.7%)

## 📦 Project Structure

```
cqut-timetable-skill/
├── check_deps.py                # Environment checker: auto-downloads & installs missing deps
├── fetch_schedule_browser.py    # Fetch script: UIS login → SSO → academic session → schedule API → semester start detection
├── today_classes.py             # Query tool: week calc + odd/even parser + credit stats + table output (zero deps)
├── config.example.json          # Configuration template (ID / password / campus / bell schedule)
├── custom_courses.example.json  # Custom course template (self-study, electives; v1.2.0)
├── sample_schedule.json         # Sample schedule data (anonymized, for demo)
├── SKILL.md                     # Skill definition (loaded by Agent)
└── .gitignore                   # Ignores config.json / custom_courses.json / real schedule (contains PII)
```

## 🧠 How It Works

CQUT's academic access chain (also common across many Chinese universities):

```
User  → uis.cqut.edu.cn         (unified auth / CAS)
      → ehall.cqut.edu.cn       (campus service portal)
      → getApplicationUrl API   (app code: UIVx60) → oauth ticket
        → jwxt.cqut.edu.cn/sso/yhiotlogin?ticket=...   (SSO exchange)
        → jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151  (schedule API)
```

Key points:
- Direct HTTP requests to the academic system are blocked by **RS-WAF** (returns 202 / challenge page); a real browser executing JavaScript is required
- After UIS login, grab `ump_token_pc-officeHall` from ehall cookies, call `getApplicationUrl` (app code `UIVx60` is the academic system's fixed platform code, independent of personal bookmarks) to obtain an oauth ticket — no UI clicking needed
- Use the ticket to access `sso/yhiotlogin` to complete ticket exchange and establish the academic session
- The schedule API POST requires `xnm` (academic year), `xqm` (semester: 3=Fall, 12=Spring), and `kzlx=ck`

## ⚠️ Disclaimer

- This project is for learning and research only. Please comply with your university's network usage policies and avoid excessive scraping.
- Credentials are stored only in your local `config.json`; the scripts never send credentials to any third party.
- Academic system API changes may break functionality. Please file an [issue](https://github.com/Lee-Hilex/cqut-timetable-skill/issues) if something stops working.

## 📄 License

[MIT](LICENSE)
