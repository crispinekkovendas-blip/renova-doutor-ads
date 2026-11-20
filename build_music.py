"""Soft background music made on this PC from scratch (no downloads, so no licence to worry about).

    python -X utf8 build_music.py OUT.wav SECONDS [TURN]

TURN (seconds) is where a story ad cuts from the problem to the solution: before it the
music is sparse (one held chord and a quiet pulse), after it the full, warmer part starts.
Without TURN the full part plays from the start.

The notes: four chords in C major (C, G, A minor, F), an electric-piano style arpeggio,
a soft pad underneath and a bass note per bar. 96 beats per minute.
"""
import pathlib
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BEAT = 60.0 / 96
BAR = 4 * BEAT

CHORDS = [                           # (bass note, chord notes) as MIDI numbers
    (48, [52, 55, 60, 62, 64]),      # C add9
    (47, [50, 55, 59, 62, 67]),      # G over B
    (45, [52, 55, 57, 60, 64]),      # A minor 7
    (41, [53, 57, 60, 64, 67]),      # F major 9
]                                    # bass kept above 85 Hz: phone speakers cannot play lower notes
ARP = [0, 2, 3, 2, 4, 2, 3, 1]       # which chord note plays on each half beat
ARP_VEL = [1.0, 0.55, 0.7, 0.55, 0.85, 0.55, 0.7, 0.5]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def clock(seconds):
    return np.arange(int(seconds * SR)) / SR


def epiano(midi, seconds, vel=1.0):
    t = clock(seconds)
    f = hz(midi)
    index = 1.1 * vel * np.exp(-t / 0.18) + 0.22
    tone = np.sin(2 * np.pi * f * t + index * np.sin(2 * np.pi * f * t))
    return tone * np.exp(-t / 0.95) * (1 - np.exp(-t / 0.004)) * vel


def pad(midi, seconds, attack=0.5, release=0.8):
    t = clock(seconds)
    f = hz(midi)
    tone = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t + 1.0)
            + 0.16 * np.sin(2 * np.pi * 2 * f * t + 0.4))
    env = np.ones_like(t)
    a, r = int(attack * SR), int(release * SR)
    env[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    env[-r:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(r) / r)
    return tone * env


def bass(midi, seconds):
    t = clock(seconds)
    f = hz(midi)
    tone = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)
    return tone * np.exp(-t / 1.1) * (1 - np.exp(-t / 0.015))


def put(mix, sound, at, gain, pan=0.0):
    """Adds a sound to the stereo mix at a time in seconds; pan -1 is left, +1 is right."""
    start = int(at * SR)
    if start >= mix.shape[0] or start < 0:
        return
    sound = sound[: mix.shape[0] - start]
    left, right = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    mix[start:start + len(sound), 0] += sound * gain * left
    mix[start:start + len(sound), 1] += sound * gain * right


def make(seconds, turn=None):
    rng = np.random.default_rng(7)
    mix = np.zeros((int((seconds + 2.5) * SR), 2))
    start = turn or 0.0

    if turn:                                   # the sparse opening of a story ad
        for k, m in enumerate([45, 52, 57, 60]):
            put(mix, pad(m, turn + 0.9, attack=0.3, release=1.2), 0.0, 0.085, pan=(-0.4, 0.3, -0.2, 0.4)[k])
        put(mix, bass(45, min(turn, 4.0)), 0.05, 0.16)
        steps = int((turn - 0.15) / (BEAT / 2))
        for n in range(steps, 0, -1):          # a quiet rocking figure that lands exactly on the turn
            when = turn - n * BEAT / 2
            vel = 0.24 + 0.2 * (1 - n / max(1, steps))
            put(mix, epiano((64, 60, 64, 57)[n % 4], 0.7, vel), when, 0.33, pan=0.15 if n % 2 else -0.15)

    bar = 0
    while start + bar * BAR < seconds:
        at = start + bar * BAR
        root, notes = CHORDS[bar % 4]
        for k, m in enumerate(notes[:4]):
            put(mix, pad(m, BAR + 0.7), at - 0.1 if at > 0.1 else at, 0.07, pan=(-0.5, 0.4, -0.25, 0.5)[k])
        put(mix, bass(root, 2.2 * BEAT), at, 0.24)
        put(mix, bass(root, 1.2 * BEAT), at + 2.5 * BEAT, 0.14)
        for step in range(8):
            when = at + step * BEAT / 2 + rng.uniform(-0.004, 0.004)
            put(mix, epiano(notes[ARP[step]], 1.6, ARP_VEL[step]), when, 0.3, pan=0.3 if step % 2 else -0.3)
        if bar % 2 == 1:                        # a small answer phrase high up, every second bar
            put(mix, epiano(notes[4] + 12, 1.8, 0.55), at + 3 * BEAT, 0.2, pan=0.1)
        bar += 1

    # room sound: the mix played through a short decaying burst of noise
    t = clock(1.8)
    wet = np.zeros_like(mix)
    low = butter(2, 4500, "low", fs=SR, output="sos")
    for ch in range(2):
        burst = sosfilt(low, rng.standard_normal(len(t)) * np.exp(-t / 0.45))
        burst /= np.sqrt(np.sum(burst ** 2))
        wet[:, ch] = fftconvolve(mix[:, ch], burst)[: mix.shape[0]]
    mix = mix + 0.3 * wet

    mix = sosfilt(butter(2, 9000, "low", fs=SR, output="sos"), mix, axis=0)
    mix = sosfilt(butter(2, 70, "high", fs=SR, output="sos"), mix, axis=0)
    mix = mix[: int(seconds * SR)]
    fade_in, fade_out = int(0.12 * SR), int(1.3 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    mix[-fade_out:] *= (0.5 + 0.5 * np.cos(np.pi * np.arange(fade_out) / fade_out))[:, None]
    return mix / np.max(np.abs(mix)) * 0.7


def write(path, seconds, turn=None):
    path = pathlib.Path(path)
    wavfile.write(str(path), SR, (make(seconds, turn) * 32767).astype(np.int16))
    return path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)
    print(write(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else None))
