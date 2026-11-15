"""Hushpad 영상 배경 음악을 코드로 합성한다 (샘플·외부 소리 없음 → 저작권 걱정 없는 직접 만든 곡).

python make_music.py          → music/hushpad_bgm_main.wav (79초), music/hushpad_bgm_shorts.wav (30초)
python make_music.py check    → 두 파일의 길이·통합 음량(LUFS)·트루 피크만 다시 잼

- 84 BPM, F장조. 부드러운 패드 + 가벼운 플럭 아르페지오 + 낮은 베이스, 합성 잔향.
- 훅(0~3.6초)은 낮은 패드 한 화음만 → 화면이 어두워질 때 음악이 잦아들고 부드러운 "쉬—" 소리 →
  로고가 나오는 순간(본편 4.95초, 쇼츠 4.24초)부터 곡이 시작. 끝 3초는 페이드아웃.
- 음량: 통합 약 -18 LUFS, 트루 피크 -6 dBTP 이하. 자막이 주인공이라 일부러 작게.
- 결과는 48 kHz 16비트 스테레오 WAV. render_video.py가 이 파일을 읽어 MP4에 AAC로 넣는다.
"""
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
OUT = HERE / "music"
SR = 48000
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
TARGET_LUFS = -18.0
PEAK_DBTP = -6.0

# 화음 (MIDI). 패드 4음 + 베이스 근음. F장조: Fmaj7 – Am7 – Dm7 – B♭maj7
CHORDS = [
    ([53, 57, 60, 64], 41),   # Fmaj7
    ([55, 57, 60, 64], 45),   # Am7
    ([53, 57, 60, 62], 38),   # Dm7
    ([53, 57, 58, 62], 46),   # B♭maj7
]
FINAL = ([53, 57, 60, 64, 67], 41)   # Fmaj9 — 끝 화음


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, r, sustain_len):
    """attack a초 → sustain → release r초 (전체 n 샘플)."""
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-3))
    rel_start = sustain_len
    e = np.where(t > rel_start, e * np.clip(1 - (t - rel_start) / r, 0, 1), e)
    return e * e  # 부드러운 곡선


def soft_saw(f, t, nharm=9, detune_cents=(-7, 0, 7), phase_seed=0):
    rng = np.random.default_rng(phase_seed)
    out = np.zeros_like(t)
    for c in detune_cents:
        ff = f * 2 ** (c / 1200)
        for k in range(1, nharm + 1):
            if ff * k > 9000:
                break
            out += np.sin(2 * np.pi * ff * k * t + rng.uniform(0, 2 * np.pi)) / k ** 1.6
    return out / len(detune_cents)


def lowpass(x, fc, order=2):
    sos = signal.butter(order, fc, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def add(buf, start, x):
    i = int(round(start * SR))
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def pad_chord(notes, dur, level=1.0, seed=0, cutoff=1400):
    rel = 1.6
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for i, m in enumerate(notes):
        v = soft_saw(hz(m), t, phase_seed=seed * 10 + i)
        pan = (i / max(1, len(notes) - 1) - 0.5) * 0.6
        out[:, 0] += v * (1 - pan)
        out[:, 1] += v * (1 + pan)
    out = lowpass(out, cutoff, 2)
    # 아주 느린 숨결 (트레몰로)
    out *= (0.9 + 0.1 * np.sin(2 * np.pi * 0.18 * t + seed))[:, None]
    out *= env_adsr(n, 0.9, rel, dur)[:, None]
    return out * level / len(notes)


def pluck(m, level, pan):
    dur = 1.6
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = (np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.18)
         + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.09))
    e = np.minimum(1, t / 0.006) * np.exp(-t / 0.38)
    x = x * e * level
    return np.stack([x * (1 - pan), x * (1 + pan)], axis=1)


def bass(m, dur, level):
    rel = 0.5
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.06) * (0.65 + 0.35 * np.exp(-t / 0.5))
    e = np.where(t > dur, e * np.clip(1 - (t - dur) / rel, 0, 1), e)
    x = x * e * level
    return np.stack([x, x], axis=1)


def shh(level):
    """부드러운 '쉬—' (걸러 낸 잡음). 실제 목소리 녹음이 아님."""
    dur = 1.15
    n = int(dur * SR)
    rng = np.random.default_rng(42)
    x = rng.standard_normal((n, 2))
    sos = signal.butter(4, [2300, 7500], "bandpass", fs=SR, output="sos")
    x = signal.sosfilt(sos, x, axis=0)
    x = lowpass(x, 6000, 2)
    t = np.arange(n) / SR
    e = np.clip(t / 0.14, 0, 1) ** 1.5 * np.clip((dur - t) / 0.75, 0, 1) ** 2
    x = x * e[:, None]
    return x / np.max(np.abs(x)) * level


def delay(x, secs, fb, mix):
    d = int(secs * SR)
    y = x.copy()
    tap = x
    for k in range(1, 6):
        tap = np.roll(tap, d, axis=0)
        tap[:d] = 0
        tap = tap[:, ::-1]  # 좌우로 번갈아 (ping-pong)
        y += tap * mix * fb ** (k - 1)
    return y


