#!/usr/bin/env python3
"""초식남녀 모션 그래픽 v2 — 종이 콜라주 스토리북 스타일 (공룡 캐릭터)

python3 make_dino_motion.py preview OUTDIR t1 t2 ...   # 특정 시점 프레임 PNG
python3 make_dino_motion.py render OUT.mp4              # 전체 렌더 (1080x1080, 24fps, 배경음악 포함)
"""
import os, sys, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as ndi
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, 'assets')
S, FPS = 1080, 24

# ---------------------------------------------------------------- colors
PAPER = (251, 247, 238); INK = (58, 46, 42); BLUE = (40, 70, 168); RED = (220, 62, 50)
CREAMT = (250, 243, 226); CREAMINK = (252, 244, 222)
NAVY = (30, 40, 92); NAVY2 = (46, 60, 124); CITY = (38, 38, 84); WIN = (250, 212, 96)
WALL = (88, 62, 130); CURT = (238, 128, 150); SILL = (196, 150, 96)
TAN = (206, 160, 104); TAN2 = (226, 188, 130)
YEL = (246, 204, 86); PINK = (242, 168, 192); MINT = (152, 212, 186); LAV = (164, 138, 204)
PEACH = (247, 186, 148); CORAL = (244, 118, 94); HEARTC = (238, 96, 108)
WARM = (234, 164, 108); FLOOR = (166, 106, 70); WOOD = (150, 96, 62)
GREEN_D = (52, 92, 44); GRAY = (200, 200, 194); GRAY_D = (120, 118, 112)


# ---------------------------------------------------------------- easing
def cl(x): return max(0.0, min(1.0, x))
def fi(t, a, d): return cl((t - a) / d)
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return 3 * x * x - 2 * x ** 3
def bo(x):
    x = cl(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def pop(t, t0, d=0.5): return bo(fi(t, t0, d))


# ---------------------------------------------------------------- fonts / text
@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, int(size))
def H(size): return font(os.path.join(A, 'YeonSung-Regular.ttf'), size)
def J(size): return font(os.path.join(A, 'Jua-Regular.ttf'), size)
def F(f, size): return H(size) if f == 'h' else J(size)

def fit(s, maxw, size, f='h'):
    while size > 20 and F(f, size).getlength(s) > maxw:
        size -= 2
    return size

@functools.lru_cache(maxsize=1024)
def tsp(s, size, col, f='h'):
    fnt = F(f, size); asc, desc = fnt.getmetrics()
    w = int(fnt.getlength(s)) + 16
    im = Image.new('RGBA', (max(w, 17), asc + desc + 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), s, font=fnt, fill=col)
    return im

def nchars(s, p):
    return int(round(len(s) * cl(p)))

def text(cv, s, x, y, size, col, f='h', p=1.0, alpha=1.0, ax=0.5, ay=0.5):
    """손글씨처럼 한 글자씩 나타나는 텍스트 (p: 0~1)"""
    if p <= 0 or alpha <= 0.01: return
    full = tsp(s, size, col, f)
    W0, H0 = full.size
    sub = s[:nchars(s, p)] if p < 1 else s
    if not sub: return
    im = tsp(sub, size, col, f)
    put(cv, im, x - W0 * ax, y - H0 * ay, 0, 0, alpha)

def textb(cv, s, x, base, size, col, f='h', p=1.0, alpha=1.0):
    """왼쪽 정렬, 기준선(baseline) 위치 지정"""
    asc, _ = F(f, size).getmetrics()
    text(cv, s, x, base - 8 - asc, size, col, f, p, alpha, 0, 0)

def tw(s, size, f='h'): return F(f, size).getlength(s)


