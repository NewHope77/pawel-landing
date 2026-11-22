"""Turn the hard-coded accent colours of the built CSS into expressions of three animatable roles:
   --a1 highlight (pin: Sun Glare #daff02), --a2 action (Exuberant Orange #fe572a), --a3 atmosphere (Blue Violet #685bc7).
   Every literal is matched to the closest  mix(role, white|black, t)  or  mix(--a2, --a3, t)  with the pin values,
   so the pin palette renders as before, and any other palette re-colours every derived tint/shade/mix consistently.
   Neutral colours (greys, whites, graphite) stay as they are; colours inside url(data:…) are never touched."""
import re
ROLES = {'a1': (218, 255, 2), 'a2': (254, 87, 42), 'a3': (104, 91, 199)}
W, K = (255, 255, 255), (0, 0, 0)

def mix(a, b, t):            # t = share of b
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))

def lin(c):
    c = c / 255
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4

def lab(rgb):                # OKLab — perceptual distance
    r, g, b = (lin(x) for x in rgb)
    l = .4122214708 * r + .5363325363 * g + .0514459929 * b
    m = .2119034982 * r + .6806995451 * g + .1073969566 * b
    s = .0883024619 * r + .2817188376 * g + .6299787005 * b
    l, m, s = (x ** (1 / 3) if x > 0 else 0 for x in (l, m, s))
    return (.2104542553 * l + .7936177850 * m - .0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + .4505937099 * s,
            .0259040371 * l + .7827717662 * m - .8086757660 * s)

def dist(a, b):
    A, B = lab(a), lab(b)
    return sum((A[i] - B[i]) ** 2 for i in range(3)) ** .5

CANDS = []
for k, rc in ROLES.items():
    for i in range(0, 19):
        t = i / 20
        CANDS.append((mix(rc, W, t), k, 'w', t))
        if t: CANDS.append((mix(rc, K, t), k, 'k', t))
for i in range(1, 20):
    t = i / 20
    CANDS.append((mix(ROLES['a2'], ROLES['a3'], t), 'a2a3', '', t))
    CANDS.append((mix(ROLES['a1'], ROLES['a2'], t), 'a1a2', '', t))

def neutral(rgb):
    mx, mn = max(rgb), min(rgb)
    return mx - mn < 26 or (mx > 0 and (mx - mn) / mx < .16)

def expr(rgb):
    best = min(CANDS, key=lambda c: dist(c[0], rgb))
    _, k, kind, t = best
    pct = lambda x: f'{round(x * 100)}%'
    if k == 'a2a3': return f'color-mix(in srgb,var(--a2),var(--a3) {pct(t)})', best
    if k == 'a1a2': return f'color-mix(in srgb,var(--a1),var(--a2) {pct(t)})', best
    if t == 0: return f'var(--{k})', best
    return f'color-mix(in srgb,var(--{k}),{"#fff" if kind == "w" else "#000"} {pct(t)})', best

HEX = r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b'
RGBA = r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)'

def to_rgb(h):
    h = h[1:]
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rolify(css, report=None):
    out, pos = [], 0
    for m in re.finditer(r'url\((?:"[^"]*"|\'[^\']*\'|[^)]*)\)', css):        # keep url(...) verbatim
        out.append(_conv(css[pos:m.start()], report)); out.append(m.group(0)); pos = m.end()
    out.append(_conv(css[pos:], report))
    return ''.join(out)

def _conv(s, report):
    def rep_rgba(m):
        rgb = tuple(int(m.group(i)) for i in (1, 2, 3)); a = m.group(4)
        if neutral(rgb): return m.group(0)
        e, best = expr(rgb)
        if report is not None: report.append((m.group(0), e, round(dist(best[0], rgb), 3)))
        if a is None or float(a) >= 1: return e
        return f'color-mix(in srgb,{e} {round(float(a) * 100, 1):g}%,transparent)'
    def rep_hex(m):
        rgb = to_rgb(m.group(0))
        if neutral(rgb): return m.group(0)
        e, best = expr(rgb)
        if report is not None: report.append((m.group(0), e, round(dist(best[0], rgb), 3)))
        return e
    s = re.sub(RGBA, rep_rgba, s)
    s = re.sub(r'(?<![\w&])' + HEX, rep_hex, s)
    return s
