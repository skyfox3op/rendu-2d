"""v11 — briques communes : cape en lambeaux animée par une brise, corde/chaîne simulée (fouet, kusarigama),
dessins soignés (fouet-lame doré, chaîne + kama + poids, grimoire), aperçu économique, helpers de chorégraphie."""
import math

import cairo
import numpy as np

import corps3 as C
from corps3 import SOL, add, dist, lerp_pt, sub, trait, unit


def _cat(pts, n=4):
    """Catmull-Rom : courbe lisse à travers les points."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            s = j / n
            s2, s3 = s * s, s * s * s
            out.append(tuple(.5 * (2 * p1[k] + (-p0[k] + p2[k]) * s + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * s2
                                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * s3) for k in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


# ===================================================================== CAPE v2
class Cape:
    """Cape plus légère et réactive (dashs, sauts), brise permanente, bas en lambeaux (pointes triangulaires)."""
    N, SEG = 10, 15

    def __init__(self, acteur, duree, coul=(.09, .08, .12), doublure=(.03, .03, .05), liseré=(.85, .68, .25), fps=60,
                 visible=None):
        self.coul, self.doub, self.lis, self.fps = coul, doublure, liseré, fps
        n_img = int(duree * fps) + 2
        sub_ = 4
        dt = 1 / (fps * sub_)
        sk = acteur.squelette(0)
        a = self.ancre(sk)
        pts = np.array([[a[0] - 5 * i * sk["d"], a[1] + self.SEG * i] for i in range(self.N)], float)
        prev = pts.copy()
        self.hist = np.zeros((n_img, self.N, 2))
        a_prec = a
        poids = np.linspace(0, 1, self.N)[:, None]
        for f in range(n_img):
            for s in range(sub_):
                t = (f + s / sub_) / fps
                sk = acteur.squelette(t)
                a = self.ancre(sk)
                if math.hypot(a[0] - a_prec[0], a[1] - a_prec[1]) > 140:
                    dd = np.array([a[0] - a_prec[0], a[1] - a_prec[1]])
                    pts += dd
                    prev += dd
                a_prec = a
                vel = (pts - prev) * .978
                prev = pts.copy()
                brise = np.array([260 * math.sin(.9 * t) + 150 * math.sin(2.3 * t + 1) + 70 * math.sin(5.7 * t + 2) - 120 * sk["d"],
                                  60 * math.sin(3.1 * t)])
                pts = pts + vel + (np.array([0, 1450]) + brise * poids) * dt * dt
                pts[0] = a
                for _ in range(3):
                    for i in range(self.N - 1):
                        d = pts[i + 1] - pts[i]
                        l = math.hypot(*d) or 1e-6
                        corr = (l - self.SEG) / l * d
                        if i == 0:
                            pts[i + 1] -= corr
                        else:
                            pts[i] += corr * .5
                            pts[i + 1] -= corr * .5
                    pts[:, 1] = np.minimum(pts[:, 1], SOL - 4)
            self.hist[f] = pts

    @staticmethod
    def ancre(sk):
        return lerp_pt(sk["epaule"], sk["cou"], .45)

    def points(self, t):
        f = min(len(self.hist) - 1, max(0, int(round(t * self.fps))))
        return self.hist[f]

    def dessiner(self, cr, t, sk, alpha=1.0):
        pts = _cat([tuple(p) for p in self.points(t)], 3)
        n_ = len(pts)
        g, dr = [], []
        for i in range(n_):
            p = pts[i]
            q = pts[i + 1] if i < n_ - 1 else add(p, sub(p, pts[i - 1]), 1)
            v = unit(sub(q, p))
            n = (-v[1], v[0])
            w = 8 + 30 * (i / (n_ - 1)) ** .8
            g.append(add(p, n, w))
            dr.append(add(p, n, -w))
        fin = unit(sub(pts[-1], pts[-4]))
        # pointes en lambeaux : 5 triangles de longueurs différentes qui flottent
        bas = []
        for k in range(6):
            u = k / 5
            b = lerp_pt(g[-1], dr[-1], u)
            bas.append(b)
        dents = []
        longs = (30, 52, 26, 60, 34)
        for k in range(5):
            m = lerp_pt(bas[k], bas[k + 1], .5)
            fl = 10 * math.sin(t * 9 + k * 1.7)
            pointe = add(add(m, fin, longs[k]), (-fin[1], fin[0]), fl)
            dents += [pointe, bas[k + 1]]
        cr.move_to(*lerp_pt(sk["epaule"], sk["cou"], .1))
        for p in g:
            cr.line_to(*p)
        for p in dents:
            cr.line_to(*p)
        for p in reversed(dr):
            cr.line_to(*p)
        cr.close_path()
        cr.set_source_rgba(*self.coul, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(*self.lis, alpha)
        cr.set_line_width(2.6)
        cr.stroke()
        cr.move_to(*lerp_pt(g[n_ // 3], dr[n_ // 3], .5))       # pli de doublure
        for i in range(n_ // 3, n_):
            cr.line_to(*lerp_pt(g[i], dr[i], .5 + .18 * math.sin(i * .5 + t * 3)))
        cr.set_source_rgba(*self.doub, .55 * alpha)
        cr.set_line_width(4)
        cr.stroke()


# ===================================================================== CORDE / CHAÎNE simulée
class Corde:
    """Chaîne verlet de n points, base tenue (base_fn), contrôles du bout : ('pin', t0, t1, f) bout collé à f(t) ;
    ('ressort', t0, t1, f, k) bout tiré vers f(t) ; ('roide', t0, t1) corde tendue (lancer droit)."""

    def __init__(self, n, longueur, base_fn, duree, controles=(), g=1500, amort=.993, fps=60, sub_=5, actif=None):
        self.n, self.seg, self.fps = n, longueur / (n - 1), fps
        n_img = int(duree * fps) + 2
        dt = 1 / (fps * sub_)
        b0 = base_fn(0)
        pts = np.array([[b0[0] - 4 * i, b0[1] + self.seg * i * .7] for i in range(n)], float)
        prev = pts.copy()
        self.hist = np.zeros((n_img, n, 2))
        for f in range(n_img):
            for s in range(sub_):
                t = (f + s / sub_) / fps
                b = base_fn(t)
                vel = (pts - prev) * amort
                prev = pts.copy()
                pts = pts + vel + np.array([0, g]) * dt * dt
                pin = None
                for c in controles:
                    if c[1] <= t < c[2]:
                        cib = np.array(c[3](t), float)
                        if c[0] == "pin":
                            pin = cib
                        elif c[0] == "ressort":
                            k = c[4]
                            pts[-1] += (cib - pts[-1]) * k
                            pts[-2] += (cib - pts[-2]) * k * .5
                pts[0] = b
                if pin is not None:
                    pts[-1] = pin
                for _ in range(6):
                    for i in range(n - 1):
                        d = pts[i + 1] - pts[i]
                        l = math.hypot(*d) or 1e-6
                        if l <= self.seg and i < n - 2:
                            continue
                        corr = (l - self.seg) / l * d
                        if i == 0:
                            pts[1] -= corr
                        elif i == n - 2 and pin is not None:
                            pts[i] += corr
                        else:
                            pts[i] += corr * .5
                            pts[i + 1] -= corr * .5
                    pts[0] = b
                    if pin is not None:
                        pts[-1] = pin
                pts[:, 1] = np.minimum(pts[:, 1], SOL - 5)
            self.hist[f] = pts

    def points(self, t):
        f = min(len(self.hist) - 1, max(0, int(round(t * self.fps))))
        return [tuple(p) for p in self.hist[f]]

    def bout(self, t):
        return self.points(t)[-1]

    def vitesse_bout(self, t):
        a, b = self.bout(t - 1 / 60), self.bout(t)
        return dist(a, b) * 60


def dessin_fouet(cr, lueur, pts, alpha=1.0, t=0.0):
    """Fouet-lame doré lumineux : tresse dorée, éclats de lame tous les 2 maillons, grande pointe en feuille."""
    c = _cat(pts, 3)
    n = len(c)
    for i in range(n - 1):
        u = i / (n - 1)
        w = 9 * (1 - u) + 3
        trait(lueur, c[i], c[i + 1], w + 16, (1, .82, .35, .5 * alpha))
        trait(cr, c[i], c[i + 1], w + 3, (.42, .28, .06, alpha))
        trait(cr, c[i], c[i + 1], w, (.98, .78, .25, alpha))
        if i % 2 == 0:
            trait(cr, c[i], lerp_pt(c[i], c[i + 1], .5), w * .4, (1, .97, .75, alpha))     # tresse
    for i in range(3, len(pts) - 2, 2):                                                  # éclats de lame
        p, q = pts[i], pts[i + 1]
        v = unit(sub(q, p))
        nn = (-v[1], v[0])
        m = lerp_pt(p, q, .5)
        s = 1 - i / len(pts)
        L_, W_ = 16 + 6 * s, 6 + 3 * s
        poly = [add(m, v, L_), add(m, nn, W_), add(m, v, -L_ * .6), add(m, nn, -W_)]
        cr.move_to(*poly[0])
        for q_ in poly[1:]:
            cr.line_to(*q_)
        cr.close_path()
        cr.set_source_rgba(.86, .88, .92, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(.35, .28, .1, alpha)
        cr.set_line_width(1.4)
        cr.stroke()
    p, q = pts[-2], pts[-1]                                                               # pointe
    v = unit(sub(q, p))
    nn = (-v[1], v[0])
    poly = [add(q, v, 34), add(add(q, v, 6), nn, 11), add(q, v, -10), add(add(q, v, 6), nn, -11)]
    cr.move_to(*poly[0])
    for q_ in poly[1:]:
        cr.line_to(*q_)
    cr.close_path()
    cr.set_source_rgba(.92, .94, .98, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.5, .38, .1, alpha)
    cr.set_line_width(2)
    cr.stroke()
    lueur.arc(*q, 26, 0, 2 * math.pi)
    lueur.set_source_rgba(1, .9, .5, .6 * alpha)
    lueur.fill()


def manche_fouet(cr, main, direction, alpha=1.0):
    v = unit(direction)
    n = (-v[1], v[0])
    a, b = add(main, v, -22), add(main, v, 26)
    trait(cr, a, b, 12, (.2, .12, .05, alpha))
    for k in range(5):
        p = lerp_pt(a, b, .1 + k * .18)
        trait(cr, add(p, n, -6), add(add(p, n, 6), v, 4), 2, (.95, .75, .3, alpha))
    trait(cr, add(b, n, -9), add(b, n, 9), 6, (.95, .75, .3, alpha))
    cr.arc(*a, 7, 0, 2 * math.pi)
    cr.set_source_rgba(.95, .75, .3, alpha)
    cr.fill()


def dessin_chaine(cr, lueur, pts, alpha=1.0):
    """Chaîne d'acier : maillons alternés (vus de face / de profil)."""
    c = _cat(pts, 4)
    acc = 0.0
    k = 0
    for i in range(len(c) - 1):
        p, q = c[i], c[i + 1]
        l = dist(p, q)
        v = unit(sub(q, p))
        while acc < l:
            m = add(p, v, acc)
            ang = math.atan2(v[1], v[0])
            cr.save()
            cr.translate(*m)
            cr.rotate(ang)
            if k % 2 == 0:
                cr.scale(1, .55)
                cr.arc(0, 0, 7, 0, 2 * math.pi)
                cr.restore()
                cr.set_source_rgba(.32, .34, .38, alpha)
                cr.set_line_width(3.2)
                cr.stroke()
            else:
                cr.restore()
                trait(cr, add(m, v, -6), add(m, v, 6), 3.4, (.22, .23, .26, alpha))
            acc += 9
            k += 1
        acc -= l


