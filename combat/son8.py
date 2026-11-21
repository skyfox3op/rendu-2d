"""Violon v8 : presto en sol mineur dans l'esprit de « L'Été » de Vivaldi (notes répétées, arpèges, gammes qui
dévalent), calé sur 92 bpm (triples croches de 0.0815 s), joué PAR-DESSUS le beat quand le héros joue."""
import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter

SR = 44100
Q = 60 / 92 / 8                       # triple croche = 0.0815 s
NOMS = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def freq(n):
    nom, oct_ = n[:-1], int(n[-1])
    return 440 * 2 ** ((NOMS[nom] + 12 * (oct_ + 1) - 69) / 12)


def note(f, dur, vol=1.0, pizz=False, rng=np.random.default_rng(1)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + .005 * np.sin(2 * np.pi * 6.2 * t) * np.clip((t - .12) / .2, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = sum((1 / k) * (1.3 if k in (2, 3) else 1.0) * np.sin(k * ph) for k in range(1, 14))
    if pizz:
        env = np.exp(-t / .09) * np.minimum(1, t / .004)
    else:
        att = min(.025, dur * .25)
        env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / min(.03, dur * .3))
    b, a = butter(2, [1800 / (SR / 2), 4500 / (SR / 2)], "band")
    bruit = lfilter(b, a, rng.normal(0, 1, n)) * (.0 if pizz else .07)
    return (s * .22 + bruit * np.minimum(1, t / .01)) * env * vol


def suite(seq):
    """seq : [(note | accord '+'-séparé, nb de triples croches, vol)]"""
    out = []
    for nom, nb, *v in seq:
        vol = v[0] if v else 1.0
        dur = nb * Q
        if nom == "-":
            out.append(np.zeros(int(dur * SR)))
        else:
            out.append(sum(note(freq(x), dur, vol) for x in nom.split("+")))
    return np.concatenate(out)


TREM_G = [("G4", 1)] * 8
TREM_D = [("D5", 1)] * 8
ARP_UP = [(n, 1) for n in ("G4", "Bb4", "D5", "G5", "Bb5", "D6", "Bb5", "G5")]
GAMME = [(n, 1) for n in ("A5", "G5", "F#5", "Eb5", "D5", "C5", "Bb4", "A4")]
ARP_D = [(n, 1) for n in ("D5", "F#5", "A5", "D6", "C6", "A5", "F#5", "D5")]
PRESTO = TREM_G + ARP_UP + GAMME + TREM_D + ARP_D + GAMME + [("G4", 2), ("D5", 2), ("G5", 4, 1.15)]
TRILLE = [("G5", 1), ("A5", 1)] * 3 + [("Bb5", 2, 1.2)]
MONTEE = [(n, 1) for n in ("G4", "A4", "Bb4", "C5", "D5", "Eb5", "F#5", "G5")] * 1 + ARP_UP


def presto(dur, seq=PRESTO, final=None):
    """Remplit `dur` secondes avec le motif (coupé net) ; `final` = dernière note tenue."""
    s = suite(seq)
    while len(s) < dur * SR:
        s = np.concatenate([s, suite(seq)])
    s = s[:int(dur * SR)]
    f = int(.03 * SR)
    s[-f:] *= np.linspace(1, 0, f)
    if final:
        s = np.concatenate([s, suite(final)])
    return s


def reverb(x, tail=1.2, mix=.22):
    n = int(tail * SR)
    ir = np.random.default_rng(3).normal(0, 1, n) * np.exp(-np.arange(n) / (SR * tail / 6))
    ir /= np.abs(ir).sum() / 8
    return x * (1 - mix) + fftconvolve(x, ir)[:len(x)] * mix


def mixer(fond, sortie, pistes, duck=.45):
    """pistes : [(t0, signal)] ; le beat baisse à `duck` pendant que le violon joue (il reste dynamique)."""
    y, sr = sf.read(fond)
    y = y.mean(1) if y.ndim > 1 else y
    g = np.ones_like(y)
    v = np.zeros(len(y) + SR * 4)
    for t0, s in pistes:
        i0, i1 = int(t0 * SR), int(t0 * SR) + len(s)
        f = int(.06 * SR)
        g[i0:i1] = np.minimum(g[i0:i1], duck)
        g[max(0, i0 - f):i0] = np.minimum(g[max(0, i0 - f):i0], np.linspace(1, duck, len(g[max(0, i0 - f):i0])))
        seg = g[i1:i1 + f]
        g[i1:i1 + f] = np.minimum(seg, np.linspace(duck, 1, len(seg)))
        v[i0:i0 + len(s)] += s
    v = reverb(v)[:len(y)]
    out = y * g + v * .62
    out /= max(1e-6, np.abs(out).max()) / .93
    sf.write(sortie, np.stack([out, out], 1), SR)


def pizz(n="D6"):
    return note(freq(n), .35, 1.3, pizz=True)


def accord():
    return suite([("G3+D4+Bb4+G5", 8, .9)]) * np.exp(-np.arange(int(8 * Q * SR)) / (SR * .9))
