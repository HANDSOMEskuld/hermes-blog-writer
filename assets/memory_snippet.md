<!-- 复制本文件全部内容，粘贴进你自己的 Hermes 记忆（MEMORY.md）。
     这样任意新对话里说"用我的风格写…"都会自动命中 blog-writer 流程。 -->

【博客写作·跨会话调用·强制】
当用户要求"用我的风格/创作风格/像我写博客/写公众号/写 appstoy 文章"时，必须执行 blog-writer skill 的流程：
1. 先读风格库 `<SKILL_DIR>/style_guide.md`（V1 规则 R1-Rn，九种声音：教程/硬核技术/游戏资源/软件清单/极简软件/社区互动/写作方法论/AI工具/随笔）。
2. 按对应类型 R 规则写：数据标来源、承上启下过渡、实操步骤可验证不造假。
3. 写作内建三维意识：情感弧线(抑扬波动) / 句子长短交错 / 情绪词点缀不刻意。
4. 定稿跑 `python3 <SKILL_DIR>/assets/review_before_publish.py` 三维质检(情感/节奏/情绪词)，据 ⚠ 微调重跑至达标。
5. 上传 WP 草稿：`python3 <SKILL_DIR>/assets/publish_draft.py <md>`（密码走环境变量 WP_USER/WP_APP_PASS/WP_SITE，脚本自动分析分类标签，仅建 draft 不发布）。
绝不可凭空用通用写法或退回 V0。选题优先挑站点已有同类型蹭热点。

（注：<SKILL_DIR> 在你机器上是 skill 实际路径，如 ~/.hermes/skills/blog-writer/）
