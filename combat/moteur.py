"""Moteur d'animation de bonhommes bâtons 2D (rendu cairo, 60 i/s).

Conventions d'angles (degrés), relatives au sens où le personnage regarde (dir = +1 droite, -1 gauche) :
  - membres et arme : 0 = vers le bas, 90 = horizontal vers l'avant, 180 = vers le haut ;
  - torse : 0 = droit, positif = penché vers l'avant ;
  - tête : inclinaison ajoutée au torse.
Le bassin est posé automatiquement pour que le point le plus bas du corps touche le sol (sauf « air »).
"""
import math
import subprocess

import cairo
import numpy as np

W, H = 1080, 1920
FPS = 60
SOL = 1500
BANDE = 560                        # bande noire du haut (texte)
FOND = (0.866, 0.855, 0.866)

LONG = dict(torse=106, cou=10, tete=27, bras=60, avb=56, cuisse=72, tibia=70, lance=290)


def vec(a, d=1):
    r = math.radians(a)
    return (math.sin(r) * d, math.cos(r))


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------ courbes d'accélération
def ease(nom, u):
    u = min(1.0, max(0.0, u))
    if nom == "lin":
        return u
    if nom == "io":                          # douce
        return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
    if nom == "in":
        return u ** 3
    if nom == "out":
        return 1 - (1 - u) ** 3
    if nom == "coup":                        # départ explosif (frappe)
        return 1 - (1 - u) ** 5
    if nom == "ressort":                     # dépasse un peu puis revient
        c1, c3 = 2.2, 3.2
        return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
    if nom == "chute":                       # gravité
        return u * u
    if nom == "saut":                        # montée qui ralentit
        return 1 - (1 - u) ** 2
    if nom == "net":
        return 0.0 if u < 1 else 1.0
    raise ValueError(nom)


CLES_POSE = ["x", "air", "t", "h", "b1", "a1", "b2", "a2", "c1", "j1", "c2", "j2", "w", "g", "rot"]


class Acteur:
    def __init__(self, nom, couleur, dir_, echelle, base):
        self.nom, self.couleur, self.dir, self.k = nom, couleur, dir_, echelle
        self.base = dict(base)
        self.cles = []                       # (t, pose complète, courbe pour ARRIVER à cette clé)
        self.lance_libre = None             # (t, point d'ancrage, angle) quand la lance quitte la main

    def cle(self, _temps, _courbe="io", **kw):
        prec = dict(self.cles[-1][1]) if self.cles else dict(self.base)
        prec.update(kw)
        self.cles.append((_temps, prec, _courbe))
        return self

    def pose(self, t):
        c = self.cles
        if t <= c[0][0]:
            return dict(c[0][1])
        for (t0, p0, _), (t1, p1, e) in zip(c, c[1:]):
            if t0 <= t <= t1:
                u = ease(e, (t - t0) / max(1e-6, t1 - t0))
                out = {k: (lerp(p0[k], p1[k], u) if isinstance(p0.get(k), (int, float)) and k in p1 else p1.get(k))
                       for k in p1}
                out["deux"] = p1.get("deux", False) if u > .5 else p0.get("deux", False)
                out["tient"] = p0.get("tient", True)
                return out
        return dict(c[-1][1])

    # -------------------------------------------------------------- squelette (positions monde)
    def squelette(self, t, sol=SOL):
        p = self.pose(t)
        k, d = self.k, self.dir
        L = {n: v * k for n, v in LONG.items()}
        rot = p.get("rot", 0)                # rotation globale du corps (vrilles, chutes)

        def R(a):                            # membres : angle depuis le bas (sens inverse du torse)
            return a - rot

        def j(pt, a, l):
            return add(pt, vec(R(a), d), l)
        bassin = (0.0, 0.0)
        # torse : angle mesuré depuis le haut
        ta = math.radians(p["t"] + rot)
        tv = (math.sin(ta) * d, -math.cos(ta))
        epaule = add(bassin, tv, L["torse"])
        cou = add(epaule, tv, L["cou"])
        ha = math.radians(p["t"] + p["h"] + rot)
        hv = (math.sin(ha) * d, -math.cos(ha))
        tete = add(cou, hv, L["tete"])
        coude1 = j(epaule, p["b1"], L["bras"])
        main1 = j(coude1, p["a1"], L["avb"])
        genou1 = j(bassin, p["c1"], L["cuisse"])
        pied1 = j(genou1, p["j1"], L["tibia"])
        genou2 = j(bassin, p["c2"], L["cuisse"])
        pied2 = j(genou2, p["j2"], L["tibia"])
        sk = dict(bassin=bassin, epaule=epaule, cou=cou, tete=tete, coude1=coude1, main1=main1,
                  genou1=genou1, pied1=pied1, genou2=genou2, pied2=pied2)
        # lance tenue en main avant
        lance = None
        if p.get("tient", True) and "w" in p:
            wv = vec(R(p["w"]), d)
            g = p.get("g", .4)
            lance = (add(main1, wv, -L["lance"] * g), add(main1, wv, L["lance"] * (1 - g)))
        # bras arrière : à deux mains (IK sur la lance) ou libre
        if lance and p.get("deux"):
            cible = lerp_pt(lance[0], lance[1], max(0.02, p.get("g", .4) - .22))
            coude2 = ik(epaule, cible, L["bras"], L["avb"], -d)
            main2 = cible if dist(epaule, cible) < L["bras"] + L["avb"] else add(coude2, unit(sub(cible, coude2)), L["avb"])
        else:
            coude2 = j(epaule, p["b2"], L["bras"])
            main2 = j(coude2, p["a2"], L["avb"])
        sk.update(coude2=coude2, main2=main2)
        # posé au sol : le point le plus bas touche SOL (pieds, genoux, bassin, tête)
        bas = max(pt[1] for n, pt in sk.items())
        bas = max(bas, tete[1] + L["tete"] * .95)
        dy = sol - bas - p.get("air", 0)
        dx = p["x"]
        sk = {n: (pt[0] + dx, pt[1] + dy) for n, pt in sk.items()}
        if lance:
            lance = tuple((q[0] + dx, q[1] + dy) for q in lance)
        sk["lance"] = lance
        sk["rayon_tete"] = L["tete"] * .95
        sk["air"] = p.get("air", 0)
        return sk


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def unit(v):
    n = math.hypot(*v) or 1
    return (v[0] / n, v[1] / n)


