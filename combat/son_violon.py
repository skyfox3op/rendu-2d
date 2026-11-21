"""Synthèse d'un violon (mélodie originale en ré mineur, 92 bpm) + mixage : la musique de fond s'efface
pendant que le personnage joue."""
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, lfilter

SR = 44100
NOTES = {"D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "Bb4": 466.16, "C5": 523.25,
         "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.0}


def note(f, dur, vol=1.0, rng=np.random.default_rng(1)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + .0045 * np.sin(2 * np.pi * 5.6 * t) * np.clip(t / .25, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = sum((1 / k) * (1.25 if k in (2, 3) else 1.0) * np.sin(k * ph) for k in range(1, 14))
    env = np.minimum(1, t / .07) * np.minimum(1, (dur - t) / .09)
    env *= .85 + .15 * np.sin(np.pi * np.clip(t / dur, 0, 1))
    b, a = butter(2, [1800 / (SR / 2), 4200 / (SR / 2)], "band")
    bruit = lfilter(b, a, rng.normal(0, 1, n)) * .05
    return (s * .22 + bruit) * env * vol


def phrase(seq, tempo=92):
    beat = 60 / tempo
    out = []
    for nom, nb, *v in seq:
        out.append(note(NOTES[nom], nb * beat, v[0] if v else 1.0))
    return np.concatenate(out)


PHRASE_A = [("D5", .75), ("F5", .5), ("A5", .5), ("G5", .75), ("F5", .5), ("E5", .5), ("D5", 1.25, 1.1)]
PHRASE_B = [("A4", .5), ("D5", .5), ("F5", .5), ("A5", .5, 1.15)]


def reverb(x, tail=1.4, mix=.28):
    n = int(tail * SR)
    ir = np.random.default_rng(3).normal(0, 1, n) * np.exp(-np.arange(n) / (SR * tail / 6))
    ir /= np.abs(ir).sum() / 8
    return x * (1 - mix) + fftconvolve(x, ir)[:len(x)] * mix


def mixer(fond, sortie, fenetres):
    """fenetres : [(t0, t1, phrase)] : la musique de fond descend à 12 % pendant t0..t1, le violon joue."""
    y, sr = sf.read(fond)
    assert sr == SR
    y = y.mean(1) if y.ndim > 1 else y
    duck = np.ones_like(y)
    v = np.zeros(len(y) + SR * 3)
    for t0, t1, ph in fenetres:
        i0, i1 = int(t0 * SR), int(t1 * SR)
        f = int(.12 * SR)
        duck[i0:i1] = .12
        duck[i0:i0 + f] = np.linspace(1, .12, f)
        duck[i1 - f:i1] = np.linspace(.12, 1, f)
        s = phrase(ph)
        v[i0:i0 + len(s)] += s
    v = reverb(v)[:len(y)]
    out = y * duck + v * .55
    out /= max(1e-6, np.abs(out).max()) / .92
    sf.write(sortie, np.stack([out, out], 1), SR)


if __name__ == "__main__":
    mixer("musique_longue.wav", "musique_violon.wav", [(3.30, 6.50, PHRASE_A), (13.10, 14.40, PHRASE_B)])
    print(len(phrase(PHRASE_A)) / SR, len(phrase(PHRASE_B)) / SR)
