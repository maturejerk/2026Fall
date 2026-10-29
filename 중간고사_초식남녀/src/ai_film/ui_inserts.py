#!/usr/bin/env python3
"""AI 애니메이션 〈만나기까지, 일주일〉용 휴대폰 화면 컷 (1920x1080, 24fps)
python3 ui_inserts.py preview OUTDIR   # 컷별 대표 프레임
python3 ui_inserts.py render OUTDIR    # ui02.mp4 ... ui17.mp4
"""
import os, sys, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.argv_backup = list(sys.argv); sys.argv = ['x']
import make_dino_motion as M
sys.argv = sys.argv_backup

W, H, FPS = 1920, 1080, 24
OUT = (28, 28, 34)
SKIN = (250, 214, 178)
CORAL = (244, 118, 94); MINT = (152, 212, 186); CREAM = (252, 247, 236); INK = (40, 40, 46); GRAY = (150, 152, 158)
cl, fi, eo, eio, bo, pop = M.cl, M.fi, M.eo, M.eio, M.bo, M.pop

@functools.lru_cache(None)
def N(size, bold=False):
    path = '/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc' % ('Bold' if bold else 'Regular')
    for idx in range(10):
        try:
            f = ImageFont.truetype(path, int(size), index=idx)
        except Exception:
            break
        if 'KR' in f.getname()[0]: return f
    return ImageFont.truetype(path, int(size))
J = M.J; HF = M.H

SW, SH = 448, 860            # 화면 크기
PX, PY = 960, 560            # 휴대폰 중심

def paste(cv, im, x, y, alpha=1.0):
    if alpha <= 0.01: return
    if alpha < 0.995:
        im = im.copy(); im.putalpha(im.getchannel('A').point(M.LUT[int(alpha * 100)]))
    w, h = im.size; x0, y0 = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x0), max(0, -y0); sx1, sy1 = min(w, cv.width - x0), min(h, cv.height - y0)
    if sx1 > sx0 and sy1 > sy0:
        cv.alpha_composite(im, (x0 + sx0, y0 + sy0), (sx0, sy0, sx1, sy1))

@functools.lru_cache(None)
def background(col):
    cv = Image.new('RGBA', (W, H), col + (255,)); d = ImageDraw.Draw(cv)
    light = tuple(min(255, c + 18) for c in col)
    d.ellipse([PX - 640, PY - 640, PX + 640, PY + 640], fill=light + (255,))
    for (x, y, r) in [(260, 220, 60), (1680, 860, 80), (1600, 200, 40), (330, 880, 34)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=light + (255,), outline=OUT + (255,), width=6)
    return cv

def phone_frame(cv, screen, dim=0.0):
    d = ImageDraw.Draw(cv)
    # 손바닥 (휴대폰 뒤)
    d.ellipse([PX - 330, PY + 250, PX + 20, PY + 620], fill=SKIN, outline=OUT, width=9)
    x0, y0 = PX - SW // 2 - 26, PY - SH // 2 - 46
    d.rounded_rectangle([x0, y0, x0 + SW + 52, y0 + SH + 92], 58, fill=(44, 44, 54), outline=OUT, width=10)
    sc = screen
    if dim > 0:
        sc = Image.blend(screen, Image.new('RGBA', screen.size, (10, 10, 14, 255)), cl(dim))
    m = Image.new('L', (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, SW, SH], 32, fill=255)
    cv.paste(sc.convert('RGB'), (x0 + 26, y0 + 46), m)
    d.rounded_rectangle([PX - 50, y0 + 18, PX + 50, y0 + 30], 6, fill=(20, 20, 24))
    # 엄지와 손가락 (휴대폰 앞)
    d.ellipse([x0 - 46, PY + 120, x0 + 60, PY + 330], fill=SKIN, outline=OUT, width=9)
    for k in range(3):
        yy = PY + 150 + 70 * k
        d.ellipse([x0 + SW + 20, yy, x0 + SW + 100, yy + 64], fill=SKIN, outline=OUT, width=9)

