"""v10 : outils de chorégraphie pour combats avec rendu en profondeur.

Combattant : clés nommées, suivi de x et d, demi-tours.
coup(...) : armement + coup + réaction du défenseur, contact exact (solveur), profondeur du membre au contact,
            ligne de vérification (touché / paré / esquivé), événement visuel, traînée autorisée.
"""
import math

import prof10 as P
from corps3 import add, lerp_pt, sub
from lib8 import P8, Verif, d_corps, d_seg  # noqa: F401
from moteur7 import fab, pause, resoudre

DT = 7.1117                     # période réelle de la boucle musicale (mesurée : 7.152 était 40 ms trop long)
B0 = dict(b1=0.093, on0=0.534, b2=0.859, on1=1.184, b3=1.533, on2=1.858, b4=2.183, b5=2.856, on3=3.297,
          b6=3.506, on4=3.831, q1=3.99, b7=4.156, fort=4.83, b9=5.387, b10=5.991, b11=6.571, b12=7.129, final=7.43)


def beats(k):
    return {n: v + k * DT for n, v in B0.items()}


BASE = dict(x=0, air=0, t=8, h=-4, b1=30, a1=160, b2=50, a2=150, c1=34, j1=-6, c2=-30, j2=-46, w=0, g=0, rot=0, z=0,
            o=0, suivi=0, d=1, deux=False, tient=False, zm1=0, zm2=0, zj1=0, zj2=0, voie=0)
