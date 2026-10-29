#!/usr/bin/env python3
"""〈만나기까지, 일주일〉 0.8배 슬로우 완성본: 오프닝(원속도) + 본편 16장면(슬로우) + 엔딩(원속도),
클로바더빙 내레이션을 원래 빠르기로 재배치, 피아노 배경음악 + 더킹
python3 assemble_slow.py SLOW_DIR NARR_DIR ONSETS_JSON OUT.mp4
"""
import sys, os, json, glob, subprocess
import numpy as np
from PIL import Image
_a = list(sys.argv); sys.argv = ['x']
import make_dino_motion as M
import finalize_film as FF
sys.argv = _a
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d

W, H, FPS = 1920, 1080, 30
SPEED = 0.8
TITLE_S, END_S = FF.TITLE_S, FF.END_S
N_SHOTS, SHOT_IN = 16, 4.0
MID_S = N_SHOTS * SHOT_IN / SPEED          # 80초
TOTAL = TITLE_S + MID_S + END_S             # 87.5초
SR = 44100

def ending(t):
    im = FF.ending(t).convert('RGBA')
    a = M.eo(M.fi(t, 1.6, 0.6))
    if t > END_S - 0.6: a *= max(0, 1 - (t - (END_S - 0.6)) / 0.6)
    cr = M.tsp('음성: 네이버 클로바더빙', 30, (150, 132, 118), 'h')
    FF.U.paste(im, cr, W - cr.width - 40, H - cr.height - 26, a)
    return im.convert('RGB')

def build_audio(narr_dir, onsets, path):
    music_wav = path + '.music.wav'
    M.music(music_wav, TOTAL)
    _, mus = wavfile.read(music_wav); os.remove(music_wav)
    mus = mus.astype(np.float32) / 32768
    n = int(TOTAL * SR)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    voice = np.zeros(n, np.float32)
    placed = []
    for f in sorted(glob.glob(os.path.join(narr_dir, '*.mp3'))):
        name = os.path.basename(f)
        t_old = onsets[name]
        t_new = TITLE_S + (t_old - TITLE_S) / SPEED
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32)
        i0 = int(t_new * SR); i1 = min(n, i0 + len(x))
        voice[i0:i1] += x[:i1 - i0]
        placed.append((name, round(t_new, 2), round(len(x) / SR, 2)))
    voice = voice / (np.abs(voice).max() + 1e-6) * 0.9
    env = uniform_filter1d((np.abs(voice) > 0.02).astype(np.float32), int(0.6 * SR))
    env = np.clip(env * 3, 0, 1)
    mus_gain = 0.42 * (1 - 0.55 * env)          # 목소리가 나올 때 음악을 줄임
    mix = mus * mus_gain[:, None] / (np.abs(mus).max() + 1e-6) + voice[:, None] * 0.85
    mix = mix / (np.abs(mix).max() + 1e-6) * 0.89
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))
    return placed

def main(slow_dir, narr_dir, onsets_json, out):
    onsets = json.load(open(onsets_json))
    wav = out + '.wav'
    placed = build_audio(narr_dir, onsets, wav)
    for p in placed: print('voice', p)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                            '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], stdin=subprocess.PIPE)
    for k in range(int(TITLE_S * FPS)):
        enc.stdin.write(FF.title(k / FPS).tobytes())
    fsz = W * H * 3
    per = int(SHOT_IN / SPEED * FPS)
    for i in range(N_SHOTS):
        f = os.path.join(slow_dir, 'slow_%d.mp4' % i)
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', f, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        frames = [raw[j * fsz:(j + 1) * fsz] for j in range(len(raw) // fsz)]
        if not frames: raise SystemExit('missing ' + f)
        while len(frames) < per: frames.append(frames[-1])
        for fr in frames[:per]: enc.stdin.write(fr)
    for k in range(int(END_S * FPS)):
        enc.stdin.write(ending(k / FPS).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print('done', out, TOTAL)

if __name__ == '__main__':
    main(*sys.argv[1:5])
