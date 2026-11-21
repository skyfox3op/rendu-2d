"""Chakram : anneau de lame à dents, tenu par le bord ; vol libre (boomerang, ricochet), images rémanentes."""
import math

import cairo
import numpy as np
from scipy.interpolate import PchipInterpolator

from corps3 import add, dist, lerp_pt, sub, unit

R = 56            # rayon extérieur
L_ARME = 2 * R + 6


def chakram(cr, centre, axe, ecrase, spin, alpha=1.0, lueur=False):
    """centre ; axe = angle (rad) de la direction écrasée ; ecrase = 0..1 (1 = vu de face) ; spin = rotation propre."""
    cr.save()
    cr.translate(*centre)
    cr.rotate(axe)
    cr.scale(max(.12, ecrase), 1)
    cr.rotate(spin)
    # dents
    n = 9
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        p0 = (ca * (R - 4), sa * (R - 4))
        p1 = (math.cos(a + .32) * (R + 15), math.sin(a + .32) * (R + 15))
        p2 = (math.cos(a + .55) * (R - 2), math.sin(a + .55) * (R - 2))
        cr.move_to(*p0)
        cr.line_to(*p1)
        cr.line_to(*p2)
        cr.close_path()
    cr.set_source_rgba(.12, .12, .14, alpha)
    cr.fill()
    # anneau
    cr.new_path()
    cr.arc(0, 0, R, 0, 2 * math.pi)
    cr.new_sub_path()
    cr.arc_negative(0, 0, R - 17, 2 * math.pi, 0)
    cr.set_source_rgba(.80, .81, .86, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.10, .10, .12, alpha)
    cr.set_line_width(3)
    cr.stroke()
    cr.arc(0, 0, R - 8.5, -1.9, -.4)
    cr.set_source_rgba(1, 1, 1, .7 * alpha)
    cr.set_line_width(2.4)
    cr.stroke()
    # poignée gainée (noire) sur le bord intérieur
    cr.arc(0, 0, R - 8.5, math.pi * .82, math.pi * 1.18)
    cr.set_source_rgba(.05, .05, .06, alpha)
    cr.set_line_width(19)
    cr.stroke()
    cr.restore()


def en_main(sk):
    """(centre, axe, ecrase) du chakram tenu : segment main -> bord opposé."""
    m, f = sk["arme"]
    v = sub(f, m)
    l = math.hypot(*v)
    return lerp_pt(m, f, .5), math.atan2(v[1], v[0]), min(1, l / L_ARME)


class Vol:
    """Phases de vol libre : liste de (t, x, y). Rotation propre rapide, légère inclinaison constante."""
    def __init__(self):
        self.phases = []

    def ajouter(self, cles, tours_s=7.0, ecrase=.82):
        ts = np.array([c[0] for c in cles])
        self.phases.append(dict(t0=ts[0], t1=ts[-1], x=PchipInterpolator(ts, [c[1] for c in cles]),
                                y=PchipInterpolator(ts, [c[2] for c in cles]), tours=tours_s, ecrase=ecrase,
                                cles=cles))

    def phase(self, t):
        for p in self.phases:
            if p["t0"] <= t <= p["t1"]:
                return p
        return None

    def etat(self, t):
        p = self.phase(t)
        if not p:
            return None
        c = (float(p["x"](t)), float(p["y"](t)))
        return c, -.25, p["ecrase"], -2 * math.pi * p["tours"] * (t - p["t0"])


def fantomes(cr, acteur, t, dessiner, couleur, seuil=900, n=4, pas=.022):
    """Images rémanentes quand le perso se déplace très vite (dash)."""
    v = dist(acteur.squelette(t)["bassin"], acteur.squelette(max(0, t - pas))["bassin"]) / pas
    if v < seuil:
        return v
    k = min(1, (v - seuil) / 900)
    for i in range(n, 0, -1):
        sk = acteur.squelette(max(0, t - i * pas))
        c = tuple(min(1, x + .35 + .1 * i) for x in couleur)
        dessiner(cr, sk, c, alpha=.42 * k * (1 - i / (n + 1)))
    return v


def lignes_vitesse(cr, centre, direction, k, rng):
    d = unit(direction)
    n_ = (-d[1], d[0])
    for _ in range(int(9 * k)):
        o = add(centre, n_, rng.uniform(-110, 110))
        o = add(o, d, -rng.uniform(60, 200))
        l = rng.uniform(80, 260) * k
        cr.set_source_rgba(.25, .25, .27, rng.uniform(.25, .6) * k)
        cr.set_line_width(rng.uniform(1.5, 4))
        cr.move_to(*o)
        cr.line_to(*add(o, d, -l))
        cr.stroke()


def trainee_centre(cr, lueur, etat, t, duree=.09, seuil=600, couleur_lueur=None):
    """Traînée du chakram : suit le chemin de son centre (anneau quand il tourne autour du doigt)."""
    pts = []
    for i in range(int(duree * 360) + 1):
        s = etat(t - i / 360)
        if not s:
            break
        pts.append(s[0])
    for i in range(len(pts) - 1, 0, -1):
        p_old, p_new = pts[i], pts[i - 1]
        v = dist(p_old, p_new) * 360
        f = min(1, max(0, (v - seuil) / 900))
        if f <= 0:
            continue
        u = i / (len(pts) - 1)
        g = .06 + .7 * u ** .8
        a = f * (1 - u) ** 1.2
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(g, g, g + .01, a * .85)
        cr.set_line_width(2 * R * (1 - .55 * u))
        cr.move_to(*p_old)
        cr.line_to(*p_new)
        cr.stroke()
        if couleur_lueur and lueur is not None:
            lueur.set_source_rgba(*couleur_lueur, a * .8)
            lueur.set_line_width(2 * R * 1.3)
            lueur.move_to(*p_old)
            lueur.line_to(*p_new)
            lueur.stroke()
