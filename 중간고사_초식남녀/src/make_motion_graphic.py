#!/usr/bin/env python3
"""초식남녀 모션 그래픽 영상 생성 스크립트 (Python + Pillow + ffmpeg)

사용법
  python3 make_motion_graphic.py preview 3 12 40      # 해당 초(sec)의 프레임을 PNG로 저장
  python3 make_motion_graphic.py render out.mp4       # 전체 영상 렌더링 (1920x1080, 30fps)
"""
import sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool

W, H, FPS = 1920, 1080, 30
FONT = {
    'r': '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    'b': '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    'k': '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc',
}
_cache = {}


def F(w, s):
    key = (w, int(s))
    if key not in _cache:
        f = None
        for idx in range(6):
            try:
                c = ImageFont.truetype(FONT[w], max(1, int(s)), index=idx)
            except Exception:
                break
            if 'KR' in c.getname()[0]:
                f = c
                break
        _cache[key] = f or ImageFont.truetype(FONT[w], max(1, int(s)))
    return _cache[key]


# ---------- 색상 / 유틸 ----------
CREAM = (255, 248, 238)
GREEN = (47, 93, 80)
CORAL = (255, 138, 91)
CORALD = (226, 98, 56)
MINT = (191, 227, 208)
MINTL = (223, 240, 232)
INK = (34, 48, 43)
GRAY = (176, 184, 180)
LIGHT = (236, 243, 239)
WHITE = (255, 255, 255)
SOFT = (90, 105, 98)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def cl(x):
    return max(0.0, min(1.0, x))


def fi(t, a, d):
    return cl((t - a) / d)


def fo(t, s, d):
    return 1 - cl((t - s) / d)


def eo(x):
    return 1 - (1 - cl(x)) ** 3


def eio(x):
    x = cl(x)
    return 3 * x * x - 2 * x ** 3


def bo(x):
    x = cl(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def T(d, x, y, s, size, w, col, bg, a=1.0, anchor='mm'):
    if a <= 0.02:
        return
    d.text((x, y), s, font=F(w, size), fill=mix(bg, col, a), anchor=anchor)


def rr(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle(box, radius=max(0, r), fill=fill, outline=outline, width=w)


def heart(d, cx, cy, s, fill):
    if s <= 1:
        return
    pts = []
    for i in range(64):
        t = 2 * math.pi * i / 64
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 16, cy + y * s / 16))
    d.polygon(pts, fill=fill)


def person(d, cx, cy, s, col):
    d.ellipse([cx - .42 * s, cy - 1.25 * s, cx + .42 * s, cy - .41 * s], fill=col)
    d.pieslice([cx - .8 * s, cy - .2 * s, cx + .8 * s, cy + 1.4 * s], 180, 360, fill=col)


def check(d, cx, cy, s, col, w=10):
    d.line([(cx - .5 * s, cy), (cx - .15 * s, cy + .4 * s), (cx + .55 * s, cy - .4 * s)],
           fill=col, width=int(w), joint='curve')


def dashed(d, x1, y, x2, col, w=5, dash=18, gap=14):
    x = x1
    while x < x2:
        d.line([(x, y), (min(x + dash, x2), y)], fill=col, width=w)
        x += dash + gap


def wrap(s, font, maxw):
    words = s.split(' ')
    lines, cur = [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if font.getlength(t) > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    return lines


def canvas(bg):
    img = Image.new('RGB', (W, H), bg)
    return img, ImageDraw.Draw(img)


# ---------- Scene 1: 타이틀 ----------
def s1(lt):
    img, d = canvas(CREAM)
    for i in range(14):
        x = (i * 263) % W + 40 * math.sin(lt * .8 + i)
        y = (i * 181) % H + 30 * math.cos(lt * .7 + i * 2)
        r = 30 + (i % 4) * 22
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(CREAM, MINT, .45))
    p = bo(fi(lt, .1, .7))
    heart(d, 960, 290, 70 * p * (1 + .05 * math.sin(lt * 5)), CORAL)
    a = eo(fi(lt, .5, .9))
    T(d, 960, 480 + (1 - a) * 40, '초식남녀', 210, 'k', GREEN, CREAM, a)
    a = eo(fi(lt, 1.7, .8))
    T(d, 960, 650 + (1 - a) * 30, '내향적인 대학생을 위한 AI 1:1 소개팅', 56, 'b', SOFT, CREAM, a)
    a = eo(fi(lt, 3.0, .8))
    T(d, 960, 770 + (1 - a) * 30, '먼저 다가가는 건 AI가, 서로를 알아가는 건 우리가', 50, 'b', CORALD, CREAM, a)
    return img


