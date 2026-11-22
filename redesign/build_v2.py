#!/usr/bin/env python3
"""Build v2.html (new design) from the content of the current index.html."""
import re, html, json, pathlib

ROOT = pathlib.Path('/Users/pauls/claude-projects/personal-page')
SRC = (pathlib.Path(__file__).with_name('content_source.html')).read_text(encoding='utf-8')   # old site = content source (portfolio, prices, FAQ, blog)
TPL = pathlib.Path(__file__).with_name('v2_template.html').read_text(encoding='utf-8')

def strip(s): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip())
def one(pat, s, default=''):
    m = re.search(pat, s, re.S); return m.group(1) if m else default

# ---------- realizacje ----------
works = []
for a in re.findall(r'<article class="work[^"]*">(.*?)</article>', SRC, re.S):
    thumb = one(r'(<div class="thumb[^>]*>)', a)
    w = {
        'img': one(r'<img src="([^"]+)"', a),
        'alt': one(r'<img[^>]*alt="([^"]*)"', a),
        'badge_cls': one(r'<span class="(done|seo|wip|app-badge)">', a),
        'badge': one(r'<span class="(?:done|seo|wip|app-badge)">([^<]*)</span>', a),
        'title': strip(one(r'<h3>(.*?)</h3>', a)),
        'tag': strip(one(r'<div class="tag">(.*?)</div>', a)),
        'desc': strip(one(r'<p>(.*?)</p>', a)),
        'href': one(r'<a class="link" href="([^"]+)"', a),
        'link_txt': strip(one(r'class="link[^"]*"[^>]*>(.*?)<span class="ar">', a)),
        'lb': one(r'data-lb="([^"]+)"', thumb), 'lb_cap': one(r'data-lb-cap="([^"]*)"', thumb),
        'gallery': one(r"data-gallery='([^']+)'", thumb),
    }
    works.append(w)

FLAG = {'wip': 'W trakcie', 'app-badge': 'Aplikacja', 'seo': 'SEO'}
cards = []
for i, w in enumerate(works):
    flag = FLAG.get(w['badge_cls'], '')
    flag_html = f'<span class="w-flag">{html.escape(flag)}</span>' if flag else ''
    label = html.escape(f"{w['title']} — {w['desc']}", quote=True)
    inner = f'<span class="w-img"><img src="{w['img']}" alt="{html.escape(w['alt'], quote=True)}" loading="lazy" width="780" height="500">{flag_html}<span class="w-go" aria-hidden="true">↗</span></span>'
    if w['href']:
        frame = f'<a class="w-frame" href="{w['href']}" target="_blank" rel="noopener" aria-label="{label}" title="{label}">{inner}</a>'
    elif w['gallery']:
        frame = f'<button class="w-frame" type="button" data-gallery=\'{w['gallery']}\' aria-label="{label}" title="{label}">{inner}</button>'
    else:
        cap = html.escape(w['lb_cap'], quote=True)
        frame = f'<button class="w-frame" type="button" data-lb="{w['lb']}" data-lb-cap="{cap}" aria-label="{label}" title="{label}">{inner}</button>'
    cards.append(f'''      <article class="w-card">
        {frame}
        <div class="w-cap"><h3>{html.escape(w['title'])}</h3><span>{html.escape(w['tag'])}</span></div>
      </article>''')

# ---------- cennik ----------
prices = []
for blk in re.findall(r'<div class="price-card[^"]*">(.*?)\n        </div>\n', SRC, re.S):
    prices.append({
        'svg': one(r'<div class="pic">(<svg.*?</svg>)</div>', blk),
        'name': strip(one(r'<h3>(.*?)</h3>', blk)),
        'desc': strip(one(r'<p>(.*?)</p>', blk)),
        'od': '<span class="od">od</span>' in blk,
        'v': one(r'<span class="v">([^<]+)</span>', blk),
        'popular': 'price-hot' in blk,
    })
