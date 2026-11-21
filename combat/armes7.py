"""Armes v7 (designées, lisibles) : éventail de guerre + shurikens, parapluie, cartes à jouer, violon + archet."""
import math

import cairo
import numpy as np
from scipy.interpolate import PchipInterpolator

from corps3 import SOL, add, dist, lerp_pt, poly, sub, trait, unit


def _ang(v):
    return math.atan2(v[1], v[0])


# =================================================================== éventail + shuriken
def eventail(cr, pivot, direction, o, alpha=1.0, r=104, spin=0.0, ecart=None):
    span = math.radians(ecart if ecart is not None else 10 + 158 * o)
    a0 = _ang(direction) + spin
    cr.save()
    cr.translate(*pivot)
    # papier rouge profond
    cr.move_to(0, 0)
    cr.arc(0, 0, r, a0 - span / 2, a0 + span / 2)
    cr.close_path()
    g = cairo.RadialGradient(0, 0, r * .2, 0, 0, r)
    g.add_color_stop_rgba(0, .45, .04, .07, alpha)
    g.add_color_stop_rgba(1, .78, .10, .14, alpha)
    cr.set_source(g)
    cr.fill()
    # motif doré (deux arcs)
    for rr in (.55, .72):
        cr.arc(0, 0, r * rr, a0 - span / 2 + .05, a0 + span / 2 - .05)
        cr.set_source_rgba(.95, .78, .3, .85 * alpha)
        cr.set_line_width(2.2)
        cr.stroke()
    # baleines laquées noires
    n = 9
    for i in range(n + 1):
        a = a0 - span / 2 + span * i / n
        cr.move_to(0, 0)
        cr.line_to(math.cos(a) * r * .93, math.sin(a) * r * .93)
    cr.set_source_rgba(.05, .04, .05, alpha)
    cr.set_line_width(3)
    cr.stroke()
    # tranchant acier
    cr.arc(0, 0, r, a0 - span / 2, a0 + span / 2)
    cr.set_source_rgba(.82, .85, .9, alpha)
    cr.set_line_width(7)
    cr.stroke()
    cr.arc(0, 0, r + 2, a0 - span / 2, a0 + span / 2)
    cr.set_source_rgba(1, 1, 1, .9 * alpha)
    cr.set_line_width(1.8)
    cr.stroke()
    cr.arc(0, 0, 8, 0, 2 * math.pi)
    cr.set_source_rgba(.95, .78, .3, alpha)
    cr.fill()
    cr.restore()


def shuriken(cr, c, ang, alpha=1.0, r=34):
    cr.save()
    cr.translate(*c)
    cr.rotate(ang)
    cr.move_to(r, 0)
    for i in range(8):
        a = (i + 1) * math.pi / 4
        rr = r if i % 2 == 1 else r * .3
        cr.line_to(math.cos(a) * rr, math.sin(a) * rr)
    cr.close_path()
    cr.set_source_rgba(.62, .65, .72, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.08, .08, .1, alpha)
    cr.set_line_width(2.4)
    cr.stroke()
    for i in range(4):                         # reflets sur les pointes
        a = i * math.pi / 2 + .25
        trait(cr, (math.cos(a) * r * .35, math.sin(a) * r * .35), (math.cos(a + .1) * r * .85, math.sin(a + .1) * r * .85),
              2, (1, 1, 1, .8 * alpha))
    cr.arc(0, 0, r * .2, 0, 2 * math.pi)
    cr.set_source_rgba(.8, .1, .14, alpha)
    cr.fill()
    cr.arc(0, 0, r * .08, 0, 2 * math.pi)
    cr.set_source_rgba(.95, .95, .97, alpha)
    cr.fill()
    cr.restore()


class Eventail:
    L, g0, deux, trainee = 104, 0.0, False, True
    lueur = (1.0, .5, .45)
    trainee_coul = (.25, .02, .05)

    def lame(self, seg, d):
        return lerp_pt(*seg, .5), seg[1]

    def dessiner_sk(self, cr, sk, alpha=1.0):
        if sk["arme"]:
            eventail(cr, sk["arme"][0], unit(sub(sk["arme"][1], sk["arme"][0])), sk.get("o", 0), alpha)