def poids_kusari(cr, lueur, p, ang, alpha=1.0):
    """Poids (fundo) : masse d'acier à pointes."""
    cr.save()
    cr.translate(*p)
    cr.rotate(ang)
    for i in range(6):
        a = i * math.pi / 3
        v = (math.cos(a), math.sin(a))
        cr.move_to(v[0] * 11 + v[1] * 5, v[1] * 11 - v[0] * 5)
        cr.line_to(v[0] * 22, v[1] * 22)
        cr.line_to(v[0] * 11 - v[1] * 5, v[1] * 11 + v[0] * 5)
        cr.close_path()
        cr.set_source_rgba(.2, .2, .23, alpha)
        cr.fill()
    cr.arc(0, 0, 13, 0, 2 * math.pi)
    cr.set_source_rgba(.28, .29, .33, alpha)
    cr.fill()
    cr.arc(-4, -4, 4, 0, 2 * math.pi)
    cr.set_source_rgba(.7, .72, .78, alpha)
    cr.fill()
    cr.restore()


def kama(cr, main, direction, d, alpha=1.0, k=1.0):
    """Faucille (kama) : manche en bois cerclé, lame courbe perpendiculaire, acier bleuté avec fil clair."""
    v = unit(direction)
    n = (-v[1], v[0]) if d > 0 else (v[1], -v[0])
    bas = add(main, v, -30 * k)
    haut = add(main, v, 70 * k)
    trait(cr, bas, haut, 10 * k, (.45, .28, .12, alpha))
    for s in (.05, .55, .95):
        p = lerp_pt(bas, haut, s)
        trait(cr, add(p, v, -3), add(p, v, 3), 13 * k, (.15, .15, .17, alpha))
    ext, intr = [], []
    for i in range(13):
        s = i / 12
        a = s * 1.25
        dirl = (n[0] * math.cos(a) - v[0] * math.sin(a), n[1] * math.cos(a) - v[1] * math.sin(a))
        c = add(haut, dirl, 92 * k * s)
        larg = (15 * (1 - s) ** .7 + 1.5) * k
        ext.append(add(c, v, larg * .5))
        intr.append(add(c, v, -larg * .5))
    cr.move_to(*ext[0])
    for q in ext[1:] + intr[::-1]:
        cr.line_to(*q)
    cr.close_path()
    cr.set_source_rgba(.78, .82, .88, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(.1, .1, .12, alpha)
    cr.set_line_width(2)
    cr.stroke()
    cr.move_to(*lerp_pt(intr[1], ext[1], .25))
    for a_, b_ in zip(intr[2:-1], ext[2:-1]):
        cr.line_to(*lerp_pt(a_, b_, .25))
    cr.set_source_rgba(1, 1, 1, .8 * alpha)
    cr.set_line_width(1.6)
    cr.stroke()
    return haut, [lerp_pt(a_, b_, .5) for a_, b_ in zip(intr, ext)]


# ===================================================================== aperçu économique
def planche(h, ens, sortie, ts, dessin_h, extra=None, avant=None, pj=(), cols=8, W=216, H=300, zoom=1.25):
    rows = (len(ts) + cols - 1) // cols
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W * cols, H * rows)
    cr = cairo.Context(surf)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    ls = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
    lueur = cairo.Context(ls)
    for i, t in enumerate(ts):
        hk = h.squelette(t)
        cx = hk["bassin"][0]
        cy = min(SOL - 300, hk["tete"][1] + 60)
        cr.save()
        cr.translate((i % cols) * W, (i // cols) * H)
        cr.rectangle(0, 0, W, H)
        cr.clip()
        cr.set_source_rgb(.97, .97, .98)
        cr.paint()
        k = W / 1080 * zoom
        cr.scale(k, k)
        cr.translate(540 / zoom - cx, 200 - cy + 300)
        cr.set_source_rgb(.75, .75, .78)
        cr.rectangle(cx - 3000, SOL, 6000, 6)
        cr.fill()
        if extra:
            extra(cr, lueur, t)
        for e in ens:
            ob = getattr(e, "objet", None)
            ek = e.squelette(t)
            C.dessiner_heros(cr, ek, (.04, .04, .05), m1=(lambda ob=ob, ek=ek: ob(cr, ek)) if ob and ek["arme"] else None)
        dessin_h(cr, lueur, hk, t)
        for p in pj:
            if p.colle is None and t > p.t1:
                p.figer()
            p.dessiner(cr, lueur, t)
        if avant:
            avant(cr, lueur, t)
        cr.restore()
        cr.set_source_rgb(.85, 0, 0)
        cr.move_to((i % cols) * W + 4, (i // cols) * H + 14)
        cr.set_font_size(13)
        cr.show_text(f"{t:.2f}")
    surf.write_to_png(sortie)
