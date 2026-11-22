"""Decoupage du rendu en segments independants + recollage sans reencodage.

Principe : dessiner la frame f ne depend que de t = f/FPS. Tout l'etat sequentiel
(particules, fumee, taches) doit etre reseede par frame -> voir graine().
Un segment est alors rendu seul, et identique au meme passage d'un rendu complet.

Usage (local, N coeurs) :
    python3 outils/rendu_parallele.py videos/dague.py sortie.mp4 --n 8
Usage (ferme GitHub Actions) : voir .github/workflows/rendu.yml

Le renderer de la video doit exposer :
    rendre_segment(f0, f1, sortie_sans_audio)   # frames [f0, f1[
Patch a appliquer une fois dans chaque moteurNN.rendre() : voir
VAULT-2D/10-PIPELINE-RENDU/01-architecture/FICHE.md § Procedure.
"""
import math
import os
import subprocess


def graine(seed_video: int, f: int):
    """RNG deterministe par frame. Remplace tout default_rng(seed) global.

    Deux appels avec le meme (seed_video, f) donnent la meme sequence, donc un
    segment rendu seul contient exactement les memes particules qu'un rendu complet.
    """
    import numpy as np                      # importe ici : le montage n'a pas besoin de numpy
    return np.random.default_rng((seed_video * 1_000_003 + f) & 0xFFFFFFFF)


def plan_segments(n_frames: int, n_jobs: int, fps: int = 60):
    """Bornes de frames par segment, equilibrees. Retourne [(i, f0, f1), ...]."""
    taille = math.ceil(n_frames / n_jobs)
    out = []
    for i in range(n_jobs):
        f0 = i * taille
        f1 = min(n_frames, f0 + taille)
        if f0 < f1:
            out.append((i, f0, f1))
    return out


# --- encodage : rapide pour les segments, une seule passe de qualite a la fin ---

def ecrivain_segment(chemin, w=1080, h=1920, fps=60):
    """Encodeur de segment : ultrafast, crf 14 (intermediaire quasi sans perte).

    Chaque segment commence par un keyframe -> le recollage se fait en -c copy.
    """
    return subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "14",
         "-g", "9999", "-force_key_frames", "expr:eq(n,0)",
         "-pix_fmt", "yuv420p", chemin], stdin=subprocess.PIPE)


def recoller(segments, sortie_video):
    """Concatene les segments sans reencoder (ffmpeg concat demuxer)."""
    liste = os.path.join(os.path.dirname(sortie_video) or ".", "_segments.txt")
    with open(liste, "w") as f:
        for s in segments:
            f.write(f"file '{os.path.abspath(s)}'\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", liste, "-c", "copy", sortie_video], check=True)
    os.remove(liste)
    return sortie_video


def finaliser(sortie_video, audio, sortie, duree=None):
    """Passe finale unique : qualite de diffusion + audio. veryfast/crf 18.

    La plateforme reencode de toute facon : au-dela de crf 18 on paie du temps pour rien.
    """
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", sortie_video, "-i", audio,
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k"]
    if duree:
        cmd += ["-t", f"{duree:.3f}"]
    subprocess.run(cmd + [sortie], check=True)
    return sortie


def verifier_determinisme(rendre_segment, f0, f1, tmp="_det"):
    """Rend [f0,f1[ seul puis en deux moities : les images doivent etre identiques.

    A lancer une fois apres le patch du moteur. Sans ce test, les segments
    peuvent differer aux jointures (particules desynchronisees).
    """
    os.makedirs(tmp, exist_ok=True)
    a = f"{tmp}/entier.mp4"
    b1, b2 = f"{tmp}/a.mp4", f"{tmp}/b.mp4"
    rendre_segment(f0, f1, a)
    m = (f0 + f1) // 2
    rendre_segment(f0, m, b1)
    rendre_segment(m, f1, b2)
    b = recoller([b1, b2], f"{tmp}/deux.mp4")
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a, "-i", b,
                        "-filter_complex", "psnr", "-f", "null", "-"],
                       capture_output=True, text=True)
    return r.stderr.strip() or "identique"