fixed = [p for p in prices if not p['od']]
ind = [p for p in prices if p['od']]
def rline(p):
    pop = ' pop' if p['popular'] else ''
    ok = '<span class="p-ok" aria-label="najczęściej wybierane">✓</span>' if p['popular'] else ''
    od = '<em>od</em>' if p['od'] else ''
    return f'''          <li class="p-row{pop}"><span class="p-ic">{p['svg']}</span><span class="p-main"><b>{html.escape(p['name'])}</b><small>{html.escape(p['desc'])}</small></span><span class="p-val">{od}{p['v']} zł</span>{ok}</li>'''
popular = next(p for p in prices if p['popular'])

# ---------- usługi ----------
usl = re.search(r'<section id="uslugi">(.*?)</section>', SRC, re.S).group(1)
services = []
for c in re.findall(r'<div class="card reveal">(.*?)\n        </div>\n', usl, re.S):
    services.append({'t': strip(one(r'<h3>(.*?)</h3>', c)), 'p': strip(one(r'<p>(.*?)</p>', c)), 'li': [strip(x) for x in re.findall(r'<li>(.*?)</li>', c)]})
srows = []
for i, s in enumerate(services, 1):
    pills = ''.join(f'<span>{html.escape(x)}</span>' for x in s['li'])
    srows.append(f'''        <li class="s-row" data-reveal style="--i:{i}"><span class="s-num">{i:02d}</span><h3>{html.escape(s['t'])}</h3><p>{html.escape(s['p'])}</p><div class="s-pills">{pills}</div></li>''')

# ---------- FAQ ----------
faq = re.search(r'<section id="faq">(.*?)</section>', SRC, re.S).group(1)
faqs = []
for q, a in re.findall(r'<summary>(.*?)</summary>\s*<div class="faq-a">(.*?)</div>', faq, re.S):
    faqs.append(f'''          <details class="q"><summary>{q}<span class="q-ic" aria-hidden="true"></span></summary><div class="q-a">{a}</div></details>''')

# ---------- blog ----------
blog = re.search(r'<section id="blog">(.*?)</section>', SRC, re.S).group(1)
posts = []
for href, img, alt, cat, h3 in re.findall(r'<a class="hb-card reveal" href="([^"]+)">\s*<img src="([^"]+)" alt="([^"]*)"[^>]*>\s*<div class="b"><span class="cat">([^<]*)</span><h3>(.*?)</h3>', blog, re.S):
    posts.append(f'''        <a class="post" href="{href}" data-reveal><div class="post-img"><img src="{img}" alt="{html.escape(alt, quote=True)}" loading="lazy" width="1200" height="630"></div><span class="post-cat">{cat}</span><h3>{h3}</h3><span class="post-more">Czytaj <span aria-hidden="true">→</span></span></a>''')

lbcss = one(r'(/\* -+ Lightbox.*?)/\* -+ O MNIE', SRC)
assert lbcss, 'lightbox css not found'
out = (TPL
       .replace('%%LBCSS%%', lbcss)
       .replace('%%WORKS%%', '\n'.join(cards))
       .replace('%%WORKS_N%%', str(len(works)))
       .replace('%%FIXED%%', '\n'.join(rline(p) for p in fixed))
       .replace('%%IND%%', '\n'.join(rline(p) for p in ind))
       .replace('%%POP_NAME%%', html.escape(popular['name']))
       .replace('%%POP_DESC%%', html.escape(popular['desc']))
       .replace('%%POP_V%%', popular['v'])
       .replace('%%SERVICES%%', '\n'.join(srows))
       .replace('%%FAQ%%', '\n'.join(faqs))
       .replace('%%POSTS%%', '\n'.join(posts)))
left = re.findall(r'%%[A-Z_]+%%', out)
assert not left, left
# orange variant is no longer published (kept buildable in `out`)
print(f'content: {len(works)} works, {len(fixed)}+{len(ind)} prices, {len(services)} services, {len(faqs)} faq, {len(posts)} posts')

