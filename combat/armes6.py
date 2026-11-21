"""Armes v6 : arc + flèches, éventail tranchant, shurikens ; projectiles (vol, plantés au sol ou dans le corps)."""
import math

import cairo
import numpy as np
from scipy.interpolate import PchipInterpolator

from corps3 import SOL, add, dist, lerp_pt, poly, sub, trait, unit


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


# ------------------------------------------------------------------ flèche / shuriken
def fleche(cr, queue, pointe, alpha=1.0, lueur=None):
    v = unit(sub(pointe, queue))
    n = (-v[1], v[0])
    trait(cr, queue, add(pointe, v, -14), 4.2, (.28, .24, .22, alpha))
    poly(cr, [add(pointe, v, 6), add(add(pointe, v, -16), n, 7), add(pointe, v, -11), add(add(pointe, v, -16), n, -7)],
         (.06, .06, .07, alpha))
    for s in (1, -1):
        poly(cr, [add(queue, v, 30), add(add(queue, v, 2), n, 9 * s), add(queue, v, 6)], (.55, .55, .58, alpha))


def shuriken(cr, c, ang, alpha=1.0, r=24):
    cr.save()
    cr.translate(*c)
    cr.rotate(ang)
    cr.move_to(r, 0)
    for i in range(8):
        a = (i + 1) * math.pi / 4
        rr = r if i % 2 == 1 else r * .32
        cr.line_to(math.cos(a) * rr, math.sin(a) * rr)
    cr.close_path()
    cr.set_source_rgba(.16, .17, .2, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.75, .78, .84, alpha)
    cr.set_line_width(1.6)
    cr.stroke()
    cr.arc(0, 0, r * .16, 0, 2 * math.pi)
    cr.set_source_rgba(.9, .9, .92, alpha)
    cr.fill()
    cr.restore()


def eventail_dessin(cr, pivot, direction, ouverture, alpha=1.0, r=96, spin=0.0, ecart=None):
    """Éventail de guerre : lames métalliques en secteur, arête tranchante claire."""
    span = math.radians(ecart if ecart is not None else 12 + 150 * ouverture)
    a0 = math.atan2(direction[1], direction[0]) + spin
    cr.save()
    cr.translate(*pivot)
    cr.move_to(0, 0)
    cr.arc(0, 0, r, a0 - span / 2, a0 + span / 2)
    cr.close_path()
    cr.set_source_rgba(.78, .8, .86, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.08, .08, .1, alpha)
    cr.set_line_width(2.6)
    cr.stroke()
    n = 7
    for i in range(n + 1):
        a = a0 - span / 2 + span * i / n
        cr.move_to(0, 0)
        cr.line_to(math.cos(a) * r * .97, math.sin(a) * r * .97)
    cr.set_source_rgba(.12, .12, .15, .8 * alpha)
    cr.set_line_width(2)
    cr.stroke()
    cr.arc(0, 0, r - 6, a0 - span / 2 + .04, a0 + span / 2 - .04)
    cr.set_source_rgba(1, 1, 1, .85 * alpha)
    cr.set_line_width(2.4)
    cr.stroke()
    cr.arc(0, 0, r * .3, a0 - span / 2, a0 + span / 2)
    cr.set_source_rgba(.55, .08, .1, .9 * alpha)              # bande rouge sombre (signature visuelle)
    cr.set_line_width(7)
    cr.stroke()
    cr.arc(0, 0, 7, 0, 2 * math.pi)
    cr.set_source_rgba(.05, .05, .06, alpha)
    cr.fill()
    cr.restore()


# ------------------------------------------------------------------ armes tenues
class Arc:
    """Arc tenu par la main avant (main1). w = direction de la branche haute ; o = tension (corde -> main2)."""
    L, g0, deux = 236, .5, False
    trainee = False
    lueur = (1.0, .9, .6)
    trainee_coul = (.1, .1, .12)

    def geo(self, sk):
        b, t = sk["arme"]
        m = sk["main1"]
        u = unit(sub(t, b))
        v = sub(m, sk["main2"])
        k = v[0] * u[0] + v[1] * u[1]
        av = unit((v[0] - k * u[0], v[1] - k * u[1]))
        return b, t, m, av

    def lame(self, seg, d):
        return seg

    def dessiner_sk(self, cr, sk, alpha=1.0, fleche_prete=True):
        if not sk["arme"]:
            return
        b, t, m, av = self.geo(sk)
        ctrl = add(m, av, 46)
        cr.move_to(*b)
        cr.curve_to(*lerp_pt(b, ctrl, .7), *lerp_pt(t, ctrl, .7), *t)
        cr.set_source_rgba(.12, .1, .1, alpha)
        cr.set_line_width(8)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.stroke()
        trait(cr, add(m, unit(sub(t, b)), -16), add(m, unit(sub(t, b)), 16), 12, (.5, .35, .2, alpha))
        o = max(0.0, min(1.0, sk.get("o", 0)))
        corde = lerp_pt(lerp_pt(b, t, .5), sk["main2"], o) if o > .02 else lerp_pt(b, t, .5)
        cr.move_to(*b)
        cr.line_to(*corde)
        cr.line_to(*t)
        cr.set_source_rgba(.85, .85, .88, alpha)
        cr.set_line_width(1.8)
        cr.stroke()
        if o > .15 and fleche_prete:
            v = unit(sub(m, corde))
            fleche(cr, corde, add(corde, v, 200), alpha)