# =================================================================== parapluie
class Parapluie:
    """Tenu près de la poignée en J. o = ouverture (0 fermé : canne-épée ; 1 ouvert : bouclier)."""

    def dessiner_m1(self, cr, sk, alpha=1.0):
        self.dessiner_sk(cr, sk, alpha)
    L, g0, deux, trainee = 250, .07, False, True
    lueur = (.7, .85, 1.0)
    trainee_coul = (.05, .06, .1)

    def lame(self, seg, d):
        return lerp_pt(*seg, .45), seg[1]

    def dessiner_sk(self, cr, sk, alpha=1.0):
        if not sk["arme"]:
            return
        b, t = sk["arme"]
        u = unit(sub(t, b))
        n = (-u[1], u[0]) if sk["d"] > 0 else (u[1], -u[0])
        o = max(0.0, min(1.0, sk.get("o", 0)))
        # poignée en J (bois verni)
        cr.move_to(*b)
        c1 = add(b, u, -40)
        cr.curve_to(*c1, *add(c1, n, 34), *add(add(b, u, -22), n, 36))
        cr.set_source_rgba(.42, .24, .12, alpha)
        cr.set_line_width(11)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.stroke()
        trait(cr, b, t, 5, (.12, .12, .14, alpha))                     # tige
        trait(cr, add(t, u, -16), add(t, u, 10), 5, (.85, .86, .9, alpha))   # embout argent
        if o < .08:                                                  # fermé : toile roulée + bride
            c0, c2 = lerp_pt(b, t, .3), lerp_pt(b, t, .9)
            m = lerp_pt(c0, c2, .55)
            poly(cr, [c0, add(m, n, 14), c2, add(m, n, -14)], (.06, .06, .08, alpha))
            trait(cr, add(c0, n, 3), add(c2, n, 2), 1.6, (.45, .47, .55, .8 * alpha))
            trait(cr, add(m, n, -15), add(m, n, 15), 4, (.55, .1, .12, alpha))
        else:                                                         # ouvert : dôme + baleines
            A_, B_ = 64 * o, 138 * o
            c = add(t, u, -A_ - 6)
            rim = []
            for k_ in range(17):
                th = math.radians(-90 + 180 * k_ / 16)
                rim.append(add(add(c, u, A_ * math.cos(th)), n, B_ * math.sin(th)))
            cr.move_to(*rim[0])
            for q in rim[1:]:
                cr.line_to(*q)
            bords = [rim[0]] + [add(c, n, B_ * (-1 + 2 * k_ / 6)) for k_ in range(1, 6)] + [rim[-1]]
            for k_ in range(len(bords) - 1, 0, -1):                   # festons du bord
                mid = lerp_pt(bords[k_], bords[k_ - 1], .5)
                cr.curve_to(*add(mid, u, 14 * o), *add(mid, u, 14 * o), *bords[k_ - 1])
            cr.close_path()
            g = cairo.LinearGradient(*add(c, n, -B_), *add(c, n, B_))
            g.add_color_stop_rgba(0, .05, .05, .07, alpha)
            g.add_color_stop_rgba(.45, .2, .21, .27, alpha)
            g.add_color_stop_rgba(1, .04, .04, .06, alpha)
            cr.set_source(g)
            cr.fill()
            for q in bords:
                cr.move_to(*t)
                cr.curve_to(*add(lerp_pt(t, q, .5), u, 30 * o), *add(lerp_pt(t, q, .5), u, 30 * o), *q)
            cr.set_source_rgba(.55, .57, .65, .9 * alpha)
            cr.set_line_width(2)
            cr.stroke()
            trait(cr, rim[0], rim[-1], 0.1, (0, 0, 0, 0))
            for k_ in range(len(bords) - 1):
                trait(cr, bords[k_], bords[k_ + 1], 2.5, (.55, .1, .12, alpha))
            trait(cr, b, t, 5, (.12, .12, .14, alpha))


