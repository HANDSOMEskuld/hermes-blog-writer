#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地/静态站发布后端 (publish_local.py)
作为 blog_writer.py publish --backend local 的执行器。
功能: 把 MD 草稿转 HTML(+YAML front-matter 供 Hexo 等), 落盘到 ./_out/<slug>.html。
设计: 这是「多平台发布」的可扩展样板 —— 使用者可复制本文件改写后对接
      Typecho/Hexo/微信公众号等。WP 后端见 publish_draft.py (走 REST API)。

用法:
  python3 publish_local.py <草稿md> [--out ./_out] [--format html|hexo]
"""
import argparse, os, re, json

def slugify(title):
    s = re.sub(r'[^\w\u4e00-\u9fff]+', '-', title.lower()).strip('-')
    return s[:60] or 'untitled'

def md_to_html(md):
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S)
    lines = md.split('\n'); title=None; body=[]; first=None
    for ln in lines:
        if ln.startswith('# ') and title is None:
            title=ln[2:].strip(); continue
        if first is None and ln.strip() and not ln.strip().startswith('#'):
            first=ln.strip()
        body.append(ln)
    if not title and first: title=first[:40]
    txt='\n'.join(body).strip()
    html=[]; in_code=False; code=[]
    def flush():
        nonlocal code,in_code
        if code:
            html.append('<pre><code>'+'\n'.join(code).replace('&','&amp;').replace('<','&lt;')+'</code></pre>')
            code=[]; in_code=False
    for ln in txt.split('\n'):
        s=ln.strip()
        if s.startswith('```'):
            if in_code: flush()
            else: in_code=True
            continue
        if in_code: code.append(ln); continue
        if not s: continue
        if re.match(r'^0x[0-9A-Fa-f]+(\s|$)', s): html.append('<h3>'+s+'</h3>'); continue
        if s.startswith('#'):
            lvl=min(len(s.split(' ')[0]),6); html.append(f'<h{lvl}>'+s.lstrip('#').strip()+'</h{lvl}>'); continue
        if re.match(r'^\[[a-z]+', s):
            html.append(s); continue
        html.append('<p>'+s.replace('&','&amp;').replace('<','&lt;')+'</p>')
    flush()
    return title,'\n'.join(html)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('draft'); ap.add_argument('--out',default='./_out'); ap.add_argument('--format',default='html',choices=['html','hexo'])
    a=ap.parse_args()
    raw=open(a.draft,encoding='utf-8').read()
    title,html=md_to_html(raw)
    slug=slugify(title)
    os.makedirs(a.out,exist_ok=True)
    if a.format=='hexo':
        out=f"---\ntitle: {title}\ndate: {__import__('datetime').date.today()}\n---\n\n{html}\n"
        fn=os.path.join(a.out, f"{slug}.md")
    else:
        out=f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body>\n{html}\n</body></html>\n"
        fn=os.path.join(a.out, f"{slug}.html")
    open(fn,'w',encoding='utf-8').write(out)
    print(f"✅ 本地草稿已生成: {fn}")
    print(f"   标题: {title} | 格式: {a.format}")
    print("   说明: 这是多平台发布的可扩展样板。对接 Hexo/Typecho/WP 等时复制本文件改写即可。")

if __name__=='__main__':
    main()