G = dict(c1=34, j1=-6, c2=-30, j2=-46)
MN = dict(P8)
MN.update({
    # ------------------------------------------------ gardes / déplacements
    "garde": dict(t=8, h=-4, b1=30, a1=160, b2=50, a2=150, **G),
    "rebond": dict(t=12, h=-4, b1=30, a1=160, b2=50, a2=150, c1=42, j1=-16, c2=-24, j2=-56),
    "pas": dict(t=8, h=-4, b1=30, a1=160, b2=50, a2=150, c1=18, j1=-4, c2=-12, j2=-30, air=6),
    "sprint1": dict(t=34, h=-14, b1=-50, a1=-10, b2=60, a2=100, c1=70, j1=10, c2=-60, j2=-20),
    "sprint2": dict(t=34, h=-14, b1=60, a1=100, b2=-50, a2=-10, c1=-60, j1=-20, c2=70, j2=10),
    # ------------------------------------------------ poings / coudes
    "arme_jab": dict(t=4, h=-4, b1=30, a1=160, b2=30, a2=150, c1=40, j1=-10, c2=-30, j2=-50),
    "jab": dict(t=14, h=-6, b1=30, a1=160, b2=90, a2=90, c1=46, j1=-2, c2=-36, j2=-52),
    "arme_cross": dict(t=-4, h=-4, b1=10, a1=150, b2=50, a2=160, c1=36, j1=-6, c2=-34, j2=-50),
    "cross": dict(t=26, h=-8, b1=88, a1=90, b2=40, a2=165, c1=58, j1=0, c2=-44, j2=-60),
    "arme_crochet": dict(t=0, h=-4, b1=30, a1=160, b2=40, a2=150, c1=36, j1=-8, c2=-32, j2=-50),
    "crochet": dict(t=20, h=-6, b1=30, a1=160, b2=86, a2=118, c1=50, j1=-4, c2=-38, j2=-54),
    "arme_upper": dict(t=36, h=-12, b1=10, a1=70, b2=50, a2=150, c1=74, j1=-24, c2=-40, j2=-84),
    "uppercut": dict(t=8, h=-16, b1=80, a1=150, b2=40, a2=150, c1=44, j1=-4, c2=-34, j2=-50),
    "arme_coude": dict(t=-6, h=-4, b1=-10, a1=150, b2=50, a2=160, c1=34, j1=-6, c2=-32, j2=-50),
    "coude": dict(t=6, h=-10, b1=128, a1=-50, b2=40, a2=165, c1=50, j1=0, c2=-40, j2=-56),
    "tour": dict(t=10, h=-4, b1=-20, a1=40, b2=-30, a2=20, c1=30, j1=-6, c2=-30, j2=-44),
    "backfist": dict(t=-6, h=-10, b1=-96, a1=-92, b2=20, a2=150, c1=34, j1=-6, c2=-40, j2=-54),
    "superman": dict(t=40, h=-12, b1=92, a1=90, b2=-60, a2=-40, c1=40, j1=10, c2=-90, j2=-70),
    "superman_appel": dict(t=20, h=-8, b1=-20, a1=40, b2=60, a2=150, c1=10, j1=-4, c2=100, j2=-20),
    # ------------------------------------------------ corps-à-corps
    "clinch": dict(t=16, h=-8, b1=96, a1=70, b2=96, a2=70, **G),
    "genou": dict(t=-6, h=-4, b1=100, a1=60, b2=100, a2=60, c1=8, j1=-4, c2=118, j2=-14),
    "porte": dict(t=64, h=-22, b1=150, a1=170, b2=150, a2=170, c1=84, j1=-30, c2=-36, j2=-96),
    "jete": dict(t=56, h=-30, b1=-20, a1=-60, b2=-10, a2=-50, c1=70, j1=-24, c2=-40, j2=-80),
    # ------------------------------------------------ jambes
    "arme_teep": dict(t=-10, h=-4, b1=40, a1=155, b2=50, a2=150, c1=110, j1=-20, c2=-10, j2=-14),
    "teep": dict(t=-22, h=-4, b1=40, a1=150, b2=40, a2=150, c1=96, j1=92, c2=-10, j2=-12),
    "arme_low": dict(t=-4, h=-4, b1=-20, a1=40, b2=50, a2=150, c1=10, j1=-6, c2=40, j2=-30),
    "low": dict(t=-14, h=-4, b1=-40, a1=10, b2=60, a2=150, c1=6, j1=-6, c2=56, j2=66),
    "arme_circ": dict(t=-8, h=-4, b1=-20, a1=40, b2=50, a2=150, c1=10, j1=-6, c2=60, j2=-30),
    "circ": dict(t=-30, h=-8, b1=-40, a1=-10, b2=60, a2=150, c1=-4, j1=-8, c2=100, j2=98),
    "arme_high": dict(t=-14, h=-4, b1=-30, a1=20, b2=60, a2=150, c1=12, j1=-6, c2=110, j2=-20),
    "high": dict(t=-38, h=-10, b1=-50, a1=-20, b2=60, a2=150, c1=-6, j1=-10, c2=140, j2=140),
    "arme_side": dict(t=-20, h=-14, b1=40, a1=150, b2=-30, a2=0, c1=120, j1=-30, c2=-14, j2=-18),
    "side": dict(t=-46, h=-28, b1=60, a1=140, b2=-70, a2=-40, c1=94, j1=92, c2=-14, j2=-18),
    "arme_retourne": dict(t=40, h=-10, b1=20, a1=60, b2=30, a2=80, c1=30, j1=-6, c2=-20, j2=-60),
    "retourne": dict(t=56, h=-26, b1=30, a1=70, b2=10, a2=40, c1=24, j1=-10, c2=-100, j2=-98),
    "balayage": dict(t=44, h=-22, b1=10, a1=10, b2=40, a2=60, c1=112, j1=-38, c2=86, j2=90),
    "arme_balayage": dict(t=40, h=-20, b1=20, a1=40, b2=40, a2=80, c1=110, j1=-36, c2=-40, j2=-96),
    "genou_vol": dict(t=-6, h=-10, b1=96, a1=70, b2=96, a2=60, c1=124, j1=-16, c2=-40, j2=-70),
    "drop": dict(t=0, h=-12, b1=160, a1=180, b2=150, a2=170, c1=94, j1=90, c2=84, j2=86),
    "tornade": dict(t=-10, h=-12, b1=70, a1=140, b2=-80, a2=-100, c1=100, j1=98, c2=40, j2=-50),
    # ------------------------------------------------ défenses / réactions
    "bloc_haut": dict(t=2, h=-12, b1=64, a1=174, b2=72, a2=170, c1=40, j1=-12, c2=-32, j2=-54),
    "bloc_ventre": dict(t=12, h=-8, b1=20, a1=96, b2=30, a2=100, c1=40, j1=-10, c2=-34, j2=-52),
    "check": dict(t=4, h=-6, b1=30, a1=160, b2=50, a2=150, c1=104, j1=-6, c2=-14, j2=-24),
    "esq_arr": dict(t=-36, h=-22, b1=30, a1=150, b2=40, a2=150, c1=44, j1=26, c2=-30, j2=-40),
    "esq_bas": dict(t=26, h=-18, b1=30, a1=150, b2=50, a2=150, c1=104, j1=-14, c2=58, j2=-64),
    "attrape": dict(t=14, h=-8, b1=40, a1=96, b2=60, a2=110, **G),
    "sonne": dict(t=-26, h=-30, b1=30, a1=90, b2=10, a2=60, c1=20, j1=-10, c2=-40, j2=-50),
    "recul": dict(t=-26, h=-24, b1=110, a1=150, b2=-50, a2=-80, c1=16, j1=40, c2=-30, j2=-16),
    "ventre": dict(t=46, h=34, b1=20, a1=-10, b2=30, a2=0, c1=20, j1=-20, c2=-26, j2=-40),
    "titube": dict(t=50, h=24, b1=100, a1=60, b2=-30, a2=-50, c1=50, j1=-6, c2=-40, j2=-64),
    "plat2": dict(rot=-90, t=0, h=-8, b1=150, a1=170, b2=20, a2=10, c1=14, j1=4, c2=-14, j2=-18),
    "boule": dict(t=40, h=20, b1=60, a1=10, b2=70, a2=20, c1=120, j1=10, c2=110, j2=0),
    "salut": dict(t=4, h=-8, b1=40, a1=150, b2=40, a2=150, c1=20, j1=-4, c2=-20, j2=-30),
})