# =================================================================== cartes à jouer
CARTES = [("A", "♠", (0, 0, 0)), ("Q", "♥", (.8, .05, .1)), ("J", "♣", (0, 0, 0)), ("K", "♦", (.8, .05, .1)),
          ("JOKER", "★", (.55, .1, .6)), ("7", "♥", (.8, .05, .1)), ("A", "♦", (.8, .05, .1))]


def carte(cr, c, ang, idx=0, alpha=1.0, k=1.0, face=True):
    w, h = 50 * k, 72 * k
    lettre, couleur_s, col = CARTES[idx % len(CARTES)]
    cr.save()
    cr.translate(*c)
    cr.rotate(ang)
    r = 6 * k
    cr.new_sub_path()
    cr.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
    cr.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
    cr.arc(w / 2 - r, h / 2 - r, r, 0, .5 * math.pi)
    cr.arc(-w / 2 + r, h / 2 - r, r, .5 * math.pi, math.pi)
    cr.close_path()
    cr.set_source_rgba(.98, .97, .94, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.1, .1, .12, alpha)
    cr.set_line_width(2)
    cr.stroke()
    if face:
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_source_rgba(*col, alpha)
        cr.set_font_size(15 * k if lettre != "JOKER" else 8 * k)
        cr.move_to(-w / 2 + 4 * k, -h / 2 + 15 * k)
        cr.show_text(lettre if lettre != "JOKER" else "JOKER")
        cr.set_font_size(30 * k)
        e = cr.text_extents(couleur_s)
        cr.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
        cr.show_text(couleur_s)
    else:
        cr.rectangle(-w / 2 + 5 * k, -h / 2 + 5 * k, w - 10 * k, h - 10 * k)
        cr.set_source_rgba(.6, .08, .14, alpha)
        cr.fill()
    cr.restore()


class Cartes:
    """Éventail de cartes tenu en main1 (o = ouverture de l'éventail de cartes)."""
    L, g0, deux, trainee = 70, 0.0, False, False
    lueur = (.9, .5, 1.0)
    trainee_coul = (.2, .05, .25)

    def lame(self, seg, d):
        return seg

    def dessiner_sk(self, cr, sk, alpha=1.0):
        if not sk["arme"]:
            return
        b, t = sk["arme"]
        u = unit(sub(t, b))
        o = sk.get("o", 0)
        n = 5 if o <= 1 else 5 + int(round(6 * (o - 1)))          # o > 1 : grand mur de cartes
        pas = math.radians(14) * min(o, 1) if o <= 1 else math.radians(14)
        for i in range(n):
            da = (i - (n - 1) / 2) * pas
            v = (u[0] * math.cos(da) - u[1] * math.sin(da), u[0] * math.sin(da) + u[1] * math.cos(da))
            carte(cr, add(b, v, 34), _ang(v) + math.pi / 2, idx=i + 1, alpha=alpha, k=.75)


# =================================================================== violon + archet
def violon(cr, centre, ang, alpha=1.0, k=1.0):
    """Violon (corps verni, ouïes, touche noire, volute) ; ang = direction corps -> volute."""
    cr.save()
    cr.translate(*centre)
    cr.rotate(ang)
    cr.scale(k, k)
    # corps : deux lobes
    cr.save()
    cr.scale(1, .62)
    for x_, r_ in ((-38, 44), (22, 37)):
        cr.arc(x_, 0, r_, 0, 2 * math.pi)
        cr.close_path()
    cr.restore()
    g = cairo.LinearGradient(-80, -30, 60, 30)
    g.add_color_stop_rgba(0, .55, .22, .06, alpha)
    g.add_color_stop_rgba(1, .78, .40, .12, alpha)
    cr.set_source(g)
    cr.fill_preserve()
    cr.set_source_rgba(.2, .07, .02, alpha)
    cr.set_line_width(2.5)
    cr.stroke()
    for s in (1, -1):                                           # ouïes
        cr.move_to(-14, 14 * s)
        cr.curve_to(-6, 8 * s, 0, 16 * s, 8, 10 * s)
        cr.set_source_rgba(.1, .03, .01, alpha)
        cr.set_line_width(2)
        cr.stroke()
    trait(cr, (-34, 0), (118, 0), 9, (.05, .05, .06, alpha))      # touche
    cr.arc(122, 0, 8, 0, 2 * math.pi)                           # volute
    cr.set_source_rgba(.45, .18, .05, alpha)
    cr.fill()
    trait(cr, (-6, -6), (-6, 6), 3, (.9, .85, .7, alpha))       # chevalet
    for dy in (-3, -1, 1, 3):
        trait(cr, (-60, dy), (118, dy * .6), .8, (.92, .92, .9, alpha))
    cr.restore()


