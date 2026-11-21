"""Acteurs v3 : buste épais, perso plus trapu, lance orientable en profondeur (canal z = lacet, pour les
rotations à plat autour du corps qui dessinent des anneaux elliptiques), traînées échantillonnées dans le temps.

Angles (degrés), relatifs au sens d (+1 regarde à droite) :
  membres / arme : 0 = bas, 90 = avant horizontal, 180 = haut ; torse : 0 droit, + penché avant ;
  z : lacet de l'arme autour de la verticale (0 = dans le plan de l'image) ; rot : rotation globale du corps.
"""
import math
import os
import sys

import cairo
import numpy as np
from scipy.interpolate import PchipInterpolator

from moteur import add, dist, ik, lerp, lerp_pt, poly, sub, trait, unit, vec  # noqa: E402,F401

W, H = 1080, 1920
FPS = 60
SOL = 1500
BANDE = 560
HORIZON = SOL - 140

LONG = dict(torse=88, cou=4, tete=36, bras=52, avb=50, cuisse=70, tibia=68)
EP, EP_BUSTE = 24, 33
INCL = .32                      # aplatissement de la perspective (vue légèrement plongeante)
NUM = ["x", "air", "t", "h", "b1", "a1", "b2", "a2", "c1", "j1", "c2", "j2", "w", "g", "rot", "z", "o", "suivi"]
ETAPES = ["d", "deux", "tient"]


class Acteur:
    def __init__(self, nom, couleur, base, arme_l=0):
        self.nom, self.couleur, self.base, self.arme_l = nom, couleur, dict(base), arme_l
        self.cles = []
        self._sp = None
        self._cache = {}

    def cle(self, _t, coupe=False, **kw):
        p = dict(self.base)
        p.update(kw)
        self.cles.append([_t, p, coupe])
        self.invalider()
        return p

    def k(self, t):
        for c in self.cles:
            if abs(c[0] - t) < 1e-6:
                return c[1]
        raise KeyError(t)

    def invalider(self):
        self._sp = None
        self._cache = {}

    def _construire(self):
        self.cles.sort(key=lambda c: c[0])
        uniq = []
        for c in self.cles:                       # deux clés au même instant : la plus récente gagne
            if uniq and abs(c[0] - uniq[-1][0]) < 1e-4:
                uniq[-1] = c
            else:
                uniq.append(c)
        self.cles[:] = uniq
        segs, cur = [], []
        for c in self.cles:
            if c[2] and cur:
                segs.append(cur)
                cur = []
            cur.append(c)
        segs.append(cur)
        self._sp = []
        for s in segs:
            ts = np.array([c[0] for c in s])
            can = {}
            for n in NUM:
                v = np.array([float(c[1].get(n, 0)) for c in s])
                can[n] = PchipInterpolator(ts, v) if len(s) > 1 else (lambda t, v0=v[0]: v0)
            self._sp.append((ts[0], ts[-1], can, s))

    def pose(self, t):
        if self._sp is None:
            self._construire()
        seg = self._sp[0]
        for s in self._sp:
            if t >= s[0]:
                seg = s
        t0, t1, can, s = seg
        tt = min(max(t, t0), t1)
        p = {n: float(can[n](tt)) for n in NUM}
        der = s[0][1]
        for c in s:
            if c[0] <= t + 1e-9:
                der = c[1]
        for n in ETAPES:
            p[n] = der.get(n, self.base.get(n))
        return p

    def squelette(self, t):
        cle_c = round(t * 7200)
        if cle_c in self._cache:
            return self._cache[cle_c]
        p = self.pose(t)
        d, rot, L = p["d"], p["rot"], LONG

        def j(pt, a, l):
            return add(pt, vec(a - rot, d), l)
        bassin = (0.0, 0.0)
        ta = math.radians(p["t"] + rot)
        tv = (math.sin(ta) * d, -math.cos(ta))
        epaule = add(bassin, tv, L["torse"])
        cou = add(epaule, tv, L["cou"])
        ha = math.radians(p["t"] + p["h"] + rot)
        tete = add(cou, (math.sin(ha) * d, -math.cos(ha)), L["tete"])
        # le poignet et l'avant-bras accompagnent la rotation de l'arme (pas de main figée pendant un moulinet)
        if p["suivi"]:
            dw = math.sin(math.radians(p["w"] - p["a1"]))
            p["a1"] += p["suivi"] * 28 * dw
            p["b1"] += p["suivi"] * 12 * dw
            p["t"] += p["suivi"] * 3 * dw
        coude1 = j(epaule, p["b1"], L["bras"])
        main1 = j(coude1, p["a1"], L["avb"])
        genou1 = j(bassin, p["c1"], L["cuisse"])
        pied1 = j(genou1, p["j1"], L["tibia"])
        genou2 = j(bassin, p["c2"], L["cuisse"])
        pied2 = j(genou2, p["j2"], L["tibia"])
        sk = dict(bassin=bassin, epaule=epaule, cou=cou, tete=tete, coude1=coude1, main1=main1,
                  genou1=genou1, pied1=pied1, genou2=genou2, pied2=pied2)
        arme, prof = None, 0.0
        if p["tient"] and self.arme_l:
            b = vec(p["w"] - rot, d)
            z = math.radians(p["z"])
            prof = b[0] * math.sin(z)
            wv = (b[0] * math.cos(z), b[1] + prof * INCL)
            arme = (add(main1, wv, -self.arme_l * p["g"]), add(main1, wv, self.arme_l * (1 - p["g"])))
        if arme and p["deux"]:
            cible = lerp_pt(arme[0], arme[1], max(0.02, p["g"] - .22))
            coude2 = ik(epaule, cible, L["bras"], L["avb"], -d)
            main2 = cible if dist(epaule, cible) < L["bras"] + L["avb"] else add(coude2, unit(sub(cible, coude2)), L["avb"])
        else:
            coude2 = j(epaule, p["b2"], L["bras"])
            main2 = j(coude2, p["a2"], L["avb"])
        sk.update(coude2=coude2, main2=main2)
        bas = max(max(q[1] for q in sk.values()) + EP / 2, tete[1] + L["tete"])
        dy = SOL - bas - p["air"]
        dx = p["x"]
        sk = {n: (q[0] + dx, q[1] + dy) for n, q in sk.items()}
        sk["arme"] = tuple((q[0] + dx, q[1] + dy) for q in arme) if arme else None
        sk["prof"], sk["air"], sk["d"] = prof, p["air"], d
        sk["o"] = p["o"]
        self._cache[cle_c] = sk
        return sk