def lerp_pt(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def ik(o, cible, l1, l2, sens):
    """Coude pour atteindre la cible depuis l'épaule (2 segments)."""
    dd = min(dist(o, cible), l1 + l2 - 1e-3)
    a = math.acos(max(-1, min(1, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))))
    base = math.atan2(cible[1] - o[1], cible[0] - o[0])
    ang = base + a * sens
    return (o[0] + math.cos(ang) * l1, o[1] + math.sin(ang) * l1)


# ------------------------------------------------------------------ dessin
def trait(cr, a, b, w, rgba):
    cr.set_source_rgba(*rgba)
    cr.set_line_width(w)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.move_to(*a)
    cr.line_to(*b)
    cr.stroke()


def poly(cr, pts, rgba):
    cr.set_source_rgba(*rgba)
    cr.move_to(*pts[0])
    for q in pts[1:]:
        cr.line_to(*q)
    cr.close_path()
    cr.fill()


def dessiner_corps(cr, sk, couleur, k, alpha=1.0, lance=True):
    c = (*couleur, alpha)
    ep = 19 * k
    # membres arrière un peu plus clairs pour la profondeur
    arr = tuple(min(1, x + .10) for x in couleur) + (alpha,)
    for a, b in (("bassin", "genou2"), ("genou2", "pied2")):
        trait(cr, sk[a], sk[b], ep, arr)
    for a, b in (("epaule", "coude2"), ("coude2", "main2")):
        trait(cr, sk[a], sk[b], ep * .86, arr)
    if lance and sk.get("lance"):
        trait(cr, sk["lance"][0], sk["lance"][1], 6.5 * k, (.08, .08, .08, alpha))
        pointe(cr, sk["lance"][0], sk["lance"][1], k, alpha)
    trait(cr, sk["bassin"], sk["epaule"], ep * 1.08, c)
    trait(cr, sk["epaule"], sk["cou"], ep, c)
    for a, b in (("bassin", "genou1"), ("genou1", "pied1")):
        trait(cr, sk[a], sk[b], ep, c)
    for a, b in (("epaule", "coude1"), ("coude1", "main1")):
        trait(cr, sk[a], sk[b], ep * .86, c)
    cr.set_source_rgba(*c)
    cr.arc(*sk["tete"], sk["rayon_tete"], 0, 2 * math.pi)
    cr.fill()


def pointe(cr, butt, tip, k, alpha=1.0):
    v = unit(sub(tip, butt))
    n = (-v[1], v[0])
    l, w = 34 * k, 10 * k
    base = add(tip, v, -l)
    poly(cr, [add(tip, v, 6 * k), add(base, n, w), add(base, v, 6 * k), add(base, n, -w)], (.06, .06, .06, alpha))


