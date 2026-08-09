---
name: cqut-timetable
description: 查询重庆理工大学课表:回答"今天有什么课/明天/第几周上什么课"等,自动算周次、解析单双周,带学分。抓取需 Playwright+学号密码(config.json),查询零配置。
---

# 课表查询(cqut-timetable)

当用户问"今天有什么课""明天上什么课""第X周周X有什么课""这个学期都有哪些课"等与上课相关的问题时,使用本技能。

## 首次使用:环境检查(必做)

**安装/首次使用前,先检查环境依赖;缺失则自动下载安装。**

1. 运行环境检查:
   ```
   python <dir>/check_deps.py
   ```
   - ✅ 全部就绪 → 直接使用
   - ❌ 有缺失 → 运行 `python <dir>/check_deps.py --install` 自动下载安装缺失依赖
2. 依赖清单:
   - `today_classes.py`(查询): **零依赖**(纯 Python 标准库)
   - `fetch_schedule_browser.py`(抓课表): 需 `playwright` + Chromium(检查脚本会自动 `pip install playwright` + `playwright install chromium`)
3. 说明: **查询课表不需要任何第三方库**,只有"换学期重新抓课表"才需要 playwright + Chromium 浏览器。

## 工具位置

- 项目目录: 本 skill 所在目录(含 `today_classes.py`、`fetch_schedule_browser.py`、`config.json`、`schedule_*.json`)
- 查询工具: `today_classes.py`
- 抓取工具: `fetch_schedule_browser.py`(换学期时用)

## 查询方法

**核心规则:必须运行 `python <dir>/today_classes.py --markdown`,并把脚本的 stdout 原样完整展示给用户(不要包代码块、不要重新排版、不要转换格式)。**

```
python <dir>/today_classes.py --markdown
```

常用参数(基于 `config.json` 的 `semester_start` 自动算周次):
- **今天**: 不带参数 → 单日三列表格(节次+时间 / 课程 / **教室**)
- **指定日期**: `--date 2026-09-23` → 单日三列表格
- **指定周次+星期**: `--week 15 --day 4`(day: 1=周一 ... 7=周日) → 单日三列表格
- **整周课表**: `--week 3`(不带 `--day`) → 七列×五行 markdown 表格
- **全部课程**: `--list` → 横向表格(旧格式,含周次/学分完整信息)
- **指定课表文件**: `--schedule schedule_2025_2.json`(春季学期时)

> ⚠️ **输出即原样**: 脚本输出已是规范的 markdown 表格,每大节一行,格内为 `课程名称 / **教室**`(教室已用 `**` 加粗),节次列带时间段。**直接把脚本打印的内容原样贴给用户**(不需要代码块包裹),markdown 会渲染成对齐的表格,`**教室**` 渲染成粗体。

### 大节概念(v1.2.0)

大学课程两节连堂: 1-2节→第1大节, 3-4节→第2大节, 5-6节→第3大节, 7-8节→第4节, 9-10节→第5大节。
- 问"有几节课"时回答大节数(附带小节数): `共 2 大节（4 小节）`
- 多教师用省略号: `张老师,李老师…`

### 自定义课程(v1.2.0)

在 skill 目录创建 `custom_courses.json`(参考 `custom_courses.example.json`):

```json
[{"title":"自习课","teacher":"无","weekday":3,"weeks":"2-16周","sessions":"7-8节","room":"图书馆301","credit":0}]
```

查询时自动合并。该文件已加入 `.gitignore`,不上传。

## 周次规则

- `semester_start` = 开学日期(第一周第一天,可能是周中);若缺失,首次查询会交互询问
- 周次按自然周对齐: 开学日所在自然周(周一起)为第 1 周,第一周不足 7 天也正确
- 今天是第几周 = (今天 - 开学日所在周周一) 天数 // 7 + 1
- 课表周次格式支持: `2-6周`、`4-6周,9-12周,14-18周`、`15-19周(单)`、`10-16周(双)`、`11周`
- 开学前(周次 0)提示未开学

## 输出

**脚本 stdout 就是最终答案。直接把命令的完整输出原样返回给用户(不加代码块),不要加工、不要重排。**

- **单日** (`--week N --day D` 或默认今天): 三列 markdown 表格(节次+时间段 / 课程 / **教室**),教室加粗,紧凑
- **整周** (`--week N`): 七列(周一~周日)markdown 表格,**每大节一行**,格内 `课程名称 / **教室**`,节次列带时间段。教室已被脚本用 `**教室**` 加粗——**原样保留 `**`**,渲染后显示粗体。**不要用 `<br>`**(raw HTML 会被聊天界面转义成字面量,已多次踩坑)
- **全部课程(--list)**: 横向表格(时间/节次/课程/教师/学分/地点)
- 底部统计: `🎓 今日学分 X / 学期总学分 Y (占比%)` / `📊 本周共 N 大节（M 小节）`

禁止行为(会导致输出错误,已多次发生):
- ❌ 把 markdown 输出包进 ``` 代码块(星号/表格不会渲染)
- ❌ 自己重新排版成 HTML 表格(带 `<br>` 以外的标签、`&nbsp;`)
- ❌ 用 `·`、`/` 之外的符号拼接教室和教师(教师已不展示)
- ❌ 把表格压成 5 列/删掉周六日列
- ❌ 去掉教室的 `**` 加粗
- ❌ 直接读 schedule JSON 自己脑补,而不运行脚本

## 换学期流程

1. 运行 `python fetch_schedule_browser.py --year <学年> --term <1|2>` 重新抓取
   - 若 `semester_start` 未填,脚本自动调用 ehall `getCurrentWeek` 反推开学日期并写入 config
2. 生成新 `schedule_<学年>_<学期>.json` 后自动生效

## 注意事项

- 抓取走 UIS 统一身份认证 + ehall `getApplicationUrl` 接口(应用 code `UIVx60`)拿 ticket,再经 `sso/yhiotlogin` 换票进教务,无需收藏或点击 UI
- 校区: `config.json` 的 `campus` 字段(huaxi/liangjiang),决定作息时间;首次使用或旧配置会自动提示选择
- 学号密码只存本机 config.json(已被 .gitignore 忽略),不外传
- 没有真实课表时可用 `--schedule sample_schedule.json` 演示
