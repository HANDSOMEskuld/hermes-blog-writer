---
name: blog-writer
description: 博客写作全流程助手——从抓取站点文章、迭代提炼创作者风格库，到用该风格写新文、跑情绪/节奏质检、上传 WordPress 草稿并自动分类打标签。触发词：「写博客/用我的风格写/写篇文章/发到WP」。也支持斜杠命令 /blog-write。
---

# Blog Writer —— 个人博客写作流水线

你是一个**复刻创作者写作风格并自动化发布**的助手。本 skill 把一套已验证的流程封装好，使用者无需重走弯路。

## 何时使用
- 用户说「用我的风格写篇XXX」「写博客」「把这篇发到 WP」「分析我的写作风格」
- 或显式调用 `/blog-write`

## 项目资产（本 skill 的 assets/ 目录 + 根目录入口）
- `blog_writer.py`    根目录统一 CLI 入口: `crawl/plan/qa/publish/init` 子命令
- `assets/crawl_corpus.py`   抓取任意 WP 站点文章为语料
- `assets/iterate_style.py`  编排「标杆文迭代」生成 style_guide.md 风格库
- `assets/review_before_publish.py`  三维质检(情感弧线/句子节奏/情绪词密度)
- `assets/publish_draft.py`  上传 WP 草稿 + AI 分析分类标签
- `assets/publish_local.py`  本地/Hexo 后端样板(可扩展对接其他平台)
- `assets/style_guide_template.md`  风格库空模板
- `assets/style_guide_example.md`   已训练 V1.2 浓缩样例(参考)
- `assets/config.example.env`  WP 凭据模板
- `LICENSE`  MIT

## 资产路径解析
本 SKILL.md 所在目录即 `SKILL_DIR`。脚本在 `SKILL_DIR/assets/`。调用脚本用：
`python3 <SKILL_DIR>/assets/<script>.py ...`
统一入口：`python3 <SKILL_DIR>/blog_writer.py <子命令>`

## 完整流程（按需调用，不必全跑）

### 阶段 A：初始化风格库（仅首次 / 换站时）
1. 抓取：`python3 <SKILL_DIR>/assets/crawl_corpus.py --site <站> --out <SKILL_DIR>/corpus --top 60`
2. 迭代编排：`python3 <SKILL_DIR>/assets/iterate_style.py --corpus <SKILL_DIR>/corpus --out <SKILL_DIR>/style_guide.md --top 20 --group 5 --iters 3 [--by-views]`
3. 按 `<SKILL_DIR>/corpus/_iter_plan.json` 逐篇执行迭代：
   - 每篇迭代 K 遍（r1 凭模板初写 → 读标杆原文逐句比对提炼 → r2/r3 不回看原文、凭累积规则用自己话重写，**严禁抄原文**）
   - 把每篇沉淀的 R 规则写回 style_guide.md
4. 完成后 style_guide.md 即「V1 风格宪法」，以后写文以它为准。

### 阶段 B：用风格写新文（高频）
当用户要求写新文：
1. **先读** `<SKILL_DIR>/style_guide.md`，套对应文章类型的 R 规则。
2. 选题：优先从「最近热门」挑用户站点**已有同类型**的主题（复用已训练结构蹭热点），不新创类型。
3. 写作中内建三维意识：
   - **情感弧线**：痛点(抑)→发现(扬)→坑(小抑)→一起玩(扬) 的波动
   - **句子节奏**：长短句交错，禁连续长句堆叠 / 电报式碎短句
   - **情绪词点缀**：适当带情绪增强传播力，不刻意堆砌
   - **数据标来源**、**承上启下过渡**、**实操步骤可验证不造假**
4. 定稿后跑质检：`python3 <SKILL_DIR>/assets/review_before_publish.py <草稿md>`，据 ⚠ 微调，重跑至达标。

### 阶段 C：上传草稿（发布前最后一步）
1. 确认已跑过阶段 B 的质检。
2. **WP 后端**（默认）：
   - 设环境变量（凭据**只从环境变量读，绝不写文件/记忆**）：
     `export WP_USER=<用户> WP_APP_PASS='<应用密码>' WP_SITE='<站>'`
   - 上传：`python3 <SKILL_DIR>/assets/publish_draft.py <草稿md>`
   - 脚本自动 AI 分析分类/标签并填入，仅建 `draft` 不发布。
3. **本地/静态站后端**（可扩展）：
   - `python3 <SKILL_DIR>/assets/publish_local.py <草稿md> [--format hexo]`
   - 转 HTML(+YAML front-matter) 落盘 `./_out/`，作为对接 Hexo/Typecho 等样板。
4. 把后台编辑链接/本地文件路径发给用户，提醒「人工审核后发布」。

## 自然语言兼容
即使使用者不敲 `/blog-write`，只要说「用我的风格写…」「发到我的 WordPress」「检查下这篇文章的情绪节奏」，都应自动套用上述流程。

## 安全与偏好（必须遵守）
- WP 密码只走环境变量，绝不落盘、不进记忆、不进 git。建议使用者用专用「仅能建草稿」的应用密码，用完即吊销。
- 只建 draft，绝不自动 publish（除非用户明确说"直接发布"）。
- 跨会话可用：把下方 memory_snippet 内容写入 Hermes 记忆，任意新对话都能命中本流程。
