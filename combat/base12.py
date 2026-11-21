"""v12 — base commune : beats MESURÉS sur musique_22.wav (onsets réels), boucle parfaite, sol texturé qui défile,
armes des ennemis (arbalète, pistolet, mitraillette, lance, bouclier+masse, kunai, couteau), projectiles."""
import math

import numpy as np

from corps3 import SOL, add, dist, lerp_pt, sub, trait, unit

P = 7.1117
# temps relatifs au début de chaque boucle de 7.11 s, mesurés (flux spectral) — l'ancienne table avait ~50 ms de retard
# et 3 beats fantômes (d'où le décalage impact/son). Force = hauteur du pic (5+ = gros coup).
B12 = dict(z=.064, a=.490, b=.821, c=1.477, c2=1.619, d=2.139, e=2.808, f=3.021, g=3.137, h=3.241, i=3.442, j=3.532,
           k=3.778, l=3.924, m=4.115, n=4.437, o=4.777, p=5.188, q=5.302, r=5.616, s=5.923, t=6.095, u=6.240, v=6.754,
           w=7.085)
FORCE = dict(z=6.9, a=5.6, b=1.9, c=2.5, c2=2.3, d=3.5, e=6.6, f=4.8, g=2.6, h=3.2, i=3.1, j=2.0, k=5.0, l=2.1, m=2.2,
             n=2.2, o=3.0, p=4.6, q=3.8, r=4.3, s=2.4, t=2.6, u=4.4, v=2.7, w=2.8)
DUREE = 3 * P - .091          # coupe telle que le 1er beat (0.064) tombe pile après la fin -> boucle audio parfaite


def bt(nom, k=0):
    if nom == "z" and k > 0:
        return k * P - .027
    return B12[nom] + k * P


# ---------------------------------------------------------------- sol qui défile (période fixe -> boucle)
def sol(cr, t, coul=(.55, .55, .58), periode=2400, graine=7, densite=1.0):
    rng = np.random.default_rng(graine)
    n = int(60 * densite)
    xs = rng.uniform(0, periode, n)
    ys = rng.uniform(-70, 230, n)
    ls = rng.uniform(8, 46, n)
    ks = rng.integers(0, 3, n)
    for rep in range(-3, 5):
        for x, y, l_, k in zip(xs, ys, ls, ks):
            X = x + rep * periode
            prof = (y + 90) / 320                         # plus bas = plus proche = plus marqué
            a = .10 + .22 * prof
            if k == 0:                                     # trait d'herbe rase / fissure
                trait(cr, (X, SOL + y), (X + l_, SOL + y + 1), 2 + 2 * prof, (*coul, a))
            elif k == 1:                                   # caillou
                cr.save()
                cr.translate(X, SOL + y)
                cr.scale(1, .45)
                cr.arc(0, 0, 3 + 5 * prof, 0, 2 * math.pi)
                cr.restore()
                cr.set_source_rgba(*coul, a * 1.2)
                cr.fill()
            else:                                          # touffe
                for j in range(3):
                    trait(cr, (X + 4 * j, SOL + y), (X + 4 * j + 3 * (j - 1), SOL + y - 6 - 4 * prof), 1.5, (*coul, a))


# ---------------------------------------------------------------- armes des ennemis (dessin sur le segment "arme")
def _rep(seg):
    b, t = seg
    v = unit(sub(t, b))
    return b, t, v, (-v[1], v[0])


def arbalete(cr, sk, charge=True, alpha=1.0):
    """Arbalète : fût en bois sombre, arc d'acier recourbé à l'avant, corde, carreau engagé."""
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    trait(cr, add(b, v, -30), t, 9, (.18, .12, .08, alpha))
    trait(cr, add(b, v, -30), add(add(b, v, -36), n, 10), 8, (.18, .12, .08, alpha))     # crosse
    av = add(t, v, -8)
    for s in (1, -1):
        bout = add(add(av, n, 46 * s), v, -16)
        cr.move_to(*av)
        cr.curve_to(*add(av, n, 20 * s), *add(add(av, n, 40 * s), v, 4), *bout)
        cr.set_source_rgba(.35, .36, .4, alpha)
        cr.set_line_width(5)
        cr.stroke()
        trait(cr, bout, add(b, v, 34 if charge else 70), 1.2, (.85, .85, .85, alpha))
    if charge:
        trait(cr, add(b, v, 34), add(t, v, 26), 3, (.25, .2, .15, alpha))
        trait(cr, add(t, v, 18), add(t, v, 30), 5, (.6, .6, .65, alpha))