# ---------- Scene 2: 문제 제시 ----------
def s2(lt):
    img, d = canvas(LIGHT)
    rr(d, (80, 60, 260, 120), 30, fill=GREEN)
    T(d, 170, 90, '문제', 34, 'b', WHITE, GREEN)
    BL = 16 / 3
    b = min(2, int(lt // BL))
    bl = lt - b * BL
    a = fi(bl, 0, .5) * fo(bl, BL - .4, .4)
    ca = lambda col: mix(LIGHT, col, a)
    if b == 0:
        p = bo(fi(bl, 0, .7))
        heart(d, 960, 400, 150 * p * (1 + .06 * math.sin(bl * 5)) * (1 if a > 0 else 0), ca(CORAL))
        T(d, 960, 770, '연애는 하고 싶은데…', 84, 'b', INK, LIGHT, a)
        T(d, 960, 880, '새로운 인연을 만나고 싶은 마음', 44, 'r', SOFT, LIGHT, a)
    elif b == 1:
        off = 60 * max(0, math.sin(bl * 2.0))
        person(d, 640 + off, 470, 110, ca(CORAL))
        person(d, 1280, 470, 110, ca(GRAY))
        dashed(d, 780 + off, 590, 1140, ca(GRAY), 5)
        if bl > 1.0:
            q = bo(fi(bl, 1.0, .4))
            bx = 720 + off
            rr(d, (bx, 330, bx + 180, 400), 35, fill=ca(WHITE), outline=ca(GRAY), w=3)
            for j in range(3):
                rad = 6 + 3 * max(0, math.sin(bl * 6 - j))
                d.ellipse([bx + 45 + 45 * j - rad, 365 - rad, bx + 45 + 45 * j + rad, 365 + rad], fill=ca(SOFT))
        T(d, 960, 770, '먼저 다가가는 건 부담스럽다', 84, 'b', INK, LIGHT, a)
        T(d, 960, 880, '일일호프, 헌팅 포차처럼 낯선 사람에게 먼저 다가가야 하는 자리', 44, 'r', SOFT, LIGHT, a)
    else:
        for i in range(7):
            cx = 480 + 160 * i
            if i < 3:
                p = bo(fi(bl, .2 + .35 * i, .5))
                if p > 0:
                    person(d, cx, 470, 70 * p, ca(GREEN))
            else:
                d.ellipse([cx - 55, 470 - 85, cx + 55, 470 + 25], outline=ca(GRAY), width=4)
        T(d, 960, 770, '소개해 줄 지인도 많지 않다', 84, 'b', INK, LIGHT, a)
        T(d, 960, 880, '새로운 이성을 만날 기회가 제한된다', 44, 'r', SOFT, LIGHT, a)
    return img


# ---------- Scene 3: 온라인에서도 ----------
def s3(lt):
    img, d = canvas(CREAM)
    a = eo(fi(lt, 0, .6))
    g = lambda col, x=1: mix(CREAM, col, a * x)
    rr(d, (430, 160, 810, 920), 50, fill=g(WHITE), outline=g(INK), w=8)
    sel = (1, 1)
    for r_i in range(3):
        for c_i in range(2):
            cx = 525 + 190 * c_i
            cy = 330 + 220 * r_i
            hot = (r_i, c_i) == sel and lt > 3.0
            rr(d, (cx - 80, cy - 95, cx + 80, cy + 95), 22, fill=g((245, 247, 246)),
               outline=g(CORAL) if hot else None, w=5)
            d.ellipse([cx - 38, cy - 80, cx + 38, cy - 4], fill=g(GRAY))
            rr(d, (cx - 55, cy + 12, cx + 55, cy + 28), 8, fill=g((214, 220, 217)))
            if not ((r_i, c_i) == sel):
                rr(d, (cx - 40, cy + 42, cx + 40, cy + 56), 7, fill=g((214, 220, 217)))
    # 선택 카드 버튼
    cx, cy = 715, 550
    hot = lt > 3.0
    rr(d, (cx - 68, cy + 40, cx + 68, cy + 80), 20, fill=g(CORAL if hot else (214, 220, 217)))
    T(d, cx, cy + 60, '관심 보내기', 20, 'b', WHITE, CORAL if hot else (214, 220, 217), a)
    # 커서
    e = eio(fi(lt, 1.0, 2.0))
    px = 900 + (cx + 20 - 900) * e
    py = 820 + (cy + 62 - 820) * e
    if lt < 4.6:
        pts = [(0, 0), (0, 38), (10, 29), (18, 46), (26, 42), (18, 26), (32, 26)]
        d.polygon([(px + x, py + y) for x, y in pts], fill=g(INK), outline=g(WHITE))
    if 3.0 < lt < 3.7:
        rad = 20 + 70 * fi(lt, 3.0, .7)
        d.ellipse([cx + 20 - rad, cy + 62 - rad, cx + 20 + rad, cy + 62 + rad], outline=mix(CREAM, CORAL, 1 - fi(lt, 3.0, .7)), width=5)
    # 텍스트
    lines = [(.6, '온라인에서도', 80, INK, 330), (1.5, '직접 찾고,', 64, INK, 450),
             (2.2, '먼저 신청해야 한다면', 64, INK, 540), (4.2, '부담은 그대로예요.', 80, CORALD, 690)]
    for st, s, sz, col, y in lines:
        q = eo(fi(lt, st, .6))
        T(d, 930, y + (1 - q) * 30, s, sz, 'b', col, CREAM, q, anchor='lm')
    return img


# ---------- Scene 4: 해결 ----------
def s4(lt):
    img, d = canvas(GREEN)
    a = eo(fi(lt, 0, .6))
    g = lambda col, x=1: mix(GREEN, col, a * x)
    person(d, 520, 360, 110, g(MINT))
    person(d, 1400, 360, 110, g(MINT))
    p = bo(fi(lt, .4, .6))
    r = 75 * p
    if r > 1:
        for j in range(2):
            ph = (lt * 1.1 + j * .5) % 1
            rr_ = r + 18 + 40 * ph
            d.ellipse([960 - rr_, 330 - rr_, 960 + rr_, 330 + rr_], outline=mix(GREEN, CORAL, (1 - ph) * .8), width=4)
        d.ellipse([960 - r, 330 - r, 960 + r, 330 + r], fill=CORAL)
        T(d, 960, 330, 'AI', int(60 * p), 'k', WHITE, CORAL)
    if lt > 1.0:
        for (x1, x2) in [(610, 880), (1310, 1040)]:
            for n in range(6):
                u = (lt * .5 + n / 6) % 1
                x = x1 + (x2 - x1) * u
                y = 345 + (330 - 345) * u
                d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=mix(GREEN, MINT, .9))
    q = eo(fi(lt, 1.4, .7))
    T(d, 960, 660 + (1 - q) * 30, '먼저 다가가는 건 AI가,', 92, 'b', WHITE, GREEN, q)
    q = eo(fi(lt, 2.6, .7))
    T(d, 960, 800 + (1 - q) * 30, '서로를 알아가는 건 우리가', 92, 'b', (255, 175, 135), GREEN, q)
    return img


# ---------- Scene 5: 이용 흐름 (6 steps) ----------
STEPS = [
    ('대학생 인증', '학생증으로 대학생임을 확인합니다', '인증'),
    ('이상형 입력', '설문, 텍스트, 참고 이미지로 취향을 전달합니다', '입력'),
    ('AI의 한 사람 소개', '양쪽의 취향을 함께 고려해 한 사람을 소개합니다', '소개'),
    ('비공개 상호 수락', '서로 비공개로 선택하고, 둘 다 수락하면 연결됩니다', '수락'),
    ('사진 없이 일주일 대화', '약 일주일 동안 한 사람과 앱에서 대화합니다', '대화'),
    ('만남으로 연결', '서로 만나볼 의사가 같으면 가까운 지역에서 만납니다', '만남'),
]


def i1(d, sl, a, g):
    rr(d, (710, 250, 1210, 520), 30, fill=g(WHITE), outline=g(GREEN), w=6)
    d.ellipse([752, 342, 868, 458], fill=g(MINT))
    person(d, 810, 412, 34, g(GREEN))
    T(d, 900, 300, '학생증', 34, 'b', GREEN, CREAM, a, anchor='lm')
    rr(d, (900, 345, 1150, 367), 10, fill=g(GRAY))
    rr(d, (900, 390, 1090, 410), 10, fill=g((214, 220, 217)))
    rr(d, (900, 430, 1010, 450), 10, fill=g((214, 220, 217)))
    p = bo(fi(sl, 1.3, .5))
    if p > 0.05:
        r = 56 * p
        d.ellipse([1190 - r, 260 - r, 1190 + r, 260 + r], fill=GREEN)
        check(d, 1190, 262, 50 * p, WHITE, 10)
    p2 = eo(fi(sl, 2.2, .5))
    if p2 > 0:
        rr(d, (570, 550, 1350, 630), 40, fill=mix(CREAM, MINT, p2 * a))
        T(d, 960, 590, '초기 지역 · 서초구, 강남구 거주 대학생', 36, 'b', GREEN, MINT, p2 * a)


def i2(d, sl, a, g):
    items = [(620, '설문'), (960, '텍스트'), (1300, '참고 이미지')]
    for idx, (cx, lab) in enumerate(items):
        p = bo(fi(sl, .4 + .7 * idx, .5))
        if p <= 0.02:
            continue
        sc = p
        cy = 400
        rr(d, (cx - 135 * sc, cy - 125 * sc, cx + 135 * sc, cy + 125 * sc), 30 * sc,
           fill=g(WHITE), outline=g(GREEN), w=5)
        if idx == 0:
            for j in range(3):
                y = cy - 60 * sc + j * 50 * sc
                d.ellipse([cx - 84 * sc, y - 14 * sc, cx - 56 * sc, y + 14 * sc],
                          fill=g(CORAL) if j < 2 else None, outline=g(GRAY), width=3)
                rr(d, (cx - 40 * sc, y - 8 * sc, cx + 80 * sc, y + 8 * sc), 8 * sc, fill=g((214, 220, 217)))
        elif idx == 1:
            rr(d, (cx - 95 * sc, cy - 85 * sc, cx + 95 * sc, cy + 15 * sc), 24 * sc, fill=g(MINT))
            d.polygon([(cx - 50 * sc, cy + 15 * sc), (cx - 70 * sc, cy + 45 * sc), (cx - 20 * sc, cy + 15 * sc)], fill=g(MINT))
            rr(d, (cx - 65 * sc, cy - 58 * sc, cx + 65 * sc, cy - 44 * sc), 7 * sc, fill=g(WHITE))
            rr(d, (cx - 65 * sc, cy - 30 * sc, cx + 25 * sc, cy - 16 * sc), 7 * sc, fill=g(WHITE))
        else:
            rr(d, (cx - 95 * sc, cy - 85 * sc, cx + 95 * sc, cy + 25 * sc), 14 * sc, outline=g(GREEN), w=4)
            d.ellipse([cx + 40 * sc, cy - 70 * sc, cx + 72 * sc, cy - 38 * sc], fill=g(CORAL))
            d.polygon([(cx - 85 * sc, cy + 20 * sc), (cx - 30 * sc, cy - 40 * sc), (cx + 15 * sc, cy + 20 * sc)], fill=g(GREEN))
            d.polygon([(cx - 10 * sc, cy + 20 * sc), (cx + 35 * sc, cy - 15 * sc), (cx + 85 * sc, cy + 20 * sc)], fill=g(MINT))
        T(d, cx, cy + 92 * sc, lab, 36 * sc, 'b', INK, WHITE, a * p)


def i3(d, sl, a, g):
    A, B, orb = (560, 420), (1360, 420), (960, 380)
    p = bo(fi(sl, .1, .5))
    person(d, A[0], A[1], 125 * p, g(GREEN))
    person(d, B[0], B[1], 125 * p, g(CORAL))
    q = bo(fi(sl, .5, .5))
    r = 80 * q
    if r > 1:
        for j in range(2):
            ph = (sl * 1.1 + j * .5) % 1
            rr_ = r + 15 + 35 * ph
            d.ellipse([orb[0] - rr_, orb[1] - rr_, orb[0] + rr_, orb[1] + rr_],
                      outline=mix(CREAM, CORAL, (1 - ph) * .8 * a), width=4)
        d.ellipse([orb[0] - r, orb[1] - r, orb[0] + r, orb[1] + r], fill=mix(CREAM, GREEN, a))
        T(d, orb[0], orb[1], 'AI', 60 * q, 'k', WHITE, GREEN, a)
    if sl > .9:
        for (x1, y1, x2, y2) in [(650, 400, 875, 385), (1270, 400, 1045, 385)]:
            for n in range(6):
                u = (sl * .5 + n / 6) % 1
                x, y = x1 + (x2 - x1) * u, y1 + (y2 - y1) * u
                d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=g(CORAL))
    e = eo(fi(sl, 2.5, .8))
    if e > 0:
        d.line([(680, 570), (680 + 560 * e, 570)], fill=g(CORAL), width=8)
    h = bo(fi(sl, 3.2, .5))
    heart(d, 960, 570, 42 * h, g(CORAL))