# ---------------------------------------------------------------- texture & paper
def _tex():
    rng = np.random.default_rng(11)
    N = S * 2
    f = Image.fromarray((rng.random((N // 3, N // 3)) * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)
    f = np.asarray(f, np.float32) / 255
    st = Image.fromarray((rng.random((26, N + N // 2)) * 255).astype(np.uint8)).resize(
        (N + N // 2, N + N // 2), Image.BICUBIC).rotate(30, resample=Image.BICUBIC)
    o = N // 4
    st = np.asarray(st, np.float32)[o:o + N, o:o + N] / 255
    spk = (rng.random((N, N)) > 0.993).astype(np.float32)
    spk = np.clip(ndi.gaussian_filter(spk, 0.9) * 4, 0, 1)
    t = 1 + 0.07 * (f - .5) + 0.13 * (st - .5) + 0.10 * spk
    return np.clip(t, 0.85, 1.15).astype(np.float32)

TEX = _tex()

def tex_fill(color, w, h, seed=0):
    rng = np.random.default_rng(seed)
    ox = int(rng.integers(0, max(1, TEX.shape[1] - w)))
    oy = int(rng.integers(0, max(1, TEX.shape[0] - h)))
    t = TEX[oy:oy + h, ox:ox + w]
    return np.clip(np.array(color, np.float32)[None, None, :] * t[..., None], 0, 255)

def paper_from(ma, fill, edge=8, shadow=True, seed=0):
    h, w = ma.shape
    rng = np.random.default_rng(seed + 100)
    if edge > 0:
        bl = ndi.gaussian_filter(ma, edge * 0.55)
        k = 6
        nz = rng.random((h // k + 3, w // k + 3)).astype(np.float32)
        nz = ndi.zoom(nz, k, order=1)[:h, :w]
        em = np.clip((bl - 0.07 + (nz - 0.5) * 0.12) * 14, 0, 1)
        em = np.maximum(em, ma)
    else:
        em = ma
    pap = tex_fill(PAPER, w, h, seed + 7)
    rgb = fill * ma[..., None] + pap * (1 - ma[..., None])
    if shadow:
        sh = ndi.gaussian_filter(em, 4.5)
        sh = np.roll(np.roll(sh, 6, 0), 4, 1) * 0.30
    else:
        sh = np.zeros_like(em)
    Aa = em + sh * (1 - em)
    RGB = rgb * (em / np.maximum(Aa, 1e-4))[..., None]
    out = np.dstack([np.clip(RGB, 0, 255), np.clip(Aa * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')

def shape(w, h, draw, color, edge=8, shadow=True, seed=0, detail=None):
    pad = int(edge * 3 + 16)
    W2, H2 = int(w + 2 * pad), int(h + 2 * pad)
    m = Image.new('L', (W2, H2), 0)
    draw(ImageDraw.Draw(m), pad, pad)
    m = m.filter(ImageFilter.GaussianBlur(0.8))
    ma = np.asarray(m, np.float32) / 255
    im = paper_from(ma, tex_fill(color, W2, H2, seed), edge, shadow, seed)
    if detail:
        detail(ImageDraw.Draw(im), im, pad, pad)
    im.info['pad'] = pad
    return im

def sticker(img, edge=9, seed=0):
    pad = int(edge * 3 + 16)
    W2, H2 = img.width + 2 * pad, img.height + 2 * pad
    c = Image.new('RGBA', (W2, H2), (0, 0, 0, 0)); c.paste(img, (pad, pad))
    arr = np.asarray(c, np.float32)
    im = paper_from(arr[..., 3] / 255, arr[..., :3], edge, True, seed)
    im.info['pad'] = pad
    return im

def solid(color, seed=0):
    return Image.fromarray(tex_fill(color, S, S, seed).astype(np.uint8), 'RGB').convert('RGBA')


# ---------------------------------------------------------------- compositing
LUT = [[int(v * a / 100) for v in range(256)] for a in range(101)]

def put(cv, spr, x, y, ax=0.5, ay=0.5, alpha=1.0):
    if alpha <= 0.01 or spr is None: return
    if alpha < 0.995:
        spr = spr.copy(); spr.putalpha(spr.getchannel('A').point(LUT[int(alpha * 100)]))
    w, h = spr.size
    x0 = int(round(x - w * ax)); y0 = int(round(y - h * ay))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(w, S - x0), min(h, S - y0)
    if sx1 <= sx0 or sy1 <= sy0: return
    cv.alpha_composite(spr, (x0 + sx0, y0 + sy0), (sx0, sy0, sx1, sy1))

def place(cv, spr, x, y, alpha=1.0):
    p = spr.info.get('pad', 0)
    put(cv, spr, x - p, y - p, 0, 0, alpha)

SPR, BUILD = {}, {}
def B(name):
    def deco(fn): BUILD[name] = fn; return fn
    return deco
def sp(name):
    if name not in SPR: SPR[name] = BUILD[name]()
    return SPR[name]

@functools.lru_cache(maxsize=600)
def _xf(name, sx, sy, rot, flip):
    im = sp(name)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if (sx, sy) != (1.0, 1.0):
        w, h = im.size
        im = im.resize((max(1, int(w * sx)), max(1, int(h * sy))), Image.BICUBIC)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im

def X(name, s=1.0, rot=0.0, flip=False, sy=None):
    sx = round(max(s, 0.01), 3); syy = sx if sy is None else round(max(sy, 0.01), 3)
    return _xf(name, sx, syy, round(rot, 1), flip)

def putc(cv, name, x, y, s=1.0, rot=0.0, flip=False, alpha=1.0, ax=0.5, ay=0.5):
    if s <= 0.02: return
    put(cv, X(name, s, rot, flip), x, y, ax, ay, alpha)


# ---------------------------------------------------------------- drawing helpers
def heart_pts(cx, cy, s):
    pts = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 16, cy + y * s / 16))
    return pts

def star(d, x, y, r, col):
    k = 0.3
    d.polygon([(x, y - r), (x + r * k, y - r * k), (x + r, y), (x + r * k, y + r * k),
               (x, y + r), (x - r * k, y + r * k), (x - r, y), (x - r * k, y - r * k)], fill=col)

def twinkle(cv, t, n=16, ymax=470, seed=4, col=CREAMINK, rmax=11):
    d = ImageDraw.Draw(cv); rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = rng.integers(40, S - 40), rng.integers(40, ymax)
        if x < 300 and y < 260: continue
        r = rmax * (0.55 + 0.45 * math.sin(t * 3 + i * 1.7))
        star(d, int(x), int(y), r, col)

def burst(cv, cx, cy, r0, r1, n, t, col, w=7, spin=0.15):
    """레퍼런스의 방사형 선 장식"""
    d = ImageDraw.Draw(cv)
    for i in range(n):
        a = 2 * math.pi * i / n + t * spin
        wob = 1 + 0.06 * math.sin(t * 4 + i)
        d.line([(cx + r0 * wob * math.cos(a), cy + r0 * wob * math.sin(a)),
                (cx + r1 * wob * math.cos(a), cy + r1 * wob * math.sin(a))], fill=col, width=w)

def checkmark(d, x, y, s, p, col=RED, w=8):
    if p <= 0: return
    a = (x - .45 * s, y); b = (x - .1 * s, y + .38 * s); c = (x + .55 * s, y - .45 * s)
    if p < 0.4:
        q = p / 0.4; d.line([a, (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)], fill=col, width=w)
    else:
        q = (p - 0.4) / 0.6
        d.line([a, b, (b[0] + (c[0] - b[0]) * q, b[1] + (c[1] - b[1]) * q)], fill=col, width=w, joint='curve')

def dashed_line(d, p0, p1, col, w=5, dash=16, gap=12, phase=0.0):
    L = math.dist(p0, p1)
    if L < 1: return
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    s = -(phase % (dash + gap))
    while s < L:
        a, b = max(0, s), min(L, s + dash)
        if b > a: d.line([(p0[0] + ux * a, p0[1] + uy * a), (p0[0] + ux * b, p0[1] + uy * b)], fill=col, width=w)
        s += dash + gap

def label(cv, lt, lines, t0=0.35, col=INK, y=None):
    n = len(lines)
    ys = [995] if n == 1 else [940, 1018]
    if y is not None: ys = [y + 78 * i for i in range(n)]
    for i, (s, size) in enumerate(lines):
        st = t0 + 0.55 * i
        p = fi(lt, st, 0.05 * len(s) + 0.15)
        text(cv, s, 540, ys[i], fit(s, 1000, int(size * 1.12)), col, p=p)


# ---------------------------------------------------------------- dinosaur
EYES = [(121, 185), (270, 228)]
OUTL = (48, 84, 40)

def _body_color(arr, cx, cy, r0=30, r1=44):
    yy, xx = np.mgrid[-r1:r1 + 1, -r1:r1 + 1]
    ring = (np.hypot(xx, yy) > r0) & (np.hypot(xx, yy) < r1)
    pix = arr[cy - r1:cy + r1 + 1, cx - r1:cx + r1 + 1][ring]
    g = pix[(pix[:, 1] > pix[:, 0] + 15) & (pix.sum(1) > 380)]
    return np.median(g, 0).astype(float) if len(g) > 10 else np.array([170., 205., 130.])

def _repaint(rgb, mask, col, seed):
    rng = np.random.default_rng(seed)
    nz = ndi.gaussian_filter(rng.random(mask.shape), 1.2)
    nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    fill = col[None, None, :] * (1 + 0.035 * nz[..., None])
    rgb[mask] = np.clip(fill[mask], 0, 255)

@functools.lru_cache(None)
def dino_raw(variant, blink, mood='n'):
    """mood: n=기본(하트, 미소) / w=걱정(하트 없음, 처진 눈썹, 시무룩한 입) / h=행복(눈웃음, 활짝 웃는 입)"""
    im = Image.open(os.path.join(A, 'dino.png')).convert('RGBA')
    arr = np.asarray(im).astype(float)
    rgb = arr[..., :3].copy(); al = arr[..., 3]
    body = _body_color(rgb.astype(int), 121, 185)
    if mood == 'w':
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        reg = np.zeros(al.shape, bool); reg[540:740, 105:315] = True
        red = (r > g + 30) & (r > b + 20) & reg & (al > 10)
        red = ndi.binary_dilation(red, iterations=2) & reg & ((r + g + b) > 330)
        _repaint(rgb, red, body, 1)
        mreg = np.zeros(al.shape, bool); mreg[222:274, 142:222] = True
        mouth = ndi.binary_dilation((r + g + b) < 400, iterations=3) & mreg
        _repaint(rgb, mouth, body, 2)
    im = Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    if blink or mood == 'h':
        for cx, cy in EYES:
            c = tuple(int(v) for v in _body_color(np.asarray(im)[..., :3].astype(int), cx, cy))
            d.ellipse([cx - 21, cy - 26, cx + 21, cy + 26], fill=c + (255,))
            d.arc([cx - 20, cy - 6, cx + 20, cy + 22], 200, 340, fill=OUTL + (255,), width=8)
    if mood == 'w':
        d.arc([160, 246, 206, 282], 200, 340, fill=OUTL + (255,), width=7)
        d.line([(94, 152), (142, 134)], fill=OUTL + (255,), width=7)
        d.line([(248, 180), (294, 196)], fill=OUTL + (255,), width=7)
    if mood == 'h':
        d.chord([150, 214, 214, 284], 0, 180, fill=(172, 62, 58, 255), outline=OUTL + (255,), width=5)
        d.ellipse([170, 258, 196, 280], fill=(242, 132, 132, 255))
    if variant == 'p':
        hsv = np.asarray(im.convert('RGB').convert('HSV')).astype(int)
        h, s_, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        sel = (h > 35) & (h < 120) & (s_ > 30)
        h2 = np.where(sel, (h - 64 + 236) % 256, h)
        v2 = np.where(sel, np.minimum(255, v * 1.05), v)
        rgbp = Image.fromarray(np.stack([h2, s_, v2], -1).astype(np.uint8), 'HSV').convert('RGB')
        a = im.getchannel('A'); im = rgbp.convert('RGBA'); im.putalpha(a)
    return im

DH = 640
def _mk_d(v, mood, b):
    return sticker(dino_raw(v, bool(b), mood).resize((int(920 * DH / 1077), DH), Image.LANCZOS), 9, 3)
for _v in 'gp':
    for _m in 'nwh':
        for _b in (0, 1):
            BUILD['d%s%s%d' % (_v, _m, _b)] = (lambda v=_v, m=_m, b=_b: _mk_d(v, m, b))

def dino(cv, x, y, h, t, v='g', flip=False, bob=1.0, rot=0.0, seed=0.0, alpha=1.0, blink=None, mood='n'):
    if blink is None:
        blink = ((t + seed * 1.3) % 3.1) < 0.14
    if mood == 'h': blink = False
    name = 'd%s%s%d' % (v, mood, int(blink))
    im0 = sp(name); pad = im0.info['pad']
    s = h / DH
    b = math.sin(t * 2.6 + seed) * bob
    im = X(name, s * (1 - 0.02 * b), rot, flip, s * (1 + 0.03 * b))
    put(cv, im, x, y + pad * s, 0.5, 1.0, alpha)


# ---------------------------------------------------------------- sprite builders
@B('moon')
def _():
    def dr(d, ox, oy):
        d.ellipse([ox, oy, ox + 140, oy + 140], fill=255); d.ellipse([ox + 46, oy - 20, ox + 186, oy + 120], fill=0)
    return shape(140, 140, dr, (250, 236, 196), 5, seed=2)

HOUSES = [(0, 110, 210, 1), (96, 96, 150, 0), (182, 122, 250, 1), (292, 100, 175, 1), (382, 92, 270, 0), (464, 116, 195, 1)]
@B('city')
def _():
    def dr(d, ox, oy):
        for x, w, top, tri in HOUSES:
            d.rectangle([ox + x, oy + top, ox + x + w, oy + 540], fill=255)
            if tri: d.polygon([(ox + x - 6, oy + top), (ox + x + w / 2, oy + top - 62), (ox + x + w + 6, oy + top)], fill=255)
    def det(d, im, ox, oy):
        rng = np.random.default_rng(9)
        for x, w, top, tri in HOUSES:
            for yy in range(top + 30, 520, 62):
                for xx in range(x + 18, x + w - 28, 38):
                    if rng.random() < 0.6:
                        d.rectangle([ox + xx, oy + yy, ox + xx + 16, oy + yy + 22], fill=WIN)
        # 지붕 위 고양이 실루엣 대신 작은 안테나
        d.line([(ox + 243, oy + 188), (ox + 243, oy + 150)], fill=CITY, width=4)
    return shape(580, 540, dr, CITY, 6, seed=8, detail=det)

@B('band')
def _():
    def dr(d, ox, oy):
        pts = [(ox - 10, oy + 120)]
        for x in range(0, S + 120, 30):
            pts.append((ox + x - 30, oy + 60 + 22 * math.sin(x / 95) + 10 * math.sin(x / 31)))
        pts += [(ox + S + 60, oy + 700), (ox - 10, oy + 700)]
        d.polygon(pts, fill=255)
    return shape(S + 40, 700, dr, NAVY2, 7, seed=5)

@B('bg_sky')
def _():
    cv = solid(NAVY, 1)
    d = ImageDraw.Draw(cv); rng = np.random.default_rng(3)
    for i in range(80):
        x, y = int(rng.integers(0, S)), int(rng.integers(0, 560)); r = int(rng.integers(1, 3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(214, 216, 236))
    place(cv, sp('band'), -20, 420)
    place(cv, sp('moon'), 110, 80)
    place(cv, sp('city'), 530, 590)
    return cv

@B('bg_win')
def _():
    cv = sp('bg_sky').copy()
    win = shape(380, 380, lambda d, ox, oy: d.rectangle([ox, oy, ox + 380, oy + 380], fill=255), WIN, 0, False, 12)
    place(cv, win, 80, 560)
    return cv

@B('win_over')
def _():
    cv = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    def wall(d, ox, oy):
        d.polygon([(ox, oy + 30), (ox + 560, oy), (ox + 560, oy + 640), (ox, oy + 640)], fill=255)
        d.rectangle([ox + 100, oy + 80, ox + 480, oy + 460], fill=0)
    def wdet(d, im, ox, oy):
        for x, y in [(30, 520), (500, 120), (36, 150), (500, 530)]:
            d.rounded_rectangle([ox + x, oy + y, ox + x + 34, oy + y + 16], 6, fill=(104, 78, 148))
    place(cv, shape(560, 640, wall, WALL, 8, seed=21, detail=wdet), -20, 480)
    def curt(d, ox, oy, flip=False):
        pts = [(0, 0), (60, 0), (52, 60), (24, 170), (34, 300), (0, 300)]
        if flip: pts = [(60 - x, y) for x, y in pts]
        d.polygon([(ox + x, oy + y) for x, y in pts], fill=255)
    place(cv, shape(60, 300, curt, CURT, 5, seed=22), 80, 560)
    place(cv, shape(60, 300, lambda d, ox, oy: curt(d, ox, oy, True), CURT, 5, seed=23), 400, 560)
    place(cv, shape(430, 38, lambda d, ox, oy: d.rectangle([ox, oy, ox + 430, oy + 38], fill=255), SILL, 5, seed=24), 55, 928)
    def pot(d, ox, oy):
        d.polygon([(ox, oy + 50), (ox + 60, oy + 50), (ox + 50, oy + 100), (ox + 10, oy + 100)], fill=255)
    def potd(d, im, ox, oy):
        d.line([(ox + 30, oy + 50), (ox + 30, oy + 8)], fill=(80, 140, 70), width=6)
        d.ellipse([ox + 14, oy - 14, ox + 46, oy + 18], fill=(236, 84, 80))
        d.ellipse([ox + 25, oy - 3, ox + 35, oy + 7], fill=(250, 210, 90))
    place(cv, shape(60, 100, pot, (214, 120, 84), 4, seed=25, detail=potd), 404, 830)
    return cv

@B('plane')
def _():
    pts = [(0, 34), (150, 0), (54, 46), (64, 82)]
    def dr(d, ox, oy): d.polygon([(ox + x, oy + y) for x, y in pts], fill=255)
    def det(d, im, ox, oy): d.line([(ox + 150, oy + 0), (ox + 54, oy + 46)], fill=(170, 170, 180), width=3)
    return shape(150, 82, dr, (246, 246, 250), 3, seed=31, detail=det)

def make_note(w, h, start=120, step=70, seed=0, margin=86, title=None):
    def dr(d, ox, oy): d.rectangle([ox, oy, ox + w, oy + h], fill=255)
    def det(d, im, ox, oy):
        y = start
        while y < h - 20:
            d.line([(ox + 10, oy + y), (ox + w - 10, oy + y)], fill=(166, 188, 228), width=3); y += step
        if margin: d.line([(ox + margin, oy + 8), (ox + margin, oy + h - 8)], fill=(236, 150, 150), width=3)
        for x in range(44, w - 20, 46):
            d.ellipse([ox + x - 7, oy + 18, ox + x + 7, oy + 32], fill=(110, 96, 92))
            d.rounded_rectangle([ox + x - 4, oy - 22, ox + x + 4, oy + 26], 4, fill=(78, 78, 88))
    return shape(w, h, dr, (252, 250, 244), 6, seed=seed, detail=det)

BUILD['note_big'] = lambda: make_note(760, 560, 120, 70, 41)
BUILD['note_xl'] = lambda: make_note(880, 720, 150, 110, 42, margin=0)
BUILD['note_wide'] = lambda: make_note(900, 520, 120, 80, 43)
BUILD['note_mid'] = lambda: make_note(620, 380, 110, 70, 44)

@B('bg_tan')
def _():
    cv = solid(TAN, 51)
    place(cv, shape(860, 860, lambda d, ox, oy: d.ellipse([ox, oy, ox + 860, oy + 860], fill=255), TAN2, 0, False, 52), -60, -160)
    return cv

@B('pencil')
def _():
    L, Wd, a = 260, 34, math.radians(50)
    u = (math.cos(a), -math.sin(a)); v = (math.sin(a), math.cos(a))
    bw = int(L * math.cos(a) + 40); bh = int(L * math.sin(a) + 40)
    def P(ox, oy, k, side=0):
        tx, ty = ox + 10, oy + bh - 10
        return (tx + u[0] * k + v[0] * side, ty + u[1] * k + v[1] * side)
    hw = Wd / 2
    def dr(d, ox, oy):
        d.polygon([P(ox, oy, 0), P(ox, oy, 50, hw), P(ox, oy, L, hw), P(ox, oy, L, -hw), P(ox, oy, 50, -hw)], fill=255)
    def det(d, im, ox, oy):
        d.polygon([P(ox, oy, 0), P(ox, oy, 50, hw), P(ox, oy, 50, -hw)], fill=(242, 214, 168))
        d.polygon([P(ox, oy, 0), P(ox, oy, 16, 5.5), P(ox, oy, 16, -5.5)], fill=(60, 60, 64))
        d.polygon([P(ox, oy, 205, hw), P(ox, oy, 222, hw), P(ox, oy, 222, -hw), P(ox, oy, 205, -hw)], fill=(180, 180, 186))
        d.polygon([P(ox, oy, 222, hw), P(ox, oy, L, hw), P(ox, oy, L, -hw), P(ox, oy, 222, -hw)], fill=(240, 146, 160))
    im = shape(bw, bh, dr, (247, 200, 70), 3, seed=61, detail=det)
    im.info['tip'] = (im.info['pad'] + 10, im.info['pad'] + bh - 10)
    return im

def put_pencil(cv, x, y, wob=0.0):
    im = sp('pencil'); tx, ty = im.info['tip']
    put(cv, im, x - tx + wob, y - ty, 0, 0)

@B('bg_hof')
def _():
    cv = solid(WARM, 71)
    place(cv, shape(S + 40, 320, lambda d, ox, oy: d.rectangle([ox, oy + 20, ox + S + 40, oy + 320], fill=255), FLOOR, 6, seed=72), -20, 760)
    d = ImageDraw.Draw(cv)
    pts = [(x, 70 + 50 * math.sin(math.pi * x / S)) for x in range(-20, S + 21, 20)]
    d.line(pts, fill=(96, 62, 50), width=4)
    # 벽의 메뉴판
    menu = shape(220, 130, lambda d2, ox, oy: d2.rectangle([ox, oy, ox + 220, oy + 130], fill=255), (70, 60, 56), 5, seed=73,
                 detail=lambda d2, im, ox, oy: [d2.text((ox + 110, oy + 42), '오늘의 호프', font=H(38), fill=CREAMINK, anchor='mm'),
                                                d2.text((ox + 110, oy + 92), '치킨, 맥주', font=H(32), fill=(250, 210, 120), anchor='mm')])
    place(cv, menu, 780, 170)
    return cv
BULBS = [(x, 70 + 50 * math.sin(math.pi * x / S) + 16) for x in range(40, S, 90)]

PCOL = [(70, 90, 160), (120, 80, 150), (60, 140, 140), (200, 90, 90), (90, 70, 120)]
for _i, _c in enumerate(PCOL):
    def _mk(c=_c, i=_i):
        def dr(d, ox, oy):
            d.ellipse([ox + 25, oy, ox + 105, oy + 80], fill=255)
            d.rounded_rectangle([ox, oy + 90, ox + 130, oy + 260], 60, fill=255)
        def det(d, im, ox, oy):
            d.ellipse([ox + 30, oy + 5, ox + 100, oy + 75], fill=(250, 222, 196))
            d.ellipse([ox + 50, oy + 34, ox + 57, oy + 42], fill=INK); d.ellipse([ox + 73, oy + 34, ox + 80, oy + 42], fill=INK)
            d.arc([ox + 52, oy + 40, ox + 78, oy + 60], 20, 160, fill=INK, width=3)
            d.chord([ox + 26, oy - 4, ox + 104, oy + 50], 180, 360, fill=[(60, 44, 40), (120, 70, 50), (40, 40, 44), (90, 60, 40), (150, 100, 60)][i])
        return shape(130, 260, dr, c, 5, seed=80 + i, detail=det)
    BUILD['p%d' % _i] = _mk

@B('table')
def _():
    def dr(d, ox, oy):
        d.rounded_rectangle([ox, oy, ox + 380, oy + 46], 20, fill=255); d.rectangle([ox + 170, oy + 40, ox + 210, oy + 160], fill=255)
    return shape(380, 160, dr, WOOD, 5, seed=90)

@B('mug')
def _():
    def dr(d, ox, oy):
        d.rounded_rectangle([ox, oy + 14, ox + 50, oy + 80], 8, fill=255); d.arc([ox + 34, oy + 28, ox + 70, oy + 66], 270, 90, fill=255, width=10)
        d.ellipse([ox - 4, oy, ox + 54, oy + 28], fill=255)
    def det(d, im, ox, oy):
        d.ellipse([ox - 4, oy, ox + 54, oy + 28], fill=(255, 252, 240))
    return shape(70, 80, dr, (246, 190, 60), 3, seed=91, detail=det)

def bubble(s, size, color, tail='l', txt=INK, seed=0):
    fnt = H(size); w = int(fnt.getlength(s)) + 60; h = size + 34
    def dr(d, ox, oy):
        d.rounded_rectangle([ox, oy, ox + w, oy + h], h // 2, fill=255)
        if tail == 'l': d.polygon([(ox + 28, oy + h - 6), (ox + 12, oy + h + 22), (ox + 64, oy + h - 6)], fill=255)
        elif tail == 'r': d.polygon([(ox + w - 28, oy + h - 6), (ox + w - 12, oy + h + 22), (ox + w - 64, oy + h - 6)], fill=255)
    def det(d, im, ox, oy): d.text((ox + w / 2, oy + h / 2 + 2), s, font=fnt, fill=txt, anchor='mm')
    return shape(w, h + 24, dr, color, 5, seed=seed, detail=det)

BUILD['bub_haha'] = lambda: bubble('하하하!', 44, PAPER, 'l', seed=101)
BUILD['bub_cheers'] = lambda: bubble('짠~!', 44, PAPER, 'r', seed=102)
BUILD['bub_note'] = lambda: bubble('랄라~', 40, PAPER, 'l', seed=103)
BUILD['b1'] = lambda: bubble('안녕하세요! 저도 산책 좋아해요', 50, (236, 234, 230), 'l', seed=111)
BUILD['b2'] = lambda: bubble('오! 어디로 자주 가요?', 50, (176, 226, 200), 'r', seed=112)
BUILD['b3'] = lambda: bubble('동네 공원이요 :)', 50, (236, 234, 230), 'l', seed=113)

@B('sweat')
def _():
    def dr(d, ox, oy): d.ellipse([ox, oy + 24, ox + 36, oy + 60], fill=255); d.polygon([(ox + 18, oy), (ox + 2, oy + 36), (ox + 34, oy + 36)], fill=255)
    return shape(36, 60, dr, (150, 202, 240), 3, seed=121)

@B('heart')
def _():
    return shape(160, 150, lambda d, ox, oy: d.polygon(heart_pts(ox + 80, oy + 78, 76), fill=255), HEARTC, 6, seed=122)

@B('cloud')
def _():
    def dr(d, ox, oy):
        for cx, cy, r in [(130, 200, 120), (260, 140, 140), (420, 140, 130), (520, 210, 100), (380, 250, 120), (220, 260, 110)]:
            d.ellipse([ox + cx - r, oy + cy - r, ox + cx + r, oy + cy + r], fill=255)
    return shape(640, 380, dr, PAPER, 6, seed=131)

@B('friend')
def _():
    def dr(d, ox, oy): d.ellipse([ox, oy, ox + 110, oy + 110], fill=255)
    def det(d, im, ox, oy):
        d.ellipse([ox + 33, oy + 44, ox + 43, oy + 54], fill=INK); d.ellipse([ox + 67, oy + 44, ox + 77, oy + 54], fill=INK)
        d.arc([ox + 38, oy + 52, ox + 72, oy + 80], 20, 160, fill=INK, width=4)
        d.chord([ox - 2, oy - 6, ox + 112, oy + 60], 180, 360, fill=(80, 60, 50))
    return shape(110, 110, dr, (250, 222, 196), 5, seed=132, detail=det)

@B('phone')
def _():
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + 400, oy + 740], 56, fill=255)
    def det(d, im, ox, oy):
        d.rounded_rectangle([ox + 22, oy + 60, ox + 378, oy + 690], 26, fill=(250, 250, 246))
        d.rounded_rectangle([ox + 150, oy + 24, ox + 250, oy + 38], 7, fill=(30, 32, 40))
    return shape(400, 740, dr, (52, 56, 72), 6, seed=141, detail=det)

@B('hand')
def _():
    def dr(d, ox, oy):
        d.rounded_rectangle([ox + 22, oy, ox + 54, oy + 90], 16, fill=255)
        d.rounded_rectangle([ox, oy + 60, ox + 100, oy + 160], 34, fill=255)
    return shape(100, 160, dr, (168, 206, 124), 4, seed=142)

@B('step_tag')
def _(): return None

def make_step(n):
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + 210, oy + 74], 37, fill=255)
    def det(d, im, ox, oy): d.text((ox + 105, oy + 39), 'STEP %d' % n, font=J(44), fill=(255, 255, 255), anchor='mm')
    return shape(210, 74, dr, CORAL, 5, seed=150 + n, detail=det)
for _n in range(1, 7): BUILD['step%d' % _n] = (lambda n=_n: make_step(n))

@B('dino_head')
def _():
    im = dino_raw('g', False).crop((0, 0, 470, 450))
    return im.resize((176, 168), Image.LANCZOS)

@B('idcard')
def _():
    w, h = 580, 360
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + w, oy + h], 26, fill=255)
    def det(d, im, ox, oy):
        d.rounded_rectangle([ox, oy, ox + w, oy + 78], 26, fill=(92, 168, 140)); d.rectangle([ox, oy + 50, ox + w, oy + 78], fill=(92, 168, 140))
        d.text((ox + w / 2, oy + 40), '초식대학교  학생증', font=J(40), fill=(255, 255, 255), anchor='mm')
        d.rounded_rectangle([ox + 34, oy + 104, ox + 214, oy + 330], 12, fill=(236, 242, 232))
        im.alpha_composite(sp('dino_head'), (ox + 36, oy + 150))
        for i, s in enumerate(['이름  초식이', '학과  연애학과', '학번  2026-0001']):
            d.text((ox + 246, oy + 140 + 62 * i), s, font=H(40), fill=INK, anchor='lm')
    return shape(w, h, dr, (255, 255, 252), 6, seed=161, detail=det)

@B('stamp')
def _():
    im = Image.new('RGBA', (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 210, 210], outline=RED + (235,), width=12)
    d.ellipse([30, 30, 190, 190], outline=RED + (235,), width=4)
    d.text((110, 112), '인증', font=J(70), fill=RED + (235,), anchor='mm')
    m = Image.fromarray((np.random.default_rng(3).random((220, 220)) > 0.18).astype(np.uint8) * 255)
    a = Image.fromarray(np.minimum(np.asarray(im.getchannel('A')), np.asarray(m)))
    im.putalpha(a)
    return im

@B('note_ideal')
def _():
    n = make_note(600, 520, 150, 100, 171, margin=0)
    return n

@B('polaroid')
def _():
    def dr(d, ox, oy): d.rectangle([ox, oy, ox + 220, oy + 250], fill=255)
    def det(d, im, ox, oy):
        d.rectangle([ox + 18, oy + 18, ox + 202, oy + 186], fill=(200, 228, 240))
        d.ellipse([ox + 140, oy + 34, ox + 180, oy + 74], fill=(250, 200, 90))
        d.polygon([(ox + 18, oy + 186), (ox + 80, oy + 100), (ox + 140, oy + 186)], fill=(110, 170, 110))
        d.polygon([(ox + 100, oy + 186), (ox + 150, oy + 130), (ox + 202, oy + 186)], fill=(150, 200, 140))
        d.text((ox + 110, oy + 218), '참고 이미지', font=H(34), fill=INK, anchor='mm')
    return shape(220, 250, dr, (255, 255, 252), 5, seed=172, detail=det)

@B('bg_v3')
def _():
    cv = solid(NAVY, 181); d = ImageDraw.Draw(cv); rng = np.random.default_rng(5)
    for i in range(90):
        x, y = int(rng.integers(0, S)), int(rng.integers(0, S)); r = int(rng.integers(1, 3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(214, 216, 236))
    for (bw, bh) in [(760, 250), (900, 330)]:
        box = [540 - bw / 2, 410 - bh / 2, 540 + bw / 2, 410 + bh / 2]
        for a in range(0, 360, 10): d.arc(box, a, a + 5, fill=(96, 110, 176), width=4)
    return cv

@B('orb')
def _():
    def dr(d, ox, oy): d.ellipse([ox, oy, ox + 260, oy + 260], fill=255)
    def det(d, im, ox, oy):
        d.ellipse([ox + 30, oy + 26, ox + 110, oy + 70], fill=(250, 160, 136))
        d.text((ox + 130, oy + 136), 'AI', font=J(124), fill=(255, 255, 255), anchor='mm')
    return shape(260, 260, dr, CORAL, 7, seed=182, detail=det)

@B('acc_card')
def _():
    w, h = 320, 420
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + w, oy + h], 30, fill=255)
    def det(d, im, ox, oy):
        d.ellipse([ox + 100, oy + 34, ox + 220, oy + 154], fill=(214, 214, 208))
        d.text((ox + 160, oy + 98), '?', font=J(84), fill=(255, 255, 255), anchor='mm')
        d.text((ox + 160, oy + 204), '새로운 소개가', font=H(48), fill=INK, anchor='mm')
        d.text((ox + 160, oy + 256), '도착했어요', font=H(48), fill=INK, anchor='mm')
        d.text((ox + 160, oy + 310), '수락할까요?', font=H(42), fill=GRAY_D, anchor='mm')
    return shape(w, h, dr, (255, 255, 252), 6, seed=191, detail=det)

@B('chat')
def _():
    w, h = 760, 500
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + w, oy + h], 34, fill=255)
    def det(d, im, ox, oy):
        d.rounded_rectangle([ox, oy, ox + w, oy + 100], 34, fill=(226, 216, 242)); d.rectangle([ox, oy + 70, ox + w, oy + 100], fill=(226, 216, 242))
        d.ellipse([ox + 28, oy + 16, ox + 96, oy + 84], fill=(204, 204, 198))
        d.text((ox + 62, oy + 52), '?', font=J(48), fill=(255, 255, 255), anchor='mm')
        d.text((ox + 116, oy + 52), '상대의 사진은 비공개', font=H(48), fill=(96, 84, 120), anchor='lm')
    return shape(w, h, dr, (255, 255, 252), 6, seed=192, detail=det)

@B('daybox')
def _():
    return shape(76, 76, lambda d, ox, oy: d.rounded_rectangle([ox, oy, ox + 76, oy + 76], 14, fill=255), (255, 255, 252), 4, seed=193)

@B('map')
def _():
    w, h = 880, 470
    def dr(d, ox, oy):
        pts = [(0, 10), (300, 0), (600, 14), (880, 0), (872, 240), (880, 470), (500, 458), (200, 470), (0, 460), (10, 230)]
        d.polygon([(ox + x, oy + y) for x, y in pts], fill=255)
    def det(d, im, ox, oy):
        P = lambda pts: [(ox + x, oy + y) for x, y in pts]
        d.line(P([(10, 90), (200, 70), (420, 110), (640, 60), (870, 90)]), fill=(150, 200, 232), width=46, joint='curve')
        for pts in [[(60, 460), (140, 120)], [(0, 300), (880, 260)], [(420, 120), (470, 470)], [(640, 70), (700, 470)], [(140, 200), (880, 400)]]:
            d.line(P(pts), fill=(255, 255, 255), width=16)
        rng = np.random.default_rng(4)
        for i in range(14):
            x, y = int(rng.integers(40, 840)), int(rng.integers(150, 440)); r = int(rng.integers(12, 20))
            d.ellipse([ox + x - r, oy + y - r, ox + x + r, oy + y + r], fill=(150, 196, 120))
    return shape(w, h, dr, (230, 238, 208), 7, seed=201, detail=det)

@B('pin')
def _():
    def dr(d, ox, oy):
        d.ellipse([ox, oy, ox + 80, oy + 80], fill=255); d.polygon([(ox + 8, oy + 56), (ox + 40, oy + 112), (ox + 72, oy + 56)], fill=255)
    def det(d, im, ox, oy): d.ellipse([ox + 24, oy + 24, ox + 56, oy + 56], fill=(255, 255, 255))
    return shape(80, 112, dr, CORAL, 5, seed=202, detail=det)

def tag(s, size=40, col=(255, 255, 252), seed=0):
    w = int(H(size).getlength(s)) + 44; h = size + 24
    return shape(w, h, lambda d, ox, oy: d.rounded_rectangle([ox, oy, ox + w, oy + h], 14, fill=255), col, 4, seed=seed,
                 detail=lambda d, im, ox, oy: d.text((ox + w / 2, oy + h / 2 + 2), s, font=H(size), fill=INK, anchor='mm'))
BUILD['tag_seocho'] = lambda: tag('우리 동네', 52, seed=211)
BUILD['tag_gangnam'] = lambda: tag('가까운 카페', 52, seed=212)
BUILD['tag_region'] = lambda: tag('내향인 대학생을 위한 서비스예요', 56, (255, 248, 220), seed=213)

@B('bg_textpaper')
def _():
    cv = solid(CREAMT, 221); d = ImageDraw.Draw(cv); rng = np.random.default_rng(8)
    for y in range(30, S, 34):
        x = int(rng.integers(-40, 20))
        while x < S:
            ln = int(rng.integers(20, 90))
            d.line([(x, y), (x + ln, y + int(rng.integers(-2, 3)))], fill=(222, 212, 196), width=3)
            x += ln + int(rng.integers(10, 26))
    return cv

@B('big_heart')
def _():
    return shape(780, 700, lambda d, ox, oy: d.polygon(heart_pts(ox + 390, oy + 360, 380), fill=255), (240, 140, 168), 9, seed=231,
                 detail=lambda d, im, ox, oy: d.line(heart_pts(ox + 390, oy + 360, 350) + [heart_pts(ox + 390, oy + 360, 350)[0]],
                                                     fill=(226, 92, 122), width=5))

@B('mini_cal')
def _():
    def dr(d, ox, oy): d.rounded_rectangle([ox, oy, ox + 150, oy + 150], 18, fill=255)
    def det(d, im, ox, oy):
        d.rounded_rectangle([ox, oy, ox + 150, oy + 44], 18, fill=CORAL); d.rectangle([ox, oy + 26, ox + 150, oy + 44], fill=CORAL)
        d.text((ox + 75, oy + 100), '7일', font=J(56), fill=INK, anchor='mm')
    return shape(150, 150, dr, (255, 255, 252), 5, seed=232, detail=det)

@B('bg_cream')
def _():
    cv = solid(CREAMT, 241); d = ImageDraw.Draw(cv); rng = np.random.default_rng(12)
    cols = [CORAL, MINT, YEL, PINK, LAV]
    for i in range(40):
        x, y = int(rng.integers(0, S)), int(rng.integers(0, S)); r = int(rng.integers(5, 11))
        if 200 < x < 880 and 150 < y < 1000: continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=cols[i % 5])
    return cv

for _nm, _c, _sd in [('bg_yel', YEL, 301), ('bg_pink', PINK, 302), ('bg_mint', MINT, 303), ('bg_lav', LAV, 304),
                     ('bg_peach', PEACH, 305)]:
    BUILD[_nm] = (lambda c=_c, s=_sd: solid(c, s))


# ================================================================ scenes
def zoom(cv, s, cx, cy):
    if s <= 1.0005: return cv
    w = S / s; x0 = min(max(cx - w / 2, 0), S - w); y0 = min(max(cy - w / 2, 0), S - w)
    return cv.resize((S, S), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + w))

def bez(p0, p1, p2, p3, u):
    a = (1 - u) ** 3; b = 3 * u * (1 - u) ** 2; c = 3 * u * u * (1 - u); d = u ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])

def fly_plane(cv, pts, u, trail=0.4):
    if u <= 0: return
    u = min(u, 1)
    d = ImageDraw.Draw(cv)
    n = 18
    for i in range(n):
        uu = u - trail * i / n
        if uu < 0: break
        if i % 2 == 0:
            x, y = bez(*pts, uu); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(236, 236, 246))
    x, y = bez(*pts, u); x2, y2 = bez(*pts, min(1, u + 0.01))
    if u >= 0.999: x2, y2 = x + (x - bez(*pts, 0.99)[0]), y + (y - bez(*pts, 0.99)[1])
    ang = math.degrees(math.atan2(-(y2 - y), x2 - x)) - 13
    putc(cv, 'plane', x, y, 1.0, ang)