def pistolet(cr, sk, alpha=1.0, k=1.0):
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    m = b
    haut = n if sk["d"] > 0 else (-n[0], -n[1])
    haut = (haut[0], haut[1]) if haut[1] < 0 else (-haut[0], -haut[1])
    canon0 = add(m, haut, 10 * k)
    trait(cr, add(canon0, v, -10 * k), add(canon0, v, 42 * k), 11 * k, (.1, .1, .11, alpha))
    trait(cr, add(canon0, v, -6 * k), add(canon0, v, 40 * k), 3 * k, (.55, .56, .6, alpha))
    trait(cr, m, add(add(m, haut, -16 * k), v, -6 * k), 9 * k, (.25, .16, .1, alpha))


def mitraillette(cr, sk, alpha=1.0):
    """Mitraillette années 30 : crosse bois, chargeur camembert, canon à ailettes."""
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    haut = n if n[1] < 0 else (-n[0], -n[1])
    trait(cr, add(b, v, -50), add(b, v, -8), 12, (.32, .2, .1, alpha))
    trait(cr, add(b, v, -8), add(b, v, 60), 13, (.12, .12, .13, alpha))
    trait(cr, add(b, v, 60), add(b, v, 104), 6, (.15, .15, .16, alpha))
    for i in range(4):
        p = add(b, v, 64 + 9 * i)
        trait(cr, add(p, haut, -6), add(p, haut, 6), 2, (.3, .3, .32, alpha))
    c = add(add(b, v, 20), haut, -16)
    cr.arc(*c, 15, 0, 2 * math.pi)
    cr.set_source_rgba(.14, .14, .15, alpha)
    cr.fill()
    trait(cr, add(add(b, v, 40), haut, -6), add(add(b, v, 46), haut, -22), 7, (.32, .2, .1, alpha))


def lance(cr, sk, alpha=1.0):
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    trait(cr, b, t, 6, (.3, .2, .12, alpha))
    pts = [add(t, n, 7), add(t, v, 34), add(t, n, -7)]
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.close_path()
    cr.set_source_rgba(.6, .62, .66, alpha)
    cr.fill()
    trait(cr, add(t, v, -4), add(t, v, 4), 9, (.2, .2, .22, alpha))
    for s in (1, -1):
        trait(cr, add(t, v, -6), add(add(t, v, -22), n, 6 * s), 2, (.7, .1, .1, alpha))


def masse(cr, sk, alpha=1.0):
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    trait(cr, b, t, 8, (.25, .18, .12, alpha))
    cr.arc(*t, 17, 0, 2 * math.pi)
    cr.set_source_rgba(.2, .2, .22, alpha)
    cr.fill()
    for i in range(8):
        a = i * math.pi / 4
        trait(cr, add(t, (math.cos(a), math.sin(a)), 14), add(t, (math.cos(a), math.sin(a)), 26), 5, (.3, .3, .33, alpha))


def bouclier(cr, sk, alpha=1.0, r=46):
    """Bouclier rond tenu main gauche (main2), vu de 3/4 : ellipse cerclée de fer, umbo."""
    c = sk["main2"]
    cr.save()
    cr.translate(*c)
    cr.scale(.42, 1)
    cr.arc(0, 0, r, 0, 2 * math.pi)
    cr.restore()
    cr.set_source_rgba(.22, .15, .1, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.45, .45, .5, alpha)
    cr.set_line_width(5)
    cr.stroke()
    cr.arc(*c, 7, 0, 2 * math.pi)
    cr.set_source_rgba(.5, .5, .55, alpha)
    cr.fill()


def kunai(cr, p, v, alpha=1.0, L=46):
    v = unit(v)
    n = (-v[1], v[0])
    q = add(p, v, -L)
    trait(cr, q, add(q, v, 16), 4, (.15, .15, .16, alpha))
    cr.arc(*add(q, v, -5), 5, 0, 2 * math.pi)
    cr.set_source_rgba(.15, .15, .16, alpha)
    cr.set_line_width(2)
    cr.stroke()
    pts = [add(add(q, v, 16), n, 6), p, add(add(q, v, 16), n, -6)]
    cr.move_to(*pts[0])
    for x in pts[1:]:
        cr.line_to(*x)
    cr.close_path()
    cr.set_source_rgba(.5, .52, .56, alpha)
    cr.fill()


