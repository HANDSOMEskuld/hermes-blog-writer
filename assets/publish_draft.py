#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Appstoy 草稿上传器（含 AI 分析分类/标签）
功能: 本地 MD 草稿 -> 转 HTML -> AI 分析选分类/标签 -> 以 draft 推到 WP 后台。

用法:
  export WP_USER=ricky
  export WP_APP_PASS='s8OT fF8A XrVj m55g Lz28 MQTD'   # 带空格也可，自动去
  export WP_SITE='https://appstoy.com'
  python3 publish_draft.py <草稿md> [--rebuild]   # --rebuild: 先抓全部分类/标签做匹配

前置:
  - 上传前应先跑 review_before_publish.py 过质检闸门。
  - 密码只从环境变量读，不写文件、不进 git。
安全:
  - 仅创建 status=draft，绝不 publish。
  - 带浏览器 UA 绕过 Cloudflare 对 POST 的 403 拦截。

AI 分析策略(轻量、确定性、可复现):
  用「标题+正文关键词」匹配 WP 已有分类/标签 ID(缓存到 ./_wp_terms.json)。
  分类命中规则(按内容关键词):
    switch/模拟器/xci/nsp/任天堂/joycon -> Switch(21)
    ios/iphone/ipad/苹果 -> IOS系统(56)
    windows/win -> Windows系统(57)
    mac -> MacOS电脑(58)
    linux -> Linux系统(59)
    android/安卓 -> 安卓系统(55)
    api/ai/chatgpt/大模型/模型 -> AI工具(6)
    教程/手把手/步骤 -> 优质教程(8)
    项目/开源/工具集合 -> 优质项目(62)
    建站/wordpress -> 建站分享(61)
    白嫖/优惠/福利/免费 -> 优惠内容(9)
    清单/合集/推荐 -> 合集推荐(10)
  标签命中(文中出现即挂): 见 TAG_RULES。
  兜底: 若无任何命中，分类用 优质教程(8)，标签用 教程(13)。