def ombre(cr, x, air, k):
    s = max(.35, 1 - air / 700)
    cr.save()
    cr.translate(x, SOL + 8)
    cr.scale(1, .16)
    cr.set_source_rgba(0, 0, 0, .13 * s)
    cr.arc(0, 0, 85 * k * s, 0, 2 * math.pi)
    cr.fill()
    cr.restore()


# ------------------------------------------------------------------ particules et décors persistants
class Particules:
    def __init__(self, rng):
        self.rng = rng
        self.p = []          # dicts : type, pos, vit, vie, age, taille, couleur
        self.taches = []     # sang au sol (persistant)
        self.cailloux = []   # débris au sol (persistant)

    def poussiere(self, pos, n=14, force=260, dirx=0.0, taille=26, vie=.7, gris=.48, haut=.35):
        r = self.rng
        for _ in range(n):
            a = r.uniform(-math.pi, 0)
            v = (math.cos(a) * force * r.uniform(.3, 1) + dirx * force, math.sin(a) * force * r.uniform(.1, haut))
            self.p.append(dict(t="pou", pos=list(pos), vit=list(v), vie=vie * r.uniform(.7, 1.3), age=0,
                               taille=taille * r.uniform(.6, 1.4), gris=gris + r.uniform(-.06, .06)))

    def sang(self, pos, dirv, n=40, force=900, cone=.7):
        r = self.rng
        base = math.atan2(dirv[1], dirv[0])
        for _ in range(n):
            a = base + r.normal(0, cone)
            f = force * r.uniform(.25, 1.1)
            self.p.append(dict(t="sang", pos=list(pos), vit=[math.cos(a) * f, math.sin(a) * f], vie=2.5, age=0,
                               taille=r.uniform(3, 9)))

    def debris(self, pos, n=10, force=700):
        r = self.rng
        for _ in range(n):
            a = r.uniform(-math.pi * .92, -math.pi * .08)
            f = force * r.uniform(.35, 1)
            self.p.append(dict(t="roc", pos=list(pos), vit=[math.cos(a) * f, math.sin(a) * f], vie=3, age=0,
                               taille=r.uniform(7, 18), ang=r.uniform(0, 6.28), va=r.uniform(-12, 12)))

    def fissure(self, pos, n=7, larg=220):
        r = self.rng
        for _ in range(n):
            x = pos[0] + r.uniform(-larg, larg) * .6
            h = r.uniform(14, 40) * (1 - abs(x - pos[0]) / (larg * 1.1))
            self.cailloux.append(dict(x=x, w=r.uniform(26, 60), h=max(8, h), gris=r.uniform(.38, .52),
                                      seed=int(r.integers(1e6))))

    def maj(self, dt):
        g = 2400
        reste = []
        for q in self.p:
            q["age"] += dt
            if q["t"] == "pou":
                q["vit"][0] *= (1 - 3.2 * dt)
                q["vit"][1] = q["vit"][1] * (1 - 3.2 * dt) - 30 * dt
                q["taille"] += 38 * dt
            else:
                q["vit"][1] += g * dt
            q["pos"][0] += q["vit"][0] * dt
            q["pos"][1] += q["vit"][1] * dt
            if q["t"] == "sang" and q["pos"][1] >= SOL + self.rng.uniform(-4, 30):
                self.taches.append(dict(x=q["pos"][0], y=min(q["pos"][1], SOL + 34), l=q["taille"] * self.rng.uniform(2, 6),
                                        h=q["taille"] * .45, a=self.rng.uniform(.75, 1)))
                continue
            if q["t"] == "roc" and q["pos"][1] >= SOL + 10:
                if abs(q["vit"][1]) > 260:
                    q["vit"][1] *= -.3
                    q["vit"][0] *= .5
                    q["pos"][1] = SOL + 9
                else:
                    self.cailloux.append(dict(x=q["pos"][0], w=q["taille"] * 1.6, h=q["taille"], gris=.42,
                                              seed=int(self.rng.integers(1e6))))
                    continue
            if q["age"] < q["vie"]:
                reste.append(q)
        self.p = reste

    def dessiner_sol(self, cr):
        for c in self.cailloux:
            r = np.random.default_rng(c["seed"])
            n = 4
            pts = [(c["x"] - c["w"] / 2, SOL + 14)]
            for i in range(n):
                pts.append((c["x"] - c["w"] / 2 + c["w"] * (i + .5) / n + r.uniform(-4, 4), SOL + 14 - c["h"] * r.uniform(.5, 1)))
            pts.append((c["x"] + c["w"] / 2, SOL + 14))
            poly(cr, pts, (c["gris"], c["gris"], c["gris"] + .01, .95))
        for s in self.taches:
            cr.save()
            cr.translate(s["x"], s["y"])
            cr.scale(1, s["h"] / max(1, s["l"]))
            cr.set_source_rgba(.62, .05, .07, s["a"])
            cr.arc(0, 0, s["l"], 0, 2 * math.pi)
            cr.fill()
            cr.restore()

    def dessiner(self, cr):
        for q in self.p:
            u = q["age"] / q["vie"]
            if q["t"] == "pou":
                g = q["gris"]
                cr.set_source_rgba(g, g, g + .01, .42 * (1 - u) ** 1.4)
                cr.arc(*q["pos"], q["taille"], 0, 2 * math.pi)
                cr.fill()
            elif q["t"] == "sang":
                v = q["vit"]
                n = math.hypot(*v) or 1
                l = min(26, n * .018) + q["taille"]
                a = q["pos"]
                b = (a[0] - v[0] / n * l, a[1] - v[1] / n * l)
                trait(cr, a, b, q["taille"], (.78, .06, .09, 1))
            elif q["t"] == "roc":
                cr.save()
                cr.translate(*q["pos"])
                cr.rotate(q["ang"] + q["va"] * q["age"])
                s = q["taille"]
                poly(cr, [(-s, s * .6), (-s * .2, -s), (s, -s * .2), (s * .5, s * .7)], (.30, .30, .31, 1))
                cr.restore()