def i4(d, sl, a, g):
    on1 = eio(fi(sl, 1.0, .4))
    on2 = eio(fi(sl, 2.0, .4))
    both = min(on1, on2)
    for cx, on in [(640, on1), (1280, on2)]:
        rr(d, (cx - 165, 230, cx + 165, 610), 34, fill=g(WHITE), outline=g(GREEN), w=5)
        person(d, cx, 385, 78, g(GRAY))
        track = mix(GRAY, CORAL, on)
        rr(d, (cx - 75, 488, cx + 75, 552), 32, fill=mix(CREAM, track, a))
        kx = cx - 43 + 86 * on
        d.ellipse([kx - 26, 520 - 26, kx + 26, 520 + 26], fill=g(WHITE))
        T(d, cx, 585, '수락', 30, 'b', SOFT, WHITE, a)
    d.line([(805, 420), (1115, 420)], fill=mix(CREAM, mix(GRAY, CORAL, both), a), width=8)
    p = bo(fi(sl, 3.0, .5))
    if p > 0.05:
        r = 58 * p
        d.ellipse([960 - r, 420 - r, 960 + r, 420 + r], fill=CORAL)
        rr(d, (960 - 28 * p, 420 - 22 * p, 960 + 28 * p, 420 + 12 * p), 10 * p, fill=WHITE)
        d.polygon([(960 - 12 * p, 420 + 12 * p), (960 - 20 * p, 420 + 30 * p), (960 + 4 * p, 420 + 12 * p)], fill=WHITE)


