"""Planche de contact : un PNG qui resume la video, pour la juger sans la regarder.

    python3 outils/qa_planche.py out/dague_v11.mp4 evenements.json --dossier qa/

evenements.json = ce que la choregraphie connait deja :
    [{"t": 1.184, "nom": "12 taille aerienne", "type": "contact"}, ...]
    type : armement | contact | reaction | special

Sort 3 planches (ffmpeg seul, aucune dependance Python) :
  planche_couleur.png     -> juger la composition et les VFX
  planche_silhouette.png  -> juger la LISIBILITE du coup (noir plein, seuil)
  planche_gris.png        -> juger la hierarchie de valeur (le heros doit ressortir)

La planche silhouette est celle qui attrape les deux defauts les plus couteux :
deux coups qui se ressemblent, et deux corps fusionnes au contact.
"""
import argparse
import json
import math
import os
import subprocess


def extraire(video, t, sortie, legende=None, mode="couleur"):
    filtres = []
    if mode == "silhouette":
        # tout ce qui est au-dessus du seuil devient blanc, le reste noir
        filtres.append("format=gray,lutyuv=y='if(gt(val,90),255,0)'")
    elif mode == "gris":
        filtres.append("format=gray")
    filtres.append("scale=270:480")
    if legende:
        txt = legende.replace(":", "\\:").replace("'", "")
        filtres.append(f"drawbox=0:0:270:34:black@0.75:t=fill,"
                       f"drawtext=text='{txt}':x=6:y=7:fontsize=18:fontcolor=white")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", video,
                    "-vf", ",".join(filtres), "-frames:v", "1", sortie], check=True)


def planche(video, evenements, dossier, mode, fps=60):
    tmp = os.path.join(dossier, f"_v_{mode}")
    os.makedirs(tmp, exist_ok=True)
    for i, e in enumerate(evenements):
        f = int(round(e["t"] * fps))
        extraire(video, e["t"], f"{tmp}/v{i:03d}.png",
                 f"{i+1}. {e.get('nom','')} f{f}", mode)
    n = len(evenements)
    cols = min(6, max(1, int(math.ceil(math.sqrt(n * 480 / 270)))))
    rows = int(math.ceil(n / cols))
    sortie = os.path.join(dossier, f"planche_{mode}.png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{tmp}/v%03d.png",
                    "-vf", f"tile={cols}x{rows}:padding=4:color=0x202024",
                    "-frames:v", "1", sortie], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return sortie


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("evenements")
    p.add_argument("--dossier", default="qa")
    p.add_argument("--fps", type=int, default=60)
    a = p.parse_args()
    os.makedirs(a.dossier, exist_ok=True)
    ev = json.load(open(a.evenements))
    for mode in ("couleur", "silhouette", "gris"):
        print(planche(a.video, ev, a.dossier, mode, a.fps))
    print(f"{len(ev)} evenements · a soumettre a l'oeil exterieur "
          f"(12-QA-AUTONOME/02-oeil-exterieur/PROMPT.md)")
