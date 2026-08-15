#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Blog Writer —— 统一 CLI 入口
把机械流程串起来: crawl -> iterate(编排) -> qa(质检) -> publish。
LLM 负责的"读标杆文重写"步骤由 iterate 生成任务卡, 由 skill/人工执行。

子命令:
  blog_writer.py crawl   --site ... [--limit N] [--by-views]
  blog_writer.py plan    --top N --group G --iters K [--by-views]   # 生成迭代计划
  blog_writer.py qa      <草稿md>                                   # 跑三维质检
  blog_writer.py publish <草稿md> [--backend wp|local]              # 上传草稿
  blog_writer.py init    [--site ...]                               # 一键初始化(抓+计划)

所有脚本在 assets/ 下, 本入口仅做编排与参数转发, 便于使用者单命令调用。
"""
import argparse, os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')

def run(script, args):
    cmd = [sys.executable, os.path.join(ASSETS, script)] + args
    print(f"\n$ {' '.join(cmd)}\n" + "-"*40)
    return subprocess.run(cmd).returncode

def main():
    ap = argparse.ArgumentParser(prog='blog_writer.py', description='Hermes Blog Writer 流水线')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('crawl'); p.add_argument('--site', required=True); p.add_argument('--limit', type=int, default=60); p.add_argument('--by-views', action='store_true'); p.add_argument('--out', default='./corpus')
    p = sub.add_parser('plan'); p.add_argument('--top', type=int, default=20); p.add_argument('--group', type=int, default=5); p.add_argument('--iters', type=int, default=3); p.add_argument('--by-views', action='store_true'); p.add_argument('--corpus', default='./corpus'); p.add_argument('--out', default='./style_guide.md')
    p = sub.add_parser('qa'); p.add_argument('draft')
    p = sub.add_parser('publish'); p.add_argument('draft'); p.add_argument('--backend', default='wp', choices=['wp','local'])
    p = sub.add_parser('init'); p.add_argument('--site', required=True); p.add_argument('--limit', type=int, default=60); p.add_argument('--top', type=int, default=20); p.add_argument('--group', type=int, default=5); p.add_argument('--iters', type=int, default=3); p.add_argument('--by-views', action='store_true')
    a = ap.parse_args()

    if a.cmd == 'crawl':
        args = ['--site', a.site, '--out', a.out, '--limit', str(a.limit)]
        if a.by_views: args.append('--by-views')
        run('crawl_corpus.py', args)

    elif a.cmd == 'plan':
        args = ['--corpus', a.corpus, '--out', a.out, '--top', str(a.top), '--group', str(a.group), '--iters', str(a.iters)]
        if a.by_views: args.append('--by-views')
        run('iterate_style.py', args)

    elif a.cmd == 'qa':
        run('review_before_publish.py', [a.draft])

    elif a.cmd == 'publish':
        if a.backend == 'wp':
            run('publish_draft.py', [a.draft])
        else:
            # 本地/Hexo 后端: 转成 HTML 落盘 + 打印
            run('publish_local.py', [a.draft])

    elif a.cmd == 'init':
        # 抓 + 计划 串起
        run('crawl_corpus.py', ['--site', a.site, '--out', './corpus', '--limit', str(a.limit)] + (['--by-views'] if a.by_views else []))
        run('iterate_style.py', ['--corpus', './corpus', '--out', './style_guide.md', '--top', str(a.top), '--group', str(a.group), '--iters', str(a.iters)] + (['--by-views'] if a.by_views else []))
        print("\n✅ 初始化完成。下一步: 按 corpus/_iter_plan.json 逐篇用 LLM 迭代(r1..rK 凭规则重写, 禁抄原文), 回填 style_guide.md。")

if __name__ == '__main__':
    main()
