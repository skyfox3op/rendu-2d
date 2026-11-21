"""Bibliothèque de mouvements réutilisables (v7) : courses, chutes mortelles, roulades, saltos, esquives."""
import moteur7 as E
from corps3 import Acteur, add, lerp_pt, poitrine, sub
from moteur7 import B, fab, pause, pres, resoudre, saut, plongee, vol_balistique  # noqa: F401
from poses5 import A as A5, AB, CORPS

A = dict(A5)
A.update({
    "boule": dict(t=40, h=20, b1=60, a1=10, b2=70, a2=20, c1=120, j1=10, c2=110, j2=0),
    "garde_large": dict(t=16, h=-4, b1=70, a1=140, b2=50, a2=130, c1=44, j1=-10, c2=-36, j2=-50),
    "esquive": dict(t=-34, h=-22, b1=30, a1=70, b2=-30, a2=-10, c1=44, j1=26, c2=-30, j2=-40),
    "frappe_haut": dict(t=30, h=-8, b1=150, a1=110, b2=40, a2=120, c1=56, j1=4, c2=-44, j2=-56),
})
COUL_E = (.04, .04, .05)


def ennemi(nom, x, d=-1):
    a = Acteur(nom, COUL_E, dict(AB, x=x, d=d))
    return a


def course(a, mk, t0, t1, x0, x1, pas=.12, **kw):
    n = max(1, int(round((t1 - t0) / pas)))
    for i in range(n + 1):
        u = i / n
        a.cle(t0 + (t1 - t0) * u, **mk("sprint1" if i % 2 == 0 else "sprint2", x=x0 + (x1 - x0) * u, **kw))


def mort(a, mk, t, x, dx, rot0=0, haut=110, duree=.42, face=False, d=-1):
    """Touché à mort : projeté (membres qui battent), retombe à plat, petit rebond, ne bouge plus.
    Retourne (x final, rot final)."""
    sens = 1 if dx * d < 0 else -1                      # projeté vers l'arrière -> salto arrière (rot négatif)
    r1 = rot0 - 90 * sens if not face else rot0 + 90 * sens
    vol_balistique(a, mk, t, t + duree, x, x + dx, 0, 0, haut, rot0, r1, d=d)
    a.cle(t + duree, **mk("plat", x=x + dx, rot=r1, d=d))
    a.cle(t + duree + .07, **mk("plat2", x=x + dx * 1.08, air=14, rot=r1 - 2, d=d))
    a.cle(t + duree + .16, **mk("plat", x=x + dx * 1.12, rot=r1, d=d))
    a.cle(30.0, **mk("plat", x=x + dx * 1.12, rot=r1, d=d))
    return x + dx * 1.12, r1


def roulade(acteur, mk, nom, t0, t1, x0, x1, rot0, avant=True, **kw):
    """Roulade : le corps tourne EN avançant (pas une image qui pivote sur place)."""
    s = 1 if avant else -1
    acteur.cle(t0, **mk(nom, x=x0, rot=rot0, air=4, **kw))
    acteur.cle((t0 + t1) / 2, **mk(nom, x=(x0 + x1) / 2, rot=rot0 + 180 * s, air=8, **kw))
    acteur.cle(t1, **mk(nom, x=x1, rot=rot0 + 360 * s, air=2, **kw))
    return rot0 + 360 * s