def sc_window(lt, mode):
    cv = sp('bg_win').copy()
    twinkle(cv, lt)
    dino(cv, 250, 952, 350, lt, 'g', bob=1.0, seed=0.3, mood='w' if mode == 0 else 'h')
    cv.alpha_composite(sp('win_over'))
    if mode == 0:
        text(cv, '하아...', 380, 640, 46, INK, alpha=eo(fi(lt, 1.8, 0.4)) * (1 - fi(lt, 4.2, 0.5)))
        text(cv, '연애는 하고 싶은데...', 610, 300, 86, CREAMINK, p=fi(lt, 0.5, 1.2))
        text(cv, '어떻게 시작하지?', 640, 400, 60, (200, 206, 240), p=fi(lt, 2.4, 0.9))
        return zoom(cv, 1 + 0.05 * eio(lt / 5.0), 430, 600)
    else:
        P = [(300, 720), (520, 520), (760, 420), (1160, 140)]
        fly_plane(cv, P, eio(fi(lt, 0.2, 2.2)), 0.5)
        text(cv, '이제, 서로를 알아갈 시간', 620, 330, 70, CREAMINK, p=fi(lt, 1.0, 1.2))
        return cv

def sc1(lt): return sc_window(lt, 0)
def sc15a(lt): return sc_window(lt, 1)