class Archet:
    """Archet tenu en main1 (fleuret improvisé) ; le violon est porté par main2 / l'épaule."""
    L, g0, deux, trainee = 230, .08, False, True
    lueur = (1.0, .9, .6)
    trainee_coul = (.3, .15, .05)

    def lame(self, seg, d):
        return lerp_pt(*seg, .3), seg[1]

    def dessiner_m1(self, cr, sk, alpha=1.0):
        if not sk["arme"]:
            return
        b, t = sk["arme"]
        u = unit(sub(t, b))
        trait(cr, b, t, 4, (.35, .16, .05, alpha))
        trait(cr, add(b, u, 14), add(t, u, -4), 1.6, (.97, .96, .9, alpha))
        trait(cr, b, add(b, u, 18), 9, (.08, .08, .1, alpha))

    def dessiner_m2(self, cr, sk, alpha=1.0):
        m2, c2 = sk["main2"], sk["coude2"]
        if sk.get("o", 0) > .5:
            v = unit(sub(m2, sk["cou"]))
            violon(cr, add(sk["cou"], v, 40), _ang(v), alpha, .9)
        elif sk.get("o", 0) < -.5:
            v = unit(sub(m2, c2))
            violon(cr, add(m2, v, 106), _ang((-v[0], -v[1])), alpha, .9)
        else:
            v = unit(sub(m2, c2))
            violon(cr, add(m2, v, -70), _ang(v), alpha, .9)

    def dessiner_sk(self, cr, sk, alpha=1.0):
        if not sk["arme"]:
            return
        b, t = sk["arme"]
        u = unit(sub(t, b))
        n = (-u[1], u[0])
        trait(cr, b, t, 4, (.35, .16, .05, alpha))
        trait(cr, add(b, u, 14), add(add(t, u, -4), n, 0), 1.6, (.97, .96, .9, alpha))     # crins
        trait(cr, b, add(b, u, 18), 9, (.08, .08, .1, alpha))                               # hausse
        # violon (main2), tenu par le manche quand il ne joue pas
        m2, c2 = sk["main2"], sk["coude2"]
        if sk.get("o", 0) > .5:                       # en position de jeu : sous le menton, vers l'avant
            cou = sk["cou"]
            v = unit(sub(m2, cou))
            violon(cr, add(cou, v, 40), _ang(v), alpha, .9)
        elif sk.get("o", 0) < -.5:                   # massue : tenu par la volute, la caisse vers l'extérieur
            v = unit(sub(m2, c2))
            violon(cr, add(m2, v, 106), _ang((-v[0], -v[1])), alpha, .9)
        else:                                         # bouclier : tenu par le manche, caisse le long de l'avant-bras
            v = unit(sub(m2, c2))
            violon(cr, add(m2, v, -70), _ang(v), alpha, .9)


def pt_violon(sk):
    """Centre de la caisse du violon selon la prise (jeu / massue / bouclier)."""
    m2, c2 = sk["main2"], sk["coude2"]
    if sk.get("o", 0) > .5:
        v = unit(sub(m2, sk["cou"]))
        return add(sk["cou"], v, 40)
    v = unit(sub(m2, c2))
    return add(m2, v, 106) if sk.get("o", 0) < -.5 else add(m2, v, -70)


