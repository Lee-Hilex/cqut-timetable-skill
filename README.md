# 🎓 cqut-timetable-skill

重庆理工大学课表查询 Skill —— 通过 AI 助手直接问"今天有什么课",自动算周次、解析单双周。

本项目是 [Reasonix](https://reasonix.ai) / Claude / 各类 Agent 可用的**技能包(Skill)**,也可作为独立命令行工具使用。核心价值:把"登录教务 → 抓课表 → 算周次 → 回答"全链路自动化,以后每天只需问一句。

> ⚠️ 本项目针对重庆理工大学定制(正方教务系统 + UIS 统一身份认证 + 瑞数 WAF)。其他使用正方教务+统一认证的高校可参考 `fetch_schedule_browser.py` 的 SSO 流程自行适配。

---

## ✨ 功能

- 🔐 **自动登录**:Playwright 真实浏览器走 UIS 统一身份认证(https://uis.cqut.edu.cn),自动处理瑞数 WAF、SSO 换票,无需手动操作
- 📥 **自动抓课表**:通过 ehall "本科生教务管理系统"应用建立教务会话,调用正方课表接口,一键抓取整学期课表
- 📅 **智能查询**:自动计算今天是第几周(基于学期开始日期),回答"今天/明天/某周周X 有什么课"
- 🔄 **单双周支持**:正确解析 `15-19周(单)`、`10-16周(双)`、`4-6周,9-12周,14-18周` 等多段周次
- 🗣️ **对话式**:装成 Skill 后,直接问"今天有什么课"即可

## 📦 项目结构

```
cqut-timetable-skill/
├── fetch_schedule_browser.py   # 抓取脚本: UIS 登录 → SSO → 教务会话 → 课表接口
├── today_classes.py            # 查询工具: 算周次 + 单双周解析 + 按节次排序
├── config.example.json         # 配置模板(学号/密码/学期开始日期/上课时间)
├── sample_schedule.json        # 示例课表(脱敏,演示用)
├── SKILL.md                    # Skill 定义(供 Agent 加载)
└── .gitignore                  # 忽略真实 config.json 与真实课表(含个人信息)
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- Playwright + Chromium:
  ```bash
  pip install playwright
  playwright install chromium
  ```

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
  "semester_start": "2026-09-07",
  "class_time": [
    ["08:00", "08:45"],
    ["08:55", "09:40"],
    ...
  ]
}
```

| 字段 | 说明 |
|---|---|
| `base_url` | 教务系统地址 |
| `sid` / `pwd` | 统一身份认证账号(与 uis.cqut.edu.cn 相同) |
| `semester_start` | 学期第一周周一日期,决定周次计算 |
| `class_time` | 每节课的起止时间,共 11 节(重理工作息) |

> 🔒 `config.json` 已加入 `.gitignore`,学号密码不会进入版本库。

### 3. 抓取课表

```bash
python fetch_schedule_browser.py --year 2026 --term 1
# --term 1 = 秋季学期, 2 = 春季学期
```

成功后生成 `schedule_2026_1.json`(包含姓名/学号/课程/老师/教室/周次/星期)。

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

## 🤖 作为 Skill 使用(Reasonix / Agent)

将本目录复制到 Agent 的 skills 目录,或在 Reasonix 中执行:

```
/install-skill <本目录路径>
```

之后直接对话:

> **你**: 今天有什么课?
> **Agent**: 📚 2026-2027 学年第1学期 课表 · 第3周 周三
> 共 2 门课:
>   08:00 1-2节 | 有机化学 | 周德文,陈志 | 花溪校区 3教0603
>   14:00 5-6节 | 中国近现代史纲要 | 刘海鑫 | 花溪校区 3教0409

## 🧠 技术原理

重庆理工的教务访问链路(这也是很多高校的通用结构):

```
用户 → uis.cqut.edu.cn(统一认证/CAS)
     → ehall.cqut.edu.cn(办事大厅)
     → 点击"本科生教务管理系统"应用
       → jwxt.cqut.edu.cn/sso/yhiotlogin?ticket=...   (SSO 换票)
       → jwglxt/ticketlogin?uid=...&verify=...          (教务建会话)
       → jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151    (课表接口)
```

关键点:
- 教务系统直接 requests 登录会被 **瑞数 WAF** 拦截(返回 202/挑战页),必须用真实浏览器执行 JS
- UIS 登录后默认跳 ehall,需点击"本科生教务管理系统"应用才能触发教务 SSO 换票
- 课表接口 POST 需带 `xnm`(学年)、`xqm`(学期: 3=秋季, 12=春季)、`kzlx=ck`

## ⚠️ 免责声明

- 本项目仅供学习与研究,请遵守学校网络使用规定,勿高频抓取
- 学号密码仅存于本机 `config.json`,脚本不向任何第三方发送凭据
- 教务系统接口变动可能导致脚本失效,欢迎提 issue

## 📄 License

MIT
