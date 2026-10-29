#!/usr/bin/env python3
"""〈만나기까지, 일주일〉 편집: AI 클립 + 휴대폰 화면 컷 + 자막 + 피아노 음악
AI 클립은 CLIPS 폴더에 cut01.mp4, cut03.mp4 ... 로 넣는다. 없는 컷은 장면 설명 카드로 대신한다.
python3 assemble_film.py CLIPS_DIR UI_DIR OUT.mp4 [narration.wav]
"""
import os, sys, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont
_a = list(sys.argv); sys.argv = ['x']
import make_dino_motion as M
sys.argv = _a

W, H, FPS = 1920, 1080, 24

SHOTS = [  # (번호, 종류, 길이, 설명)
    (1, 'AI', 5, '캠퍼스 벤치에 혼자 앉은 지호'), (2, 'UI', 5, 'ui02'), (3, 'AI', 5, '밤, 휴대폰을 엎어 놓고 한숨 쉬는 지호'),
    (4, 'UI', 5, 'ui04'), (5, 'AI', 5, '휴대폰을 다시 보다 살짝 웃는 지호'), (6, 'UI', 7, 'ui06'), (7, 'UI', 5, 'ui07'),
    (8, 'AI', 5, '알림을 보고 수락하는 서연'), (9, 'AI', 5, '도서관에서 메시지를 읽고 웃는 지호'),
    (10, 'AI', 5, '버스 창가에서 답장하는 서연'), (11, 'UI', 5, 'ui11'), (12, 'AI', 5, '밤, 휴대폰을 보며 웃는 지호'),
    (13, 'UI', 6, 'ui13'), (14, 'AI', 5, '카페 창가에서 문 쪽을 보는 지호'), (15, 'AI', 5, '카페에 들어와 두리번거리는 서연'),
    (16, 'AI', 5, '처음 같은 화면에, 마주 보고 웃는 두 사람'), (17, 'UI', 4, 'ui17')]

SUBS = [  # (시작, 끝, 문장, 종류) n=내레이션 d=대사
    (0.4, 4.8, '누군가를 만나고 싶었다.', 'n'),
    (5.3, 9.8, '그런데 처음 다가가는 일은 늘 어려웠다.', 'n'),
    (15.3, 19.8, '소개를 부탁할 사람도, 선뜻 꺼낼 용기도 많지 않았다.', 'n'),
    (20.3, 24.8, '그러다 알게 된 곳이 있었다.', 'n'),
    (25.3, 31.8, '학생증으로 인증하고, 내가 바라는 사람을 이야기하면 먼저 소개해 주는 곳.', 'n'),
    (42.3, 46.8, '"오늘 수업 어땠어요?"', 'd'),
    (47.3, 51.8, '"발표했는데 엄청 떨었어요."', 'd'),
    (52.3, 56.8, '"저도요. 끝나고 나서야 숨 쉬었어요."', 'd'),
    (62.3, 67.8, '사진은 몰랐지만, 내 이야기를 기다려 주는 사람이라는 건 알게 됐다.', 'n'),
    (73.3, 77.8, '"혹시... 초식남녀?"', 'd'),
    (78.3, 82.8, '"네. 안녕하세요."', 'd'),
]

@functools.lru_cache(None)
def NF(size):
    path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
    for idx in range(10):
        f = ImageFont.truetype(path, size, index=idx)
        if 'KR' in f.getname()[0]: return f

@functools.lru_cache(None)
def sub_img(s, kind):
    f = NF(46)
    col = (255, 255, 255) if kind == 'd' else (255, 236, 196)
    w = int(f.getlength(s)) + 60
    im = Image.new('RGBA', (w, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((w / 2, 45), s, font=f, fill=col, anchor='mm', stroke_width=4, stroke_fill=(20, 20, 24))
    return im

@functools.lru_cache(None)
def placeholder(num, desc):
    im = Image.new('RGB', (W, H), (54, 60, 74)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([360, 300, 1560, 780], 40, outline=(120, 128, 146), width=6)
    d.text((960, 420), '컷 %02d · AI 생성 예정' % num, font=NF(64), fill=(250, 214, 150), anchor='mm')
    d.text((960, 540), desc, font=NF(48), fill=(236, 238, 244), anchor='mm')
    d.text((960, 650), 'cut%02d.mp4 를 넣으면 이 자리에 들어갑니다' % num, font=NF(30), fill=(160, 166, 182), anchor='mm')
    return im

def clip_frames(path, n):
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', path, '-vf',
           'scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d' % (W, H, W, H, FPS),
           '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    k = len(raw) // (W * H * 3)
    frames = [Image.frombytes('RGB', (W, H), raw[i * W * H * 3:(i + 1) * W * H * 3]) for i in range(k)]
    while len(frames) < n: frames.append(frames[-1] if frames else Image.new('RGB', (W, H)))
    return frames

def main(clips, ui, out, narr=None):
    total = sum(s[2] for s in SHOTS)
    wav = out + '.music.wav'
    M.music(wav, total)
    audio_in = ['-i', wav]
    if narr:
        mix = out + '.mix.wav'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-i', narr, '-filter_complex',
                        '[0:a]volume=0.45[m];[1:a]volume=1.6[n];[m][n]amix=inputs=2:duration=first:normalize=0[a]', '-map', '[a]', mix], check=True)
        audio_in = ['-i', mix]
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
           *audio_in, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = 0.0; used = []
    for num, kind, du, desc in SHOTS:
        n = int(du * FPS)
        if kind == 'UI':
            frames = clip_frames(os.path.join(ui, desc + '.mp4'), n); used.append((num, 'UI'))
        else:
            f = os.path.join(clips, 'cut%02d.mp4' % num)
            if os.path.exists(f):
                frames = clip_frames(f, n); used.append((num, 'AI 클립'))
            else:
                frames = [placeholder(num, desc)] * n; used.append((num, '설명 카드'))
        for i, fr in enumerate(frames):
            t = t0 + i / FPS
            fr = fr.convert('RGBA')
            for a, b, s, k in SUBS:
                if a <= t <= b:
                    al = min(1, (t - a) / 0.25, (b - t) / 0.25)
                    im = sub_img(s, k)
                    M.put  # noqa
                    if al < 0.995:
                        im = im.copy(); im.putalpha(im.getchannel('A').point(M.LUT[int(max(0, al) * 100)]))
                    fr.alpha_composite(im, (int(W / 2 - im.width / 2), H - 150))
            if t < 0.6:
                fr = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), fr, t / 0.6)
            if t > total - 0.8:
                fr = Image.blend(fr, Image.new('RGBA', (W, H), (0, 0, 0, 255)), min(1, (t - (total - 0.8)) / 0.8))
            pr.stdin.write(fr.convert('RGB').tobytes())
        t0 += du
    pr.stdin.close(); pr.wait()
    for f in (wav, out + '.mix.wav'):
        if os.path.exists(f): os.remove(f)
    print('done', out, total)
    for u in used: print('컷 %02d: %s' % u)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