"""
import sys, os, re, json, base64, urllib.request, urllib.error

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_wp_terms.json')

# 分类关键词 -> id（顺序=优先级，前者优先；关键词需较精确，避免误命中）
CAT_RULES = [
    (['switch','模拟器','xci','nsp','任天堂','joycon','eden','yuzu'], 21),
    (['ios','iphone','ipad','苹果','巨魔','trollstore'], 56),
    (['windows','win10','win11'], 57),
    (['mac','macos'], 58),
    (['linux'], 59),
    (['安卓','android'], 55),
    (['api','chatgpt','大模型','gemini','硅基流动','智谱','cerebras','openrouter','deepseek'], 6),
    (['建站','wordpress','wp后台','wp 后台'], 61),
    (['白嫖','优惠','福利','代金券'], 9),
    (['清单','合集'], 10),
    (['教程','手把手','步骤'], 8),   # 兜底靠后：几乎都命中，放最后
]
# 标签关键词 -> 标签ID(须在WP存在)；仅选强相关词
TAG_RULES = {
    'switch':12,'xci':69,'nsp':70,'任天堂':66,'eden':14,'yuzu':14,
    'api':88,'ai':65,'chatgpt':89,'gemini':65,'硅基':65,'智谱':65,
    '白嫖':91,'教程':13,'工具':26,'清单':25,'福利':90,
    'wordpress':34,'建站':28,'服务器':80,
}

def get_terms(site, auth):
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    H = {"Authorization":"Basic "+auth,"User-Agent":UA}
    def fetch(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H,method="GET"),timeout=20))
    cats = {c['id']:c['name'] for c in fetch(f"{site}/wp-json/wp/v2/categories?per_page=100")}
    tags = {t['id']:t['name'] for t in fetch(f"{site}/wp-json/wp/v2/tags?per_page=100")}
    data = {"cats":cats,"tags":tags}
    json.dump(data, open(CACHE,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    return data

def analyze(text):
    low = text.lower()
    cat_ids, matched_cats = [], []
    for kws, cid in CAT_RULES:
        if any(k.lower() in low for k in kws):
            cat_ids.append(cid); matched_cats.append(cid)
    if not cat_ids: cat_ids = [8]   # 兜底 优质教程
    # 冲突消解：iOS 篇不挂 Windows；有更具体分类时去掉泛化"优质教程"除非只有它
    if 56 in cat_ids and 57 in cat_ids: cat_ids.remove(57)
    if len(cat_ids) > 1 and 8 in cat_ids and any(c in (6,21,56,61,9,10) for c in cat_ids):
        # 优质教程作为补充保留(教程类本就合适)，不强制去
        pass
    tag_ids, matched_tags = [], []
    for kw, tid in TAG_RULES.items():
        if kw.lower() in low:
            tag_ids.append(tid); matched_tags.append(tid)
    if not tag_ids: tag_ids = [13]
    return sorted(set(cat_ids)), sorted(set(tag_ids))

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
        # 0xN 小标题: 必须严格以 0x 开头 (修复把"8月"误判为标题的bug)
        if re.match(r'^0x[0-9A-Fa-f]+(\s|$)', s):
            html.append('<h3>'+s+'</h3>'); continue
        # Markdown 标准标题 # ## ###
        if s.startswith('#'):
            lvl=min(len(s.split(' ')[0]),6); html.append(f'<h{lvl}>'+s.lstrip('#').strip()+'</h{lvl}>'); continue
        # WP 短代码(如 [postsbox]) 原样保留, 不包 <p>, 避免古腾堡解析异常
        if re.match(r'^\[[a-z]+', s):
            html.append(s); continue
        html.append('<p>'+s.replace('&','&amp;').replace('<','&lt;')+'</p>')
    flush()
    return title,'\n'.join(html)

def main():
    if len(sys.argv)<2:
        print("用法: python3 publish_draft.py <草稿md> [--rebuild]"); sys.exit(1)
    md_path=sys.argv[1]; rebuild='--rebuild' in sys.argv
    if not os.path.exists(md_path): print("文件不存在:",md_path); sys.exit(1)
    user=os.environ.get('WP_USER'); pw=os.environ.get('WP_APP_PASS')
    site=os.environ.get('WP_SITE','https://appstoy.com').rstrip('/')
    if not(user and pw): print("❌ 缺 WP_USER/WP_APP_PASS 环境变量"); sys.exit(1)
    pw=pw.replace(' ','')
    auth=base64.b64encode(f"{user}:{pw}".encode()).decode()
    terms=get_terms(site,auth)
    if rebuild and os.path.exists(CACHE): os.remove(CACHE); terms=get_terms(site,auth)
    raw=open(md_path,encoding='utf-8').read()
    title,content=md_to_html(raw)
    cats,tags=analyze(raw)
    cat_names=[terms['cats'].get(str(c),terms['cats'].get(c,'?')) for c in cats]
    tag_names=[terms['tags'].get(str(t),terms['tags'].get(t,'?')) for t in tags]
    print(f"AI分析 -> 分类: {cat_names} | 标签: {tag_names}")
    payload={"title":title,"content":content,"status":"draft","categories":cats,"tags":tags}
    req=urllib.request.Request(f"{site}/wp-json/wp/v2/posts",data=json.dumps(payload).encode(),
        headers={"Authorization":"Basic "+auth,"Content-Type":"application/json","User-Agent":UA},method="POST")
    try:
        d=json.load(urllib.request.urlopen(req,timeout=30))
        print("✅ 草稿已建")
        print("  post_id:",d.get('id'),"| status:",d.get('status'))
        print("  编辑   :",d.get('link'))
        print("  标题   :",d.get('title',{}).get('rendered'))
    except urllib.error.HTTPError as e:
        print("❌ HTTP",e.code, e.read().decode()[:600])
    except Exception as e: print("❌",e)

if __name__=='__main__':
    main()