def reverb(x, secs=2.6, decay=0.75, mix=0.28):
    n = int(secs * SR)
    rng = np.random.default_rng(3)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t / decay * 3.0)[:, None]
    ir = lowpass(ir, 5000, 2)
    ir[: int(0.012 * SR)] = 0  # pre-delay
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return x * (1 - mix * 0.5) + wet * mix


# ---------------------------------------------------------------- 음량 (ITU-R BS.1770)
def lufs(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    ms = np.array([(y[i:i + blk] ** 2).mean(axis=0).sum() for i in range(0, len(y) - blk, hop)])
    ld = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[ld > -70]
    if not len(g):
        return -99.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = ms[(ld > -70) & (ld > rel)]
    return -0.691 + 10 * np.log10(g2.mean())


def true_peak_db(x):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.max(np.abs(up)) + 1e-12)


# ---------------------------------------------------------------- 곡
def compose(total, t_dark, t_shh, t_start):
    n = int(total * SR)
    pads = np.zeros((n, 2))
    plk = np.zeros((n, 2))
    low = np.zeros((n, 2))
    acc = np.zeros((n, 2))
    rng = np.random.default_rng(11)

    # 훅: 낮고 조용한 화음 하나 (화면이 어두워지면 잦아듦)
    intro = pad_chord([53, 60, 64], t_dark + 0.2, 0.55, seed=99, cutoff=900)
    fade = np.ones(len(intro))
    i0, i1 = int(t_dark * SR), int((t_dark + 0.35) * SR)
    fade[i0:i1] = np.linspace(1, 0, i1 - i0)
    fade[i1:] = 0
    add(pads, 0.0, intro * fade[:, None])
    add(acc, t_shh - 0.05, shh(0.55))

    # 본곡: 로고 시점부터 마디 단위
    end_body = total - 4.2           # 마지막 화음이 시작할 대략의 시각
    bars = max(1, int((end_body - t_start) / BAR))
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]      # 8분음표 아르페지오 (화음 안 음 순서)
    for b in range(bars):
        notes, root = CHORDS[b % 4]
        tb = t_start + b * BAR
        add(pads, tb, pad_chord(notes, BAR, 1.0, seed=b, cutoff=1300 + 300 * (b % 2)))
        if b >= 1:  # 베이스는 둘째 마디부터
            add(low, tb, bass(root, BAR * 0.92, 0.55))
        for s in range(8):
            if b == 0 and s < 2:
                continue
            if rng.random() < (0.3 if s % 2 else 0.12):
                continue   # 쉼표로 숨 쉴 틈
            m = notes[pattern[s]] + 12
            vel = (0.55 if s % 2 else 0.75) * rng.uniform(0.8, 1.0)
            add(plk, tb + s * BEAT / 2 + rng.uniform(-0.008, 0.008), pluck(m, vel, 0.35 if s % 2 else -0.35))
    tf = t_start + bars * BAR
    notes, root = FINAL
    add(pads, tf, pad_chord(notes, total - tf + 0.5, 1.0, seed=77, cutoff=1500))
    add(low, tf, bass(root, total - tf, 0.5))
    for s, (k, v) in enumerate(((4, 0.7), (2, 0.5), (1, 0.45))):
        add(plk, tf + s * BEAT, pluck(notes[k] + 12, v, (-0.3, 0.3, 0.0)[s]))

    plk = delay(plk, BEAT * 0.75, 0.32, 0.35)
    mix = pads * 0.55 + plk * 0.30 + low * 0.38 + acc * 0.42
    mix = reverb(mix, mix=0.30)
    # 전체 페이드 인/아웃
    t = np.arange(n) / SR
    fin = np.clip(t / 1.2, 0, 1) ** 2
    fout = np.clip((total - t) / 3.0, 0, 1) ** 1.5
    mix *= (fin * fout)[:, None]
    # 가벼운 고역 정리 + DC 제거
    mix = signal.sosfilt(signal.butter(1, 30, "high", fs=SR, output="sos"), mix, axis=0)
    mix = lowpass(mix, 12000, 2)
    return mix


def normalize(x):
    g = 10 ** ((TARGET_LUFS - lufs(x)) / 20)
    x = x * g
    tp = true_peak_db(x)
    if tp > PEAK_DBTP:
        x = x * 10 ** ((PEAK_DBTP - tp) / 20)
    return x


def write_wav(path, x):
    path.parent.mkdir(exist_ok=True)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, w.getnchannels())
    return x.astype(np.float64) / 32768


def report(path):
    x = read_wav(path)
    print(f"{path.name}: {len(x) / SR:.2f}s  {lufs(x):.1f} LUFS  true peak {true_peak_db(x):.1f} dBTP")


# 훅 시각은 render_video.py sc_hook()과 같아야 함 (장면 길이 D, k = D/7)
SPECS = {
    "main": dict(total=79.0, hook=7.0),
    "shorts": dict(total=30.0, hook=6.0),
}


def build(kind):
    s = SPECS[kind]
    k = s["hook"] / 7.0
    x = compose(s["total"], t_dark=3.6 * k, t_shh=3.75 * k, t_start=4.95 * k)
    x = normalize(x)
    out = OUT / f"hushpad_bgm_{kind}.wav"
    write_wav(out, x)
    report(out)


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        for kind in SPECS:
            report(OUT / f"hushpad_bgm_{kind}.wav")
    else:
        for kind in SPECS:
            build(kind)
