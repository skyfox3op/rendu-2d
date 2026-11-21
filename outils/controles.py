"""Les 7 controles geometriques : tout ce qui se verifie SANS regarder une image.

Ils tournent avant le rendu, sur un dump de la choregraphie :
    python3 videos/dague.py --dump dague.json     # a implementer une fois par moteur
    python3 outils/controles.py dague.json

Format du dump (une entree par frame) :
{
 "fps": 60, "sol": 1500,
 "beats": [0.093, 0.534, ...],
 "frames": [
   {"f": 0,
    "acteurs": [{"nom":"h", "torse":[x,y], "bassin":[x,y], "pieds":[[x,y],[x,y]],
                 "main_arme":[x,y], "avant_bras":[x,y], "au_sol":[true,false]}],
    "armes":    [{"acteur":"h", "poignee":[x,y], "pointe":[x,y]}],
    "impacts":  [{"t":1.184, "issue":"touche", "cible":[x,y], "arme":"h"}]}
 ]
}

Sortie : une ligne par controle, code de retour 1 si un seul echoue.
Aucun rendu complet ne doit etre lance avant 7/7.
"""
import argparse
import json
import math
import sys

SEUIL_PRISE = 4.0        # px entre la main et la poignee
SEUIL_POIGNET = 80.0     # degres entre la main-arme et l'avant-bras
SEUIL_PATINAGE = 3.0     # px de deplacement d'un pied declare au sol
SEUIL_VITESSE = 450.0    # px/s au sol hors dash
SEUIL_BEAT = 1           # frames d'ecart impact/beat
SEUIL_TORSE = 18.0       # px de chevauchement de torses


def ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def ecart_angle(u, v):
    return abs((u - v + 180) % 360 - 180)


def controles(d):
    fps = d.get("fps", 60)
    frames = d["frames"]
    pb = {k: [] for k in ("prise", "poignet", "patinage", "vitesse",
                          "beats", "contact", "torses")}

    for fr in frames:
        f = fr["f"]
        par_nom = {a["nom"]: a for a in fr.get("acteurs", [])}
        # 1. prise : la poignee est dans la main
        # 2. poignet : la main ne casse pas
        for w in fr.get("armes", []):
            a = par_nom.get(w["acteur"])
            if not a:
                continue
            m = a["main_arme"]
            dist = math.dist(m, w["poignee"])
            if dist > SEUIL_PRISE:
                pb["prise"].append(f"f{f} {w['acteur']} main-poignee {dist:.1f}px")
            da = ecart_angle(ang(w["poignee"], w["pointe"]), ang(a["avant_bras"], m))
            if da > SEUIL_POIGNET:
                pb["poignet"].append(f"f{f} {w['acteur']} poignet {da:.0f}deg")
        # 7. torses qui se chevauchent
        acts = fr.get("acteurs", [])
        for i in range(len(acts)):
            for j in range(i + 1, len(acts)):
                if math.dist(acts[i]["torse"], acts[j]["torse"]) < SEUIL_TORSE:
                    pb["torses"].append(f"f{f} {acts[i]['nom']}/{acts[j]['nom']}")

    # 3. patinage et 4. sauts de position
    for p, q in zip(frames, frames[1:]):
        pn = {a["nom"]: a for a in p.get("acteurs", [])}
        for a in q.get("acteurs", []):
            b = pn.get(a["nom"])
            if not b:
                continue
            for k, (pied, au_sol) in enumerate(zip(a["pieds"], a.get("au_sol", []))):
                if au_sol and b.get("au_sol", [])[k:k + 1] == [True]:
                    if abs(pied[0] - b["pieds"][k][0]) > SEUIL_PATINAGE:
                        pb["patinage"].append(f"f{q['f']} {a['nom']} pied{k}")
            v = abs(a["bassin"][0] - b["bassin"][0]) * fps
            if v > SEUIL_VITESSE and all(a.get("au_sol", [])):
                pb["vitesse"].append(f"f{q['f']} {a['nom']} {v:.0f}px/s")

    # 5. impacts sur les beats · 6. contact resolu (une cible par impact)
    beats = d.get("beats", [])
    for fr in frames:
        for im in fr.get("impacts", []):
            if beats:
                e = min(abs(im["t"] - b) for b in beats) * fps
                if e > SEUIL_BEAT:
                    pb["beats"].append(f"t{im['t']:.3f} ecart {e:.1f} frames")
            if im.get("issue") not in ("touche", "pare", "esquive"):
                pb["contact"].append(f"t{im['t']:.3f} issue '{im.get('issue')}' inconnue")
    return pb


NOMS = {"prise": "1. prise d'arme (main sur la poignee)",
        "poignet": "2. poignet non casse",
        "patinage": "3. aucun patinage de pied",
        "vitesse": "4. aucun saut de position",
        "beats": "5. impacts sur la grille musicale",
        "contact": "6. chaque impact a une issue connue",
        "torses": "7. aucune interpenetration de corps"}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("dump")
    p.add_argument("--max", type=int, default=5, help="exemples affiches par controle")
    a = p.parse_args()
    pb = controles(json.load(open(a.dump)))
    ko = 0
    for k, nom in NOMS.items():
        v = pb[k]
        if v:
            ko += 1
            print(f"✗ {nom} — {len(v)} violation(s)")
            for x in v[:a.max]:
                print(f"    {x}")
        else:
            print(f"✔ {nom}")
    print(f"\n{7 - ko}/7 controles verts")
    sys.exit(1 if ko else 0)
