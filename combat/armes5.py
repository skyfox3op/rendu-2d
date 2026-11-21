"""Armes v5 : épée fine (lame acier bleuté, très distincte du gris de l'adversaire) et faux."""
import math

import cairo

from corps3 import add, dist, lerp_pt, poly, sub, trait, unit


class Fine:
    """Épée fine mi-longue : poignée noire, petite garde en coupelle, lame étroite acier bleuté."""
    L, g0, deux = 178, .1, False
    lueur = (.75, .88, 1.0)
    trainee_coul = (.10, .12, .16)

    def points(self, seg, d):
        b, t = seg
        v = unit(sub(t, b))
        return dict(pommeau=b, garde=add(b, v, 30), pointe=t, v=v)

    def lame(self, seg, d):
        p = self.points(seg, d)
        return p["garde"], p["pointe"]

    def dessiner(self, cr, seg, d, alpha=1.0):
        if not seg or dist(*seg) < 10:
            return
        p = self.points(seg, d)
        v = p["v"]
        n = (-v[1], v[0])
        k = min(1, dist(*seg) / self.L)
        trait(cr, p["pommeau"], p["garde"], 9, (.05, .05, .06, alpha))
        cr.set_source_rgba(.05, .05, .06, alpha)
        cr.arc(*p["pommeau"], 6, 0, 2 * math.pi)
        cr.fill()
        g = p["garde"]
        cr.save()
        cr.translate(*g)
        cr.rotate(math.atan2(v[1], v[0]))
        cr.scale(.55, 1)
        cr.arc(0, 0, 13, 0, 2 * math.pi)
        cr.set_source_rgba(.14, .15, .18, alpha)
        cr.fill()
        cr.restore()
        b0 = add(g, v, 4)
        pts = [add(b0, n, 3.6), add(p["pointe"], v, -18 * k), p["pointe"], add(b0, n, -3.6)]
        cr.move_to(*pts[0])
        for q in pts[1:]:
            cr.line_to(*q)
        cr.close_path()
        cr.set_source_rgba(.66, .72, .82, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(.13, .15, .2, alpha)
        cr.set_line_width(1.8)
        cr.stroke()
        trait(cr, add(b0, v, 6), add(p["pointe"], v, -24 * k), 1.4, (.95, .97, 1, .8 * alpha))


class Faux:
    """Faux : longue hampe sombre, grande lame courbe perpendiculaire en haut, tournée vers l'avant."""
    L, g0, deux = 330, .58, True
    lueur = (1.0, .78, .55)
    trainee_coul = (.05, .05, .06)
    LAME = 175

    def points(self, seg, d):
        b, t = seg
        u = unit(sub(t, b))
        perp = (-u[1] * d, u[0] * d)                  # vers l'avant quand la hampe est verticale
        perp = (perp[0], perp[1]) if d > 0 else (perp[0], perp[1])
        perp = (-u[1], u[0]) if d > 0 else (u[1], -u[0])
        base = add(t, u, -6)
        pts_ext, pts_int = [], []
        n = 12
        for i in range(n + 1):
            s = i / n
            ang = -.15 + s * .75                        # part un peu vers le haut puis se recourbe vers le talon
            dirl = (perp[0] * math.cos(ang) - u[0] * math.sin(ang), perp[1] * math.cos(ang) - u[1] * math.sin(ang))
            rext = self.LAME * s
            c = add(base, dirl, rext * .95)
            c = add(c, u, 26 * math.sin(s * math.pi) * .6)
            larg = 30 * (1 - s) ** .7 + 1.5
            pts_ext.append(add(c, u, larg * .45))
            pts_int.append(add(c, u, -larg * .55))
        return dict(base=base, pointe=pts_ext[-1], ext=pts_ext, int=pts_int, u=u)

    def lame(self, seg, d):
        p = self.points(seg, d)
        return p["base"], p["pointe"]

    def dessiner(self, cr, seg, d, alpha=1.0):
        if not seg or dist(*seg) < 10:
            return
        p = self.points(seg, d)
        b, t = seg
        trait(cr, b, t, 9, (.24, .22, .22, alpha))
        trait(cr, add(t, p["u"], -40), add(t, p["u"], -8), 12, (.06, .06, .07, alpha))
        trait(cr, b, add(b, p["u"], 12), 11, (.06, .06, .07, alpha))
        cr.move_to(*p["ext"][0])
        for q in p["ext"][1:]:
            cr.line_to(*q)
        for q in reversed(p["int"]):
            cr.line_to(*q)
        cr.close_path()
        cr.set_source_rgba(.83, .84, .88, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(.08, .08, .1, alpha)
        cr.set_line_width(2.6)
        cr.stroke()
        cr.move_to(*lerp_pt(p["int"][1], p["ext"][1], .2))
        for a_, b_ in zip(p["int"][2:-1], p["ext"][2:-1]):
            cr.line_to(*lerp_pt(a_, b_, .2))
        cr.set_source_rgba(1, 1, 1, .75 * alpha)
        cr.set_line_width(1.8)
        cr.stroke()


def trainee_lame(cr, lueur, acteur, arme, t, duree=.09, seuil=850, coul_lueur=None, force=1.0):
    """Ruban suivant la LAME (base -> pointe) échantillonnée dans le temps."""
    segs = []
    for i in range(int(duree * 360) + 1):
        ti = t - i / 360
        sk = acteur.squelette(ti) if ti >= 0 else None
        if not sk or not sk["arme"] or (segs and sk["d"] != d0):
            break
        d0 = sk["d"]
        segs.append(arme.lame(sk["arme"], sk["d"]))
    if len(segs) < 3:
        return
    for i in range(len(segs) - 1, 0, -1):
        (b0, t0), (b1, t1) = segs[i], segs[i - 1]
        v = dist(t0, t1) * 360
        f = min(1, max(0, (v - seuil) / 900)) * force
        if f <= 0:
            continue
        u = i / (len(segs) - 1)
        gris = arme.trainee_coul[0] + .75 * u ** .8
        a = f * (1 - u) ** 1.2
        poly(cr, [b0, t0, t1, b1], (gris, gris, gris + .02, a * .85))
        trait(cr, t0, t1, 2.5 + 5 * (1 - u), (1, 1, 1, a))
        if coul_lueur and lueur is not None:
            trait(lueur, t0, t1, 16, (*coul_lueur, a * .9))
