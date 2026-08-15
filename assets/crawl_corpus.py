#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取任意 WordPress 站点的文章语料，用于后续风格迭代。
用法:
  python3 crawl_corpus.py --site https://你的站.com --out ./corpus [--per-page 50] [--limit 60]
依赖: 仅标准库 (urllib)。需要站点开放 WP REST API (默认开启)。
输出: corpus/full_<id>.txt 每篇一篇，首行"标题|日期|浏览量(若暴露)"，余为正文纯文本。
说明: 若站点用 Cloudflare，需在 header 带浏览器 UA (已内置)。
"""
import argparse, json, os, re, base64, urllib.request, urllib.error, html

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def fetch(url, auth=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if auth: headers["Authorization"] = "Basic " + auth
    req = urllib.request.Request(url, headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=30))

def strip_html(h):
    h = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
    h = re.sub(r'<style.*?</style>', ' ', h, flags=re.S)
    h = re.sub(r'<[^>]+>', '\n', h)
    h = html.unescape(h)
    return '\n'.join(line.strip() for line in h.splitlines() if line.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', required=True, help='WordPress 站点根，如 https://appstoy.com')
    ap.add_argument('--out', default='./corpus')
    ap.add_argument('--per-page', type=int, default=50)
    ap.add_argument('--limit', type=int, default=60, help='最多抓取篇数')
    ap.add_argument('--user', help='若需鉴权(私密站)填 WP 用户名')
    ap.add_argument('--pass', dest='pw', help='应用密码(可带空格)')
    a = ap.parse_args()
    site = a.site.rstrip('/')
    os.makedirs(a.out, exist_ok=True)
    auth = base64.b64encode(f"{a.user}:{a.pw.replace(' ','')}".encode()).decode() if a.user else None
    page, collected = 1, []
    while len(collected) < a.limit:
        try:
            posts = fetch(f"{site}/wp-json/wp/v2/posts?per_page={a.per_page}&page={page}&_fields=id,date,title,content,link,meta", auth=auth)
        except urllib.error.HTTPError as e:
            if e.code == 400: break
            raise
        if not posts: break
        collected.extend(posts)
        page += 1
    collected = collected[:a.limit]
    idx = []
    for p in collected:
        pid = p['id']
        title = re.sub(r'<[^>]+>', '', p['title']['rendered']).strip()
        date = p.get('date', '')[:10]
        body = strip_html(p['content']['rendered'])
        # 尝试从 meta 取浏览量(各主题字段不同，常见 views/post_views)
        views = p.get('meta', {}).get('views') or p.get('meta', {}).get('post_views') or ''
        fn = os.path.join(a.out, f"full_{pid}.txt")
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(f"{title}|{date}|{views}\n{body}\n")
        idx.append({"id": pid, "title": title, "date": date, "views": views, "file": fn})
    json.dump(idx, open(os.path.join(a.out, "_index.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"✅ 抓取 {len(idx)} 篇 -> {a.out}/")
    print("提示: 部分主题浏览量不暴露 REST，可改用 ?orderby=views 抓列表页解析，或人工标注热度。")

if __name__ == '__main__':
    main()