def couteau(cr, sk, alpha=1.0):
    if not sk["arme"]:
        return
    b, t, v, n = _rep(sk["arme"])
    trait(cr, b, add(b, v, 18), 6, (.15, .1, .07, alpha))
    pts = [add(add(b, v, 18), n, 4), add(b, v, 52), add(add(b, v, 18), n, -4)]
    cr.move_to(*pts[0])
    for x in pts[1:]:
        cr.line_to(*x)
    cr.close_path()
    cr.set_source_rgba(.62, .64, .68, alpha)
    cr.fill()


def carreau(cr, p, v, alpha=1.0, L=70):
    v = unit(v)
    n = (-v[1], v[0])
    q = add(p, v, -L)
    trait(cr, q, p, 3, (.3, .22, .14, alpha))
    pts = [add(add(p, v, -12), n, 5), p, add(add(p, v, -12), n, -5)]
    cr.move_to(*pts[0])
    for x in pts[1:]:
        cr.line_to(*x)
    cr.close_path()
    cr.set_source_rgba(.4, .4, .44, alpha)
    cr.fill()
    for s in (1, -1):
        trait(cr, add(q, v, 4), add(add(q, v, 16), n, 6 * s), 2.2, (.75, .2, .15, alpha))


def balle(cr, lueur, p, v, alpha=1.0):
    """Balle traçante : trait jaune-blanc + lueur."""
    v = unit(v)
    trait(cr, add(p, v, -60), p, 3, (1, .85, .45, .7 * alpha))
    trait(cr, add(p, v, -14), p, 4, (1, 1, .9, alpha))
    lueur.arc(*p, 14, 0, 2 * math.pi)
    lueur.set_source_rgba(1, .8, .3, .6 * alpha)
    lueur.fill()


def flash_bouche(cr, lueur, p, v, alpha=1.0):
    v = unit(v)
    n = (-v[1], v[0])
    for s, l_ in ((0, 46), (.6, 26), (-.6, 26)):
        d = unit(add(v, n, s))
        cr.move_to(*add(p, n, 5))
        cr.line_to(*add(p, d, l_))
        cr.line_to(*add(p, n, -5))
        cr.close_path()
        cr.set_source_rgba(1, .9, .5, alpha)
        cr.fill()
    lueur.arc(*p, 40, 0, 2 * math.pi)
    lueur.set_source_rgba(1, .7, .2, alpha)
    lueur.fill()


class Projectile:
    """Trajectoire rectiligne (ou balistique légère) p0(t0) -> p1(t1), puis éventuellement déviée ou plantée."""
    def __init__(self, t0, t1, p0, p1, kind="carreau", apres=None, g=0.0):
        self.t0, self.t1, self.p0, self.p1, self.kind, self.apres, self.g = t0, t1, p0, p1, kind, apres, g

    def pos(self, t):
        p0 = self.p0(self.t0) if callable(self.p0) else self.p0
        p1 = self.p1(self.t1) if callable(self.p1) else self.p1
        if t <= self.t1:
            u = (t - self.t0) / (self.t1 - self.t0)
            p = lerp_pt(p0, p1, u)
            return (p[0], p[1] - self.g * u * (1 - u)), sub(p1, p0)
        if self.apres:
            return self.apres(t, p1, sub(p1, p0))
        return p1, sub(p1, p0)


def dissout(fx, e, t, couleur=(.04, .04, .05), n=26):
    """Le corps se dissout (pour la boucle : aucun cadavre ne reste). Renvoie les clés à poser."""
    sk = e.squelette(t)
    for nom in ("tete", "epaule", "bassin", "genou1", "genou2", "main1", "main2"):
        p = sk[nom]
        for _ in range(n // 7):
            a = fx.rng.uniform(-math.pi, 0)
            v = fx.rng.uniform(100, 380)
            fx.ajoute(k="fumee", t0=t + fx.rng.uniform(0, .1), vie=.7, p=p, v=(math.cos(a) * v, math.sin(a) * v - 80),
                      r0=10, r1=40, coul=couleur, a=.5)
