#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风格迭代编排器：根据抓取的语料，生成"标杆文迭代计划"并累积风格规则。
设计: 本脚本负责 ①选标杆(按热度/日期) ②分组(每N篇一组) ③产出每篇的迭代任务卡
      ④把每篇沉淀的 R 规则累加进 style_guide.md。真正"读文+重写"由 Hermes(LLM)执行，
      本脚本给出结构化的任务与规则模板，保证可复跑、可配置。
用法:
  python3 iterate_style.py --corpus ./corpus --out ./style_guide.md \
      --top 20 --group 5 --iters 3
参数:
  --top N     取热度/日期前 N 篇作标杆 (默认20)
  --group G   每 G 篇为一组批量迭代 (默认5)
  --iters K   每篇迭代 K 遍 r1..rK (默认3，对应 凭V0 / 读原文比 / 不回看重写)
  --by views  按浏览量排序(需语料含views) 否则按日期
输出:
  style_guide.md   累积的 V1 风格库 (R1..Rn)
  _iter_plan.json  每篇任务卡，供 skill 驱动 LLM
"""
import argparse, json, os, re

def load_index(corpus):
    idx = json.load(open(os.path.join(corpus, "_index.json"), encoding='utf-8'))
    return idx

def pick_top(idx, top, by_views):
    if by_views:
        def key(m):
            try: return int(m.get('views') or 0)
            except: return 0
        idx2 = sorted(idx, key=key, reverse=True)
        if not any(key(m) for m in idx2):
            print("⚠ 语料 views 为空(REST未暴露)，已降级按日期排序。需热度排序请改抓 ?orderby=views 列表页。")
            idx2 = sorted(idx, key=lambda m: m.get('date',''), reverse=True)
        return idx2[:top]
    return sorted(idx, key=lambda m: m.get('date',''), reverse=True)[:top]

# 文章类型自动判定(轻量关键词)，供分组与 R 规则种子
TYPE_RULES = [
    ('游戏资源', ['switch','模拟器','xci','nsp','塞尔达','马里奥','动森','游戏']),
    ('软件清单', ['清单','合集','软件','推荐','下载']),
    ('AI工具', ['ai','chatgpt','api','大模型','gemini','硅基','智谱']),
    ('硬核技术', ['教程','配置','服务器','docker','优化','部署']),
    ('社区互动', ['福利','抽奖','建站','送','读者']),
    ('写作方法论', ['写作','文章','表达','叙事']),
    ('随笔', ['生活','感悟','牢笼','情绪','焦虑','我']),
]
def detect_type(text):
    low = text.lower()
    for name, kws in TYPE_RULES:
        if any(k in low for k in kws): return name
    return '教程'

# 每类文章的 R 规则种子(使用者/LLM 会在迭代中细化)
SEED_RULES = {
    '游戏资源': 'R: 固定四件套(百科介绍段/文件清单/[postsbox互链]/免责声明块); 用 | 堆利益点标题',
    '软件清单': 'R: 用 0xN 十六进制小标题分大类; 每项"软件名+真实用法+主观评价"; 结尾升华+互动问句',
    'AI工具': 'R: 痛点开场+递工具; 实测数据(百分比/额度); 双免费方案; [postsbox]互链旧文',
    '硬核技术': 'R: 效果前置(先晒成果); 原理外包"大佬科普"; 利弊直说; 路径因人而异提示',
    '社区互动': 'R: 个人渊源故事+粉丝福利+呼唤社区; 轻松声',
    '写作方法论': 'R: 可用0x小标题; 学术/实践引用; 付费隐藏段; 推广自家产品自然带',
    '随笔': 'R: 禁用0x小标题; 白描+内省+单隐喻+开放结尾; 情绪克制',
    '教程': 'R: 现场钩子带行动; 玩耍感"一起玩/随便造"; 免费低门槛贯穿; 结尾干脆',
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', default='./corpus')
    ap.add_argument('--out', default='./style_guide.md')
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--group', type=int, default=5)
    ap.add_argument('--iters', type=int, default=3)
    ap.add_argument('--by-views', action='store_true')
    a = ap.parse_args()

    idx = pick_top(load_index(a.corpus), a.top, a.by_views)
    plan = []
    type_counter = {}
    for m in idx:
        text = open(m['file'], encoding='utf-8').read()
        t = detect_type(text)
        type_counter[t] = type_counter.get(t, 0) + 1
        plan.append({
            "id": m['id'], "title": m['title'], "type": t,
            "file": m['file'],
            "iters": [f"r{i+1}" for i in range(a.iters)],
            "seed_rule": SEED_RULES.get(t, SEED_RULES['教程']),
        })

    # 生成 style_guide.md 骨架
    lines = ["# 博客写作风格库 (V1, 由 iterate_style.py 生成)", ""]
    lines.append(f"> 标杆样本: {len(idx)} 篇 | 分组: 每 {a.group} 篇 | 每篇迭代 {a.iters} 遍 | 排序: {'浏览量' if a.by_views else '日期'}")
    lines.append("")
    lines.append("## 文章类型分布与 R 规则种子")
    for t, c in sorted(type_counter.items(), key=lambda x:-x[1]):
        lines.append(f"- **{t}** (x{c}): {SEED_RULES.get(t, SEED_RULES['教程'])}")
    lines.append("")
    lines.append("## 通用声音 (R1-R14, 适用于所有类型)")
    lines.append("- R1 现场钩子+行动感；R2 玩耍感'一起玩/随便造'；R3 真实场景而非抽象；")
    lines.append("- R4 免费低门槛贯穿；R5 结尾干脆不拖；R6 大方示弱立信；R7 旧文互链成网；")
    lines.append("- R8 数据标来源；R9 承上启下过渡；R10 实操步骤可验证不造假；")
    lines.append("- R11 情感弧线(抑扬)；R12 句子长短交错；R13 情绪词点缀不刻意；R14 结尾互动问句")
    lines.append("")
    lines.append("## 迭代进度 (每篇 r1..rK 定稿后回填)")
    for p in plan:
        lines.append(f"- [{p['id']}] {p['title'][:30]} | 类型:{p['type']} | 迭代:{','.join(p['iters'])} | 状态:pending")
    lines.append("")
    lines.append("## 发布前质检闸门")
    lines.append("- 写完跑 `python3 review_before_publish.py <草稿>` 做三维诊断(情感R11/节奏R12/情绪词R13)。")
    lines.append("- 据 ⚠ 项微调后重跑，直至节奏/情感达标。清单型'免费'主题词致密度偏高属正常。")
    open(a.out, 'w', encoding='utf-8').write('\n'.join(lines))
    json.dump(plan, open(os.path.join(a.corpus, "_iter_plan.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"✅ 风格库骨架 -> {a.out}")
    print(f"✅ 迭代计划({len(plan)}篇) -> {a.corpus}/_iter_plan.json")
    print(f"类型分布: {type_counter}")
    print("下一步: 按 _iter_plan.json 逐篇执行 r1..rK (读标杆标题+主题, 凭规则重写, 禁抄原文)，回填规则到本文件。")

if __name__ == '__main__':
    main()
