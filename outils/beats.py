"""Grille de beats mesuree sur le signal (jamais estimee a l'oreille).

    python3 outils/beats.py assets/musique_22.wav --boucle 3

Sort : la duree exacte de la boucle et la liste des onsets, prets a coller
dans le dict B = dict(b1=..., on0=..., fort=...) de la video.
Erreur deja payee : boucle lue a 7,152 s au lieu de 7,1117 s -> tous les impacts
de la 2e moitie en retard de 40 ms sur les videos v7 a v9.
"""
import argparse
import sys

import numpy as np
import soundfile as sf


def enveloppe(x, sr, hop=256):
    """Enveloppe d'energie en dB, une valeur par hop."""
    if x.ndim > 1:
        x = x.mean(axis=1)
    n = len(x) // hop
    e = np.abs(x[:n * hop].reshape(n, hop)).max(axis=1)
    return 20 * np.log10(e + 1e-9), hop


def onsets(chemin, seuil_db=6.0, ecart_min=0.12):
    x, sr = sf.read(chemin)
    env, hop = enveloppe(x, sr)
    d = np.diff(env, prepend=env[0])
    pics = []
    dernier = -1e9
    for i in range(1, len(d) - 1):
        if d[i] > seuil_db and d[i] >= d[i - 1] and d[i] > d[i + 1]:
            t = i * hop / sr
            if t - dernier > ecart_min:
                pics.append(round(t, 4))
                dernier = t
    return pics, len(x) / sr


def duree_boucle(chemin, n_tours):
    """Duree d'un tour, mesuree par autocorrelation sur l'enveloppe."""
    x, sr = sf.read(chemin)
    env, hop = enveloppe(x, sr)
    env = env - env.mean()
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    total = len(x) / sr
    cible = total / max(1, n_tours)
    lo, hi = int(cible * 0.85 * sr / hop), int(cible * 1.15 * sr / hop)
    pic = lo + int(np.argmax(ac[lo:hi]))
    return pic * hop / sr, total


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("--boucle", type=int, default=0, help="nombre de tours dans le fichier")
    a = p.parse_args()
    pics, total = onsets(a.audio)
    print(f"duree fichier : {total:.4f} s · {len(pics)} onsets")
    if a.boucle:
        b, _ = duree_boucle(a.audio, a.boucle)
        print(f"BOUCLE mesuree : {b:.4f} s  ({a.boucle} tours = {b * a.boucle:.4f} s)")
        print(f"frames par boucle a 60 i/s : {b * 60:.2f}")
    print("B = dict(" + ", ".join(f"b{i+1}={t}" for i, t in enumerate(pics[:24])) + ")")
