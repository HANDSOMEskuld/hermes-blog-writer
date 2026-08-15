#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Appstoy 发布前质检闸门
用法: python3 review_before_publish.py <草稿md路径>
输出: 情感弧线 + 句子节奏诊断 + 情绪词密度建议

依据: style-guide-v1.md R52(情感弧线) / R53(节奏交替) / R54(情绪词点缀)
原则: 只检测、只建议，不改稿；由作者/助理据此微调。
"""
import sys, re, os

# ---------- 配置 ----------
# 情绪词表（R54 优化用，可按站点调）：正向/负向/惊喜/警示
EMOTION_WORDS = {
    "惊喜": ["惊了","没想到","居然","竟然","绝了","香","离谱","狠","猛","爽","牛","神","宝藏","白嫖","免费","划算","稳","顶用","好用","舒服"],
    "负向": ["坑","踩坑","烦","恶心","坑爹","割韭菜","贵","卡","慢","崩","翻车","受限","坑人","套路","忽悠"],
    "警示": ["注意","警惕","小心","别","务必","一定","千万","提醒","当心","慎用"],
    "兴奋": ["一起玩","搞起","冲","盘它","整一个","安排","可玩","折腾","玩起来","一起去"],
}
# 情感弧线：给每段一个极性评分（-2 很负 ... +2 很正），基于关键词+句式启发式
NEG_HINT = ["痛点","烦","贵","卡","坑","慢","崩","翻车","受限","套路","割韭菜","愁","难","卡顿","不够","不行","问题"]
POS_HINT = ["免费","白嫖","香","稳","爽","神","宝藏","好用","顶用","划算","一起玩","搞起","惊了","没想到","猛","牛","方便","简单","快"]
QUESTION_HINT = ["？","?","有没有","是不是","会不会","难道"]  # 设问/过渡段，弧线视为"钩子neutral偏抑"

def split_paragraphs(text):
    # 去掉 markdown 代码块/注释/图片占位，避免干扰
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.S)
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    # 过滤纯标题/标记行
    paras = [p for p in paras if not p.startswith('#') and not p.startswith('[postsbox') and not p.startswith('0x')]
    return paras

def score_para(p):
    s = 0
    for w in NEG_HINT:
        if w in p: s -= 1
    for w in POS_HINT:
        if w in p: s += 1
    if any(q in p for q in QUESTION_HINT): s -= 0.5  # 设问偏抑(钩子)
    # 归一到 -2..2
    return max(-2, min(2, s))

def rhythm_stats(paras):
    # 以句号/问号/感叹号切句，统计句长
    sentences = []
    for p in paras:
        # 去 markdown 链接语法干扰
        p2 = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', p)
        for s in re.split(r'[。！？!?]', p2):
            s = s.strip()
            if len(s) >= 2:
                sentences.append(s)
    lens = [len(s) for s in sentences]
    n = len(lens)
    short = [l for l in lens if l <= 12]      # 短句
    mid = [l for l in lens if 12 < l <= 30]
    long = [l for l in lens if l > 30]        # 长句
    # 连续长句堆叠检测
    runs_long = 0
    max_run = 0
    for l in lens:
        if l > 30:
            runs_long += 1
            max_run = max(max_run, runs_long)
        else:
            runs_long = 0
    runs_short = 0
    max_run_short = 0
    for l in lens:
        if l <= 8:
            runs_short += 1
            max_run_short = max(max_run_short, runs_short)
        else:
            runs_short = 0
    return {
        "n_sent": n, "avg_len": round(sum(lens)/n,1) if n else 0,
        "n_short": len(short), "n_mid": len(mid), "n_long": len(long),
        "short_rate": round(len(short)/n,2) if n else 0,
        "long_rate": round(len(long)/n,2) if n else 0,
        "max_consec_long": max_run, "max_consec_short": max_run_short,
    }

def emotion_density(paras):
    full = "\n".join(paras)
    found = {}
    total = 0
    for cat, ws in EMOTION_WORDS.items():
        c = sum(full.count(w) for w in ws)
        if c:
            found[cat] = c
            total += c
    words_total = len(re.findall(r'[\u4e00-\u9fff]', full))
    density = round(total / words_total * 1000, 1) if words_total else 0  # 每千字情绪词数
    return found, total, density

def main():
    if len(sys.argv) < 2:
        print("用法: python3 review_before_publish.py <草稿md>")
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.exists(path):
        print("文件不存在:", path); sys.exit(1)
    text = open(path, encoding='utf-8').read()
    paras = split_paragraphs(text)

    print("="*60)
    print("Appstoy 发布前质检 —", os.path.basename(path))
    print("="*60)

    # 1) 情感弧线
    print("\n【一、情感弧线】 (R52)  每段极性 -2(很负) ~ +2(很正)")
    curve = []
    for i, p in enumerate(paras):
        sc = score_para(p)
        curve.append(sc)
        bar = '█'*int(abs(sc)*3) if sc!=0 else '·'
        sign = '+' if sc>0 else ('-' if sc<0 else ' ')
        print(f"  段{i+1:02d} {sign}{bar:<6} {sc:+.1f}  {p[:18]}...")
    # 弧线形状判断
    print("  曲线:", " → ".join(f"{s:+.0f}" for s in curve[:12]))
    # 是否全平
    if max(curve)-min(curve) < 1.0:
        print("  ⚠ 弧线偏平(起伏<1.0)：建议加入『痛点(抑)→发现(扬)→坑(小抑)→一起玩(扬)』波动")
    else:
        print("  ✓ 存在情绪波动，OK")

    # 2) 节奏
    print("\n【二、句子节奏】 (R53)")
    r = rhythm_stats(paras)
    print(f"  总句数 {r['n_sent']} | 平均句长 {r['avg_len']}字")
    print(f"  短句(≤12字) {r['n_short']} ({r['short_rate']*100:.0f}%) | 中句 {r['n_mid']} | 长句(>30字) {r['n_long']} ({r['long_rate']*100:.0f}%)")
    print(f"  最长连续长句堆叠 {r['max_consec_long']} 句 | 最长连续碎短句 {r['max_consec_short']} 句")
    if r['max_consec_long'] >= 4:
        print("  ⚠ 连续长句堆叠≥4：读者会闷，建议在中间插入1-2个短句段做呼吸")
    if r['long_rate'] > 0.6:
        print("  ⚠ 长句率>60%：整体偏重，加密短句")
    if r['short_rate'] > 0.5 and r['max_consec_short'] >= 4:
        print("  ⚠ 碎短句成片：像发电报，适当合并成长句铺信息")
    if 0.15 <= r['short_rate'] <= 0.45 and r['max_consec_long'] < 4:
        print("  ✓ 长短交错健康")

    # 3) 情绪词
    print("\n【三、情绪词密度】 (R54)")
    found, total, density = emotion_density(paras)
    for cat, c in found.items():
        print(f"  {cat}: {c}")
    print(f"  情绪词总数 {total} | 密度 {density} 个/千字")
    if density < 5:
        print("  ⚠ 情绪词偏稀(<5/千字)：在『发现好东西/踩坑』处补惊喜/警示词(绝了/香/坑/警惕)，增强传播力，但别堆")
    elif density > 20:
        # 注: 清单/资源型文章主题词(免费/白嫖/免费用)天然高频, 密度高不一定是"演"。
        # 若惊喜类多为"免费/稳/顶用"等中性实用词而非"绝了/神/宝藏"夸张词, 可视为合理, 人工把关。
        print("  ⚠ 情绪词过密(>20/千字)：若多为『免费/白嫖』类主题词属清单型正常；若多为夸张词(绝了/神)，适当稀释")
    else:
        print("  ✓ 密度适中")

    print("\n" + "="*60)
    print("提示: 本脚本只检测建议，不改稿。据以上 ⚠ 项微调后再次运行即可。")
    print("="*60)

if __name__ == '__main__':
    main()