def status_bar(d, title=None, sub=None, color=(255, 255, 255), tcol=INK, avatar=None):
    d.rectangle([0, 0, SW, 120], fill=color)
    d.text((24, 22), '9:41', font=N(22, True), fill=tcol, anchor='lm')
    d.rounded_rectangle([SW - 70, 14, SW - 30, 30], 4, outline=tcol, width=2)
    d.rectangle([SW - 66, 18, SW - 42, 26], fill=tcol)
    x = 24
    if avatar is not None:
        d.ellipse([20, 52, 80, 112], fill=avatar[0]); d.text((50, 82), avatar[1], font=J(34), fill=(255, 255, 255), anchor='mm')
        x = 96
    if title: d.text((x, 70 if sub else 82), title, font=N(30, True), fill=tcol, anchor='lm')
    if sub: d.text((x, 102), sub, font=N(20), fill=GRAY if tcol == INK else tcol, anchor='lm')
    d.line([(0, 120), (SW, 120)], fill=(226, 226, 230), width=2)

def bubble(scr, s, y, side, p=1.0, col=None, size=26, maxw=300):
    if p <= 0.01: return 0
    d = ImageDraw.Draw(scr); f = N(size)
    lines, cur = [], ''
    for ch in s:
        if f.getlength(cur + ch) > maxw: lines.append(cur); cur = ch
        else: cur += ch
    lines.append(cur)
    tw = max(f.getlength(l) for l in lines); th = len(lines) * (size + 10)
    bw, bh = tw + 40, th + 26
    col = col or ((236, 236, 240) if side == 'l' else (255, 226, 92))
    x = 24 if side == 'l' else SW - 24 - bw
    s_ = bo(p)
    im = Image.new('RGBA', (int(bw) + 2, int(bh) + 2), (0, 0, 0, 0)); di = ImageDraw.Draw(im)
    di.rounded_rectangle([0, 0, bw, bh], 22, fill=col)
    for i, l in enumerate(lines): di.text((20, 13 + i * (size + 10)), l, font=f, fill=INK)
    if s_ < 0.999:
        im = im.resize((max(1, int(im.width * s_)), max(1, int(im.height * s_))), Image.BICUBIC)
    ax = x if side == 'l' else x + bw - im.width
    scr.alpha_composite(im, (int(ax), int(y + (bh - im.height) / 2)))
    return bh

def keyboard(d, y0=600):
    d.rectangle([0, y0, SW, SH], fill=(214, 216, 222))
    rows = [10, 9, 7]
    for r, n in enumerate(rows):
        kw = (SW - 20) / 10
        off = (SW - n * kw) / 2
        for k in range(n):
            x = off + k * kw
            d.rounded_rectangle([x + 3, y0 + 14 + r * 62, x + kw - 3, y0 + 66 + r * 62], 8, fill=(255, 255, 255))
    d.rounded_rectangle([110, y0 + 204, SW - 110, y0 + 250], 8, fill=(255, 255, 255))

def tap(scr, x, y, t, t0):
    u = fi(t, t0, 0.45)
    if 0 < u < 1:
        d = ImageDraw.Draw(scr); r = 18 + 40 * u
        a = int(160 * (1 - u))
        ov = Image.new('RGBA', scr.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).ellipse([x - r, y - r, x + r, y + r], fill=(60, 60, 70, a))
        scr.alpha_composite(ov)

@functools.lru_cache(None)
def dino_icon(size, v='g', mood='n'):
    im = M.dino_raw(v, False, mood)
    im = im.resize((int(im.width * size / im.height), size), Image.LANCZOS)
    return im

def check(d, x, y, s, col=(255, 255, 255), w=6):
    d.line([(x - .45 * s, y), (x - .1 * s, y + .38 * s), (x + .55 * s, y - .45 * s)], fill=col, width=w, joint='curve')