# ---------- palette variant "pin" (Pantone: Sun Glare / Exuberant Orange / Blue Violet / Cloud Dancer / Darkest Hour) ----------
PIN_MAP = [
    ('rgba(69,48,39', 'rgba(58,54,56'), ('#453027', '#3a3638'), ('rgba(22,19,22', 'rgba(32,30,31'), ('#161316', '#201e1f'),
    ('#211a17', '#2a2728'), ('#1a1512', '#1b191a'), ('#231c19', '#2a2728'), ('#120e0d', '#181617'), ('#4a1d06', '#201e1f'),
    ('#f6f1ed', '#f3f0eb'), ('#efe7e1', '#ebe7e0'), ('rgba(246,241,237', 'rgba(243,240,235'),
    ('rgba(255,109,41', 'rgba(254,87,42'), ('rgba(255,100,30', 'rgba(254,87,42'), ('rgba(255,90,20', 'rgba(254,87,42'),
    ('#ff6d29', '#fe572a'), ('#FF6D29', '#FE572A'), ('#ff5a14', '#e8431a'), ('#e9520f', '#e8431a'), ('#ea5310', '#e8431a'),
    ('rgba(255,146,84', 'rgba(255,128,96'), ('rgba(255,104,36', 'rgba(254,87,42'), ('rgba(238,78,14', 'rgba(230,64,26'),
    ('rgba(255,138,72', 'rgba(255,122,92'), ('rgba(255,100,32', 'rgba(254,87,42'), ('rgba(232,74,12', 'rgba(226,62,24'),
]
pin_css = (pathlib.Path(__file__).with_name('palette_pin.css')).read_text(encoding='utf-8')
a, b = out.index('<style>'), out.index('</style>')
style = out[a:b]
for o, n in PIN_MAP:
    style = style.replace(o, n)
anchor = '@media (prefers-reduced-motion: reduce){.btn-blue::before'
assert style.count(anchor) == 1
style = style.replace(anchor, pin_css + anchor)
import sys as _sys; _sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rolify import rolify
style = rolify(style)                                                     # accents → --a1/--a2/--a3
style = style.replace('</style>', '') + (pathlib.Path(__file__).with_name('palettes.css')).read_text(encoding='utf-8')
pin = out[:a] + style + out[b:]
pin = pin.replace('<meta name="theme-color" content="#161316">', '<meta name="theme-color" content="#201e1f">')

# ---------- production: index.html = pin palette + the SEO head of the old site ----------
oh = SRC[SRC.index('<head>'):SRC.index('</head>')]
seo = oh[oh.index('<meta name="description"'):oh.index('<link rel="preconnect"')]      # description … twitter:image, favicons, manifest
seo = seo.replace('<meta name="theme-color" content="#0e1116">', '<meta name="theme-color" content="#201e1f">')
ld = re.search(r'\s*<script type="application/ld\+json">.*?</script>', SRC, re.S).group(0)
title = re.search(r'<title>.*?</title>', SRC, re.S).group(0)
idx = pin
idx = re.sub(r'<title>.*?</title>', title, idx, count=1, flags=re.S)
assert '<meta name="robots" content="noindex">' in idx
idx = idx.replace('<meta name="robots" content="noindex">\n', '').replace('<meta name="robots" content="noindex">', '')
idx = idx.replace('<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">', seo.strip(), 1)
idx = idx.replace('</body>', ld.rstrip() + '\n</body>', 1)
assert 'noindex' not in idx and 'application/ld+json' in idx and 'rel="canonical"' in idx
json_txt = re.search(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S).group(1)
json.loads(json_txt)
(ROOT / 'index.html').write_text(idx, encoding='utf-8')
print('index.html: pin palette + SEO head + JSON-LD')