# ------------------------------------------------------------------ effets d'impact
def flash(cr, pos, u, taille=170):
    """Éclair blanc-jaune qui gonfle puis s'éteint (u de 0 à 1)."""
    if u >= 1:
        return
    r = taille * (0.55 + 0.9 * min(1, u * 3))
    a = (1 - u) ** 1.5
    g = cairo.RadialGradient(pos[0], pos[1], 0, pos[0], pos[1], r)
    g.add_color_stop_rgba(0, 1, 1, 1, a)
    g.add_color_stop_rgba(.35, 1, .96, .78, a * .85)
    g.add_color_stop_rgba(.7, 1, .82, .45, a * .28)
    g.add_color_stop_rgba(1, 1, .8, .4, 0)
    cr.set_source(g)
    cr.arc(*pos, r, 0, 2 * math.pi)
    cr.fill()


def rayons(cr, pos, u, n, rng_seed, long=260):
    if u >= 1:
        return
    r = np.random.default_rng(rng_seed)
    for i in range(n):
        a = r.uniform(0, 2 * math.pi)
        l0 = long * r.uniform(.25, .5) * (1 + u)
        l1 = long * r.uniform(.6, 1.1) * (1 + u * .6)
        p0 = (pos[0] + math.cos(a) * l0, pos[1] + math.sin(a) * l0)
        p1 = (pos[0] + math.cos(a) * l1, pos[1] + math.sin(a) * l1)
        trait(cr, p0, p1, r.uniform(3, 7) * (1 - u), (1, 1, 1, (1 - u)))


def entaille(cr, pos, angle, u, long=430):
    """Trait rouge flou en travers de la cible (signature du style)."""
    if u >= 1:
        return
    a = math.radians(angle)
    v = (math.cos(a), math.sin(a))
    l = long * (0.6 + 0.4 * min(1, u * 4))
    p0, p1 = add(pos, v, -l / 2), add(pos, v, l / 2)
    al = (1 - u) ** 1.2
    for w, aa in ((34, .10), (22, .18), (12, .45), (5, .9)):
        trait(cr, p0, p1, w * (1 - u * .5), (.86, .07, .1, aa * al))


def onde(cr, pos, u):
    if u >= 1:
        return
    cr.save()
    cr.translate(pos[0], SOL + 6)
    cr.scale(1, .18)
    cr.set_source_rgba(1, 1, 1, .8 * (1 - u))
    cr.set_line_width(10 * (1 - u) + 2)
    cr.arc(0, 0, 60 + 520 * (1 - (1 - u) ** 2), 0, 2 * math.pi)
    cr.stroke()
    cr.restore()


