"""v10 : effets ANALYTIQUES (chaque particule = formule du temps, aucun état -> peu de calcul, rendu reproductible),
cape simulée (chaîne verlet pré-calculée une fois), cocon de téléportation, tornade, feu.
Impacts variés : cartes qui éclatent, feu, encre, cratère + fissures, croissant de faux, anneaux."""
import math

import numpy as np

import armes7 as W7
from corps3 import SOL, add, lerp_pt, sub, trait, unit

ROUGE_CAPE = (.66, .07, .12)
DOUBLURE = (.30, .02, .07)


def _rgba(c, a):
    return (*c[:3], max(0.0, min(1.0, a)))


class FX:
    def __init__(self, seed=3):
        self.rng = np.random.default_rng(seed)
        self.p = []                     # particules : dict(k=type, t0, vie, ...)

    # ---------------------------------------------------------------- émetteurs
    def ajoute(self, **kw):
        self.p.append(kw)

    def etincelles(self, t0, p, n=14, coul=(1, .85, .4), force=900, vie=.35, cone=math.pi, ang=-math.pi / 2):
        for _ in range(n):
            a = ang + self.rng.uniform(-cone, cone)
            v = self.rng.uniform(.35, 1) * force
            self.ajoute(k="etinc", t0=t0, vie=vie * self.rng.uniform(.6, 1.2), p=p, v=(math.cos(a) * v, math.sin(a) * v),
                        g=1500, coul=coul)

    def cartes(self, t0, p, n=12, force=700, vie=.9):
        for i in range(n):
            a = self.rng.uniform(0, 2 * math.pi)
            v = self.rng.uniform(.4, 1) * force
            self.ajoute(k="carte", t0=t0, vie=vie * self.rng.uniform(.7, 1.1), p=p, v=(math.cos(a) * v, math.sin(a) * v - 250),
                        g=900, spin=self.rng.uniform(-14, 14), idx=i)

    def feu(self, t0, p, n=22, force=520, vie=.75, taille=34):
        for _ in range(n):
            a = -math.pi / 2 + self.rng.uniform(-1.3, 1.3)
            v = self.rng.uniform(.3, 1) * force
            self.ajoute(k="flamme", t0=t0 + self.rng.uniform(0, .08), vie=vie * self.rng.uniform(.5, 1.1), p=p,
                        v=(math.cos(a) * v, math.sin(a) * v), g=-500, r=taille * self.rng.uniform(.6, 1.2))
        for _ in range(n // 2):
            self.ajoute(k="braise", t0=t0, vie=1.2 * self.rng.uniform(.6, 1.2), p=p,
                        v=(self.rng.uniform(-260, 260), self.rng.uniform(-700, -200)), g=380)
        self.ajoute(k="anneau", t0=t0, vie=.22, p=p, r1=140, coul=(1, .6, .15), larg=8)
        self.ajoute(k="fumee", t0=t0 + .1, vie=.8, p=p, v=(0, -160), r0=14, r1=55, coul=(.25, .22, .22), a=.22)

    def encre(self, t0, p, n=7, long=190, vie=.55):
        for i in range(n):
            a = self.rng.uniform(0, 2 * math.pi)
            self.ajoute(k="encre", t0=t0, vie=vie, p=p, ang=a, long=long * self.rng.uniform(.5, 1.1),
                        larg=self.rng.uniform(8, 18))
        self.ajoute(k="anneau", t0=t0, vie=.22, p=p, r1=120, coul=(.05, .05, .06), larg=10)

    def cratere(self, t0, x, force=1.0):
        s = (x, SOL)
        self.ajoute(k="fissures", t0=t0, vie=2.2, p=s, seed=int(self.rng.integers(1e6)), n=9, l=260 * force)
        self.ajoute(k="anneau_sol", t0=t0, vie=.45, p=s, r1=420 * force)
        for _ in range(int(28 * force)):
            a = -math.pi / 2 + self.rng.uniform(-1.25, 1.25)
            v = self.rng.uniform(300, 1100) * force
            self.ajoute(k="debris", t0=t0, vie=.9, p=(x + self.rng.uniform(-40, 40), SOL - 6), v=(math.cos(a) * v, math.sin(a) * v),
                        g=2600, r=self.rng.uniform(3, 8))
        for i in range(10):
            self.ajoute(k="fumee", t0=t0 + .02 * i, vie=1.1, p=(x + self.rng.uniform(-60, 60), SOL - 20),
                        v=((i - 4.5) * 90, -60), r0=24, r1=100, coul=(.6, .58, .56), a=.55)

    def croissant(self, t0, p, r, a0, a1, vie=.28, coul=(1, 1, 1), larg=26):
        self.ajoute(k="croissant", t0=t0, vie=vie, p=p, r=r, a0=a0, a1=a1, coul=coul, larg=larg)

    def scintille(self, t0, p, n=8, coul=(.85, .55, 1.0)):
        for _ in range(n):
            q = add(p, (self.rng.uniform(-40, 40), self.rng.uniform(-40, 40)), 1)
            self.ajoute(k="etoile", t0=t0 + self.rng.uniform(0, .08), vie=.25, p=q, r=self.rng.uniform(10, 22), coul=coul)

    def fumee_violette(self, t0, p, n=14):
        for i in range(n):
            a = self.rng.uniform(0, 2 * math.pi)
            self.ajoute(k="fumee", t0=t0 + self.rng.uniform(0, .06), vie=.8, p=p,
                        v=(math.cos(a) * 340, math.sin(a) * 240 - 80), r0=14, r1=70, coul=(.32, .1, .4), a=.32)

    # ---------------------------------------------------------------- dessin
    def dessiner(self, cr, lueur, t):
        for q in self.p:
            u = (t - q["t0"]) / q["vie"]
            if not 0 <= u < 1:
                continue
            dt = t - q["t0"]
            k = q["k"]
            if "v" in q:
                pos = (q["p"][0] + q["v"][0] * dt, q["p"][1] + q["v"][1] * dt + .5 * q.get("g", 0) * dt * dt)
                pos = (pos[0], min(pos[1], SOL - 2)) if k in ("debris", "carte", "etinc") else pos
            else:
                pos = q["p"]
            if k == "etinc":
                vv = (q["v"][0], q["v"][1] + q["g"] * dt)
                n_ = math.hypot(*vv) or 1
                trait(cr, pos, add(pos, (vv[0] / n_, vv[1] / n_), -min(36, n_ * .03)), 3 * (1 - u) + 1, _rgba(q["coul"], 1 - u))
                trait(lueur, pos, add(pos, (vv[0] / n_, vv[1] / n_), -20), 10, _rgba(q["coul"], .7 * (1 - u)))
            elif k == "carte":
                W7.carte(cr, pos, q["spin"] * dt, idx=q["idx"], alpha=min(1, 2.4 * (1 - u)), k=.55)
            elif k == "flamme":
                r = q["r"] * (1 - u * .7)
                c = (1, .95 - .7 * u, .35 - .3 * u)
                cr.set_source_rgba(*c, .85 * (1 - u))
                cr.move_to(pos[0], pos[1] - r * 1.6)
                cr.curve_to(pos[0] + r, pos[1] - r * .4, pos[0] + r * .7, pos[1] + r * .8, pos[0], pos[1] + r * .8)
                cr.curve_to(pos[0] - r * .7, pos[1] + r * .8, pos[0] - r, pos[1] - r * .4, pos[0], pos[1] - r * 1.6)
                cr.fill()
                lueur.arc(*pos, r * 1.1, 0, 2 * math.pi)
                lueur.set_source_rgba(1, .55, .15, .3 * (1 - u))
                lueur.fill()
            elif k == "braise":
                fl = .6 + .4 * math.sin(dt * 40 + q["v"][0])
                cr.arc(*pos, 3.2 * (1 - u) + 1, 0, 2 * math.pi)
                cr.set_source_rgba(1, .6, .15, fl * (1 - u))
                cr.fill()
                lueur.arc(*pos, 10, 0, 2 * math.pi)
                lueur.set_source_rgba(1, .5, .1, .6 * fl * (1 - u))
                lueur.fill()
            elif k == "fumee":
                r = q["r0"] + (q["r1"] - q["r0"]) * (1 - (1 - u) ** 2)
                cr.arc(*pos, r, 0, 2 * math.pi)
                cr.set_source_rgba(*q["coul"], q["a"] * (1 - u) ** 1.5)
                cr.fill()
            elif k == "anneau":
                r = q["r1"] * (1 - (1 - u) ** 3)
                cr.arc(*pos, r, 0, 2 * math.pi)
                cr.set_source_rgba(*q["coul"], (1 - u) * .9)
                cr.set_line_width(q["larg"] * (1 - u) + 1)
                cr.stroke()
            elif k == "anneau_sol":
                r = q["r1"] * (1 - (1 - u) ** 3)
                cr.save()
                cr.translate(*pos)
                cr.scale(1, .16)
                cr.arc(0, 0, r, 0, 2 * math.pi)
                cr.restore()
                cr.set_source_rgba(.25, .23, .22, .8 * (1 - u))
                cr.set_line_width(10 * (1 - u) + 2)
                cr.stroke()
            elif k == "encre":
                ext = min(1, u * 5)
                v = (math.cos(q["ang"]), math.sin(q["ang"]))
                a0 = add(pos, v, 20)
                a1 = add(pos, v, 20 + q["long"] * ext)
                n = (-v[1], v[0])
                w = q["larg"] * (1 - u) ** .7
                cr.move_to(*add(a0, n, w * .3))
                cr.line_to(*add(lerp_pt(a0, a1, .4), n, w))
                cr.line_to(*a1)
                cr.line_to(*add(lerp_pt(a0, a1, .4), n, -w))
                cr.line_to(*add(a0, n, -w * .3))
                cr.close_path()
                cr.set_source_rgba(.03, .03, .04, .95 * (1 - u * u))
                cr.fill()
            elif k == "fissures":
                rg = np.random.default_rng(q["seed"])
                a = 1 if u < .7 else (1 - u) / .3
                ext = min(1, u * 9)
                for i in range(q["n"]):
                    sens = 1 if i % 2 else -1
                    x, y = pos
                    lmax = q["l"] * rg.uniform(.4, 1) * ext
                    pts = [(x, y)]
                    pas = lmax / 6
                    for j in range(6):
                        x += sens * pas * rg.uniform(.6, 1.2)
                        y += rg.uniform(-4, 4) * (j + 1) * .5
                        pts.append((x, min(SOL + 12, max(SOL - 6, y))))
                    cr.move_to(*pts[0])
                    for p_ in pts[1:]:
                        cr.line_to(*p_)
                    cr.set_source_rgba(.12, .1, .1, .8 * a)
                    cr.set_line_width(4 * (1 - .5 * i / q["n"]))
                    cr.stroke()
            elif k == "debris":
                cr.rectangle(pos[0] - q["r"] / 2, pos[1] - q["r"] / 2, q["r"], q["r"])
                cr.set_source_rgba(.3, .28, .27, 1 - u)
                cr.fill()
            elif k == "croissant":
                a0, a1 = q["a0"], q["a1"]
                fin = a0 + (a1 - a0) * min(1, u * 3)
                deb = a0 + (a1 - a0) * max(0, u * 1.6 - .5)
                if abs(fin - deb) > .02:
                    n_ = 16
                    ext, intr = [], []
                    for i in range(n_ + 1):
                        s = i / n_
                        a = deb + (fin - deb) * s
                        w = q["larg"] * math.sin(math.pi * s) * (1 - u)
                        ext.append((pos[0] + math.cos(a) * (q["r"] + w / 2), pos[1] + math.sin(a) * (q["r"] + w / 2) * .55))
                        intr.append((pos[0] + math.cos(a) * (q["r"] - w / 2), pos[1] + math.sin(a) * (q["r"] - w / 2) * .55))
                    cr.move_to(*ext[0])
                    for p_ in ext[1:] + intr[::-1]:
                        cr.line_to(*p_)
                    cr.close_path()
                    cr.set_source_rgba(*q["coul"], .95 * (1 - u))
                    cr.fill()
                    lueur.move_to(*ext[0])
                    for p_ in ext[1:] + intr[::-1]:
                        lueur.line_to(*p_)
                    lueur.close_path()
                    lueur.set_source_rgba(1, .9, .8, .8 * (1 - u))
                    lueur.fill()
            elif k == "etoile":
                r = q["r"] * math.sin(math.pi * u)
                for a in (0, math.pi / 2):
                    v = (math.cos(a), math.sin(a))
                    trait(cr, add(pos, v, -r), add(pos, v, r), 3, _rgba(q["coul"], 1))
                lueur.arc(*pos, r, 0, 2 * math.pi)
                lueur.set_source_rgba(*q["coul"], .8)
                lueur.fill()


# ==================================================================== cape
class Cape:
    """Chaîne verlet accrochée entre les épaules et le cou, pré-simulée à 240 Hz sur toute la durée (une seule fois)."""
    N, SEG = 9, 17

    def __init__(self, acteur, duree, fps=60):
        self.fps = fps
        n_img = int(duree * fps) + 2
        sub_ = 4
        dt = 1 / (fps * sub_)
        sk = acteur.squelette(0)
        a = self.ancre(sk)
        pts = np.array([[a[0] - 6 * i * sk["d"], a[1] + self.SEG * i] for i in range(self.N)], float)
        prev = pts.copy()
        self.hist = np.zeros((n_img, self.N, 2))
        a_prec = a
        for f in range(n_img):
            for s in range(sub_):
                t = (f + s / sub_) / fps
                sk = acteur.squelette(t)
                a = self.ancre(sk)
                if math.hypot(a[0] - a_prec[0], a[1] - a_prec[1]) > 140:   # téléportation : la cape suit d'un bloc
                    dd = np.array([a[0] - a_prec[0], a[1] - a_prec[1]])
                    pts += dd
                    prev += dd
                a_prec = a
                vel = (pts - prev) * .965
                prev = pts.copy()
                pts = pts + vel + np.array([0, 2400]) * dt * dt
                pts[:, 0] += math.sin(t * 7.3) * .25           # léger vent
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
        return lerp_pt(sk["epaule"], sk["cou"], .5)

    def points(self, t):
        f = min(len(self.hist) - 1, max(0, int(round(t * self.fps))))
        return self.hist[f]

    def dessiner(self, cr, t, sk, alpha=1.0):
        pts = self.points(t)
        cote_g, cote_d = [], []
        for i in range(self.N):
            p = pts[i]
            q = pts[min(i + 1, self.N - 1)] if i < self.N - 1 else pts[i] + (pts[i] - pts[i - 1])
            v = unit(sub(q, p))
            n = (-v[1], v[0])
            w = 8 + 24 * (i / (self.N - 1)) ** .8
            cote_g.append(add(p, n, w))
            cote_d.append(add(p, n, -w))
        epa = sk["epaule"]
        cr.move_to(*lerp_pt(epa, sk["cou"], .1))
        for p in cote_g:
            cr.line_to(*p)
        for p in reversed(cote_d):
            cr.line_to(*p)
        cr.close_path()
        cr.set_source_rgba(*ROUGE_CAPE, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(*DOUBLURE, alpha)
        cr.set_line_width(3)
        cr.stroke()
        cr.move_to(*cote_d[-1])
        cr.line_to(*cote_g[-1])
        cr.set_source_rgba(*DOUBLURE, alpha)
        cr.set_line_width(6)
        cr.stroke()


# ==================================================================== téléportation à la cape
def cocon(cr, lueur, centre_bas, haut, u, phase_tour, alpha=1.0):
    """Cape refermée qui tourne sur elle-même. u : 0 -> enroulé complet ; collapse géré par `haut`."""
    x, y = centre_bas
    larg = 104 * (.72 + .28 * abs(math.cos(phase_tour)))
    h = haut
    cr.move_to(x, y - h)
    cr.curve_to(x + larg * .9, y - h * .85, x + larg * .6, y - h * .1, x + larg * .5, y)
    cr.line_to(x - larg * .5, y)
    cr.curve_to(x - larg * .6, y - h * .1, x - larg * .9, y - h * .85, x, y - h)
    cr.close_path()
    cr.set_source_rgba(*ROUGE_CAPE, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(*DOUBLURE, alpha)
    cr.set_line_width(3)
    cr.stroke()
    for k in range(3):                     # plis qui défilent : on lit la rotation
        ph = phase_tour + k * 2 * math.pi / 3
        if math.cos(ph) <= 0:
            continue
        xs = x + math.sin(ph) * larg * .55
        cr.move_to(xs, y - h * .8)
        cr.line_to(xs * .9 + x * .1, y - 4)
        cr.set_source_rgba(*DOUBLURE, alpha * math.cos(ph))
        cr.set_line_width(6)
        cr.stroke()
    lueur.arc(x, y - h * .5, larg * 1.2, 0, 2 * math.pi)
    lueur.set_source_rgba(.6, .1, .2, .25 * alpha)
    lueur.fill()


def tornade(cr, lueur, c, rayon, haut, u, phase, alpha=1.0):
    """Spirale de vent autour d'un axe vertical (anneaux elliptiques qui tournent)."""
    for i in range(7):
        y = c[1] - haut / 2 + haut * i / 6
        r = rayon * (.6 + .5 * i / 6)
        a0 = phase * 3 + i * .9
        cr.save()
        cr.translate(c[0], y)
        cr.scale(1, .22)
        cr.arc(0, 0, r, a0, a0 + 2.2)
        cr.restore()
        cr.set_source_rgba(.42, .45, .5, .8 * alpha)
        cr.set_line_width(7)
        cr.stroke()


def fleche_feu(fx_cr, lueur, proj, t, rng_seed=0):
    """Traînée de flammes derrière une flèche enflammée en vol (analytique : positions passées du projectile)."""
    if not proj.t0 <= t <= proj.t1 + .05:
        return
    for i in range(10):
        tt = t - i * .012
        if tt < proj.t0:
            break
        p = proj.pos(min(tt, proj.t1))
        r = 16 * (1 - i / 10) + 4
        c = (1, .9 - .06 * i, .3 - .03 * i)
        fx_cr.arc(p[0], p[1] - i * 1.5, r, 0, 2 * math.pi)
        fx_cr.set_source_rgba(*c, .8 * (1 - i / 10))
        fx_cr.fill()
        lueur.arc(p[0], p[1], r * 2.2, 0, 2 * math.pi)
        lueur.set_source_rgba(1, .5, .1, .5 * (1 - i / 10))
        lueur.fill()