# ------------------------------------------------------------ 컷 2: 일일호프 메시지
def ui02(t):
    cv = background((246, 200, 150)).copy()
    scr = Image.new('RGBA', (SW, SH), (186, 206, 224, 255)); d = ImageDraw.Draw(scr)
    status_bar(d, '과 동기 단톡방', '8명', avatar=((120, 150, 200), '단'))
    bubble(scr, '오늘 저녁에 다 같이 일일호프 갈래?', 170, 'l', fi(t, 0.2, 0.3))
    bubble(scr, '나 갈게~', 280, 'l', fi(t, 0.5, 0.3))
    bubble(scr, '나도나도', 360, 'l', fi(t, 0.7, 0.3))
    keyboard(d, 600)
    d.rectangle([0, 520, SW, 600], fill=(255, 255, 255))
    d.rounded_rectangle([20, 534, SW - 90, 586], 26, fill=(242, 242, 246))
    full = '응 나도 갈'
    if t < 1.3: n = 0
    elif t < 2.5: n = int(len(full) * (t - 1.3) / 1.2) + 1
    elif t < 3.0: n = len(full)
    else: n = max(0, len(full) - int((t - 3.0) / 0.12))
    s = full[:min(n, len(full))]
    d.text((40, 560), s, font=N(26), fill=INK, anchor='lm')
    if int(t * 2.5) % 2 == 0:
        cx = 40 + N(26).getlength(s) + 3; d.line([(cx, 544), (cx, 576)], fill=(60, 120, 230), width=3)
    d.ellipse([SW - 76, 536, SW - 26, 586], fill=(255, 226, 92) if s else (230, 230, 234))
    phone_frame(cv, scr)
    return cv

# ------------------------------------------------------------ 컷 4: 친구에게 소개 부탁
def ui04(t):
    cv = background((200, 196, 232)).copy()
    scr = Image.new('RGBA', (SW, SH), (186, 206, 224, 255)); d = ImageDraw.Draw(scr)
    status_bar(d, '수아', avatar=((240, 160, 140), '수'))
    bubble(scr, '혹시 주변에 소개해 줄 사람 있어?', 160, 'r', 1.0)
    bubble(scr, '음… 지금은 딱히 없네 ㅠㅠ', 290, 'l', fi(t, 0.4, 0.3))
    bubble(scr, '소개해 줄 사람 생기면 알려줄게!', 380, 'l', fi(t, 1.2, 0.3))
    bubble(scr, '응 고마워', 500, 'r', fi(t, 2.2, 0.3))
    phone_frame(cv, scr, dim=fi(t, 3.7, 0.6))
    return cv

# ------------------------------------------------------------ 컷 6: 초식남녀 앱 시작, 학생증 인증, 설문
def app_header(d, title, step=None):
    d.rectangle([0, 0, SW, 120], fill=CREAM)
    d.text((24, 22), '9:41', font=N(22, True), fill=INK, anchor='lm')
    d.text((24, 82), title, font=J(36), fill=(52, 92, 44), anchor='lm')
    if step: d.text((SW - 24, 82), step, font=N(22), fill=GRAY, anchor='rm')