def note_scene(lt, note, lines, cx, cy, pencil=True, extra=None, peek=None):
    """lines: (text, size, x_local, baseline_local, t0, dur, col)"""
    cv = sp('bg_tan').copy()
    burst(cv, 540, 540, 470, 520, 28, lt, (186, 136, 86), 6)
    if peek: peek(cv, lt)
    n = sp(note); pad = n.info['pad']
    q = pop(lt, 0, 0.5)
    comp = n.copy()
    head = None
    for (s, size, xl, bl, t0, du, col) in lines:
        p = fi(lt, t0, du)
        textb(comp, s, pad + xl, pad + bl, size, col, p=p)
        if 0 < p < 1: head = (pad + xl + tw(s[:nchars(s, p)], size), pad + bl - 22)
    if extra: extra(comp, lt, pad)
    if q < 0.999:
        comp = comp.resize((max(1, int(comp.width * q)), max(1, int(comp.height * q))), Image.BICUBIC)
    put(cv, comp, cx, cy)
    if pencil and head and q >= 0.999:
        put_pencil(cv, cx - n.width / 2 + head[0], cy - n.height / 2 + head[1], 4 * math.sin(lt * 30))
    return cv

def sc2(lt):
    s1, s2 = '먼저 다가가는 건', '너무 어려워...'
    z = fit(s1, 600, 96)
    return note_scene(lt, 'note_big', [(s1, z, 110, 260, 0.5, 1.3, BLUE), (s2, z, 110, 400, 2.0, 1.0, BLUE)], 540, 560,
                      peek=lambda cv, t: dino(cv, 140, 1130, 330, t, 'g', flip=True, seed=1.1, mood='w'))

