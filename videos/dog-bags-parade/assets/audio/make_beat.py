"""Synthesize the 10s, 120 BPM beat for the bag-parade clip.

Deterministic (seeded noise), pure standard library. Hits line up with the
composition: slams at 0.5s/1.0s, bag landings at 2-5s, chip pops at 6-8.75s,
final hit at 9.0s. Run: python3 make_beat.py  ->  parade-beat.wav
"""

import math
import os
import random
import struct
import wave

SR = 44100
DUR = 10.0
N = int(SR * DUR)
BEAT = 0.5
rng = random.Random(7)
buf = [0.0] * N
TWO_PI = 2 * math.pi


def noise():
    return rng.uniform(-1.0, 1.0)


def add(t0, dur, fn):
    i0 = max(0, int(t0 * SR))
    i1 = min(N, int((t0 + dur) * SR))
    state = {}
    for i in range(i0, i1):
        u = i / SR - t0
        buf[i] += fn(u, state)


def kick(t0, amp=0.9):
    def fn(u, s):
        f = 48 + 120 * math.exp(-u * 30)
        s["ph"] = s.get("ph", 0.0) + TWO_PI * f / SR
        click = noise() * math.exp(-u * 300) * 0.25
        return amp * (math.sin(s["ph"]) * math.exp(-u * 7) + click)

    add(t0, 0.4, fn)


def clap(t0, amp=0.32):
    def fn(u, s):
        n = noise()
        hp = n - s.get("prev", 0.0)
        s["prev"] = n
        bursts = sum(math.exp(-(u - d) * 180) for d in (0.0, 0.011, 0.022) if u >= d)
        return amp * hp * (0.5 * bursts + math.exp(-u * 22))

    add(t0, 0.25, fn)


def hat(t0, amp=0.1):
    def fn(u, s):
        n = noise()
        hp = n - s.get("prev", 0.0)
        s["prev"] = n
        return amp * hp * math.exp(-u * 90)

    add(t0, 0.07, fn)


def bass(t0, f, dur=0.25, amp=0.3, decay=5.0):
    def fn(u, s):
        ph = TWO_PI * f * u
        w = math.sin(ph) + 0.45 * math.sin(2 * ph) + 0.25 * math.sin(3 * ph) + 0.1 * math.sin(4 * ph)
        env = math.exp(-u * decay) * min(1.0, u / 0.004) * (1 - (u / dur) ** 4)
        return amp * w * env

    add(t0, dur, fn)


def stab(t0, freqs, dur=0.22, amp=0.07, decay=10.0):
    def fn(u, s):
        env = math.exp(-u * decay) * min(1.0, u / 0.003) * (1 - (u / dur) ** 4)
        v = 0.0
        for f in freqs:
            ph = TWO_PI * f * u
            v += math.sin(ph) + 0.3 * math.sin(2 * ph)
        return amp * env * v

    add(t0, dur, fn)


def whoosh(t_end, length=0.4, amp=0.3):
    def fn(u, s):
        p = u / length
        a = 0.97 - 0.4 * p
        y = a * s.get("y", 0.0) + (1 - a) * noise()
        s["y"] = y
        return amp * 6 * y * p * p

    add(t_end - length, length, fn)


def impact(t0, amp=0.55):
    def fn(u, s):
        f = 32 + 25 * math.exp(-u * 6)
        s["ph"] = s.get("ph", 0.0) + TWO_PI * f / SR
        y = 0.85 * s.get("y", 0.0) + 0.15 * noise()
        s["y"] = y
        return amp * (math.sin(s["ph"]) * math.exp(-u * 5) + 1.5 * y * math.exp(-u * 30))

    add(t0, 0.6, fn)


def pop(t0, amp=0.16, f0=620, f1=1300):
    def fn(u, s):
        f = f0 + (f1 - f0) * min(1.0, u / 0.05)
        s["ph"] = s.get("ph", 0.0) + TWO_PI * f / SR
        return amp * math.sin(s["ph"]) * math.exp(-u * 38) * min(1.0, u / 0.002)

    add(t0, 0.13, fn)


def crash(t0, amp=0.16, length=1.0):
    def fn(u, s):
        n = noise()
        hp = n - s.get("prev", 0.0)
        s["prev"] = n
        return amp * hp * math.exp(-u * 2.6)

    add(t0, length, fn)


# Chords per 2s bar: Am, F, C, G, Am.
BARS = [
    (55.00, (220.0, 261.63, 329.63)),
    (43.65, (174.61, 220.0, 261.63)),
    (65.41, (261.63, 329.63, 392.0)),
    (49.00, (196.0, 246.94, 293.66)),
    (55.00, (220.0, 261.63, 329.63)),
]

END_OF_GROOVE = 9.0
for k in range(int(END_OF_GROOVE / BEAT)):
    t = k * BEAT
    kick(t)
    if k % 2 == 1:
        clap(t)
    hat(t + BEAT / 2)
    root, chord = BARS[int(t // 2)]
    bass(t, root)
    bass(t + BEAT / 2, root * (2 if k % 4 == 3 else 1))
    stab(t + BEAT / 2, chord)

# Hook slams and bag landings.
for t in (0.5, 1.0):
    impact(t, amp=0.4)
for t in (2.0, 3.0, 4.0, 5.0):
    whoosh(t)
    impact(t)

# Finale pops: grid, then the delivery and payment chips.
for t in (6.0, 6.25, 6.5, 6.75):
    pop(t, amp=0.12, f0=500, f1=1000)
for t in (7.5, 8.0, 8.25, 8.5, 8.75):
    pop(t)

# Final hit and ring-out.
kick(9.0, amp=1.0)
impact(9.0, amp=0.6)
crash(9.0)
bass(9.0, 55.0, dur=1.0, amp=0.32, decay=1.6)
stab(9.0, (220.0, 261.63, 329.63), dur=1.0, amp=0.08, decay=1.4)

# Master: soft clip, peak-normalize, short fades.
drive = 1.2
out = [math.tanh(x * drive) / math.tanh(drive) for x in buf]
peak = max(abs(x) for x in out) or 1.0
gain = 0.89 / peak
fade_in, fade_out = int(0.005 * SR), int(0.2 * SR)
for i in range(N):
    g = gain
    if i < fade_in:
        g *= i / fade_in
    if i >= N - fade_out:
        g *= (N - i) / fade_out
    out[i] *= g

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parade-beat.wav")
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    frames = bytearray()
    for x in out:
        v = int(max(-1.0, min(1.0, x)) * 32767)
        frames += struct.pack("<hh", v, v)
    w.writeframes(bytes(frames))
print(path)
