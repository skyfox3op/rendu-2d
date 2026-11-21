"""v13 — audio : musique étendue (boucles de 7.1117 s) + bruitages SYNTHÉTISÉS (aucun fichier externe),
mixés bas sous la musique ; coupure de la musique pour les moments de silence (final)."""
import math

import numpy as np
import soundfile as sf

SR = 44100
P = 7.1117


def musique(n_boucles=6, src="musique_22.wav"):
    """Boucle 0 + (n-2) fois la boucle 1 + boucle 2 et la queue -> n boucles. Fondus de 8 ms aux raccords."""
    x, sr = sf.read(src)
    assert sr == SR
    p = int(round(P * SR))
    b0, b1, fin = x[:p], x[p:2 * p], x[2 * p:]
    parts = [b0] + [b1] * (n_boucles - 2) + [fin]
    out = parts[0]
    f = int(.008 * SR)
    for q in parts[1:]:
        w = np.linspace(0, 1, f)[:, None]
        mid = out[-f:] * (1 - w) + q[:f] * w
        out = np.concatenate([out[:-f], mid, q[f:]])
    return out


def _env(n, a=.002, d=.2, courbe=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-courbe * t / max(d, 1e-4))
    return e


def _bruit(n, rng):
    return rng.standard_normal(n)


def _passe_bas(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def _pb_rapide(x, fc):
    """Passe-bas 1er ordre vectorisé (approximatif) via scipy."""
    from scipy.signal import lfilter
    a = math.exp(-2 * math.pi * fc / SR)
    return lfilter([1 - a], [1, -a], x)


def _ph(x, fc):
    return x - _pb_rapide(x, fc)


def _bande(x, f1, f2):
    return _pb_rapide(_ph(x, f1), f2)


def clang(rng, f0=1800, dur=.6, force=1.0):
    """Choc métal : partiels inharmoniques qui décroissent + attaque de bruit."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k, (r, a, d) in enumerate(((1, 1, .35), (2.76, .6, .22), (5.4, .4, .15), (8.93, .25, .1), (1.5, .3, .3))):
        s += a * np.sin(2 * math.pi * f0 * r * (1 + rng.uniform(-.01, .01)) * t) * np.exp(-t / (d * dur / .6))
    s += .8 * _ph(_bruit(n, rng), 2000) * _env(n, .0005, .015)
    return force * s * .5


def impact(rng, dur=.35, force=1.0, grave=70):
    """Coup sourd : sinus grave glissant + bruit filtré."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = grave * (1 + 1.5 * np.exp(-t / .03))
    s = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / .12)
    s += .6 * _pb_rapide(_bruit(n, rng), 1200) * _env(n, .001, .06)
    return force * s * .8


def tranche(rng, dur=.25, force=1.0):
    """Lame qui tranche : souffle aigu court + « shing »."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = _bande(_bruit(n, rng), 2500, 9000) * np.sin(np.pi * np.minimum(1, t / dur)) ** 2
    s += .25 * np.sin(2 * math.pi * 5200 * t) * np.exp(-t / .08)
    return force * s * .7


def souffle(rng, dur=.4, force=1.0, montee=True, f1=300, f2=3000):
    """Whoosh : bruit filtré dont la bande glisse."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    x = _bruit(n, rng)
    nb = 8
    for k in range(nb):
        u = (k + .5) / nb
        fc = f1 * (f2 / f1) ** (u if montee else 1 - u)
        seg = _bande(x, fc * .7, fc * 1.4)
        w = np.exp(-((t / dur - u) ** 2) / .02)
        s += seg * w
    s *= np.sin(np.pi * t / dur)
    return force * s * .8


def cape(rng, dur=.35, force=1.0):
    """Claquement de tissu : rafales de bruit grave modulé."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    mod = (1 + np.sin(2 * math.pi * 23 * t + rng.uniform(0, 6))) * .5
    s = _bande(_bruit(n, rng), 120, 1500) * mod * np.sin(np.pi * t / dur)
    return force * s * .9


def tir(rng, dur=.5, force=1.0):
    """Coup de feu (pistolet / mousquet) : claquement + queue grave."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = _bruit(n, rng) * np.exp(-t / .02)
    s += .7 * _pb_rapide(_bruit(n, rng), 600) * np.exp(-t / .12)
    s += .5 * np.sin(2 * math.pi * 90 * t) * np.exp(-t / .08)
    return force * s * .8


