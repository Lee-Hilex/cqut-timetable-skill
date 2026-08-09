<!-- markdownlint-disable -->

<div align="right">

**<a href="README.md">🇨🇳 简体中文</a>** | <a href="README.en.md">🇬🇧 English</a>

</div>

<div align="center">

# 🎓 cqut-timetable-skill

重庆理工大学课表查询 Skill — 问一句"今天有什么课",自动登录教务抓课表、算周次、查学分<br>
基于 Python + Playwright(真实浏览器自动过 SSO / 瑞数 WAF)

[反馈问题](https://github.com/Lee-Hilex/cqut-timetable-skill/issues) · [更新日志](https://github.com/Lee-Hilex/cqut-timetable-skill/releases) <br>
[快速开始](#快速开始) · [技术原理](#-技术原理) · [免责声明](#-免责声明)

[![Version](https://img.shields.io/badge/version-1.2.4-blue)](https://github.com/Lee-Hilex/cqut-timetable-skill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Stars](https://img.shields.io/github/stars/Lee-Hilex/cqut-timetable-skill?color=ffcb47&labelColor=black)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Playwright](https://img.shields.io/badge/Playwright-v1-%232EAD33)
![零依赖查询](https://img.shields.io/badge/查询-零依赖-brightgreen)

</div>

<!-- markdownlint-restore -->

---

## 为什么选择 cqut-timetable-skill

查课表还要打开教务系统、输入学号密码、忍受验证码和 WAF 拦截?本 Skill 把**登录 → 抓课表 → 算周次 → 回答**全链路自动化,以后每天只需问一句"今天有什么课",少一步是一步。

- **针对重庆理工大学定制**:正方教务 + UIS 统一身份认证 + 瑞数 WAF,一条链路全打通
- **对话即所得**:装成 Skill 后直接问,Agent 自动算好今天第几周、有什么课、几点到几点
- **零配置查询**:课表抓一次存本地,之后查询纯本地计算,不登录、不联网、零依赖

> ⚠️ 其他使用「正方教务系统 + 统一认证」的高校可参考 `fetch_schedule_browser.py` 的 SSO 流程自行适配。

## 功能特点

- **🔐 自动登录抓课表** — Playwright 真实浏览器走 UIS 统一身份认证,自动处理瑞数 WAF、SSO 换票,一键抓取整学期课表

  ```text
  $ python fetch_schedule_browser.py --year 2026 --term 1
  ① 登录统一身份认证 (学号 1251*****25)...
  ② 获取 SSO ticket,进入教务系统...
  ③ 抓取 2026 学年第1学期课表...
  ✅ 抓取成功: 示例同学 / 应用化学 / 15 门课 → schedule_2026_1.json
  ```

- **📅 智能查询** — 自动算今天是第几周,回答"今天/明天/某周周X 有什么课",带学分统计

  ```text
  $ python today_classes.py --date 2026-09-18
  📚 2026-2027 学年第1学期 · 第3周 周五 (2026-09-18)
  🏫 花溪校区 · 共 2 大节（2 小节）

  ┌──────────────────────┐
  │  1-2节  08:20-10:00  │
  │  示例课程A            │
  │  1教0101             │
  │  张老师              │
  ├──────────────────────┤
  │  5-6节  14:00-15:40  │
  │  示例课程C            │
  │  3教0303             │
  │  王老师              │
  └──────────────────────┘

  🎓 今日学分 6.5 / 学期总学分 18.75 (34.7%)
  ```

  单日每个大节一行表格(节次+时间段 / 课程 / **教室**),教室粗体,紧凑。

- **🗓️ 整周网格视图** — `--week 3` 七列(周一~日)表格,每大节一行,格内 `课程 / **教室**`,节次列带时间段

  ```text
  $ python today_classes.py --week 3
  📅 2026-2027 学年第1学期 · 第3周课表
  ┌──────┬────────┬────────┬────────┬────────┬────────┬──────┬──────┐
  │      │  周一  │  周二  │  周三  │  周四  │  周五  │  周六  │  周日  │
  │ 1-2节│        │示例课程A │示例课程B │        │示例课程D │        │      │
  │      │        │**1教0101** │**2教0202** │        │**操场**  │        │      │
  │      │        │李老师  │张老师  │        │赵老师  │        │      │
  ├──────┼────────┼────────┼────────┼────────┼────────┼──────┼──────┤
  …(共 5 大节行)
  📊 本周共 11 大节（11 小节）
  ```

  单周网格为七列(周一~周日),每大节一行,格内 `课程名称 / **教室**`,节次列带时间段,**教室加粗**。

- **✏️ 自定义课程(v1.2.0)** — 在 `custom_courses.json` 中添加自习、选修等,查询时自动合并到课表

  ```json
  [{"title":"自习课","teacher":"无","weekday":3,"weeks":"2-16周","sessions":"7-8节","room":"图书馆301","credit":0}]
  ```

- **🎯 大节计数(v1.2.0)** — 大学两节连堂:1-2节→第1大节,…,提问"有几节课"回答大节数(附小节数)
- **📐 输出格式规范化(v1.2.2)** — 单日/单周紧凑输出:每大节一行 `课程名称 / **教室**`,节次带时间段,教室加粗
- **📋 原样输出强制(v1.2.3)** — Agent 必须直接展示脚本 stdout,禁止自行重排/转 markdown 表格/丢失教室加粗
- **📝 Markdown 输出模式(v1.2.4)** — `--markdown` 输出规范的 markdown 表格(七列×五行、教室 `**` 加粗),Agent 原样粘贴即可在聊天中渲染成真表格
- **👥 多教师省略号(v1.2.0)** — 多位教师(如 `张老师,李老师`)只显示第一个+`…`
- **🔄 单双周 + 多段周次** — 正确解析 `15-19周(单)`、`10-16周(双)`、`4-6周,9-12周,14-18周`
- **⏱️ 第一周不完整兼容** — 开学日在周中时按自然周对齐,第一周不足 7 天也正确
- **⏰ 时间段显示** — 时间列显示上课时间段(如 `10:20-12:00`),跨节取起止,不再只是时间点
- **🏫 双校区作息** — 花溪(8:20 起 11 节)与两江(8:30 起 10 节),首次使用自动选择
- **🛡️ 隐私安全** — 学号密码只存本机 `config.json`(已 .gitignore),不上传任何第三方
- **🧰 依赖自动处理** — 自带 `check_deps.py`,缺失依赖自动下载安装

## 应用场景

- 早上出门前问一句"今天有什么课",几节课、几点到几点、哪个教室,一目了然
- 想知道"这学期都有哪些课 / 总共多少学分",一条命令列全
- 换学期后重抓一次课表,整学期不用再登教务

## 📥 下载安装

| 方式 | 说明 |
|------|------|
| **zip 包(推荐)** | [cqut-timetable-skill-1.2.4.zip](dist/cqut-timetable-skill-1.2.4.zip) — 解压即用,含全部 11 个文件 |
| **GitHub Releases** | [Releases 页](https://github.com/Lee-Hilex/cqut-timetable-skill/releases) 下载对应版本源码包 |
| **Git 克隆** | `git clone git@github.com:Lee-Hilex/cqut-timetable-skill.git` |

## 快速开始

### 1. 环境检查(自动引导安装依赖)

本项目自带 `check_deps.py`,**安装 Skill 或首次使用时会自动检查环境依赖,缺失的依赖自动下载安装**:

```bash
# 检查环境(会明确提示缺什么)
python check_deps.py

# 自动下载安装缺失依赖(playwright + Chromium)
python check_deps.py --install
```

| 功能 | 依赖 | 说明 |
|------|------|------|
| 查询课表 `today_classes.py` | **零依赖** | 纯 Python 标准库,装好即用 |
| 抓取课表 `fetch_schedule_browser.py` | `playwright` + Chromium | `check_deps.py --install` 自动 `pip install playwright` + `playwright install chromium` |

### 2. 配置

```bash
cp config.example.json config.json
```

编辑 `config.json`,填入学号密码:

```json
{
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

| 字段 | 说明 |
|---|---|
| `sid` / `pwd` | 统一身份认证账号(与 uis.cqut.edu.cn 相同) |
| `campus` | 校区: `huaxi`(花溪)或 `liangjiang`(两江),决定用哪套作息时间 |
| `semester_start` | 开学日期(第一周第一天,可能是周中;建议手动填写,如 `2026-09-02`) |
| `class_time` | 按校区分组的作息时间表(花溪 11 节 8:20 起 / 两江 10 节 8:30 起) |

> 🔒 `config.json` 已加入 `.gitignore`,学号密码不会进入版本库。
>
> 💡 首次使用(或旧版单作息配置)时,`today_classes.py` 会自动提示选择校区并升级配置,无需手动编辑 `class_time`。
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
# 第3周全周课表(网格视图,v1.2.0 新增)
python today_classes.py --week 3

# 今天有什么课(默认单日卡片)
python today_classes.py

# 指定日期
python today_classes.py --date 2026-09-18

# 第15周周四
python today_classes.py --week 15 --day 4

# 列出全部课程(旧表格格式)
python today_classes.py --list

# Agent / 聊天场景: 输出 markdown 表格(教室加粗,直接原样展示)
python today_classes.py --week 3 --markdown
python today_classes.py --date 2026-09-18 --markdown
```

> 💡 终端直接看用默认 ASCII 网格;**Agent 回答用户时用 `--markdown`**,得到规范的 markdown 表格(七列×五行、教室 `**` 加粗),聊天界面会渲染成对齐表格。

> ✏️ **自定义课程**(v1.2.0): 参考 `custom_courses.example.json` 创建 `custom_courses.json`,查询时自动合并到课表。

## 🤖 作为 Skill 使用(Reasonix / Agent)

将本目录复制到 Agent 的 skills 目录,或在 Reasonix 中执行:

```
/install-skill <本目录路径>
```

> 🤖 **安装引导**:Agent 安装本 Skill 后,首次使用前会运行 `check_deps.py` 检查环境依赖,缺失的依赖会自动下载安装(见上方「环境检查」)。查询功能零依赖,可立即使用。

之后直接对话(Agent 运行 `today_classes.py --markdown`,**原样展示脚本输出**):

```text
你: 今天有什么课?

Agent:
📚 2026-2027 学年第1学期 · 第3周 周五
🏫 花溪校区 · 共 2 大节（2 小节）

**1-2节 08:20-10:00**
示例课程A
1教0101
张老师

**5-6节 14:00-15:40**
示例课程C
3教0303
王老师

🎓 今日学分 6.5 / 学期总学分 18.75 (34.7%)
```

> 问整周课表时,Agent 同样**原样展示** `--markdown` 输出的七列×五行 markdown 表格(教室已用 `**` 加粗,渲染后为粗体)。

## 📦 项目结构

```
cqut-timetable-skill/
├── check_deps.py                 # 环境依赖检查脚本: 缺失自动下载安装
├── fetch_schedule_browser.py    # 抓取脚本: UIS 登录 → SSO → 教务会话 → 课表接口 → 开学日期检测
├── today_classes.py             # 查询工具: 大节映射 + 单双周解析 + 学分统计 + 卡片/网格输出(零依赖)
├── config.example.json          # 配置模板(学号/密码/校区/作息时间)
├── custom_courses.example.json  # 自定义课程示例(自习/选修等,v1.2.0)
├── sample_schedule.json         # 示例课表(脱敏,演示用)
├── SKILL.md                     # Skill 定义(供 Agent 加载)
└── .gitignore                   # 忽略真实 config.json / custom_courses.json / 真实课表(含个人信息)
```

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
- 教务系统接口变动可能导致脚本失效,欢迎提 [issue](https://github.com/Lee-Hilex/cqut-timetable-skill/issues)

## 📄 License

[MIT](LICENSE)