def ui06(t):
    cv = background((246, 214, 160)).copy()
    scr = Image.new('RGBA', (SW, SH), CREAM + (255,)); d = ImageDraw.Draw(scr)
    if t < 1.6:   # 홈 화면
        scr.paste((132, 170, 214, 255), (0, 0, SW, SH)); d = ImageDraw.Draw(scr)
        d.text((24, 22), '9:41', font=N(22, True), fill=(255, 255, 255), anchor='lm')
        cols = [(250, 120, 110), (110, 190, 140), (250, 200, 90), (150, 130, 220), (90, 160, 230), (240, 150, 190), (120, 120, 130)]
        k = 0
        for r in range(4):
            for c in range(4):
                x = 30 + c * 104; y = 80 + r * 130
                if (r, c) == (1, 1):
                    s = 1 + 0.06 * math.sin(t * 8)
                    sz = int(84 * s); o = (84 - sz) / 2
                    d.rounded_rectangle([x + o, y + o, x + o + sz, y + o + sz], 20, fill=CREAM)
                    ic = dino_icon(int(70 * s)); scr.alpha_composite(ic, (int(x + 42 - ic.width / 2), int(y + 42 - ic.height / 2)))
                    d.text((x + 42, y + 104), '초식남녀', font=N(18, True), fill=(255, 255, 255), anchor='mm')
                else:
                    d.rounded_rectangle([x, y, x + 84, y + 84], 20, fill=cols[k % 7]); k += 1
        tap(scr, 30 + 104 + 42, 80 + 130 + 42, t, 0.9)
    elif t < 3.9:  # 학생증 인증
        lt = t - 1.6
        app_header(d, '학생증 인증', '1 / 3')
        d.text((SW / 2, 170), '학생증을 사각형 안에 맞춰 주세요', font=N(22), fill=INK, anchor='mm')
        d.rounded_rectangle([40, 210, SW - 40, 480], 18, fill=(60, 64, 72))
        card = M.sp('idcard'); cs = 340 / card.width
        cim = card.resize((int(card.width * cs), int(card.height * cs)), Image.BICUBIC)
        scr.alpha_composite(cim, (int(SW / 2 - cim.width / 2), int(345 - cim.height / 2)))
        M.brackets(d, SW / 2, 345, 330, 230, (255, 255, 255), 30, 6)
        if lt < 1.1:
            yy = 240 + 210 * (0.5 - 0.5 * math.cos(lt * 5.5))
            d.line([(70, yy), (SW - 70, yy)], fill=CORAL, width=4)
        q = pop(lt, 1.1, 0.4)
        if q > 0.05:
            r = 34 * q; d.ellipse([SW / 2 - r, 520 - r, SW / 2 + r, 520 + r], fill=(92, 168, 140)); check(d, SW / 2, 522, 34 * q)
            d.text((SW / 2, 580), '대학생 인증 완료', font=N(26, True), fill=(52, 92, 44), anchor='mm')
        q2 = pop(lt, 1.6, 0.4)
        if q2 > 0.05:
            d.rounded_rectangle([30, 630, SW - 30, 760], 20, fill=(255, 236, 222))
            head = dino_icon(84); scr.alpha_composite(head, (50, 653))
            d.text((150, 672), '학생증 사진으로', font=N(24, True), fill=INK, anchor='lm')
            d.text((150, 708), 'AI가 매칭해요', font=N(24, True), fill=(204, 70, 46), anchor='lm')
            d.text((150, 740), '사진은 상대에게 공개되지 않아요', font=N(17), fill=GRAY, anchor='lm')
    else:          # 이상형 설문
        lt = t - 3.9
        app_header(d, '이상형 설문', '3 / 3')
        d.rounded_rectangle([24, 140, SW - 24, 150], 5, fill=(230, 226, 216))
        d.rounded_rectangle([24, 140, 24 + (SW - 48) * (0.66 + 0.34 * eio(fi(lt, 0.5, 2.0))), 150], 5, fill=CORAL)
        d.text((24, 200), '어떤 분위기의 사람이 좋아요?', font=N(26, True), fill=INK, anchor='lm')
        d.text((24, 238), '여러 개를 골라도 괜찮아요', font=N(20), fill=GRAY, anchor='lm')
        chips = ['다정한', '차분한', '웃음이 많은', '산책 좋아하는', '책 좋아하는', '음악 좋아하는', '대화가 편한', '조용한 카페']
        sel = {0: 0.6, 3: 1.2, 6: 1.8, 7: 2.4}
        x, y = 24, 290
        for i, c in enumerate(chips):
            f = N(23, True); w = f.getlength(c) + 44
            if x + w > SW - 24: x = 24; y += 70
            on = i in sel and lt > sel[i]
            d.rounded_rectangle([x, y, x + w, y + 54], 27, fill=CORAL if on else (255, 255, 255), outline=CORAL if on else (220, 216, 208), width=2)
            d.text((x + w / 2, y + 27), c, font=f, fill=(255, 255, 255) if on else INK, anchor='mm')
            if i in sel: tap(scr, x + w / 2, y + 27, t, 3.9 + sel[i] - 0.05)
            x += w + 12
        d.rounded_rectangle([30, SH - 110, SW - 30, SH - 40], 35, fill=(52, 92, 44) if lt > 2.6 else (200, 200, 196))
        d.text((SW / 2, SH - 75), '소개 받기', font=N(26, True), fill=(255, 255, 255), anchor='mm')
    phone_frame(cv, scr)
    return cv

