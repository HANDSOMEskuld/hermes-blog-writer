# Hermes Blog Writer

> 把「个人博客写作」变成一条可复用的流水线：**抓取你的旧文 → 迭代提炼你的写作风格 → 用你的风格写新文 → 自动跑情绪/节奏质检 → 一键上传 WordPress 草稿并自动分类打标签**。

任何人都能把这个项目导入自己的 [Hermes Agent](https://hermes-agent.nousresearch.com)，然后要么敲斜杠命令 `/blog-write`，要么直接用自然语言（「用我的风格写篇XXX」）驱动整套流程。

---

## 特性

- 🕸️ **语料抓取**：从任意 WordPress 站点（开放 REST API）抓取文章，作为风格样本
- 🔁 **风格迭代**：按标杆文自动编排「每篇迭代 N 遍」计划，沉淀成 `style_guide.md` 风格宪法
- ✍️ **风格写作**：写新文时套用你的风格规则（九种声音 + 通用声音）
- 📊 **三维质检**：情感弧线 / 句子节奏 / 情绪词密度，发布前自动诊断
- 🏷️ **智能分类标签**：上传时 AI 分析正文，自动匹配 WP 已有分类与标签
- 📝 **仅建草稿**：默认 `draft` 不发布，人工审核后发；密码只走环境变量，安全
- 💬 **自然语言兼容**：不敲命令也能用，记忆固化后任意对话自动命中

---

## 安装（3 步）

```bash
# 1. 克隆
git clone https://github.com/<你>/hermes-blog-writer.git
cd hermes-blog-writer

# 2. 作为 Hermes skill 安装（软链或复制）
ln -s "$(pwd)" ~/.hermes/skills/blog-writer
# 或： cp -r . ~/.hermes/skills/blog-writer

# 3. 固化跨会话记忆：把 assets/memory_snippet.md 的内容粘进你的 Hermes 记忆(MEMORY.md)
```

完成。重启 Hermes 后即可用 `/blog-write` 或自然语言触发。

---

## 使用流程

### 阶段 A：首次初始化风格库（换站/重训时再做）
```bash
# 抓取你的站点文章（--limit 控制篇数，--by-views 尝试按浏览量排序）
python3 assets/crawl_corpus.py --site https://你的站.com --out ./corpus --limit 60

# 编排迭代（--top 标杆数，--group 每组篇数，--iters 每篇遍数；--by-views 按浏览量）
python3 assets/iterate_style.py --corpus ./corpus --out ./style_guide.md \
    --top 20 --group 5 --iters 3 --by-views
# 注：若 REST 未暴露浏览量(views空)，--by-views 会自动降级为按日期排序并提示。

# 按 corpus/_iter_plan.json 逐篇迭代：
#   r1 凭模板初写 → 读标杆原文逐句比对 → r2/r3 不回看原文、凭规则重写（禁抄）
#   每篇沉淀的 R 规则写回 style_guide.md
```
> 迭代可自定义：`--top N`（标杆数）`--group G`（每组篇数）`--iters K`（每篇遍数）。

### 阶段 B：日常写新文
直接说：「**用我的风格写篇《XXX》**」
- 助手会读 `style_guide.md`，套对应类型规则
- 写作内建情感弧线 / 长短句节奏 / 情绪词意识
- 定稿跑 `python3 assets/review_before_publish.py <草稿>` 看三维诊断，微调至达标

### 阶段 C：上传 WP 草稿
```bash
export WP_USER=你的用户名
export WP_APP_PASS='你的应用密码'   # 建议专用「仅建草稿」密码，用完吊销
export WP_SITE='https://你的站.com'
python3 assets/publish_draft.py <草稿md>
```
脚本自动分析分类/标签并填入，仅建 `draft`。把后台链接发你，审核后手动发布。

---

## 脚本参考

| 脚本 | 作用 | 关键参数 |
|---|---|---|
| `blog_writer.py` | 统一 CLI 入口 | `crawl/plan/qa/publish/init` 子命令 |
| `crawl_corpus.py` | 抓 WP 文章 | `--site --out --limit [--by-views]` |
| `iterate_style.py` | 风格迭代编排 | `--corpus --out --top --group --iters [--by-views]` |
| `review_before_publish.py` | 三维质检 | `<草稿md路径>` |
| `publish_draft.py` | WP 上传+分类标签 | `<草稿md>`（需 WP_* 环境变量） |
| `publish_local.py` | 本地/Hexo 后端 | `<草稿md> [--format hexo]`（多平台扩展样板） |

### CLI 速查
```bash
python3 blog_writer.py crawl   --site https://你的站.com --limit 60
python3 blog_writer.py plan    --top 20 --group 5 --iters 3 --by-views
python3 blog_writer.py qa      drafts/xxx.md
python3 blog_writer.py publish drafts/xxx.md --backend wp      # 需 WP_* 环境变量
python3 blog_writer.py publish drafts/xxx.md --backend local   # 落盘 ./_out
python3 blog_writer.py init    --site https://你的站.com      # 抓+计划 一键
```

---

## 安全说明

- **密码绝不落盘**：只从环境变量 `WP_USER/WP_APP_PASS/WP_SITE` 读取，不写文件、不进记忆、不进 git。
- **仅建草稿**：默认 `status=draft`，绝不自动发布。需发布时你手动点，或显式让助手 publish。
- **Cloudflare 兼容**：上传带浏览器 UA，绕过对 POST 的 WAF 拦截。
- 建议使用 WordPress 后台「用户 → 应用密码」生成的**专用最低权限密码**，用完即吊销。

---

## 文件结构

```
hermes-blog-writer/
├── SKILL.md                    # Hermes skill：流程编排 + 触发词
├── README.md
├── LICENSE                     # MIT
├── blog_writer.py              # 统一 CLI 入口(crawl/plan/qa/publish/init)
├── assets/
│   ├── crawl_corpus.py         # 抓语料
│   ├── iterate_style.py        # 风格迭代编排
│   ├── review_before_publish.py# 三维质检
│   ├── publish_draft.py        # WP 上传+分类标签
│   ├── publish_local.py        # 本地/Hexo 后端样板(可扩展)
│   ├── style_guide_template.md # 风格库模板
│   ├── style_guide_example.md  # 已训练 V1.2 浓缩样例(参考)
│   ├── memory_snippet.md       # 粘进 Hermes 记忆的段落
│   └── config.example.env      # WP 凭据模板
└── (运行时生成) corpus/ style_guide.md _wp_terms.json _out/
```

## License
MIT
