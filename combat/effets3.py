"""Couches floues (fumée, ombres, lueurs), décor « pièce blanche », fumée volumétrique."""
import math

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter

from corps3 import EP, H, HORIZON, LONG, SOL, W

Q = 4                     # les couches floues sont calculées en 1/4 de résolution


class Couche:
    def __init__(self):
        self.s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // Q, H // Q)
        self.cr = cairo.Context(self.s)

    def debut(self, matrice):
        cr = self.cr
        cr.identity_matrix()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.scale(1 / Q, 1 / Q)
        cr.transform(matrice)
        return cr

    def poser(self, cr, sigma, additif=False, alpha=1.0):
        self.s.flush()
        a = np.ndarray((H // Q, W // Q, 4), np.uint8, self.s.get_data()).astype(np.float32)
        if sigma > 0:
            a = gaussian_filter(a, sigma=(sigma, sigma, 0))
        np.ndarray((H // Q, W // Q, 4), np.uint8, self.s.get_data())[:] = np.clip(a, 0, 255).astype(np.uint8)
        self.s.mark_dirty()
        cr.save()
        cr.identity_matrix()
        cr.scale(Q, Q)
        cr.set_source_surface(self.s, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        if additif:
            cr.set_operator(cairo.OPERATOR_ADD)
        cr.paint_with_alpha(alpha)
        cr.restore()


def decor(cr):
    """Fond blanc pur, bande d'horizon grise douce juste au-dessus des pieds (comme l'exemple du fusil)."""
    cr.set_source_rgb(.985, .985, .988)
    cr.rectangle(-4000, -3000, 12000, 9000)
    cr.fill()
    y0 = SOL - 92
    for i_, (dy, a, w) in enumerate(((0, .10, 70), (0, .10, 40), (0, .12, 18))):
        g = cairo.LinearGradient(0, y0 - w, 0, y0 + w)
        g.add_color_stop_rgba(0, .55, .55, .58, 0)
        g.add_color_stop_rgba(.5, .55, .55, .58, a)
        g.add_color_stop_rgba(1, .55, .55, .58, 0)
        cr.set_source(g)
        cr.rectangle(-4000, y0 - w, 12000, 2 * w)
        cr.fill()


def vignette(cr, haut):
    g = cairo.RadialGradient(W / 2, (haut + H) / 2, 300, W / 2, (haut + H) / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, .04)
    cr.set_source(g)
    cr.rectangle(0, haut, W, H - haut)
    cr.fill()


class Fumee:
    """Bouffées qui gonflent, montent, ralentissent ; dessinées dans une couche floue (aspect volumétrique)."""
    def __init__(self, rng):
        self.rng, self.p = rng, []

    def bouffee(self, pos, n=10, force=260, taille=40, vie=1.0, gris=.55, haut=.4, dirx=0.0, alpha=.75,
                coul=None, etal=0.0):
        r = self.rng
        for _ in range(n):
            a = r.uniform(-math.pi, 0)
            v = [math.cos(a) * force * r.uniform(.3, 1) + dirx * force, math.sin(a) * force * r.uniform(.15, haut)]
            self.p.append(dict(pos=[pos[0] + r.uniform(-etal, etal), pos[1] + r.uniform(-8, 4)], vit=v,
                               age=0.0, vie=vie * r.uniform(.75, 1.25), r=taille * r.uniform(.6, 1.3),
                               g=gris + r.uniform(-.05, .05), a=alpha, coul=coul))

    def maj(self, dt):
        for q in self.p:
            q["age"] += dt
            k = math.exp(-2.6 * dt)
            q["vit"][0] *= k
            q["vit"][1] = q["vit"][1] * k - 22 * dt
            q["pos"][0] += q["vit"][0] * dt
            q["pos"][1] = min(SOL + 20, q["pos"][1] + q["vit"][1] * dt)
            q["r"] += 34 * dt
        self.p = [q for q in self.p if q["age"] < q["vie"]]

    def dessiner(self, cr):
        for q in self.p:
            u = q["age"] / q["vie"]
            a = q["a"] * min(1, u * 8) * (1 - u) ** 1.3
            c = q["coul"] or (q["g"], q["g"], q["g"] + .01)
            cr.set_source_rgba(*c, a)
            cr.arc(*q["pos"], q["r"], 0, 2 * math.pi)
            cr.fill()


def ombre(cr, x, air, large=1.0):
    s = max(.25, 1 - air / 600)
    cr.save()
    cr.translate(x, SOL + 6)
    cr.scale(1, .22)
    cr.set_source_rgba(.18, .18, .2, .5 * s)
    cr.arc(0, 0, 70 * s * large, 0, 2 * math.pi)
    cr.fill()
    cr.restore()


def eclat(cr, pos, u, taille, coul=(1, .95, .8)):
    """Étoile à 4 branches (scintillement d'impact)."""
    if u >= 1:
        return
    s = taille * (1 - u) ** .7 * (.6 + .8 * min(1, u * 5))
    cr.save()
    cr.translate(*pos)
    cr.rotate(.3)
    cr.set_source_rgba(*coul, 1 - u)
    for a in range(4):
        cr.rotate(math.pi / 2)
        cr.move_to(0, -s * .09)
        cr.line_to(s, 0)
        cr.line_to(0, s * .09)
        cr.close_path()
        cr.fill()
    cr.restore()


def ombre_projetee(cr, sk, couleur=(0, 0, 0)):
    """Ombre portée du squelette (lumière en haut à gauche) : s'étire et se déforme avec la pose,
    se détache et s'élargit en s'éloignant quand le perso est en l'air."""
    def proj(p):
        hgt = SOL - p[1]
        return (p[0] + hgt * .42, SOL + 8 + hgt * .05)
    air = sk["air"]
    a = max(.15, 1 - air / 700)
    cr.set_source_rgba(*couleur, a)
    for u, v in (("bassin", "epaule"), ("epaule", "cou"), ("bassin", "genou1"), ("genou1", "pied1"),
                 ("bassin", "genou2"), ("genou2", "pied2"), ("epaule", "coude1"), ("coude1", "main1"),
                 ("epaule", "coude2"), ("coude2", "main2")):
        p0, p1 = proj(sk[u]), proj(sk[v])
        cr.set_line_width(EP * 1.15 * (1 + air / 500))
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(*p0)
        cr.line_to(*p1)
        cr.stroke()
    c = proj(sk["tete"])
    cr.save()
    cr.translate(*c)
    cr.scale(1.3, .5)
    cr.arc(0, 0, LONG["tete"] * (1 + air / 500), 0, 2 * math.pi)
    cr.fill()
    cr.restore()
    # tache de contact sous les pieds (plus dense)
    cr.save()
    cr.translate(sk["bassin"][0] + 20, SOL + 6)
    cr.scale(1, .2)
    cr.arc(0, 0, 60 * max(.3, 1 - air / 400), 0, 2 * math.pi)
    cr.fill()
    cr.restore()