def sc3(lt):
    cv = sp('bg_hof').copy(); d = ImageDraw.Draw(cv)
    for i, (x, y) in enumerate(BULBS):
        on = (int(lt * 4) + i) % 2 == 0
        d.ellipse([x - 14, y - 10, x + 14, y + 24], fill=(255, 232, 140) if on else (230, 176, 96))
    xs = [150, 300, 470, 640, 800]
    for i, x in enumerate(xs):
        yb = 790 - abs(math.sin(lt * 5 + i * 1.3)) * 16
        putc(cv, 'p%d' % i, x, yb, 0.95, 4 * math.sin(lt * 4 + i), ay=1.0)
    place(cv, sp('table'), 90, 770); place(cv, sp('table'), 560, 770)
    for x in (150, 260, 380, 640, 760):
        put(cv, sp('mug'), x, 760, 0.5, 0.5)
    for nm, x, y, t0 in [('bub_haha', 230, 420, 0.5), ('bub_cheers', 680, 400, 1.1), ('bub_note', 470, 360, 1.7)]:
        putc(cv, nm, x, y, pop(lt, t0, 0.4))
    jit = 3 * math.sin(lt * 37)
    dino(cv, 930 + jit, 880, 280, lt, 'g', bob=0.3, seed=2.0, mood='w')
    putc(cv, 'sweat', 940 + jit, 650 + 6 * math.sin(lt * 6), pop(lt, 1.0, 0.4) * 0.9)
    label(cv, lt, [('일일호프, 헌팅포차...', 54), ('먼저 다가가는 건 너무 떨려', fit('먼저 다가가는 건 너무 떨려', 980, 68))], 0.6)
    return cv

def sc4(lt):
    cv = sp('bg_lav').copy()
    burst(cv, 690, 330, 330, 380, 22, lt, (140, 116, 186), 6)
    dino(cv, 300, 900, 450, lt, 'g', flip=True, seed=0.7, mood='w', rot=-4 * math.sin(lt * 1.5))
    for i, (x, y, r) in enumerate([(470, 520, 14), (520, 478, 22)]):
        s = pop(lt, 0.2 + 0.1 * i, 0.3)
        if s > 0.05:
            ImageDraw.Draw(cv).ellipse([x - r * s, y - r * s, x + r * s, y + r * s], fill=PAPER)
    putc(cv, 'cloud', 700, 320, pop(lt, 0.4, 0.5))
    d = ImageDraw.Draw(cv)
    putc(cv, 'friend', 560, 320, pop(lt, 0.9, 0.4), 10 * math.sin(lt * 9) * fi(lt, 1.8, 0.2))
    for i, x in enumerate([710, 860]):
        s = pop(lt, 1.2 + 0.2 * i, 0.4)
        if s > 0.05:
            r = 55 * s
            for a in range(0, 360, 30): d.arc([x - r, 320 - r, x + r, 320 + r], a, a + 16, fill=GRAY_D, width=5)
            text(cv, '?', x, 318, int(70 * s) + 1, GRAY_D, f='j')
    label(cv, lt, [('소개해 줄 친구도 별로 없고...', 70)], 1.6)
    return cv

def sc5(lt):
    cv = sp('bg_mint').copy()
    burst(cv, 380, 500, 430, 480, 26, lt, (118, 184, 158), 6)
    px, py = 380, 500
    ph = sp('phone'); put(cv, ph, px, py)
    scr = Image.new('RGBA', (356, 630), (250, 250, 246, 255)); d = ImageDraw.Draw(scr)
    d.text((178, 34), '추천 프로필', font=H(40), fill=INK, anchor='mm')
    off = -160 * eio(fi(lt, 0.3, 1.2))
    for r in range(4):
        for c in range(2):
            x0 = 22 + c * 166; y0 = 80 + r * 210 + off
            hot = (r, c) == (1, 1)
            d.rounded_rectangle([x0, y0, x0 + 148, y0 + 194], 18, fill=(232, 236, 232))
            d.ellipse([x0 + 44, y0 + 18, x0 + 104, y0 + 78], fill=(196, 200, 196))
            d.rounded_rectangle([x0 + 30, y0 + 84, x0 + 118, y0 + 130], 22, fill=(196, 200, 196))
            d.rounded_rectangle([x0 + 22, y0 + 146, x0 + 126, y0 + 180], 17, fill=CORAL if hot else (214, 218, 214))
            if hot: d.text((x0 + 74, y0 + 163), '신청하기', font=H(28), fill=(255, 255, 255), anchor='mm')
            if hot: btn = (x0 + 74, y0 + 163)
    d.rectangle([0, 0, 356, 66], fill=(250, 250, 246)); d.text((178, 34), '추천 프로필', font=H(40), fill=INK, anchor='mm')
    m = Image.new('L', scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, 356, 630], 26, fill=255); scr.putalpha(m)
    sx, sy = px - 178, py - 370 + 60 + 0
    put(cv, scr, sx, sy, 0, 0)
    # 망설이는 손가락
    bx, by = sx + btn[0], sy + btn[1]
    k = 0.5 - 0.5 * math.cos(max(0, lt - 1.6) * 2 * math.pi / 1.4)
    hx, hy = bx + 40 + 120 * (1 - k), by + 20 + 150 * (1 - k)
    if lt > 1.3: putc(cv, 'hand', hx + 30, hy + 60, 0.9, 20)
    dino(cv, 850, 920, 400, lt, 'g', seed=1.9, mood='w')
    putc(cv, 'sweat', 860, 600 + 5 * math.sin(lt * 6), pop(lt, 1.4, 0.4))
    label(cv, lt, [('직접 찾고, 먼저 신청해도 답이 안 오네', fit('직접 찾고, 먼저 신청해도 답이 안 오네', 1000, 68))], 0.8, y=1010)
    return cv

