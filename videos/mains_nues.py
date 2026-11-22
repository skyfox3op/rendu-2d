"""« my weapon type: » MAINS NUES — 1 contre 1, 21,9 s (3 tours de la musique), boucle parfaite.
Héros bleu canard (H), adversaire noir (E). Les deux attaquent et défendent.
python3 mains_nues.py sortie.mp4 [--muet] [--verif] [--jusqua s] [--images dossier]"""
import sys

import combat10 as K
import prof10 as P
from combat10 import Choree, Combattant, beats, chute, releve, salto
from lib7 import COUL_E
from moteur7 import pause, resoudre, vol_balistique

BLEU = (.02, .50, .62)
DUREE = 2 * K.DT + 7.672          # = durée de musique_22.wav
X_H, X_E = 420, 690


def construire():
    c = Choree()
    H = Combattant("H", BLEU, X_H, 1)
    E = Combattant("E", COUL_E, X_E, -1)
    V = c.V

    def recule(p, t, nom, dist, **kw):
        p.k(t, nom, x=p.x - p.d * dist, **kw)

    # =========================================================== TOUR 1
    b = beats(0)
    H.k(0, "garde")
    E.k(0, "garde")
    H.k(b["b1"], "rebond", x=X_H + 12)
    E.k(b["b1"], "rebond", x=X_E - 12)
    # on0 : E jab -> H bloc haut
    c.coup(E, H, b["on0"], "jab", "tete", "bloque", t_arm=.34, defpose="bloc_haut")
    # b2 : E cross -> H plonge sous le coup
    c.coup(E, H, b["b2"], "cross", "tete", "esquive", t_arm=.68, defpose="esq_bas")
    # on1 : H uppercut en sortant de l'esquive -> menton
    E.k(1.02, "garde")
    c.coup(H, E, b["on1"], "uppercut", "menton", "touche", t_arm=1.0, arm="arme_upper", f=1.2)
    recule(E, 1.27, "sonne", 50)
    H.k(1.30, "garde")
    # b3 : E low kick -> H check au tibia
    c.coup(E, H, b["b3"], "low", "jambe", "bloque", t_arm=1.37, defpose="check")
    E.k(1.66, "garde")
    # on2 : H middle kick -> E attrape la jambe
    c.coup(H, E, b["on2"], "circ", "ventre", "bloque", t_arm=1.70, defpose="attrape", defkw=K.bras_devant(-1),
           f=.9, pause_=0)
    pause(H.a, b["on2"], .16)
    # b4 : E balaie la jambe d'appui -> H tombe sur le dos
    c.coup(E, H, b["b4"], "balayage", "pied", "touche", t_arm=2.03, arm="arme_balayage", defpose=None, f=1.0,
           pause_=0, var=("x", "c2"))
    chute(H, b["b4"] + .02, 40, duree=.22, haut=50, choc=c, court=True)
    E.k(2.42, "garde", x=E.x + 110)
    # b5 : relevé ninja de H
    releve(H, b["b5"] - .34)
    c.evt(b["b5"], "poussiere", (H.x, 1500), n=8)
    # on3 : E superman punch -> touche H au visage
    E.k(3.02, "garde")
    c.coup(E, H, b["on3"], "superman", "tete", "touche", t_arm=3.08, arm="superman_appel", akw=dict(air=46),
           var=("x", "b1"), defpose="garde", f=1.2, pause_=0)
    E.k(3.35, "arme_cross", air=0, x=E.x - 20 * E.d)
    recule(H, 3.39, "recul", 70)
    # b6 : E cross -> H bloc haut
    c.coup(E, H, b["b6"], "cross", "tete", "bloque", t_arm=None, defpose="bloc_haut")
    V.armement(E.a, b["b6"], 3.35, "E cross 2")
    # on4 : E high kick -> H penché en arrière
    c.coup(E, H, b["on4"], "high", "tete", "esquive", t_arm=3.66, defpose="esq_arr")
    E.k(3.96, "garde")
    # b7 : H coup de pied retourné -> ventre
    H.k(3.90, "arme_retourne")
    H.flip(3.99, "arme_retourne")
    c.coup(H, E, b["b7"], "retourne", "ventre", "touche", f=1.3, defpose="garde")
    V.armement(H.a, b["b7"], 3.90, "H retourné")
    recule(E, 4.27, "ventre", 110)
    E.k(4.50, "titube")
    H.flip(4.30, "garde")
    # fort : genou volant -> tête (E penché)
    H.k(4.52, "accroupi")
    c.coup(H, E, b["fort"], "genou_vol", "tete", "touche", t_arm=4.60, arm="", akw=dict(air=80),
           var=("x", "air"), defpose="titube", f=1.6, sang=4)
    V.armement(H.a, b["fort"], 4.52, "H genou volant")
    chute(E, b["fort"] + .02, 250, duree=.38, haut=110, choc=c, court=True)
    H.k(5.02, "reception", air=0, x=H.x + 30)
    H.k(5.20, "garde")
    # b9 : E relevé ninja
    releve(E, 5.33)
    # b10 : E side kick -> H salto arrière
    H.lire(5.20)
    c.coup(E, H, b["b10"], "side", "poitrine", "esquive", t_arm=5.84, arm="arme_side", defpose=None, marge=20)
    salto(H, 5.84, 6.12, -190, 150, avant=False)
    E.k(6.12, "garde", x=E.x)
    # b11 : H tornade -> E bloc haut
    E.k(6.30, "garde")
    H.k(6.27, "accroupi")
    H.k(6.36, "groupe", air=80, x=H.x + 40, d=-1)
    H.k(6.44, "tour", air=140, x=H.x + 40, d=1)
    H.k(6.51, "groupe", air=150, x=H.x + 30, d=-1)
    H.d = 1
    c.coup(H, E, b["b11"], "tornade", "tete", "bloque", t_arm=None, akw=dict(air=130), var=("x", "air"),
           defpose="bloc_haut", f=1.3)
    V.armement(H.a, b["b11"], 6.27, "H tornade")
    H.k(6.80, "reception", air=0, x=H.x - 30)
    recule(E, 6.72, "garde", 50)
    H.k(6.92, "garde")
    # b12 : H jab -> E bloc haut
    c.coup(H, E, b["b12"], "jab", "tete", "bloque", t_arm=6.97, defpose="bloc_haut")
    # =========================================================== TOUR 2
    b = beats(1)
    H.k(b["b1"], "rebond", x=H.x - 20)
    E.k(b["b1"], "rebond")
    # on0 : E cross -> H plonge
    c.coup(E, H, b["on0"], "cross", "tete", "esquive", t_arm=7.44, defpose="esq_bas")
    # b2 : H coude remontant -> tête
    c.coup(H, E, b["b2"], "coude", "menton", "touche", t_arm=7.80, f=1.2)
    recule(E, 8.06, "sonne", 30)
    # on1 : saisie à la nuque + GENOU au ventre
    c.coup(H, E, b["on1"], "genou", "poitrine", "touche", t_arm=8.13, arm="clinch", defpose="titube", f=1.3)
    # b3 : 2e genou -> E bloque avec les avant-bras
    H.k(8.47, "clinch")
    c.coup(H, E, b["b3"], "genou", "ventre", "bloque", t_arm=8.47, arm="", defpose="bloc_ventre",
           defkw=dict(t=36), f=.9)
    # on2 : E PROJECTION PAR-DESSUS L'ÉPAULE : H passe au-dessus et retombe de l'autre côté
    E.k(8.80, "porte")
    V.touche(8.80, "E saisit H (projection d'épaule)", lambda t: E.sk(t)["main1"], H.a, tol=60)
    xh0, xe = H.x, E.x
    H.k(8.78, "clinch")
    x_arr = xe + 230
    vol_balistique(H.a, H.mk, 8.80, 9.22, xh0, x_arr, 0, 0, 200, 0, 360, poses=("groupe",), d=1)
    H.k(9.22, "reception", x=x_arr, rot=360)
    H.k(9.26, "reception", x=x_arr + 10, rot=0, coupe=True)
    H.x = x_arr + 10
    c.evt(b["on2"], "frappe", (xe, 1180), f=.6)
    E.k(9.04, "jete")
    E.flip(9.16, "garde")
    c.evt(9.22, "poussiere", (x_arr, 1500), n=12)
    H.flip(b["b4"], "garde")
    # b5 : H balayage -> E saute par-dessus
    E.k(9.62, "accroupi")
    E.k(9.82, "groupe", air=120, x=E.x)
    E.k(9.98, "groupe", air=110, x=E.x)
    c.coup(H, E, b["b5"], "balayage", "pied", "esquive", t_arm=9.70, defpose=None, var=("x", "c2"), marge=12)
    E.k(10.16, "reception", air=0)
    H.k(10.20, "garde")
    # on3 : E teep -> H bloc ventre
    c.coup(E, H, b["on3"], "teep", "ventre", "bloque", t_arm=10.25, defpose="bloc_ventre")
    # b6 : H backfist retourné -> E plonge
    H.k(10.46, "tour")
    H.flip(10.52, "tour")
    E.k(10.52, "garde")
    c.coup(H, E, b["b6"], "backfist", "tete", "esquive", defpose="esq_bas", marge=12)
    V.armement(H.a, b["b6"], 10.46, "H backfist")
    H.flip(10.74, "garde")
    # on4 : E uppercut depuis l'esquive -> H penché en arrière
    c.coup(E, H, b["on4"], "uppercut", "menton", "bloque", t_arm=10.66, arm="", defpose="bloc_haut")
    V.armement(E.a, b["on4"], b["b6"], "E uppercut")
    # b7 : H teep -> ventre, E repoussé
    c.coup(H, E, b["b7"], "teep", "ventre", "touche", t_arm=11.08, defpose="garde", f=1.2)
    recule(E, 11.40, "ventre", 160)
    E.k(11.56, "garde")
    # fort : E sprint + GENOU VOLANT -> H roule sous lui (les deux changent de côté)
    H.k(11.70, "garde")
    H.lire(11.70)
    xh, xs = H.x, E.x
    K.L8.naruto(E.a, E.mk, 11.58, 11.78, xs, xh - 250, d=1)
    E.k(11.84, "genou_vol", air=90, x=xh - 200, voie=.5)
    E.k(b["fort"], "genou_vol", air=150, x=xh + 10, voie=.5)
    E.k(12.10, "genou_vol", air=50, x=xh + 110, voie=.5)
    E.k(12.18, "reception", air=0, x=xh + 130, voie=0)
    E.x = xh + 130
    H.k(11.80, "accroupi", x=xh)
    K.L8.roulade(H.a, H.mk, "boule", 11.86, 12.16, xh - 20, xh - 190, 0, avant=True, d=-1)
    H.k(12.24, "garde", x=xh - 200, rot=0, coupe=True)
    H.x = xh - 200
    V.esquive(b["fort"] - .1, b["fort"] + .05, "E genou volant -> H roule dessous", lambda t: E.sk(t)["genou1"], H.a,
              marge=10)
    c.membres.append((E.a, "genou1", 11.84, b["fort"]))
    H.flip(12.30, "garde")
    E.flip(12.22, "garde")
    # b9 : E crochet -> H bloc haut
    c.coup(E, H, b["b9"], "crochet", "tete", "bloque", t_arm=12.34, defpose="bloc_haut")
    # b10 : H side kick -> poitrine
    c.coup(H, E, b["b10"], "side", "poitrine", "touche", t_arm=12.90, f=1.4, defpose="garde")
    recule(E, 13.22, "recul", 130)
    E.k(13.44, "garde")
    # b11 : E low kick -> H check
    c.coup(E, H, b["b11"], "low", "jambe", "bloque", t_arm=13.50, defpose="check")
    E.k(13.86, "garde")
    H.k(13.84, "garde")
    # b12 : H jab -> touche
    c.coup(H, E, b["b12"], "jab", "tete", "touche", t_arm=14.06, f=.8, defpose="garde")
    recule(E, 14.33, "sonne", 30)
    # =========================================================== TOUR 3
    b = beats(2)
    H.k(b["b1"], "rebond")
    # on0 : E crochet -> H plonge
    c.coup(E, H, b["on0"], "crochet", "tete", "esquive", t_arm=14.56, defpose="esq_bas")
    # b2 : H uppercut -> E penché en arrière
    c.coup(H, E, b["b2"], "uppercut", "menton", "bloque", t_arm=14.92, arm="arme_upper", defpose="bloc_haut")
    # on1 : E balayage -> H saute ; b3 : DROP KICK en l'air -> poitrine
    E.k(15.16, "arme_balayage")
    H.k(15.20, "accroupi")
    xh = H.x
    H.k(b["on1"], "groupe", air=175, x=xh + 20)
    c.coup(E, H, b["on1"], "balayage", "pied", "esquive", t_arm=15.16, arm="", defpose=None, var=("x", "c2"), marge=10)
    E.k(15.60, "garde")
    H.k(15.60, "groupe", air=185, x=xh + 60)
    c.coup(H, E, b["b3"], "drop", "poitrine", "touche", akw=dict(air=110, rot=-60), var=("x", "air"), f=1.5,
           defpose="garde")
    V.armement(H.a, b["b3"], 15.58, "H drop kick")
    chute(E, b["b3"] + .02, 240, duree=.36, haut=80, choc=c)
    H.k(15.96, "plat", air=0, rot=-90, x=H.x - 40)
    c.evt(15.96, "sol", (H.x, 1480), f=.6)
    H.x -= 40
    # b4 : les deux se relèvent
    releve(H, b["b4"] - .34)
    releve(E, 16.30)
    # b5 : E cross -> H bloc haut
    H.k(16.66, "garde", x=H.x + 50)
    c.coup(E, H, b["b5"], "cross", "tete", "bloque", t_arm=16.86, defpose="bloc_haut")
    # on3 : H crochet -> tête ; b6 : H cross -> tête
    c.coup(H, E, b["on3"], "crochet", "tete", "touche", t_arm=17.32, f=1.1, defpose="garde", pause_=.04)
    c.coup(H, E, b["b6"], "cross", "tete", "touche", t_arm=17.575, f=1.2, defpose="garde")
    recule(E, 17.80, "sonne", 50)
    # on4 : E high kick -> H plonge dessous
    c.coup(E, H, b["on4"], "high", "tete", "esquive", t_arm=17.88, defpose="esq_bas")
    # b7 : H uppercut depuis l'esquive -> menton
    c.coup(H, E, b["b7"], "uppercut", "menton", "touche", t_arm=18.15, arm="", defpose="garde", f=1.4)
    recule(E, 18.48, "recul", 60)
    E.k(18.70, "titube")
    # fort : H TORNADE -> tête (gros coup)
    H.k(18.70, "accroupi")
    H.k(18.80, "groupe", air=80, x=H.x + 30, d=-1)
    H.k(18.90, "tour", air=140, x=H.x + 30, d=1)
    H.k(18.98, "groupe", air=150, x=H.x + 20, d=-1)
    H.d = 1
    c.coup(H, E, b["fort"], "tornade", "tete", "touche", akw=dict(air=130), var=("x", "air"), defpose="titube",
           f=1.8, sang=6)
    V.armement(H.a, b["fort"], 18.70, "H tornade 2")
    chute(E, b["fort"] + .02, 280, duree=.40, haut=120, choc=c, court=True)
    H.k(19.30, "reception", air=0, x=H.x - 20)
    H.k(19.46, "garde")
    # b9 : E relevé
    releve(E, 19.56)
    # b10 : E jab -> H bloc haut
    H.k(19.80, "pas", x=H.x + 150)
    H.k(20.0, "garde", x=H.x + 110)
    c.coup(E, H, b["b10"], "jab", "tete", "bloque", t_arm=20.06, defpose="bloc_haut")
    # b11 : H cross -> E plonge
    c.coup(H, E, b["b11"], "cross", "tete", "esquive", t_arm=20.6, defpose="esq_bas")
    # b12 : E uppercut -> H penché en arrière
    c.coup(E, H, b["b12"], "uppercut", "menton", "esquive", t_arm=21.15, arm="arme_upper", defpose="esq_arr")
    # final : les deux middle kicks se percutent, tibia contre tibia, puis retour en garde (boucle)
    tf = b["final"]
    H.lire(b["b12"])
    E.lire(b["b12"])
    DX = round((H.x + E.x - X_H - X_E) / 2)        # décalage du monde (fond uniforme) : la boucle reste parfaite
    H.k(21.48, "arme_circ", x=X_H + DX + 6)
    E.k(21.48, "arme_circ", x=X_E + DX - 6)
    H.k(tf, "circ", x=X_H + DX + 6, **K.z_devant("pied2", 1, .1))
    E.k(tf, "circ", x=X_E + DX - 6, **K.z_devant("pied2", -1, .2))
    c.rap["tibias"] = resoudre([(H.a, [tf], "x"), (E.a, [tf], "x"), (H.a, [tf], "c2")],
                               lambda: list(K.sub(H.sk(tf)["pied2"], K.lerp_pt(E.sk(tf)["genou2"], E.sk(tf)["pied2"], .6)))
                               + [H.X(tf) + E.X(tf) - X_H - X_E - 2 * DX])
    V.pare(tf, "H middle vs E middle (tibias)", lambda t: H.sk(t)["pied2"],
           lambda t: (E.sk(t)["genou2"], E.sk(t)["pied2"]))
    c.evt(tf, "parade", H.sk(tf)["pied2"], f=1.6)
    c.membres += [(H.a, "pied2", 21.48, tf), (E.a, "pied2", 21.48, tf)]
    pause(H.a, tf, .05)
    pause(E.a, tf, .05)
    for p, x in ((H, X_H), (E, X_E)):
        p.k(21.80, "garde", x=x + DX, d=p.d)
        p.k(DUREE, "garde", x=x + DX)
        p.k(DUREE + beats(0)["b1"], "rebond", x=x + DX + p.d * 12)
    c.DX = DX
    return H, E, c