def i5(d, sl, a, g):
    rows = [(590, 215, 1010, 285, 'L', MINT), (910, 305, 1330, 375, 'R', WHITE), (590, 395, 1010, 465, 'L', MINT)]
    for n, (x1, y1, x2, y2, side, col) in enumerate(rows):
        p = bo(fi(sl, .3 + .7 * n, .5))
        if p <= 0.05:
            continue
        cy = (y1 + y2) / 2
        ax = 520 if side == 'L' else 1400
        d.ellipse([ax - 40, cy - 40, ax + 40, cy + 40], fill=g(GRAY))
        T(d, ax, cy, '?', 40, 'b', WHITE, GRAY, a)
        cx = (x1 + x2) / 2
        hw = (x2 - x1) / 2 * p
        rr(d, (cx - hw, y1, cx + hw, y2), 30, fill=g(col), outline=g(GRAY) if col == WHITE else None, w=3)
        if p > .9:
            rr(d, (x1 + 30, cy - 8, x2 - 130 + 60 * (n % 2), cy + 8), 8, fill=g(WHITE if col == MINT else (214, 220, 217)))
    for j in range(7):
        t0 = .6 + .55 * j
        cx = 610 + 100 * j + 50
        f = eo(fi(sl, t0, .35))
        col = CORAL if j == 6 else GREEN
        rr(d, (cx - 38, 528, cx + 38, 604), 16, fill=mix(CREAM, mix(WHITE, col, f), a), outline=mix(CREAM, GRAY, a), w=3)
        T(d, cx, 566, str(j + 1), 34, 'b', mix(GRAY, WHITE, f), mix(WHITE, col, f), a)