def corde(rng, dur=.6, force=1.0, f0=110):
    """Corde d'arc qui claque (twang)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + .3 * np.exp(-t / .02))
    ph = 2 * math.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + .5 * np.sin(2 * ph) + .3 * np.sin(3 * ph)) * np.exp(-t / .18)
    s += .5 * _ph(_bruit(n, rng), 3000) * np.exp(-t / .01)
    return force * s * .5


def sifflement(rng, dur=.5, force=1.0, f1=2500, f2=900):
    """Flèche / projectile qui fend l'air (glissando)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 * (f2 / f1) ** (t / dur)
    s = np.sin(2 * math.pi * np.cumsum(f) / SR) * .3 + _bande(_bruit(n, rng), 1500, 6000) * .6
    return force * s * np.sin(np.pi * t / dur) * .6


def fil(rng, dur=.5, force=1.0, f0=3200):
    """Fil d'ombre qui se tend (zing métallique aigu)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + .5 * (1 - np.exp(-t / .05)))
    s = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / .25) * .4
    s += _bande(_bruit(n, rng), 4000, 12000) * np.exp(-t / .04) * .4
    return force * s


def grondement(rng, dur=2.0, force=1.0, f0=38):
    """Grondement grave (invocation)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * math.pi * f0 * t + 3 * np.sin(2 * math.pi * .7 * t)) * .6
    s += _pb_rapide(_bruit(n, rng), 160) * 3
    s *= np.minimum(1, t / (dur * .6)) * np.minimum(1, (dur - t) / .2)
    return force * s * .7


def aspiration(rng, dur=1.5, force=1.0):
    """Aspiration (whoosh inversé qui monte et coupe net)."""
    s = souffle(rng, dur, force, montee=True, f1=80, f2=6000)
    n = len(s)
    t = np.arange(n) / SR
    return s * (t / (dur)) ** 2 * 1.6


def explosion(rng, dur=3.0, force=1.0):
    """Grosse explosion : attaque énorme, grave long, crépitements."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = _bruit(n, rng) * np.exp(-t / .05) * 1.2
    s += _pb_rapide(_bruit(n, rng), 300) * np.exp(-t / .9) * 6
    s += np.sin(2 * math.pi * (45 + 60 * np.exp(-t / .2)) * t) * np.exp(-t / .7) * .9
    cr = (rng.random(n) > .9993).astype(float) * rng.uniform(-1, 1, n)
    s += _ph(cr, 2000) * 4 * np.exp(-t / 1.2)
    return force * s * .7


def tintement(rng, dur=.8, force=1.0):
    """Petites étoiles qui scintillent (cloches aiguës)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(5):
        t0 = rng.uniform(0, dur * .5)
        f = rng.uniform(2500, 5200)
        m = t >= t0
        s[m] += np.sin(2 * math.pi * f * (t[m] - t0)) * np.exp(-(t[m] - t0) / .15) * .3
    return force * s


def coeur(rng, dur=.5, force=1.0):
    """Battement sourd (tension)."""
    s = impact(rng, .25, .7, grave=48)
    n = int(dur * SR)
    out = np.zeros(n)
    out[:len(s)] += s
    k = int(.18 * SR)
    out[k:k + len(s)] += .7 * s[:n - k]
    return force * out


SONS = dict(clang=clang, impact=impact, tranche=tranche, souffle=souffle, cape=cape, tir=tir, corde=corde,
            sifflement=sifflement, fil=fil, grondement=grondement, aspiration=aspiration, explosion=explosion,
            tintement=tintement, coeur=coeur)


def mixer(sorties, duree, mus, evenements, silences=(), vol_sfx=.32, graine=7):
    """evenements = liste (t, nom, kwargs). silences = [(t0, t1)] -> musique coupée (fondus 60 ms)."""
    rng = np.random.default_rng(graine)
    n = int(duree * SR) + 1
    m = np.zeros((n, 2))
    k = min(n, len(mus))
    m[:k] = mus[:k]
    g = np.ones(n)
    for t0, t1 in silences:
        a, b = int(t0 * SR), int(t1 * SR)
        f = int(.06 * SR)
        g[a:b] = 0
        g[max(0, a - f):a] = np.minimum(g[max(0, a - f):a], np.linspace(1, 0, a - max(0, a - f)))
        if b < n:
            e = min(n, b + f)
            g[b:e] = np.minimum(g[b:e], np.linspace(0, 1, e - b))
    m *= g[:, None]
    fx = np.zeros((n, 2))
    for t, nom, kw in evenements:
        s = SONS[nom](rng, **kw)
        a = int(t * SR)
        if a >= n:
            continue
        s = s[:n - a]
        pan = kw.get("pan", 0) if False else rng.uniform(-.25, .25)
        fx[a:a + len(s), 0] += s * (1 - pan)
        fx[a:a + len(s), 1] += s * (1 + pan)
    out = m + fx * vol_sfx
    pk = np.abs(out).max()
    if pk > .98:
        out *= .98 / pk
    sf.write(sorties, out, SR)
    return out