# ---------------------------------------------------------------- ferme de rendu
FPS = 60
MUSIQUE = None            # la musique n'est pas sur le depot : segments MUETS

_CHOREE = None


def rendre_segment(f0, f1, sortie):
    """Rend les frames [f0, f1[ dans leur propre mp4 muet. Appele par outils/rendu_parallele."""
    global _CHOREE
    import os
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from outils import segments as S
    P.M.ecrivain = S.ecrivain_segment          # ultrafast + keyframe en 0 (au lieu de preset slow)
    if _CHOREE is None:
        _CHOREE = construire()
    H_, E_, c_ = _CHOREE
    P.rendre10(H_.a, [E_.a], c_.ev, sortie, DUREE, None, BLEU, son=False,
               morceau=(f0, f1), coups_membres=c_.membres, seed=21, poids_h=.6)


if __name__ == "__main__":
    H, E, c = construire()
    for k_, v in c.rap.items():
        if v > 2:
            print(f"  solveur {k_:40s} {v:7.2f}")
    c.V.globaux([H.a, E.a], DUREE)
    ok, txt = c.V.rapport()
    print(txt)
    print("VÉRIF", "OK" if ok else "ÉCHECS")
    open("verif_mains_nues.txt", "w").write(txt)
    if "--verif" in sys.argv:
        for t in [i * .25 for i in range(int(DUREE * 4) + 1)]:
            print(f"{t:6.2f} H:{H.sk(t)['bassin'][0]:6.0f}{'>' if H.sk(t)['d'] > 0 else '<'} "
                  f"E:{E.sk(t)['bassin'][0]:6.0f}{'>' if E.sk(t)['d'] > 0 else '<'}")
        sys.exit(0)
    arg = sys.argv
    P.rendre10(H.a, [E.a], c.ev, arg[1], DUREE, "musique_22.wav", BLEU, son="--muet" not in arg,
               dossier=arg[arg.index("--images") + 1] if "--images" in arg else None,
               jusqua=float(arg[arg.index("--jusqua") + 1]) if "--jusqua" in arg else None,
               morceau=(int(arg[arg.index("--morceau") + 1]), int(arg[arg.index("--morceau") + 2])) if "--morceau" in arg else None,
               coups_membres=c.membres, seed=21, poids_h=.6)


def persos(r):
    H, E, c = r
    return [(H.a, BLEU, None, None), (E.a, COUL_E, None, None)]