class Trainee:
    """Traînée de l'arme : ruban noir déchiqueté + arc blanc le long de la pointe."""
    def __init__(self, n=7):
        self.h = []
        self.n = n

    def ajouter(self, lance):
        self.h.append(lance)
        self.h = self.h[-self.n:]

    def vider(self):
        self.h = []

    def dessiner(self, cr, rng, k):
        brut = [x for x in self.h if x]
        if len(brut) < 3:
            return
        # sur-échantillonnage polaire autour de la main : arcs lisses au lieu de facettes
        hs = []
        for (b0, t0), (b1, t1) in zip(brut, brut[1:]):
            a0 = math.atan2(t0[1] - b0[1], t0[0] - b0[0])
            a1 = math.atan2(t1[1] - b1[1], t1[0] - b1[0])
            da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            l0, l1 = dist(b0, t0), dist(b1, t1)
            for k_ in range(6):
                f = k_ / 6
                b = lerp_pt(b0, b1, f)
                ang, L = a0 + da * f, l0 + (l1 - l0) * f
                hs.append((b, (b[0] + L * math.cos(ang), b[1] + L * math.sin(ang))))
        hs.append(brut[-1])
        # pas plus d'un demi-tour de traînée (sinon cercles concentriques sur le moulinet)
        tot, coupe = 0.0, 0
        for i in range(len(hs) - 1, 0, -1):
            (b0, t0), (b1, t1) = hs[i - 1], hs[i]
            d = math.atan2(t1[1] - b1[1], t1[0] - b1[0]) - math.atan2(t0[1] - b0[1], t0[0] - b0[0])
            tot += abs((d + math.pi) % (2 * math.pi) - math.pi)
            if tot > 3.3:
                coupe = i
                break
        hs = hs[coupe:]
        if len(hs) < 3:
            return
        P = [t for _, t in hs]                       # pointe (ancien -> récent)
        Q = [lerp_pt(b, t, .38) for b, t in hs]      # bord intérieur du ruban
        if sum(dist(P[i], P[i + 1]) for i in range(len(P) - 1)) < 90:
            return
        n = len(P)
        # ruban en coups de pinceau : des traînées fines qui suivent la trajectoire,
        # longues vers la pointe, courtes et effilochées vers la main
        cr.save()
        cr.set_line_cap(cairo.LINE_CAP_BUTT)
        for r in [.42 + .58 * (q / 15) ** .8 for q in range(16)]:
            debut = int((1 - r) * (n - 1) * rng.uniform(.6, 1.1))
            jit = rng.uniform(-.02, .02)
            pts = [lerp_pt(b, t, r + jit) for b, t in hs][debut:]
            if len(pts) < 2:
                continue
            larg = (8 + 16 * r) * rng.uniform(.7, 1.2)
            for m in range(len(pts) - 1):
                u = (debut + m + 1) / (n - 1)
                cr.set_source_rgba(.04, .04, .04, (.1 + .85 * u ** 1.4) * (.7 + .3 * r))
                cr.set_line_width(larg * (.35 + .65 * u))
                cr.move_to(*pts[m])
                cr.line_to(*pts[m + 1])
                cr.stroke()
        cr.restore()
        # arc blanc extérieur, ombré de gris pour ressortir sur le fond clair
        c = lerp_pt(hs[-1][0], hs[-1][1], .2)
        ext = [add(p, unit(sub(p, c)), 22) for p in P]
        for col, plus in (((.55, .55, .57), 5), ((1, 1, 1), 0)):
            for i in range(n - 1):
                u = (i + 1) / (n - 1)
                trait(cr, ext[i], ext[i + 1], 2 + 9 * u + plus, (*col, (.25 + .7 * u) * (.5 if plus else 1)))


def trainee_membres(cr, prec, sk, couleur, alpha=.22, seuil=34):
    """Étirement des membres rapides (smear) entre l'image précédente et l'actuelle."""
    if not prec:
        return
    for a, b in (("epaule", "main1"), ("coude1", "main1"), ("bassin", "pied1"), ("genou1", "pied1"),
                 ("genou2", "pied2"), ("bassin", "tete")):
        if dist(prec[b], sk[b]) > seuil:
            poly(cr, [prec[a], prec[b], sk[b], sk[a]], (*couleur, alpha))


# ------------------------------------------------------------------ texte et écriture vidéo
def texte(cr, s, y, taille=86):
    cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(taille)
    e = cr.text_extents(s)
    cr.move_to(W / 2 - e.width / 2 - e.x_bearing, y)
    cr.set_source_rgb(1, 1, 1)
    cr.show_text(s)


def ecrivain(chemin):
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                             "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", chemin],
                            stdin=subprocess.PIPE)
