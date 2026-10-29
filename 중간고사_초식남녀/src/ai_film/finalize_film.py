#!/usr/bin/env python3
"""사용자가 만든 〈만나기까지, 일주일〉 영상에 오프닝 타이틀을 붙이고, 엔딩을 크레파스 공룡 로고로 교체
python3 finalize_film.py IN.mp4 OUT.mp4 [preview_dir]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
_a = list(sys.argv); sys.argv = ['x']
import make_dino_motion as M
import ui_inserts as U
sys.argv = _a

W, H, FPS = 1920, 1080, 30
CUT = 1920            # 원본에서 엔딩이 시작하는 프레임 (64.0초)
TITLE_S, END_S = 2.5, 5.0

def paper_bg(seed):
    tex = M.tex_fill((250, 243, 226), M.S * 2 - 200, H, seed)[:, :W]
    return Image.fromarray(np.dstack([tex, np.full(tex.shape[:2], 255)]).astype(np.uint8), 'RGBA')

BG_T = None
def title(t):
    global BG_T
    if BG_T is None: BG_T = paper_bg(4)
    cv = BG_T.copy()
    hs = M.pop(t, 0.2, 0.6) * 0.42
    if hs > 0.02:
        hm = M.X('heart', hs); U.paste(cv, hm, 960 - hm.width / 2, 330 - hm.height / 2)
    s = '만나기까지, 일주일'
    full = M.tsp(s, 150, (70, 52, 44), 'h')
    p = M.fi(t, 0.35, 0.9)
    if p > 0:
        im = M.tsp(s[:M.nchars(s, p)], 150, (70, 52, 44), 'h')
        U.paste(cv, im, 960 - full.width / 2, 520 - full.height / 2)
    a = M.eo(M.fi(t, 1.2, 0.5))
    sub = M.tsp('초식남녀 단편 애니메이션', 50, (150, 120, 100), 'h')
    U.paste(cv, sub, 960 - sub.width / 2, 680 - sub.height / 2, a)
    g = M.X('dgn0', 0.26, 0, True)
    U.paste(cv, g, 1600, 1080 - g.height + 40, M.eo(M.fi(t, 0.9, 0.5)))
    im = cv.convert('RGB')
    k = min(1, t / 0.5, (TITLE_S - t) / 0.45)
    return Image.blend(Image.new('RGB', (W, H)), im, max(0, k))

def ending(t):
    im = U.ui17(t).convert('RGB')
    if t > END_S - 0.6:
        im = Image.blend(im, Image.new('RGB', (W, H)), min(1, (t - (END_S - 0.6)) / 0.6))
    return im

def main(src, out, prev=None):
    if prev:
        os.makedirs(prev, exist_ok=True)
        for t in (0.3, 1.0, 2.0): title(t).save(os.path.join(prev, 'title_%.1f.png' % t))
        for t in (0.6, 2.0, 3.3): ending(t).save(os.path.join(prev, 'end_%.1f.png' % t))
        return
    total = TITLE_S + CUT / FPS + END_S
    delay = int(TITLE_S * 1000)
    af = 'adelay=%d|%d,apad,atrim=0:%.3f,afade=t=out:st=%.3f:d=1.5' % (delay, delay, total, total - 1.5)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                            '-r', str(FPS), '-i', '-', '-i', src, '-map', '0:v', '-map', '1:a', '-af', af,
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k', '-t', '%.3f' % total, out], stdin=subprocess.PIPE)
    for n in range(int(TITLE_S * FPS)):
        enc.stdin.write(title(n / FPS).tobytes())
    dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-frames:v', str(CUT), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    fsz = W * H * 3; k = 0
    while k < CUT:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz: break
        enc.stdin.write(buf); k += 1
    dec.wait()
    for n in range(int(END_S * FPS)):
        enc.stdin.write(ending(n / FPS).tobytes())
    enc.stdin.close(); enc.wait()
    print('done', out, 'frames from source:', k, 'total', total)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