class Eventail:
    """Éventail tranchant tenu en main1 : pivot = main, w = direction du centre, o = ouverture."""
    L, g0, deux = 96, 0.0, False
    lueur = (1.0, .75, .7)
    trainee_coul = (.08, .08, .1)

    def lame(self, seg, d):
        b, t = seg
        return lerp_pt(b, t, .45), t

    def dessiner_sk(self, cr, sk, alpha=1.0):
        if not sk["arme"]:
            return
        b, t = sk["arme"]
        eventail_dessin(cr, b, unit(sub(t, b)), sk.get("o", 0), alpha)


# ------------------------------------------------------------------ projectiles
class Projectile:
    """Trajet (t, x, y) interpolé ; ensuite : planté au sol, planté dans un os d'un acteur, ou disparu (rattrapé)."""
    def __init__(self, genre, cles, tours_s=0.0, fin="sol", cible=None, os_=("bassin", "epaule"), lueur=False,
                 angle_fin=None):
        cles = sorted(cles, key=lambda c: c[0])
        cles = [c for i, c in enumerate(cles) if i == 0 or c[0] - cles[i - 1][0] > 1e-4]
        self.genre, self.cles, self.tours, self.fin, self.cible, self.os, self.lueur = genre, cles, tours_s, fin, cible, os_, lueur
        ts = [c[0] for c in cles]
        self.t0, self.t1 = ts[0], ts[-1]
        self.fx = PchipInterpolator(ts, [c[1] for c in cles])
        self.fy = PchipInterpolator(ts, [c[2] for c in cles])
        self.colle = None
        self.angle_fin = angle_fin

    def pos(self, t):
        t = min(max(t, self.t0), self.t1)
        return (float(self.fx(t)), float(self.fy(t)))

    def dir(self, t):
        a, b = self.pos(t - .004), self.pos(t)
        if t - .004 < self.t0:
            a, b = self.pos(self.t0), self.pos(self.t0 + .004)
        return unit(sub(b, a))

    def figer(self):
        """À l'impact, mémorise la position relative à l'os de la cible (pour suivre le corps ensuite)."""
        if self.fin == "corps" and self.cible:
            sk = self.cible.squelette(self.t1)
            o0, o1 = sk[self.os[0]], sk[self.os[1]]
            ax = unit(sub(o1, o0))
            rel = sub(self.pos(self.t1), o0)
            d = self.dir(self.t1)
            self.colle = ((rel[0] * ax[0] + rel[1] * ax[1], -rel[0] * ax[1] + rel[1] * ax[0]),
                          math.atan2(d[1], d[0]) - math.atan2(ax[1], ax[0]))

    def etat(self, t):
        """-> (position, angle) ou None."""
        if t < self.t0:
            return None
        if t <= self.t1:
            d = self.dir(t)
            if self.genre in ("shuriken", "eventail"):
                return self.pos(t), self.tours * 2 * math.pi * (t - self.t0)
            return self.pos(t), math.atan2(d[1], d[0])
        if self.fin == "disparait":
            return None
        if self.fin == "corps" and self.colle:
            sk = self.cible.squelette(t)
            o0, o1 = sk[self.os[0]], sk[self.os[1]]
            ax = unit(sub(o1, o0))
            (u, v), da = self.colle
            p = add(add(o0, ax, u), (-ax[1], ax[0]), v)
            return p, math.atan2(ax[1], ax[0]) + da
        d = self.dir(self.t1)
        ang = math.atan2(d[1], d[0]) if self.angle_fin is None else self.angle_fin
        if self.genre in ("shuriken", "eventail"):
            ang = self.tours * 2 * math.pi * (self.t1 - self.t0)
        return self.pos(self.t1), ang

    def dessiner(self, cr, lueur_cr, t):
        e = self.etat(t)
        if not e:
            return
        p, a = e
        vol = self.t0 <= t <= self.t1
        if vol:                                        # traînée de vitesse
            for i in range(1, 8):
                q0, q1 = self.pos(t - i * .008), self.pos(t - (i - 1) * .008)
                if t - i * .008 < self.t0:
                    break
                trait(cr, q0, q1, (6 if self.genre == "fleche" else 14) * (1 - i / 8), (.2, .2, .22, .5 * (1 - i / 8)))
                if self.lueur and lueur_cr is not None:
                    trait(lueur_cr, q0, q1, 40, (1, .85, .5, .8 * (1 - i / 8)))
        if self.genre == "fleche":
            v = (math.cos(a), math.sin(a))
            enf = 0 if vol else (55 if self.fin == "corps" else 40)        # partie enfoncée
            pointe = add(p, v, enf)
            fleche(cr, add(pointe, v, -200), pointe)
            if self.lueur and lueur_cr is not None and vol:
                trait(lueur_cr, add(pointe, v, -200), pointe, 34, (1, .9, .6, .9))
        elif self.genre == "shuriken":
            shuriken(cr, p, a)
        elif self.genre == "eventail":
            eventail_dessin(cr, p, (1, 0), 1, spin=a, ecart=300)