def poitrine(sk, u=.6):
    return lerp_pt(sk["bassin"], sk["epaule"], u)


def sur_arme(sk, u):
    a = sk["arme"]
    return lerp_pt(a[0], a[1], u)


def dist_segment(p, a, b):
    ab = sub(b, a)
    u = max(0, min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / max(1e-9, ab[0] ** 2 + ab[1] ** 2)))
    return dist(p, lerp_pt(a, b, u)), u


# ------------------------------------------------------------------ dessin
def dessiner_corps(cr, sk, couleur, alpha=1.0, arme=None):
    c = (*couleur, alpha)
    arr = tuple(min(1, x + .06) for x in couleur) + (alpha,)
    derriere = arme and sk["arme"] and sk["prof"] > .05
    if derriere:
        arme(cr, sk["arme"], alpha)
    for a, b in (("bassin", "genou2"), ("genou2", "pied2"), ("epaule", "coude2"), ("coude2", "main2")):
        trait(cr, sk[a], sk[b], EP, arr)
    trait(cr, sk["bassin"], sk["epaule"], EP_BUSTE, c)
    trait(cr, sk["epaule"], sk["cou"], EP_BUSTE * .8, c)
    if arme and sk["arme"] and not derriere:
        arme(cr, sk["arme"], alpha)
    for a, b in (("bassin", "genou1"), ("genou1", "pied1"), ("epaule", "coude1"), ("coude1", "main1")):
        trait(cr, sk[a], sk[b], EP, c)
    cr.set_source_rgba(*c)
    cr.arc(*sk["tete"], LONG["tete"], 0, 2 * math.pi)
    cr.fill()


