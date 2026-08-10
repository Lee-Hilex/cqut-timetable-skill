# 更新日志 (Changelog)

本项目的所有重要变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.2.5] - 2026-08-09

### ✨ 新增
- **单日三列 markdown 表格**:查询某一天课程时输出 `节次+时间段 / 课程 / **教室**` 三列表格,教室加粗
- **单周七列 markdown 表格**:整周课表每大节一行,格内 `课程 / **教室**`,节次列带时间段

### 🔧 改进
- 单日/单周输出均改为紧凑 markdown 表格,不再包含教师
- 彻底移除 `<br>` 拼接(聊天界面会把 raw HTML 转义成字面量,导致显示异常)
- 空大节(整周无课)仅显示一行节次标签,不再占三行
- README(中英)示例同步为新 markdown 表格格式

## [v1.2.4] - 2026-08-09

### ✨ 新增
- **`--markdown` 输出模式**:脚本直接输出规范的 markdown 表格(单日三列 / 单周七列、教室 `**` 加粗),Agent 原样粘贴即可在聊天中渲染成真表格
- 终端默认仍为 ASCII 网格输出,不影响手动使用

### 🔧 改进
- SKILL.md 强制 Agent 使用 `--markdown` 并原样粘贴输出
- README 对话示例修复为代码块渲染,复制不再塌成一行

## [v1.2.3] - 2026-08-09

### 🔧 改进
- SKILL.md 增加强指令:Agent 必须原样展示 `today_classes.py` 的输出,禁止自行重排为 HTML/markdown 表格、禁止添加 `<br>` 或 ` · ` 等分隔符
- 确保单周网格教室 `**加粗**` 原样保留、七列×五行完整展示

### 🐛 修复
- 修复 Agent 重新排版导致教室不加粗、列数压缩、计数错误的问题

## [v1.2.2] - 2026-08-09

### ✨ 新增
- 单周网格教室 Markdown 加粗(`**教室**`),列宽计算忽略 `**` 符号,渲染后仍对齐
- 单日卡片输出格式规范化:每大节三行(课程名称/课程教室/任课老师),从上到下排列

### 🔧 改进
- README(中英)/SKILL.md 示例去除残留真实人名

## [v1.2.1] - 2026-08-09

### 🐛 修复
- `stdout` 输出加 try-except 保护,避免编码错误中断
- `--day` 必须配合 `--week` 使用,单独使用时报错提示
- 网格模式下 `week <= 0`(未开学)正确处理

## [v1.2.0] - 2026-08-09

### ✨ 新增
- **大节概念**:大学两节连堂,1-2节→第1大节,…,9-10节→第5大节;问"有几节课"按大节回答
- **自定义课程**:支持 `custom_courses.json` 添加自习、选修等,查询时自动合并
- **单日卡片布局**与**单周七列×五行网格布局**
- **README 中英双语**切换

### 🔧 改进
- 自检修复:学分去重统计、表格截断处理、学号掩码、Chromium 显式 close、死字段清理

## [v1.1.2] - 2026-08-09

### ✨ 新增
- **环境依赖检查脚本 `check_deps.py`**:安装 Skill 或首次使用时自动检查依赖,缺失自动下载安装
- **时间段显示**:课表时间显示为时间段(如 `08:20-10:00`),跨节次取起止

### 🔧 改进
- README 借鉴花笺风格重写(居中徽章墙/功能示例/应用场景/表格化下载与快速开始)
- 移除 README 中提及花笺的文案
- 自检修复:学分去重/表格截断/学号掩码/chromium 显式 close/死字段清理
- README 双语切换(简体中文 + English)

## [v1.1.1] - 2026-08-08

### 🐛 修复
- 开学日期自动检测在未开学时不可靠,改为提示人工确认

## [v1.1.0] - 2026-08-08

### ✨ 新增
- **开学日期自动检测**
- **学分统计**
- **第一周不完整兼容**:开学日在周中时按自然周对齐,第一周不足 7 天也正确

## [v1.0.0] - 2026-08-08

### ✨ 首发版本
- 重庆理工大学课表查询 Skill
- **双校区作息表**:花溪(8:20 起 11 节)与两江(8:30 起 10 节),首次使用自动选择
- **通用 SSO 抓取**:UIS 统一身份认证 + ehall `getApplicationUrl` 接口(应用 code `UIVx60`)拿 ticket,再经 `sso/yhiotlogin` 换票进教务,无需收藏或点击 UI
- **表格输出**:单日卡片 / 单周网格
- **隐私安全**:学号密码只存本机 `config.json`(已 .gitignore),示例去除真实人名

[unreleased]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.5...HEAD
[v1.2.5]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.4...v1.2.5
[v1.2.4]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.3...v1.2.4
[v1.2.3]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.2...v1.2.3
[v1.2.2]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.1...v1.2.2
[v1.2.1]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.2.0...v1.2.1
[v1.2.0]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.1.2...v1.2.0
[v1.1.2]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.1.1...v1.1.2
[v1.1.1]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.1.0...v1.1.1
[v1.1.0]: https://github.com/Lee-Hilex/cqut-timetable-skill/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/Lee-Hilex/cqut-timetable-skill/releases/tag/v1.0.0