def i6(d, sl, a, g):
    e = eio(fi(sl, .3, 2.2))
    xa = 500 + (860 - 500) * e
    xb = 1420 - (1420 - 1060) * e
    bob = 6 * math.sin(sl * 6) * (1 - fi(sl, 2.5, .3))
    person(d, xa, 430 + bob, 125, g(GREEN))
    person(d, xb, 430 - bob, 125, g(CORAL))
    h = bo(fi(sl, 2.6, .5))
    heart(d, 960, 270, 70 * h * (1 + .05 * math.sin(sl * 6)), g(CORAL))
    p = eo(fi(sl, 3.0, .5))
    if p > 0:
        rr(d, (660, 550, 1260, 630), 40, fill=mix(CREAM, MINT, p * a))
        T(d, 960, 590, '가까운 생활권에서 만나요', 38, 'b', GREEN, MINT, p * a)


ICONS = [i1, i2, i3, i4, i5, i6]


def s5(lt):
    img, d = canvas(CREAM)
    k = min(5, int(lt // 5))
    sl = lt - 5 * k
    a = fi(sl, 0, .5) * fo(sl, 4.55, .45)
    xs = [360 + 240 * i for i in range(6)]
    head = max(0, (k - 1) + eio(fi(sl, 0, .6))) if k > 0 else 0
    d.line([(xs[0], 120), (xs[5], 120)], fill=(214, 220, 217), width=8)
    if head > 0:
        d.line([(xs[0], 120), (xs[0] + 240 * head, 120)], fill=GREEN, width=8)
    for i, x in enumerate(xs):
        if i < k:
            d.ellipse([x - 34, 86, x + 34, 154], fill=GREEN)
            T(d, x, 120, str(i + 1), 34, 'b', WHITE, GREEN)
            T(d, x, 190, STEPS[i][2], 26, 'b', SOFT, CREAM)
        elif i == k:
            r = 34 + 10 * bo(fi(sl, 0, .5))
            d.ellipse([x - r, 120 - r, x + r, 120 + r], fill=CORAL)
            T(d, x, 120, str(i + 1), 40, 'b', WHITE, CORAL)
            T(d, x, 190, STEPS[i][2], 28, 'b', INK, CREAM)
        else:
            d.ellipse([x - 34, 86, x + 34, 154], fill=WHITE, outline=GRAY, width=5)
            T(d, x, 120, str(i + 1), 34, 'b', GRAY, WHITE)
            T(d, x, 190, STEPS[i][2], 26, 'r', GRAY, CREAM)
    g = lambda col, x=1: mix(CREAM, col, a * x)
    ICONS[k](d, sl, a, g)
    off = (1 - eo(fi(sl, 0, .5))) * 30
    T(d, 960, 650 + off, 'STEP %d' % (k + 1), 34, 'b', CORALD, CREAM, a)
    T(d, 960, 735 + off, STEPS[k][0], 88, 'b', INK, CREAM, a)
    T(d, 960, 840 + off, STEPS[k][1], 44, 'r', SOFT, CREAM, a)
    return img


# ---------- Scene 6: 차별화 ----------
CARDS = [
    ('AI가 먼저 소개', '상대를 찾아 먼저 신청해야 하는 부담을 AI의 소개로 줄입니다.'),
    ('일주일, 한 사람에게 집중', '연결된 동안 추가 매칭 없이 약 일주일 동안 한 사람과 대화합니다.'),
    ('사진은 매칭에만 활용', '사진은 AI 매칭에 활용하고 상대에게는 공개하지 않습니다.'),
    ('실제 만남까지', '가까운 생활권의 대학생을 연결하고 만남 의사를 확인합니다.'),
]


def s6(lt):
    img, d = canvas(MINTL)
    a = eo(fi(lt, 0, .6))
    T(d, 960, 140, '초식남녀의 차별화 방향', 66, 'b', GREEN, MINTL, a)
    pos = [(520, 410), (1400, 410), (520, 750), (1400, 750)]
    for i, ((cx, cy), (tt, ds)) in enumerate(zip(pos, CARDS)):
        q = eo(fi(lt, .6 + .7 * i, .6))
        if q <= 0.02:
            continue
        cy2 = cy + (1 - q) * 50
        rr(d, (cx - 400, cy2 - 140, cx + 400, cy2 + 140), 36, fill=mix(MINTL, WHITE, q))
        d.ellipse([cx - 368, cy2 - 108, cx - 292, cy2 - 32], fill=mix(MINTL, CORAL, q))
        T(d, cx - 330, cy2 - 70, str(i + 1), 44, 'b', WHITE, CORAL, q)
        T(d, cx - 270, cy2 - 70, tt, 46, 'b', INK, WHITE, q, anchor='lm')
        font = F('r', 34)
        for j, ln in enumerate(wrap(ds, font, 700)):
            T(d, cx - 350, cy2 + 15 + 46 * j, ln, 34, 'r', SOFT, WHITE, q, anchor='lm')
    return img


# ---------- Scene 7: 엔딩 ----------
def s7(lt):
    img, d = canvas(GREEN)
    p = bo(fi(lt, .1, .7))
    heart(d, 960, 230, 64 * p * (1 + .05 * math.sin(lt * 5)), CORAL)
    a = eo(fi(lt, .4, .8))
    T(d, 960, 420 + (1 - a) * 30, '초식남녀', 190, 'k', WHITE, GREEN, a)
    a = eo(fi(lt, 1.4, .7))
    T(d, 960, 600 + (1 - a) * 25, '먼저 다가가는 건 AI가,', 64, 'b', MINT, GREEN, a)
    a = eo(fi(lt, 2.2, .7))
    T(d, 960, 690 + (1 - a) * 25, '서로를 알아가는 건 우리가', 64, 'b', (255, 175, 135), GREEN, a)
    a = eo(fi(lt, 3.6, .8))
    font = F('r', 34)
    msg = 'AI가 완벽한 이상형이나 관계의 성공을 보장하지는 않습니다. 대화를 시작하는 부담을 줄이는 것이 초식남녀의 목표입니다.'
    for j, ln in enumerate(wrap(msg, font, 1400)):
        T(d, 960, 860 + 48 * j, ln, 34, 'r', mix(GREEN, MINT, .85), GREEN, a)
    return img


SCENES = [(s1, 6), (s2, 16), (s3, 8), (s4, 7), (s5, 30), (s6, 9), (s7, 8)]
TOT = sum(du for _, du in SCENES)
TR = 0.7


def frame(t):
    acc = 0.0
    for i, (fn, du) in enumerate(SCENES):
        if t < acc + du or i == len(SCENES) - 1:
            lt = t - acc
            break
        acc += du
    img = fn(lt)
    if i > 0 and lt < TR:
        pf, pdu = SCENES[i - 1]
        base = pf(pdu - 0.01)
        r = int(eio(lt / TR) * 1250)
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).ellipse([960 - r, 540 - r, 960 + r, 540 + r], fill=255)
        img = Image.composite(img, base, m)
    if t > TOT - 0.6:
        img = Image.blend(img, Image.new('RGB', (W, H), (0, 0, 0)), cl((t - (TOT - 0.6)) / 0.6))
    return img


def render_bytes(n):
    return frame(n / FPS).tobytes()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'preview':
        outdir = sys.argv[2]
        for s in sys.argv[3:]:
            frame(float(s)).save('%s/prev_%05.1f.png' % (outdir, float(s)))
    else:
        out = sys.argv[2]
        N = int(TOT * FPS)
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
               '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
               '-shortest', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(2) as pool:
            for i, chunk in enumerate(pool.imap(render_bytes, range(N), chunksize=6)):
                proc.stdin.write(chunk)
                if i % 300 == 0:
                    print('frame', i, '/', N, flush=True)
        proc.stdin.close()
        proc.wait()
        print('done', out)