def sc6a(lt):
    cv = sp('bg_sky').copy(); twinkle(cv, lt, 20, 520)
    P = [(-120, 820), (200, 380), (520, 760), (560, 520)]
    u = eio(fi(lt, 0.0, 1.4))
    if u < 1:
        fly_plane(cv, P, u, 0.45)
    else:
        lines = [('먼저 다가가는 건,', 80, 70, 180, 1.6, 0.8, BLUE), ('저희가 할게요!', 92, 70, 320, 2.5, 0.6, RED)]
        n = sp('note_mid'); pad = n.info['pad']; comp = n.copy()
        for (s, size, xl, bl, t0, du, col) in lines:
            textb(comp, s, pad + xl, pad + bl, size, col, p=fi(lt, t0, du))
        q = pop(lt, 1.4, 0.5)
        burst(cv, 560, 540, 360, 420, 24, lt, (120, 132, 196), 6)
        put(cv, comp.resize((max(1, int(comp.width * q)), max(1, int(comp.height * q))), Image.BICUBIC) if q < .999 else comp, 560, 540)
    return cv

def title_scene(lt, final=False):
    cv = sp('bg_cream').copy()
    burst(cv, 540, 430, 330, 390, 30, lt, (232, 176, 150), 7)
    if not final:
        s = pop(lt, 0.1, 0.6)
        if s > 0.02: dino(cv, 540, 740, 560 * s, lt, 'g', bob=0.8, seed=0.2)
        text(cv, '초식남녀', 540, 840, 150, GREEN_D, f='j', alpha=eo(fi(lt, 0.7, 0.4)))
        text(cv, '내향적인 대학생을 위한 1:1 매칭 소개팅 앱', 540, 960, fit('내향적인 대학생을 위한 1:1 매칭 소개팅 앱', 980, 56), INK, p=fi(lt, 1.3, 1.2))
    else:
        s1, s2 = pop(lt, 0.1, 0.6), pop(lt, 0.35, 0.6)
        if s2 > 0.02: dino(cv, 400, 700, 400 * s2, lt, 'p', flip=True, seed=1.0, mood='h' if lt > 1.0 else 'n')
        if s1 > 0.02: dino(cv, 680, 700, 430 * s1, lt, 'g', seed=0.2, mood='h' if lt > 1.0 else 'n')
        putc(cv, 'heart', 540, 230 + 8 * math.sin(lt * 3), pop(lt, 0.8, 0.5) * 0.7)
        text(cv, '초식남녀', 540, 790, 140, GREEN_D, f='j', alpha=eo(fi(lt, 1.0, 0.4)))
        text(cv, '먼저 다가가는 건 저희가, 서로를 알아가는 건 우리가', 540, 890, fit('먼저 다가가는 건 저희가, 서로를 알아가는 건 우리가', 980, 54), RED, p=fi(lt, 1.5, 1.4))
        text(cv, '내향인 대학생을 위한 1:1 소개팅 앱', 540, 970, 46, GRAY_D, alpha=eo(fi(lt, 3.0, 0.5)))
    return cv

def sc6b(lt): return title_scene(lt, False)
def sc16(lt):
    cv = title_scene(lt, True)
    if lt > 4.9:
        cv = Image.blend(cv, Image.new('RGBA', (S, S), (0, 0, 0, 255)), cl((lt - 4.9) / 0.6))
    return cv

# ---------------- vignettes
def vign(lt, bg, n, burst_col, bc=(540, 470), br=(390, 440), title=None, tcol=INK):
    cv = sp(bg).copy()
    burst(cv, bc[0], bc[1], br[0], br[1], 28, lt, burst_col, 7)
    putc(cv, 'step%d' % n, 150, 92, pop(lt, 0.05, 0.4))
    if title: text(cv, title, 272, 94, 56, tcol, f='j', ax=0, alpha=eo(fi(lt, 0.15, 0.4)))
    return cv

def _idphoto(v):
    head = dino_raw(v, False).crop((0, 0, 470, 450)).resize((176, 168), Image.LANCZOS)
    def det(d, im, ox, oy):
        d.rectangle([ox + 12, oy + 12, ox + 188, oy + 180], fill=(236, 242, 232))
        im.alpha_composite(head, (ox + 12, oy + 12))
        d.text((ox + 100, oy + 202), '학생증 사진', font=H(28), fill=INK, anchor='mm')
    return shape(200, 222, lambda d, ox, oy: d.rectangle([ox, oy, ox + 200, oy + 222], fill=255), (255, 255, 252), 5, seed=271, detail=det)
BUILD['idphoto'] = lambda: _idphoto('g')
BUILD['idphoto_p'] = lambda: _idphoto('p')
BUILD['tag_private'] = lambda: tag('학생증 사진은 상대에게 공개되지 않아요', 46, (255, 248, 220), seed=272)

def brackets(d, cx, cy, w, h, col, L=46, wd=9):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=col, width=wd, joint='curve')

def v1(lt):
    cv = vign(lt, 'bg_yel', 1, (222, 170, 60), title='학생증 인증')
    shake = 6 * math.sin(lt * 50) * (1 - fi(lt, 1.6, 0.25)) * (lt > 1.45)
    putc(cv, 'idcard', 355 + shake, 430, pop(lt, 0.2, 0.5) * 0.9, -4)
    ss = fi(lt, 1.3, 0.2)
    if ss > 0: putc(cv, 'stamp', 535, 528, (1.8 - 0.8 * eo(ss)) * 0.85, 12, alpha=ss)
    if lt > 2.9:
        u = eio(fi(lt, 3.0, 1.0))
        x0, y0, x1, y1 = 206, 463, 840, 400
        x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u - 130 * math.sin(math.pi * u)
        putc(cv, 'idphoto', x, y, 0.8 + 0.5 * u, -4 * (1 - u) + 3 * u)
        if u >= 1:
            d = ImageDraw.Draw(cv)
            q = pop(lt, 4.0, 0.35)
            brackets(d, 840, 400, 320 * q, 350 * q, CORAL)
            if lt > 4.2:
                yy = 400 - 150 + 300 * (0.5 - 0.5 * math.cos((lt - 4.2) * 3.2))
                d.line([(700, yy), (980, yy)], fill=CORAL, width=5)
            putc(cv, 'orb', 975, 235, pop(lt, 4.4, 0.4) * 0.36)
    putc(cv, 'tag_private', 540, 760, pop(lt, 5.4, 0.4), 1.5)
    s1, s2 = '학생증으로 대학생 인증', '학생증 사진으로 AI가 매칭해요'
    text(cv, s1, 540, 940, fit(s1, 1000, 80), INK, p=fi(lt, 0.6, 0.7))
    text(cv, s2, 540, 1020, fit(s2, 1000, 80), (204, 70, 46), p=fi(lt, 3.4, 0.9))
    return cv

FLOW = [('학생증 인증', YEL, 'idcard', .2, -6), ('이상형 입력', PINK, 'note_ideal', .17, 4), ('AI 1:1 매칭', NAVY, 'orb', .44, 0),
        ('비공개 수락', MINT, 'heart', .6, 0), ('일주일 대화', LAV, 'mini_cal', .66, -4), ('실제 만남', PEACH, 'pin', .8, 0)]
FPOS = [(210, 330), (540, 330), (870, 330), (870, 640), (540, 640), (210, 640)]
for _i, _f in enumerate(FLOW):
    BUILD['node%d' % _i] = (lambda c=_f[1], i=_i: shape(196, 196, lambda d, ox, oy: d.ellipse([ox, oy, ox + 196, oy + 196], fill=255), c, 7, seed=280 + i))

def sc_flow(lt):
    cv = sp('bg_cream').copy()
    text(cv, '초식남녀는 이렇게 연결해요', 540, 112, 70, GREEN_D, f='j', p=fi(lt, 0.1, 0.8))
    d = ImageDraw.Draw(cv)
    for i in range(5):
        pr = fi(lt, 0.85 + 0.7 * i, 0.45)
        if pr > 0:
            a, b = FPOS[i], FPOS[i + 1]
            dashed_line(d, a, (a[0] + (b[0] - a[0]) * pr, a[1] + (b[1] - a[1]) * pr), (214, 176, 150), 7, 18, 12)
    for i, (lab, col, ic, isc, r) in enumerate(FLOW):
        t0 = 0.5 + 0.7 * i
        s = pop(lt, t0, 0.45)
        if s < 0.02: continue
        x, y = FPOS[i]
        putc(cv, 'node%d' % i, x, y, s)
        putc(cv, ic, x, y, isc * s, r + 3 * math.sin(lt * 3 + i))
        if s > 0.9:
            d = ImageDraw.Draw(cv)
            d.ellipse([x - 98, y - 98, x - 46, y - 46], fill=CORAL)
            d.text((x - 72, y - 70), str(i + 1), font=J(36), fill=(255, 255, 255), anchor='mm')
        text(cv, lab, x, y + 130, 50, INK, p=fi(lt, t0 + 0.2, 0.4))
    text(cv, '가입부터 만남까지, 단 6단계', 540, 905, 70, (204, 70, 46), p=fi(lt, 4.9, 0.8))
    dino(cv, 990, 1075, 190, lt, 'g', mood='h', seed=0.6)
    return cv

def v2(lt):
    cv = vign(lt, 'bg_pink', 2, (222, 138, 166), (600, 470), title='이상형 입력')
    n = sp('note_ideal'); pad = n.info['pad']; comp = n.copy(); d = ImageDraw.Draw(comp)
    textb(comp, '나의 이상형', pad + 40, pad + 120, 64, BLUE, f='h', p=fi(lt, 0.4, 0.6))
    items = ['두부상', '웃는 게 예쁜 사람', '산책 좋아하는 사람']
    for i, s in enumerate(items):
        bl = pad + 230 + 100 * i
        d.rounded_rectangle([pad + 44, bl - 44, pad + 88, bl], 6, outline=BLUE, width=4)
        textb(comp, s, pad + 112, bl, 54, BLUE, p=fi(lt, 1.0 + 0.7 * i, 0.5))
        checkmark(d, pad + 68, bl - 24, 40, fi(lt, 1.4 + 0.7 * i, 0.3), RED, 7)
    q = pop(lt, 0.15, 0.5)
    put(cv, comp if q > .999 else comp.resize((max(1, int(comp.width * q)), max(1, int(comp.height * q)))), 640, 440)
    putc(cv, 'polaroid', 210, 300, pop(lt, 2.6, 0.5), 9)
    dino(cv, 190, 860, 300, lt, 'g', flip=True, seed=0.4)
    label(cv, lt, [('설문, 글, 참고 이미지로 이상형 입력', fit('설문, 글, 참고 이미지로 이상형 입력', 1000, 68))], 0.7)
    return cv