PORTEE = dict(jab=150, cross=150, crochet=130, uppercut=112, coude=100, backfist=150, superman=150, genou=88,
              teep=190, low=170, circ=190, high=200, side=205, retourne=200, balayage=175)
OS = dict(jab="main2", cross="main1", crochet="main2", uppercut="main1", coude="coude1", backfist="main1",
          superman="main1", genou="genou2", teep="pied1", low="pied2", circ="pied2", high="pied2", side="pied1",
          retourne="pied2", balayage="pied2", genou_vol="genou1", drop="pied1", tornade="pied1")
UN_SEUL = ("uppercut", "coude")          # coups de près : seul x bouge (sinon le solveur colle les corps)
VAR = dict(pointe="w", lame="w", pommeau="b1", main1="b1", main2="b2", coude1="b1", genou2="c2", genou1="c1", pied1="c1", pied2="c2")


def pos(sk, os_):
    if os_ == "pointe":
        return sk["arme"][1]
    if os_ == "lame":
        return lerp_pt(sk["arme"][0], sk["arme"][1], .74)
    if os_ == "pommeau":
        return sk["arme"][0]
    return sk[os_]


def z_devant(os_, d, z=.14):
    """Décalage de profondeur pour amener le membre qui frappe au CENTRE, devant la cible."""
    if os_ in ("main1", "coude1", "pointe", "lame", "pommeau"):
        return {"zm1": z + .5 * d}
    if os_ == "main2":
        return {"zm2": z - .5 * d}
    if os_ in ("pied1", "genou1"):
        return {"zj1": z - .35 * d}
    return {"zj2": z + .35 * d}


def bras_devant(d, z=.26):
    return {"zm1": z + .5 * d, "zm2": z - .5 * d}


class Combattant:
    def __init__(self, nom, coul, x, d, lib=MN, base=BASE, arme_l=0):
        self.base = dict(base, x=x, d=d)
        self.a = P.Acteur10(nom, coul, self.base, arme_l)
        self.nom, self.coul, self.x, self.d = nom, coul, x, d
        self.mk = fab(self.base, lib)
        self.lib = lib

    def k(self, _t, nom, coupe=False, **kw):
        kw.setdefault("x", self.x)
        kw.setdefault("d", self.d)
        self.x, self.d = kw["x"], kw["d"]
        self.a.cle(_t, coupe=coupe, **self.mk(nom, **kw))

    def flip(self, _t, nom, **kw):
        kw.pop("d", None)
        self.k(_t, nom, **kw)
        self.d = -self.d
        self.k(_t + 1 / 120, nom, coupe=True, **kw)

    def sk(self, t):
        return self.a.squelette(t)

    def X(self, t):
        return self.a.k(t)["x"]

    def lire(self, t):
        self.x = self.X(t)