# ------------------------------------------------------------ 컷 7: 소개 카드, 수락
def ui07(t):
    cv = background((168, 214, 196)).copy()
    scr = Image.new('RGBA', (SW, SH), CREAM + (255,)); d = ImageDraw.Draw(scr)
    app_header(d, '오늘의 소개')
    d.text((SW / 2, 165), '서로의 취향을 고려한', font=N(22), fill=INK, anchor='mm')
    d.text((SW / 2, 197), '한 사람을 소개해 드려요', font=N(22), fill=INK, anchor='mm')
    q = pop(t, 0.3, 0.5)
    card = Image.new('RGBA', (SW - 60, 450), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
    dc.rounded_rectangle([0, 0, SW - 61, 449], 28, fill=(255, 255, 255), outline=(226, 220, 208), width=2)
    cx = (SW - 60) / 2
    dc.ellipse([cx - 66, 30, cx + 66, 162], fill=(214, 214, 208)); dc.text((cx, 98), '?', font=J(84), fill=(255, 255, 255), anchor='mm')
    dc.text((cx, 196), '사진은 만나기 전까지 비공개', font=N(18), fill=GRAY, anchor='mm')
    dc.text((cx, 240), '이런 점이 잘 맞아요', font=N(22, True), fill=INK, anchor='mm')
    tags = ['산책', '조용한 카페', '잔잔한 음악']
    tw = sum(N(20, True).getlength(s) + 34 for s in tags) + 10 * (len(tags) - 1)
    x = cx - tw / 2
    for s in tags:
        w = N(20, True).getlength(s) + 34
        dc.rounded_rectangle([x, 268, x + w, 312], 22, fill=(255, 236, 222)); dc.text((x + w / 2, 290), s, font=N(20, True), fill=(204, 70, 46), anchor='mm'); x += w + 10
    dc.text((cx, 350), '"대화가 편한 사람이 좋아요"', font=N(20), fill=INK, anchor='mm')
    acc = t > 2.2
    dc.rounded_rectangle([30, 380, SW - 90, 436], 28, fill=CORAL if not acc else (200, 200, 196))
    dc.text((cx, 408), '수락하기' if not acc else '수락했어요', font=N(24, True), fill=(255, 255, 255), anchor='mm')
    if q < 0.999: card = card.resize((max(1, int(card.width * q)), max(1, int(card.height * q))), Image.BICUBIC)
    scr.alpha_composite(card, (int(SW / 2 - card.width / 2), int(240 + 225 - card.height / 2)))
    tap(scr, SW / 2, 240 + 408, t, 2.0)
    d.text((SW / 2, 735), '거절해도 상대에게 알리지 않아요', font=N(18), fill=GRAY, anchor='mm')
    m = fi(t, 3.0, 0.35)
    if m > 0:
        ov = Image.new('RGBA', scr.size, (0, 0, 0, int(120 * m))); scr.alpha_composite(ov)
        s = bo(fi(t, 3.0, 0.5))
        box = Image.new('RGBA', (SW - 60, 300), (0, 0, 0, 0)); db = ImageDraw.Draw(box)
        db.rounded_rectangle([0, 0, SW - 61, 299], 30, fill=CREAM)
        hd = dino_icon(110, 'g', 'h'); box.alpha_composite(hd, (int((SW - 60) / 2 - hd.width / 2), 18))
        db.text(((SW - 60) / 2, 170), '서로 수락했어요!', font=J(38), fill=(204, 70, 46), anchor='mm')
        db.text(((SW - 60) / 2, 222), '일주일 동안 알아가 볼까요?', font=N(24, True), fill=INK, anchor='mm')
        if s < 0.999: box = box.resize((max(1, int(box.width * s)), max(1, int(box.height * s))), Image.BICUBIC)
        scr.alpha_composite(box, (int(SW / 2 - box.width / 2), int(SH / 2 - box.height / 2)))
    phone_frame(cv, scr)
    return cv

# ------------------------------------------------------------ 컷 11: 일주일 대화
def chat_header(d, day):
    d.rectangle([0, 0, SW, 150], fill=(234, 226, 248))
    d.text((24, 22), '9:41', font=N(22, True), fill=INK, anchor='lm')
    d.ellipse([20, 52, 80, 112], fill=(204, 204, 198)); d.text((50, 84), '?', font=J(40), fill=(255, 255, 255), anchor='mm')
    d.text((96, 70), '소개받은 사람', font=N(26, True), fill=INK, anchor='lm')
    d.text((96, 102), '사진은 비공개예요', font=N(18), fill=GRAY, anchor='lm')
    d.rounded_rectangle([SW - 130, 60, SW - 20, 104], 22, fill=CORAL); d.text((SW - 75, 82), 'DAY %d' % day, font=J(28), fill=(255, 255, 255), anchor='mm')
    for k in range(7):
        x = 40 + k * ((SW - 80) / 6)
        d.ellipse([x - 9, 126, x + 9, 144], fill=CORAL if k < day else (214, 206, 230))

def ui11(t):
    cv = background((214, 196, 236)).copy()
    scr = Image.new('RGBA', (SW, SH), (250, 248, 255, 255)); d = ImageDraw.Draw(scr)
    day = 1 if t < 1.6 else (3 if t < 3.2 else 6)
    chat_header(d, day)
    y = 180
    msgs = [('오늘 수업 어땠어요?', 'l', 0.3), ('발표했는데 엄청 떨었어요.', 'r', 1.3), ('저도요. 끝나고 나서야 숨 쉬었어요.', 'l', 2.3),
            ('ㅋㅋ 우리 비슷하네요', 'r', 3.3), ('내일도 얘기해요 :)', 'l', 4.0)]
    for s, side, t0 in msgs:
        if t > t0:
            h = bubble(scr, s, y, side, fi(t, t0, 0.3), (176, 226, 200) if side == 'r' else None)
            y += h + 18
    d.rectangle([0, SH - 80, SW, SH], fill=(255, 255, 255)); d.rounded_rectangle([20, SH - 64, SW - 90, SH - 16], 24, fill=(242, 240, 248))
    phone_frame(cv, scr)
    return cv

# ------------------------------------------------------------ 컷 13: 7일째 만남 제안
def ui13(t):
    cv = background((246, 196, 160)).copy()
    scr = Image.new('RGBA', (SW, SH), (250, 248, 255, 255)); d = ImageDraw.Draw(scr)
    chat_header(d, 7)
    q = pop(t, 0.2, 0.5)
    box = Image.new('RGBA', (SW - 50, 330), (0, 0, 0, 0)); db = ImageDraw.Draw(box)
    db.rounded_rectangle([0, 0, SW - 51, 329], 28, fill=CREAM, outline=(226, 220, 208), width=2)
    bx = (SW - 50) / 2
    hd = dino_icon(84, 'g', 'n'); box.alpha_composite(hd, (int(bx - hd.width / 2), 14))
    db.text((bx, 126), '일주일이 지났어요', font=N(22), fill=GRAY, anchor='mm')
    db.text((bx, 166), '직접 만나보고 싶나요?', font=J(36), fill=INK, anchor='mm')
    for k, (lab, t0) in enumerate([('나', 1.0), ('상대', 1.8)]):
        x = 30 + k * (bx - 10)
        on = t > t0
        db.rounded_rectangle([x, 210, x + bx - 40, 300], 22, fill=CORAL if on else (255, 255, 255), outline=CORAL, width=3)
        db.text((x + (bx - 40) / 2, 238), lab, font=N(20), fill=(255, 255, 255) if on else GRAY, anchor='mm')
        db.text((x + (bx - 40) / 2, 272), '만나볼래요' if on else '대기 중', font=N(22, True), fill=(255, 255, 255) if on else GRAY, anchor='mm')
    if q < 0.999: box = box.resize((max(1, int(box.width * q)), max(1, int(box.height * q))), Image.BICUBIC)
    scr.alpha_composite(box, (int(SW / 2 - box.width / 2), int(190 + 165 - box.height / 2)))
    tap(scr, 25 + 30 + (SW - 100) / 4, 190 + 255, t, 0.8)
    if t > 2.4:
        d.text((SW / 2, 560), '둘 다 만나보고 싶어해요!', font=N(22, True), fill=(204, 70, 46), anchor='mm')
    y = 610
    for s, side, t0 in [('토요일 오후, 카페에서 만나요', 'r', 3.0), ('좋아요 :) 떨리네요', 'l', 4.0)]:
        if t > t0:
            h = bubble(scr, s, y, side, fi(t, t0, 0.3), (176, 226, 200) if side == 'r' else None); y += h + 16
    phone_frame(cv, scr)
    return cv

# ------------------------------------------------------------ 컷 17: 엔딩 로고
def ui17(t):
    cv = Image.new('RGBA', (W, H), (250, 243, 226, 255))
    tex = M.tex_fill((250, 243, 226), M.S * 2 - 200, H, 9)[:, :W]
    cv = Image.fromarray(np.dstack([tex, np.full(tex.shape[:2], 255)]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(cv)
    for i in range(30):
        a = 2 * math.pi * i / 30 + t * 0.15
        r0, r1 = 330, 390
        d.line([(960 + r0 * math.cos(a), 400 + r0 * math.sin(a)), (960 + r1 * math.cos(a), 400 + r1 * math.sin(a))], fill=(232, 176, 150), width=7)
    for v, x, flip, t0, h in [('p', 820, True, 0.25, 380), ('g', 1090, False, 0.0, 400)]:
        s = pop(t, t0, 0.6)
        if s > 0.02:
            nm = 'd%sh0' % v
            im = M.X(nm, h * s / M.DH, 0, flip)
            paste(cv, im, x - im.width / 2, 640 - im.height + M.sp(nm).info['pad'] * h * s / M.DH)
    hs = pop(t, 0.7, 0.5) * 0.6
    if hs > 0.02:
        hm = M.X('heart', hs); paste(cv, hm, 955 - hm.width / 2, 200 - hm.height / 2)
    a = eo(fi(t, 0.8, 0.4))
    if a > 0:
        im = M.tsp('초식남녀', 150, M.GREEN_D, 'j'); paste(cv, im, 960 - im.width / 2, 760 - im.height / 2, a)
    s = '먼저 다가가는 건 저희가, 서로를 알아가는 건 우리가'
    p = fi(t, 1.3, 1.6)
    if p > 0:
        sub = s[:M.nchars(s, p)]
        full = M.tsp(s, 60, M.RED, 'h'); im = M.tsp(sub, 60, M.RED, 'h')
        paste(cv, im, 960 - full.width / 2, 900 - full.height / 2)
    return cv

def frame(fn, name, t):
    im = fn(t).convert('RGB')
    if name == 'ui17': return im
    z = 1.2; w, h = W / z, H / z; cx, cy = 960, 560
    x0 = cx - w / 2; y0 = min(max(cy - h / 2, 0), H - h)
    return im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))

CUTS = [('ui02', ui02, 5.0), ('ui04', ui04, 5.0), ('ui06', ui06, 7.0), ('ui07', ui07, 5.0), ('ui11', ui11, 5.0), ('ui13', ui13, 6.0), ('ui17', ui17, 4.0)]

if __name__ == '__main__':
    mode, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    if mode == 'preview':
        for name, fn, du in CUTS:
            for tt in (du * 0.35, du * 0.9):
                frame(fn, name, tt).save(os.path.join(od, '%s_%.1f.png' % (name, tt)))
    else:
        for name, fn, du in CUTS:
            out = os.path.join(od, name + '.mp4')
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out]
            pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for n in range(int(du * FPS)):
                pr.stdin.write(frame(fn, name, n / FPS).tobytes())
            pr.stdin.close(); pr.wait(); print('done', out)
