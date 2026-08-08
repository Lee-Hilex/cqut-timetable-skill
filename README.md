# 🎓 cqut-timetable-skill

![Version](https://img.shields.io/badge/version-1.1.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)

重庆理工大学课表查询 Skill —— 通过 AI 助手直接问"今天有什么课",自动算周次、解析单双周。

本项目是 [Reasonix](https://reasonix.ai) / Claude / 各类 Agent 可用的**技能包(Skill)**,也可作为独立命令行工具使用。核心价值:把"登录教务 → 抓课表 → 算周次 → 回答"全链路自动化,以后每天只需问一句。

> ⚠️ 本项目针对重庆理工大学定制(正方教务系统 + UIS 统一身份认证 + 瑞数 WAF)。其他使用正方教务+统一认证的高校可参考 `fetch_schedule_browser.py` 的 SSO 流程自行适配。

## 📥 下载

直接下载 zip 包(v1.1.2): [cqut-timetable-skill-1.1.2.zip](dist/cqut-timetable-skill-1.1.2.zip)

或通过 GitHub Releases 下载对应版本源码包。

---

## ✨ 功能

- 🔐 **自动登录**:Playwright 真实浏览器走 UIS 统一身份认证(https://uis.cqut.edu.cn),自动处理瑞数 WAF、SSO 换票,无需手动操作
- 📥 **自动抓课表**:通过 ehall `getApplicationUrl`(固定应用 code)拿 ticket 进教务,调用正方课表接口,一键抓取整学期课表
- 📅 **开学日期**:抓课表时尝试自动调用 ehall `getCurrentWeek` 反推,但**未开学时教务周次可能不准,结果仅供参考**;最可靠的方式是在 `config.json` 填 `semester_start` 或查询时手动输入一次
- 📅 **智能查询**:自动计算今天是第几周(基于开学日期),回答"今天/明天/某周周X 有什么课"
- 🔄 **单双周支持**:正确解析 `15-19周(单)`、`10-16周(双)`、`4-6周,9-12周,14-18周` 等多段周次
- ⏱️ **第一周不完整兼容**:开学日在周中时,周次按自然周对齐(开学日所在周即第 1 周),第一周不足 7 天也正确
- 🎓 **学分展示**:查询结果带学分列,并统计"今日学分 / 学期总学分 (占比)"
- 🏫 **双校区作息**:花溪(8:20 起 11 节)与两江(8:30 起 10 节)作息时间表,首次使用自动选择
- 🗣️ **对话式**:装成 Skill 后,直接问"今天有什么课"即可

## 📦 项目结构

```
cqut-timetable-skill/
├── check_deps.py                # 环境依赖检查脚本: 缺失自动下载安装
├── fetch_schedule_browser.py   # 抓取脚本: UIS 登录 → SSO → 教务会话 → 课表接口 → 开学日期检测
├── today_classes.py            # 查询工具: 算周次 + 单双周解析 + 学分统计 + 表格输出(零依赖)
├── config.example.json         # 配置模板(学号/密码/校区/作息时间)
├── sample_schedule.json        # 示例课表(脱敏,演示用)
├── SKILL.md                    # Skill 定义(供 Agent 加载)
└── .gitignore                  # 忽略真实 config.json 与真实课表(含个人信息)
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- **依赖自动处理**:本项目自带 `check_deps.py` 依赖检查脚本。**安装 Skill 或首次使用时会自动检查环境依赖,缺失的依赖会引导并自动下载安装**,无需手动逐个安装:

```bash
# 检查环境(会明确提示缺什么)
python check_deps.py

# 自动下载安装缺失依赖(playwright + Chromium)
python check_deps.py --install
```

依赖说明:
- **查询课表(`today_classes.py`): 零依赖**,纯 Python 标准库,装好即可用
- **抓取课表(`fetch_schedule_browser.py`): 需要 `playwright` + Chromium**,`check_deps.py --install` 会自动执行 `pip install playwright` + `playwright install chromium`

### 2. 配置

```bash
cp config.example.json config.json
```

编辑 `config.json`:

```json
{
  "base_url": "https://jwxt.cqut.edu.cn/jwglxt",
  "sid": "你的学号",
  "pwd": "你的教务密码",
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

> 💡 首次使用(或旧版单作息配置)时,`today_classes.py` 会自动提示选择校区并升级配置,无需手动编辑 `class_time`。

| 字段 | 说明 |
|---|---|
| `base_url` | 教务系统地址 |
| `sid` / `pwd` | 统一身份认证账号(与 uis.cqut.edu.cn 相同) |
| `campus` | 校区: `huaxi`(花溪)或 `liangjiang`(两江),决定用哪套作息时间 |
| `semester_start` | 开学日期(第一周第一天,可能是周中;留空则抓取时自动检测,查询时交互询问) |
| `class_time` | 按校区分组的作息时间表(花溪 11 节 8:20 起 / 两江 10 节 8:30 起) |

> 🔒 `config.json` 已加入 `.gitignore`,学号密码不会进入版本库。
>
> 📅 `semester_start` 建议手动填写(如 `2026-09-02`,开学当天;第一周周一会自动对齐为当周周一)。留空时抓取脚本会尝试自动检测,但**未开学时教务返回的周次可能不准**,检测结果会提示你人工确认,查询时也可手动输入一次。

### 3. 抓取课表

```bash
python fetch_schedule_browser.py --year 2026 --term 1
# --term 1 = 秋季学期, 2 = 春季学期
```

成功后:
- 生成 `schedule_2026_1.json`(包含姓名/学号/课程/老师/教室/周次/星期/学分)
- 若 `config.json` 未填 `semester_start`,脚本尝试自动检测开学日期:已开学时直接写入;未开学时提示人工确认(未开学时教务返回的周次可能不准),也可之后查询时手动输入

### 4. 查询课表

```bash
# 今天有什么课
python today_classes.py

# 指定日期
python today_classes.py --date 2026-09-23

# 第15周周四
python today_classes.py --week 15 --day 4

# 列出全部课程
python today_classes.py --list
```

命令行输出示例:

```text
$ python today_classes.py --date 2026-09-23
📚 2026-2027 学年第1学期 · 第3周 周三
┌─────────────┬───────┬───────────┬────────┬──────┬─────────┐
│ 时间        │ 节次  │ 课程      │ 教师   │ 学分 │ 地点    │
├─────────────┼───────┼───────────┼────────┼──────┼─────────┤
│ 10:20-12:00 │ 3-4节 │ 示例课程B │ 李老师 │ 2    │ 2教0202 │
└─────────────┴───────┴───────────┴────────┴──────┴─────────┘
🏫 花溪校区 · 共 1 门课
🎓 今日学分 2 / 学期总学分 7.5 (26.7%)
```

> ⏱️ 时间列显示**时间段**(如 `10:20-12:00` 表示第 3-4 节:第 3 节开始 10:20 到第 4 节结束 12:00),跨节次课程取起始节开始、结束节结束。

## 🤖 作为 Skill 使用(Reasonix / Agent)

将本目录复制到 Agent 的 skills 目录,或在 Reasonix 中执行:

```
/install-skill <本目录路径>
```

> 🤖 **安装引导**:Agent 安装本 Skill 后,首次使用前会运行 `check_deps.py` 检查环境依赖,缺失的依赖会自动下载安装(见上方「环境要求」)。查询功能零依赖,可立即使用。

之后直接对话:

> **你**: 今天有什么课?
> **Agent**:
> 📚 2026-2027 学年第1学期 · 第3周 周三
> ┌─────────────┬───────┬───────────┬────────┬──────┬─────────┐
> │ 时间        │ 节次  │ 课程      │ 教师   │ 学分 │ 地点    │
> ├─────────────┼───────┼───────────┼────────┼──────┼─────────┤
> │ 10:20-12:00 │ 3-4节 │ 示例课程B │ 李老师 │ 2    │ 2教0202 │
> └─────────────┴───────┴───────────┴────────┴──────┴─────────┘
> 🏫 花溪校区 · 共 1 门课
> 🎓 今日学分 2 / 学期总学分 7.5 (26.7%)

## 🧠 技术原理

重庆理工的教务访问链路(这也是很多高校的通用结构):

```
用户 → uis.cqut.edu.cn(统一认证/CAS)
     → ehall.cqut.edu.cn(办事大厅)
     → 调 getApplicationUrl 接口(应用 code: UIVx60)拿 oauth ticket
       → jwxt.cqut.edu.cn/sso/yhiotlogin?ticket=...   (SSO 换票)
       → jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151  (课表接口)
```

关键点:
- 教务系统直接 requests 登录会被 **瑞数 WAF** 拦截(返回 202/挑战页),必须用真实浏览器执行 JS
- UIS 登录后从 ehall cookie 取 `ump_token_pc-officeHall`,调 `getApplicationUrl`(应用 code `UIVx60` 为教务系统在平台的固定 code,与个人收藏无关)即可拿到 oauth ticket,无需点击任何 UI
- 用 ticket 访问 `sso/yhiotlogin` 完成换票,教务会话即建立
- 课表接口 POST 需带 `xnm`(学年)、`xqm`(学期: 3=秋季, 12=春季)、`kzlx=ck`

## ⚠️ 免责声明

- 本项目仅供学习与研究,请遵守学校网络使用规定,勿高频抓取
- 学号密码仅存于本机 `config.json`,脚本不向任何第三方发送凭据
- 教务系统接口变动可能导致脚本失效,欢迎提 issue

## 📄 License

MIT