def point(sk, c):
    if c == "tete":
        return sk["tete"]
    if c == "menton":
        return lerp_pt(sk["cou"], sk["tete"], .55)
    if c == "poitrine":
        return lerp_pt(sk["bassin"], sk["epaule"], .72)
    if c == "ventre":
        return lerp_pt(sk["bassin"], sk["epaule"], .35)
    if c == "jambe":
        return lerp_pt(sk["genou1"], sk["pied1"], .35)
    if c == "jambe2":
        return lerp_pt(sk["genou2"], sk["pied2"], .35)
    if c == "poignet":
        return sk["main1"]
    if c == "cou":
        return lerp_pt(sk["cou"], sk["tete"], .2)
    if c == "cuisse":
        return lerp_pt(sk["bassin"], sk["genou1"], .6)
    if c == "jarret":
        return lerp_pt(sk["genou2"], sk["genou1"], .5)
    if c == "pied":
        return lerp_pt(sk["genou1"], sk["pied1"], .8)
    raise KeyError(c)


class Choree:
    def __init__(self):
        self.V = Verif()
        self.ev = []
        self.rap = {}
        self.membres = []           # fenêtres de traînées

    def evt(self, t, typ, pt, **kw):
        self.ev.append(dict(t=t, typ=typ, pt=pt, **kw))

    def coup(self, att, dfn, t, tech, cible, issue, t_arm=None, arm=None, defpose="garde", defkw=None, akw=None,
             var=None, f=1.0, sang=0, nom=None, bloc="avant", tol=26, marge=14, pause_=.06, os_=None, solve=True,
             cle=True, partage=True, seg_def=None, typ=None, dirv=None):
        """issue : 'touche' | 'bloque' | 'esquive'. Le défenseur prend `defpose` à t ; l'attaquant `tech` à t."""
        defkw = dict(defkw or {})
        akw_init = akw
        akw = dict(akw or {})
        os_ = os_ or OS[tech]
        nom = nom or f"{att.nom} {tech} -> {cible} {dfn.nom}"
        v0 = 1 if dfn.x > att.x else -1                      # côté de l'adversaire AVANT le coup
        if issue == "bloque" and defpose in ("bloc_haut", "bloc_ventre"):
            defkw = {**bras_devant(dfn.d), **defkw}
        if issue == "bloque" and defpose == "check":
            defkw = {"zj1": .26 - .35 * dfn.d, **defkw}
        if defpose is not None:
            if issue == "esquive" and not any(t - .14 < c_[0] < t for c_ in dfn.a.cles):
                dfn.k(t - .09, defpose, **defkw)          # l'esquive part AVANT le coup (on la voit venir)
            dfn.k(t, defpose, **defkw)
        if t_arm is not None and arm != "":
            att.k(t_arm, arm or ("arme_" + tech))
        if cle:
            if "x" not in akw and "air" not in (var or ()) and defpose is not None:
                R = PORTEE.get(tech, 190)
                akw["x"] = dfn.x - v0 * R                     # point de départ plausible pour le solveur
            att.k(t, tech, **{**z_devant(os_, att.d), **akw})
        sd = dfn.sk
        if issue == "touche":
            peau = 30 if cible in ("tete", "menton") else 14                     # on frappe la SURFACE, pas le centre
            cib = lambda: add(point(sd(t), cible), (-v0, 0), peau)              # noqa: E731
        elif issue == "bloque":
            if seg_def is not None:
                seg = seg_def
            elif defpose == "check":
                seg = lambda tt: (sd(tt)["genou1"], sd(tt)["pied1"])            # noqa: E731
            else:
                i = "2" if (bloc == "avant") == (dfn.d > 0) else "1"
                seg = lambda tt, i=i: (sd(tt)["coude" + i], sd(tt)["main" + i])  # noqa: E731
            cib = lambda: lerp_pt(*seg(t), .55)                                 # noqa: E731
        else:
            p_fixe = point(sd(t_arm if t_arm is not None else t - .15), cible)
            cib = lambda: p_fixe                                               # noqa: E731
        if solve and not (issue == "esquive" and var is None and cle and "x" not in (akw_init or {})):
            inc = [(att.a, [t], v) for v in (var or (("x",) if issue == "esquive" or tech in UN_SEUL else ("x", VAR[os_])))]
            if partage and issue != "esquive" and defpose is not None:
                inc.append((dfn.a, [t], "x"))            # l'écart se répartit entre les deux (pas de téléportation)
            self.rap[nom] = resoudre(inc, lambda: sub(pos(att.sk(t), os_), cib()))
            if defpose is not None:
                dfn.lire(t)
        bouge_arm = t_arm is not None and arm != "" and solve and "air" not in (var or ())
        vers = v0
        if bouge_arm:
            att.a.k(t_arm)["x"] = att.a.k(t)["x"] - 22 * vers      # le déplacement se fait AVANT l'armement
            att.a.invalider()
        if issue == "esquive":                     # le coup tombe court / passe à côté : on recule l'attaquant si besoin
            for _ in range(40):
                jeu = min(d_corps(pos(att.sk(t - .1 + .14 * i / 20), os_), dfn.sk(t - .1 + .14 * i / 20)) for i in range(21))
                if jeu >= marge + 3:
                    break
                att.a.k(t)["x"] -= 6 * vers
                if bouge_arm:
                    att.a.k(t_arm)["x"] -= 6 * vers
                att.a.invalider()
        att.lire(t)
        pt = lambda tt: pos(att.sk(tt), os_)                                    # noqa: E731
        if t_arm is not None:
            self.V.armement(att.a, t, t_arm, f"{att.nom} {tech}")
        if issue == "touche":
            self.V.touche(t, nom, pt, dfn.a, tol=tol)
            self.evt(t, typ or "frappe", cib(), f=f, sang=sang, dirv=dirv or (att.d, -.5), ang=-30 * att.d)
            if pause_:
                pause(att.a, t, pause_)
        elif issue == "bloque":
            self.V.pare(t, nom, pt, seg, tol=tol)
            self.evt(t, typ or "parade", cib(), f=f)
            if pause_:
                pause(att.a, t, pause_ * .7)
        else:
            self.V.esquive(t - .1, t + .04, nom, pt, dfn.a, marge=marge)
        if os_ not in ("pointe", "lame", "pommeau"):
            self.membres.append((att.a, os_, (t_arm if t_arm is not None else t - .2), t))
        return cib()