def v3(lt):
    cv = sp('bg_v3').copy(); twinkle(cv, lt, 14, 1000, 21)
    putc(cv, 'step3', 150, 92, pop(lt, 0.05, 0.4))
    text(cv, 'AI 1:1 매칭', 272, 94, 56, CREAMINK, f='j', ax=0, alpha=eo(fi(lt, 0.15, 0.4)))
    d = ImageDraw.Draw(cv)
    for i in range(3):
        a = lt * 1.1 + i * 2.09
        star(d, 540 + 400 * math.cos(a), 410 + 140 * math.sin(a), 16, (250, 220, 120))
    if lt > 1.0:
        for (x0, y0) in [(330, 580), (750, 580)]:
            for k in range(7):
                u = ((lt - 1.0) * 0.6 + k / 7) % 1
                x, y = x0 + (540 - x0) * u, y0 + (430 - y0) * u
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(250, 200, 180))
    s = pop(lt, 0.3, 0.5)
    putc(cv, 'orb', 540, 410 + 8 * math.sin(lt * 2.2), s * (1 + 0.03 * math.sin(lt * 5)))
    for k, nm in enumerate(['idphoto', 'idphoto_p']):
        a = lt * 0.9 + k * math.pi
        putc(cv, nm, 540 + 330 * math.cos(a), 410 + 120 * math.sin(a), 0.48 * pop(lt, 0.9 + 0.25 * k, 0.4), 6 * math.sin(lt * 2 + k))
    dino(cv, 230, 860, 330, lt, 'g', flip=True, seed=0.1)
    dino(cv, 850, 860, 320, lt, 'p', seed=1.6)
    putc(cv, 'heart', 540, 680, pop(lt, 2.4, 0.5) * 0.75)
    label(cv, lt, [('학생증 사진과 이상형을 보고', 66), ('AI가 딱 한 사람을 소개해요', 66)], 0.8, col=CREAMINK)
    return cv

def toggle(d, cx, cy, on):
    track = tuple(int(GRAY[i] + (CORAL[i] - GRAY[i]) * on) for i in range(3))
    d.rounded_rectangle([cx - 70, cy - 32, cx + 70, cy + 32], 32, fill=track)
    kx = cx - 38 + 76 * on
    d.ellipse([kx - 25, cy - 25, kx + 25, cy + 25], fill=(255, 255, 255))

def v4(lt):
    cv = vign(lt, 'bg_mint', 4, (114, 182, 156), title='비공개 수락')
    on1, on2 = eio(fi(lt, 1.1, 0.3)), eio(fi(lt, 1.8, 0.3))
    d = ImageDraw.Draw(cv)
    if lt > 2.2:
        dashed_line(d, (470, 430), (610, 430), CORAL, 8, 18, 10, -lt * 60)
    for (cx, on, t0, sd) in [(300, on1, 0.2, 0), (780, on2, 0.4, 1)]:
        s = pop(lt, t0, 0.5)
        putc(cv, 'acc_card', cx, 430, s, (-3, 3)[sd])
        if s > 0.98: toggle(ImageDraw.Draw(cv), cx, 430 + 150, on)
    putc(cv, 'heart', 540, 430, pop(lt, 2.4, 0.5) * 0.7)
    text(cv, '연결!', 540, 320, 64, RED, f='j', alpha=eo(fi(lt, 2.6, 0.3)))
    dino(cv, 110, 1000, 250, lt, 'g', flip=True, seed=0.5)
    dino(cv, 975, 1000, 240, lt, 'p', seed=2.2)
    label(cv, lt, [('서로 비공개로 수락하고', 64), ('둘 다 OK면 연결!', 64)], 0.8, y=820)
    return cv

def v5(lt):
    cv = vign(lt, 'bg_lav', 5, (140, 116, 186), title='일주일 대화')
    putc(cv, 'chat', 570, 400, pop(lt, 0.1, 0.5))
    for nm, x, y, ax, t0 in [('b1', 222, 300, 0, 0.5), ('b2', 918, 410, 1, 1.1), ('b3', 222, 520, 0, 1.7)]:
        s = pop(lt, t0, 0.4)
        if s > 0.02:
            im = X(nm, s); put(cv, im, x, y, ax, 0.5)
    text(cv, 'DAY', 300, 760, 40, INK, f='j', alpha=eo(fi(lt, 1.9, 0.3)))
    d = ImageDraw.Draw(cv)
    for k in range(7):
        x = 390 + 92 * k
        s = pop(lt, 1.9 + 0.05 * k, 0.4)
        if s < 0.05: continue
        putc(cv, 'daybox', x, 760, s)
        f = fi(lt, 2.3 + 0.32 * k, 0.15)
        if f > 0 and s > .98:
            col = RED if k == 6 else CORAL
            d.rounded_rectangle([x - 32, 728, x + 32, 792], 12, fill=col)
        if s > .98: d.text((x, 762), str(k + 1), font=J(40), fill=(255, 255, 255) if f > 0 else INK, anchor='mm')
    dino(cv, 140, 905, 280, lt, 'g', flip=True, seed=0.9, mood='h' if lt > 1.2 else 'n')
    label(cv, lt, [('사진 없이, 일주일 동안', 66), ('한 사람과만 대화해요', 66)], 0.9)
    return cv

def v6(lt):
    cv = vign(lt, 'bg_peach', 6, (226, 150, 112), title='실제 만남')
    putc(cv, 'map', 540, 400, pop(lt, 0.1, 0.5), -1.5)
    for nm, tg, x, y, t0 in [('pin', 'tag_seocho', 330, 420, 0.5), ('pin', 'tag_gangnam', 760, 330, 0.8)]:
        u = fi(lt, t0, 0.45)
        if u > 0:
            yy = y - 260 * (1 - bo(u))
            putc(cv, nm, x, yy, 1.0, ay=1.0)
            putc(cv, tg, x, y + 40, pop(lt, t0 + 0.35, 0.3))
    e = eio(fi(lt, 0.6, 1.7))
    hop = abs(math.sin(lt * 7)) * 28 * (1 - fi(lt, 2.3, 0.1))
    dino(cv, 170 + 260 * e, 900 - hop, 290, lt, 'g', flip=True, seed=0.2, mood='h' if lt > 2.3 else 'n')
    dino(cv, 910 - 260 * e, 900 - hop, 280, lt, 'p', seed=1.4, mood='h' if lt > 2.3 else 'n')
    hs = pop(lt, 2.4, 0.5)
    putc(cv, 'heart', 540, 590, hs * 0.8)
    if lt > 2.5:
        for i in range(5):
            u = ((lt - 2.5) * 0.55 + i * 0.2) % 1
            putc(cv, 'heart', 540 + 160 * math.sin(i * 2.3 + u * 3), 580 - 260 * u, 0.22 * (1 - u) + 0.05, alpha=1 - u)
    label(cv, lt, [('마음이 맞으면', 66), ('가까운 동네에서 만나요', 66)], 0.9)
    return cv

def sc13(lt):
    cv = sp('bg_textpaper').copy()
    s = pop(lt, 0.1, 0.6)
    putc(cv, 'big_heart', 540, 470, s * (1 + 0.015 * math.sin(lt * 4)))
    icons = [('idcard', .40, 210, 210, -10), ('orb', .52, 890, 190, 8), ('pin', 1.1, 960, 520, 10),
             ('mini_cal', 1.05, 125, 540, -8), ('b2', .8, 250, 860, 4), ('polaroid', .62, 860, 830, 9)]
    for i, (nm, sc, x, y, r) in enumerate(icons):
        q = pop(lt, 0.7 + 0.22 * i, 0.4)
        if q > 0.02: putc(cv, nm, x, y, sc * q, r + 4 * math.sin(lt * 3 + i))
    if s > 0.6:
        dino(cv, 445, 700, 300 * min(1, s), lt, 'p', flip=True, seed=1.2, mood='h')
        dino(cv, 650, 700, 310 * min(1, s), lt, 'g', seed=0.4, mood='h')
    label(cv, lt, [('한 사람을 천천히 알아가는 시간', 70)], 1.6, y=1000)
    return cv

def sc14(lt):
    items = ['AI가 먼저 한 사람을 소개해요', '사진은 매칭에만, 상대에겐 비공개', '일주일 동안 한 사람에게 집중', '가까운 동네에서 실제 만남까지']
    size = min(fit(s, 700, 58) for s in items)
    lines = [('초식남녀는 이렇게 달라요', 66, 60, 112, 0.3, 0.8, RED)]
    for i, s in enumerate(items):
        lines.append((s, size, 130, 150 + 110 * (i + 1) - 18, 1.2 + 1.05 * i, 0.7, BLUE))
    def extra(comp, t, pad):
        d = ImageDraw.Draw(comp)
        for i in range(4):
            bl = pad + 150 + 110 * (i + 1) - 18
            if t > 1.0 + 1.05 * i:
                d.rounded_rectangle([pad + 50, bl - 50, pad + 100, bl], 8, outline=BLUE, width=4)
            checkmark(d, pad + 78, bl - 26, 44, fi(t, 1.85 + 1.05 * i, 0.3), RED, 8)
    return note_scene(lt, 'note_xl', lines, 540, 520, extra=extra,
                      peek=None) if lt < 0 else _sc14(lt, lines, extra)

def _sc14(lt, lines, extra):
    cv = note_scene(lt, 'note_xl', lines, 520, 520, extra=extra)
    dino(cv, 960, 1120, 320, lt, 'g', seed=2.5)
    return cv

@B('qmark')
def _():
    return shape(110, 110, lambda d, ox, oy: d.ellipse([ox, oy, ox + 110, oy + 110], fill=255), (204, 204, 198), 5, seed=251,
                 detail=lambda d, im, ox, oy: d.text((ox + 55, oy + 58), '?', font=J(80), fill=(255, 255, 255), anchor='mm'))

DIFF = [('orb', 0.44, ('AI가 먼저', '한 사람을 소개'), (255, 236, 222)),
        ('qmark', 1.0, ('사진은 매칭에만', '상대에겐 비공개'), (234, 226, 248)),
        ('mini_cal', 0.8, ('일주일 동안', '한 사람에게 집중'), (224, 244, 232)),
        ('pin', 0.95, ('가까운 동네에서', '실제 만남까지'), (255, 244, 204))]
for _i, _d in enumerate(DIFF):
    BUILD['dcard%d' % _i] = (lambda c=_d[3], i=_i: shape(440, 320, lambda d, ox, oy: d.rounded_rectangle([ox, oy, ox + 440, oy + 320], 30, fill=255), c, 7, seed=260 + i))