# =================================================================== projectiles
class Projectile:
    def __init__(self, genre, cles, tours_s=0.0, fin="sol", cible=None, os_=("bassin", "epaule"), lueur=False, idx=0,
                 traverse=0.0):
        cles = sorted(cles, key=lambda c: c[0])
        cles = [c for i, c in enumerate(cles) if i == 0 or c[0] - cles[i - 1][0] > 1e-4]
        self.genre, self.tours, self.fin, self.cible, self.os, self.lueur, self.idx = genre, tours_s, fin, cible, os_, lueur, idx
        self.traverse = traverse
        ts = [c[0] for c in cles]
        self.t0, self.t1 = ts[0], ts[-1]
        self.fx = PchipInterpolator(ts, [c[1] for c in cles])
        self.fy = PchipInterpolator(ts, [c[2] for c in cles])
        self.colle = None

    def pos(self, t):
        t = min(max(t, self.t0), self.t1)
        return (float(self.fx(t)), float(self.fy(t)))

    def dir(self, t):
        t = min(max(t, self.t0 + .004), self.t1)
        return unit(sub(self.pos(t), self.pos(t - .004)))

    def figer(self):
        if self.fin == "corps" and self.cible:
            sk = self.cible.squelette(self.t1)
            o0, o1 = sk[self.os[0]], sk[self.os[1]]
            ax = unit(sub(o1, o0))
            rel = sub(self.pos(self.t1), o0)
            d = self.dir(self.t1)
            self.colle = ((rel[0] * ax[0] + rel[1] * ax[1], -rel[0] * ax[1] + rel[1] * ax[0]), _ang(d) - _ang(ax))

    def etat(self, t):
        if t < self.t0:
            return None
        rot_propre = self.tours * 2 * math.pi * (min(t, self.t1) - self.t0)
        if t <= self.t1:
            return self.pos(t), (rot_propre if self.tours else _ang(self.dir(t)))
        if self.fin == "disparait":
            return None
        if self.fin == "corps" and self.colle:
            sk = self.cible.squelette(t)
            o0, o1 = sk[self.os[0]], sk[self.os[1]]
            ax = unit(sub(o1, o0))
            (u, v), da = self.colle
            return add(add(o0, ax, u), (-ax[1], ax[0]), v), _ang(ax) + da
        return self.pos(self.t1), (rot_propre if self.tours and self.genre != "carte" else _ang(self.dir(self.t1)))

    def dessiner(self, cr, lueur_cr, t):
        e = self.etat(t)
        if not e:
            return
        p, a = e
        vol = self.t0 <= t <= self.t1
        if vol:
            for i in range(1, 9):
                if t - i * .008 < self.t0:
                    break
                q0, q1 = self.pos(t - i * .008), self.pos(t - (i - 1) * .008)
                trait(cr, q0, q1, 22 * (1 - i / 9), (.25, .25, .28, .45 * (1 - i / 9)))
                if lueur_cr is not None:
                    trait(lueur_cr, q0, q1, 34, ((1, .85, .5) if not self.lueur else self.lueur) + (.5 * (1 - i / 9),))
        if self.genre == "shuriken":
            shuriken(cr, p, a)
        elif self.genre == "eventail":
            eventail(cr, p, (1, 0), 1, spin=a, ecart=320)
        elif self.genre == "carte":
            if vol:
                carte(cr, p, a, self.idx)
            else:                                     # plantée : à moitié enfoncée, de biais
                carte(cr, p, a + math.pi / 2, self.idx, k=.9)
        elif self.genre == "balle":
            trait(cr, add(p, (math.cos(a), math.sin(a)), -30), p, 5, (1, .95, .6, 1))
        elif self.genre == "note":
            cr.save()
            cr.translate(*p)
            cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(64)
            cr.set_source_rgba(.95, .75, .25, 1)
            cr.move_to(-20, 20)
            cr.show_text("♪" if self.idx % 2 else "♫")
            cr.restore()
        elif self.genre == "lame_vent":
            d = self.dir(t) if vol else (1, 0)
            if vol:
                n = (-d[1], d[0])
                for k_, (w_, al) in enumerate(((30, .25), (16, .5), (6, .95))):
                    cr.move_to(*add(p, n, -90))
                    cr.curve_to(*add(add(p, d, 50), n, -50), *add(add(p, d, 50), n, 50), *add(p, n, 90))
                    cr.set_source_rgba(.75, .95, 1, al)
                    cr.set_line_width(w_)
                    cr.stroke()