# ------------------------------------------------------------------ positions composées
import lib8 as L8  # noqa: E402
import lib7 as L7  # noqa: E402
from moteur7 import vol_balistique  # noqa: E402


def chute(c, t, dx, duree=.36, haut=90, choc=None, court=False):
    """Projeté sur le dos vers l'arrière (dx > 0 = distance reculée). Retourne l'instant où il touche le sol.
    court=True : pas de rebond (pour enchaîner un relevé 0.1 s après)."""
    x0 = c.x
    arr = -c.d
    x1 = x0 + arr * dx
    c.k(t, "recul", x=x0)
    vol_balistique(c.a, c.mk, t, t + duree, x0, x1, 0, 0, haut, 0, -90, poses=("vol1", "vol2"), d=c.d)
    c.k(t + duree, "plat", x=x1, rot=-90)
    if court:
        c.k(t + duree + .05, "plat2", x=x1 + arr * dx * .04, air=6, rot=-92)
        c.x = x1 + arr * dx * .04
    else:
        c.k(t + duree + .07, "plat2", x=x1 + arr * dx * .06, air=12, rot=-93)
        c.k(t + duree + .16, "plat", x=x1 + arr * dx * .1, rot=-90)
        c.x = x1 + arr * dx * .1
    if choc:
        choc.evt(t + duree, "sol", (x1, 1480), f=min(1.6, dx / 200))
    return t + duree


def releve(c, t0, rot0=-90):
    """Relevé ninja (kip-up) de 0.44 s ; atterrit debout à t0 + 0.34."""
    c.x = L8.releve_ninja(c.a, c.mk, t0, c.x, c.d, rot0=rot0, pose="garde")
    c.k(t0 + .44 + 1 / 120, "garde", coupe=True)


def salto(c, t0, t1, dx, haut, avant):
    """Salto (rot ±360) puis remise à rot=0 (identique à l'écran) pour ne pas « dérouler » ensuite."""
    x1 = c.x + c.d * dx
    L8.salto(c.a, c.mk, t0, t1, c.x, x1, haut, avant, rot0=0, d=c.d)
    c.x = x1 + (x1 - c.x) * .04
    c.k(t1 + .09, "garde", coupe=True, rot=0)