def sc_diff(lt):
    cv = sp('bg_textpaper').copy()
    burst(cv, 540, 520, 480, 530, 30, lt, (226, 200, 170), 6)
    text(cv, '초식남녀는 이렇게 달라요', 540, 92, 78, RED, p=fi(lt, 0.1, 0.8))
    pos = [(300, 335), (780, 335), (300, 695), (780, 695)]
    for i, ((ic, isc, lines, col), (x, y)) in enumerate(zip(DIFF, pos)):
        t0 = 0.5 + 0.75 * i
        s = pop(lt, t0, 0.45)
        if s < 0.02: continue
        putc(cv, 'dcard%d' % i, x, y, s, (-2, 2, 2, -2)[i])
        if s > 0.9:
            putc(cv, ic, x, y - 72, isc * pop(lt, t0 + 0.15, 0.4) * (1 + 0.04 * math.sin(lt * 4 + i)))
            for j, ln in enumerate(lines):
                text(cv, ln, x, y + 46 + 58 * j, fit(ln, 400, 54), INK, p=fi(lt, t0 + 0.3 + 0.3 * j, 0.4))
    dino(cv, 540, 1078, 230, lt, 'g', mood='h', seed=1.0)
    return cv

def sc15b(lt):
    l1, l2 = '먼저 다가가는 건 저희가,', '서로를 알아가는 건 우리가'
    z = fit(l2, 760, 80)
    def extra(comp, t, pad):
        p = eio(fi(t, 2.9, 0.7))
        if p > 0:
            x0 = pad + 90 + tw('서로를 알아가는 건 ', z); x1 = pad + 90 + tw(l2, z)
            bl = pad + 440
            box = [x0 - 20, bl - z * 0.95, x1 + 20, bl + 18]
            ImageDraw.Draw(comp).arc(box, -200, -200 + 370 * p, fill=RED, width=8)
        q = pop(t, 3.6, 0.4)
        if q > 0.02:
            st = X('dgh0', 0.24 * q, 12)
            comp.alpha_composite(st, (int(pad + 900 - st.width + 20), int(pad + 10)))
    return note_scene(lt, 'note_wide', [(l1, z, 90, 280, 0.3, 1.1, BLUE), (l2, z, 90, 440, 1.5, 1.2, BLUE)], 540, 540, extra=extra)


SCENES = [(sc1, 5.0), (sc3, 4.5), (sc4, 3.5), (sc5, 4.0), (sc6a, 3.5), (sc6b, 4.0), (sc_flow, 7.0),
          (v1, 8.0), (v2, 5.5), (v3, 6.0), (v4, 5.0), (v5, 5.5), (v6, 5.0),
          (sc13, 4.0), (sc_diff, 5.5), (sc15a, 3.0), (sc15b, 4.8), (sc16, 5.5)]
TOT = sum(d for _, d in SCENES)


TR = 0.42
def _tear():
    rng = np.random.default_rng(77)
    j = 18 + 6 * ndi.gaussian_filter(rng.standard_normal(S), 5.0) / 0.12 + 2 * rng.standard_normal(S) * 0.5
    j = np.clip(j, 6, 30)[:, None]
    x = np.arange(S + 40)[None, :]
    inner = x > j; rim = (x > j - 9) & ~inner
    a = np.where(inner | rim, 255, 0).astype(np.uint8)
    rimimg = np.zeros((S, S + 40, 4), np.uint8); rimimg[rim] = PAPER + (255,)
    sh = np.zeros((S, 60, 4), np.uint8); sh[..., 3] = (np.linspace(0, 1, 60) ** 2 * 90).astype(np.uint8)[None, :]
    return Image.fromarray(a, 'L'), Image.fromarray(rimimg, 'RGBA'), Image.fromarray(sh, 'RGBA')
TEAR = None

def frame(t):
    global TEAR
    acc = 0.0
    for i, (fn, du) in enumerate(SCENES):
        if t < acc + du or i == len(SCENES) - 1:
            lt = t - acc
            cur = fn(lt)
            if i == 0 or lt >= TR:
                return cur.convert('RGB')
            if TEAR is None: TEAR = _tear()
            am, rim, sh = TEAR
            pf, pdu = SCENES[i - 1]
            base = pf(pdu - 0.01).convert('RGBA')
            off = int(S * (1 - eo(lt / TR)))
            sheet = Image.new('RGBA', (S + 40, S), (0, 0, 0, 0)); sheet.paste(cur, (40, 0)); sheet.paste(cur.crop((0, 0, 40, S)), (0, 0))
            sheet.putalpha(am); sheet.alpha_composite(rim)
            put(base, sh, off - 30, 0, 0, 0)
            put(base, sheet, off - 40, 0, 0, 0)
            return base.convert('RGB')
        acc += du

def render_bytes(n): return frame(n / FPS).tobytes()


# ================================================================ music (잔잔한 피아노, 배음 합성)
def music(path, dur, sr=44100):
    from scipy.signal import fftconvolve, butter, sosfilt
    from scipy.io import wavfile
    rng = np.random.default_rng(7)
    bpm = 70; beat = 60 / bpm; bar = 4 * beat
    N = int((dur + 6) * sr)
    Lc = np.zeros(N, np.float32); Rc = np.zeros(N, np.float32)
    mf = lambda m: 440 * 2 ** ((m - 69) / 12)

    def note(m, t0, hold, vel):
        f0 = mf(m)
        i0 = int(max(0, t0) * sr)
        rel = 0.35
        n = min(int((hold + rel) * sr), N - i0)
        if n <= 0: return
        t = np.arange(n) / sr
        tau = float(np.clip(3.2 * (261.6 / f0) ** 0.6, 0.9, 7.0))
        B = 0.00035 * (f0 / 261.6) ** 0.5
        sig = np.zeros(n)
        bright = 0.42 + 0.25 * vel
        for k in range(1, 13):
            fk = k * f0 * math.sqrt(1 + B * k * k)
            if fk > 5500: break
            ak = (1 / k ** 1.5) * math.exp(-(k - 1) * (1 - bright) * 0.9)
            tk = tau / (1 + 0.55 * (k - 1))
            env = 0.65 * np.exp(-t / (tk * 0.22)) + 0.35 * np.exp(-t / tk)
            for det in (-0.9, 0.9):   # 한 음에 두 줄, 미세한 맥놀이
                ph = rng.uniform(0, 2 * np.pi)
                sig += 0.5 * ak * env * np.sin(2 * np.pi * fk * 2 ** (det / 1200) * t + ph)
        att = np.minimum(1, t / 0.003)
        end = np.clip((hold + rel - t) / rel, 0, 1)
        sig *= att * end * vel
        hn = min(n, int(0.012 * sr))     # 해머가 닿는 소리
        sig[:hn] += rng.standard_normal(hn) * np.exp(-np.arange(hn) / (0.003 * sr)) * 0.015 * vel
        pan = float(np.clip(0.5 + (m - 60) / 60, 0.25, 0.75))
        Lc[i0:i0 + n] += (sig * (1.2 - pan)).astype(np.float32)
        Rc[i0:i0 + n] += (sig * (0.2 + pan)).astype(np.float32)

    CH = {'C': [48, 55, 64], 'G/B': [47, 55, 62], 'Am': [45, 52, 60], 'F': [41, 48, 57],
          'C/E': [52, 55, 60], 'Dm': [50, 57, 65], 'G': [43, 50, 59]}
    MEL = {('A', 0): [(0, 76, 2), (2, 79, 2)], ('A', 1): [(0, 74, 3), (3, 71, 1)],
           ('A', 2): [(0, 72, 2), (2, 76, 2)], ('A', 3): [(0, 72, 1), (1, 74, 1), (2, 69, 2)],
           ('B', 0): [(0, 77, 2), (2, 76, 1), (3, 74, 1)], ('B', 1): [(0, 72, 3), (3, 76, 1)],
           ('B', 2): [(0, 74, 2), (2, 77, 2)], ('B', 3): [(0, 79, 2), (2, 74, 2)]}
    SEC = {'A': ['C', 'G/B', 'Am', 'F'], 'B': ['F', 'C/E', 'Dm', 'G']}
    form = ['A0', 'A', 'B', 'A', 'B', 'A']     # A0 = 왼손만 나오는 도입
    b = 0
    for sec in form:
        key = sec[0]
        for k, ch in enumerate(SEC[key]):
            t0 = b * bar
            if t0 > dur - bar - 1: break
            v = CH[ch]
            pat = [0, 1, 2, 1, 2, 1, 2, 1]
            for e in range(8):
                te = t0 + e * beat / 2 + rng.normal(0, 0.004)
                vel = (0.42 if e == 0 else 0.26 + 0.04 * (e % 2 == 0)) * (0.8 if sec == 'A0' else 1.0)
                note(v[pat[e]], te, bar - e * beat / 2 + 0.15, vel)
            if sec != 'A0':
                mel = MEL[(key, k)]
                for idx, (bt, m, ln) in enumerate(mel):
                    note(m, t0 + bt * beat + 0.01, ln * beat + 0.35, 0.50 if bt == 0 else 0.42)
            b += 1
    # 마지막 C 화음을 천천히 펼쳐 마무리
    tf = b * bar
    for i, m in enumerate([36, 48, 55, 64, 67, 72]):
        note(m, tf + i * 0.07, max(2.0, dur - tf), 0.40 if i < 5 else 0.48)

    st = np.stack([Lc, Rc], 1)
    st = sosfilt(butter(2, 6000, 'low', fs=sr, output='sos'), st, axis=0)
    tt = np.arange(int(2.6 * sr)) / sr
    for c in range(2):
        nz = sosfilt(butter(2, 3500, 'low', fs=sr, output='sos'), rng.standard_normal(len(tt)))
        ir = (nz * np.exp(-tt * 2.4)).astype(np.float32)
        ir = ir / np.sqrt((ir ** 2).sum()) * 0.38
        dry = st[:, c].copy()
        st[:, c] = dry + fftconvolve(dry, ir)[:N]
    y = st[:int(dur * sr)]
    n = len(y)
    fade = np.minimum(1, np.arange(n) / (0.6 * sr)) * np.minimum(1, (n - np.arange(n)) / (2.5 * sr))
    y = y * fade[:, None]
    y = y / (np.abs(y).max() + 1e-6) * 0.5
    wavfile.write(path, sr, (y * 32767).astype(np.int16))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'preview':
        od = sys.argv[2]
        for s in sys.argv[3:]:
            frame(float(s)).save(os.path.join(od, 'f_%05.1f.png' % float(s)))
    elif mode == 'music':
        music(sys.argv[2], TOT)
    else:
        out = sys.argv[2]
        wav = out + '.wav'
        music(wav, TOT)
        N = int(TOT * FPS)
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (S, S),
               '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(2) as pool:
            for i, b in enumerate(pool.imap(render_bytes, range(N), chunksize=8)):
                pr.stdin.write(b)
                if i % 240 == 0: print('frame', i, '/', N, flush=True)
        pr.stdin.close(); pr.wait()
        os.remove(wav)
        print('done', out, TOT)