def dessiner_heros(cr, sk, couleur, m1=None, m2=None, alpha=1.0):
    """Arme tenue en main DROITE (main1), violon/objet en main GAUCHE (main2) : le côté éloigné du spectateur passe
    DERRIÈRE le corps (assombri). Regarde à droite (d>0) : main droite côté loin -> arme en partie cachée."""
    c = (*couleur, alpha)
    sombre = c                                     # v10 : une seule couleur uniforme par personnage
    loin_1 = sk["d"] > 0 or sk.get("prof", 0) > .05
    bras = {1: (("epaule", "coude1"), ("coude1", "main1")), 2: (("epaule", "coude2"), ("coude2", "main2"))}
    objet = {1: m1, 2: m2}
    loin, pres_ = (1, 2) if loin_1 else (2, 1)
    if objet[loin]:
        objet[loin]()
    for a, b in bras[loin]:
        trait(cr, sk[a], sk[b], EP, sombre)
    for a, b in (("bassin", "genou2"), ("genou2", "pied2")):
        trait(cr, sk[a], sk[b], EP, sombre)
    trait(cr, sk["bassin"], sk["epaule"], EP_BUSTE, c)
    trait(cr, sk["epaule"], sk["cou"], EP_BUSTE * .8, c)
    for a, b in (("bassin", "genou1"), ("genou1", "pied1")):
        trait(cr, sk[a], sk[b], EP, c)
    cr.set_source_rgba(*c)
    cr.arc(*sk["tete"], LONG["tete"], 0, 2 * math.pi)
    cr.fill()
    for a, b in bras[pres_]:
        trait(cr, sk[a], sk[b], EP, c)
    if objet[pres_]:
        objet[pres_]()


def lance(cr, seg, alpha=1.0):
    if not seg:
        return
    butt, tip = seg
    l = dist(butt, tip)
    if l < 8:
        return
    v = unit(sub(tip, butt))
    n = (-v[1], v[0])
    k = min(1, l / 300)
    base = add(tip, v, -44 * k)
    trait(cr, butt, base, 7.5, (.40, .40, .42, alpha))
    trait(cr, add(base, v, -10 * k), add(base, v, -2 * k), 11, (.10, .10, .11, alpha))
    trait(cr, butt, add(butt, v, 9 * k), 9, (.10, .10, .11, alpha))
    pts = [add(tip, v, 4), add(add(base, v, 14 * k), n, 11), base, add(add(base, v, 14 * k), n, -11)]
    poly(cr, pts, (.04, .04, .05, alpha))
    cr.set_source_rgba(.95, .95, .97, .6 * alpha)
    cr.set_line_width(1.6)
    cr.move_to(*pts[0])
    cr.line_to(*pts[1])
    cr.stroke()


def trainee(cr, glow, acteur, t, duree=.09, r0=.35, seuil=650, lueur=None, force=1.0):
    """Ruban échantillonné dans le temps : sombre près de l'arme, s'éclaircit et s'efface en vieillissant.
    Seuls les passages rapides laissent une trace (vitesse de la pointe > seuil px/s)."""
    n = max(4, int(duree * 360))
    segs = []
    for i in range(n + 1):
        ti = t - i / 360
        s = acteur.squelette(ti)["arme"] if ti >= 0 else None
        if not s:
            break
        segs.append(s)
    if len(segs) < 3:
        return
    for i in range(len(segs) - 1, 0, -1):
        (b0, t0), (b1, t1) = segs[i], segs[i - 1]          # i = ancien, i-1 = récent
        v = dist(t0, t1) * 360
        f = min(1, max(0, (v - seuil) / 900)) * force
        if f <= 0:
            continue
        u = i / (len(segs) - 1)                              # âge 0 (récent) -> 1 (ancien)
        gris = .05 + .75 * u ** .8
        a = f * (1 - u) ** 1.2
        q0, q1 = lerp_pt(b0, t0, r0), lerp_pt(b1, t1, r0)
        poly(cr, [q0, add(t0, unit(sub(t0, q0)), 10), add(t1, unit(sub(t1, q1)), 10), q1], (gris, gris, gris + .01, a * .92))
        trait(cr, add(t0, unit(sub(t0, q0)), 14), add(t1, unit(sub(t1, q1)), 14), 3 + 5 * (1 - u), (1, 1, 1, a))
        if lueur and glow is not None:
            trait(glow, add(t0, unit(sub(t0, q0)), 14), add(t1, unit(sub(t1, q1)), 14), 16, (*lueur, a * .9))
