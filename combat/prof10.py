"""v10 : RENDU EN PROFONDEUR.

Chaque perso est découpé en pièces (cuisses, tibias, bras, avant-bras, torse, tête) et chaque arme en tranches le long
de sa longueur. Chaque pièce reçoit une profondeur z (positive = vers le spectateur) puis TOUTES les pièces de TOUS les
persos sont triées et dessinées du fond vers l'avant (algorithme du peintre).

Profondeurs locales (perso de profil) :
  côté gauche du corps = +0.5*d (proche quand il regarde à droite), côté droit = -0.5*d ; torse 0 ; tête +0.05.
  main1 = main DROITE, main2 = main GAUCHE ; jambe1 = jambe GAUCHE, jambe2 = jambe DROITE.
  zm1 / zm2 : décalage de profondeur de la main (une main qui croise devant le ventre, un poing qui vient au centre).
  zj1 / zj2 : idem pour le pied. voie : profondeur globale du perso (qui passe devant qui).
  z (canal existant) : lacet de l'arme ; sa profondeur varie le long de la lame : z(u) = z_main + (u-g)*L/100*sin(lacet).
Une lame peut donc être cachée par le torse, la tête ou l'autre bras, et ressortir de l'autre côté.
"""
import math
import subprocess

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter1d

import arme4 as K
import corps3 as C
import effets3 as F
from corps3 import EP, EP_BUSTE, LONG, add, dist, lerp_pt, poly, sub, trait, unit
import moteur7 as E

M = E.M
for _n in ("zm1", "zm2", "zj1", "zj2", "voie"):
    if _n not in C.NUM:
        C.NUM.append(_n)


class Acteur10(C.Acteur):
    def squelette(self, t):
        sk = super().squelette(t)
        if "zm1" not in sk:
            p = self.pose(t)
            for n in ("zm1", "zm2", "zj1", "zj2", "voie", "z", "w", "g", "rot"):
                sk[n] = p[n]
        return sk


# =================================================================== armes (dessin complet ; découpage fait plus bas)
class Dague:
    """Dague du héros. Lame en feuille 62 px (acier clair, arête centrale sombre, fil blanc), garde dorée recourbée,
    poignée de cuir sombre ficelée d'or, pommeau doré. Tenue à une main, en prise directe (lame devant le pouce)
    ou inversée (lame sous l'auriculaire, le long de l'avant-bras). g = part derrière la main."""
    L = 96
    trainee_coul = (.10,)

    def lame(self, seg, d):
        b, t = seg
        return lerp_pt(b, t, .38), t

    def dessiner(self, cr, seg, d, alpha=1.0):
        b, t = seg
        l = dist(b, t)
        if l < 6:
            return
        v = unit(sub(t, b))
        n = (-v[1], v[0])
        k = l / self.L                                   # raccourci quand l'arme pointe vers le spectateur
        P = lambda u, w=0.0: add(add(b, v, u * k), n, w)  # noqa: E731
        # pommeau + poignée
        cr.set_source_rgba(.93, .74, .26, alpha)
        cr.arc(*P(2), 6.5, 0, 2 * math.pi)
        cr.fill()
        trait(cr, P(5), P(28), 9.5, (.20, .11, .06, alpha))
        for u in (10, 16, 22):
            trait(cr, P(u, -4.5), P(u + 2, 4.5), 2, (.93, .74, .26, alpha))
        # garde recourbée
        cr.set_source_rgba(.93, .74, .26, alpha)
        cr.set_line_width(5.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(*P(36, -15))
        cr.curve_to(*P(30, -9), *P(30, 9), *P(36, 15))
        cr.stroke()
        # lame en feuille
        pts = [P(31, -5.5), P(52, -8.5), P(80, -6), P(96, 0), P(80, 6), P(52, 8.5), P(31, 5.5)]
        g = cairo.LinearGradient(*P(60, -9), *P(60, 9))
        g.add_color_stop_rgba(0, .93, .95, .98, alpha)
        g.add_color_stop_rgba(.5, .70, .73, .79, alpha)
        g.add_color_stop_rgba(1, .86, .88, .93, alpha)
        cr.move_to(*pts[0])
        for q in pts[1:]:
            cr.line_to(*q)
        cr.close_path()
        cr.set_source(g)
        cr.fill_preserve()
        cr.set_source_rgba(.12, .12, .15, alpha)
        cr.set_line_width(1.8)
        cr.stroke()
        trait(cr, P(34), P(84), 1.6, (.32, .34, .40, alpha))            # arête
        trait(cr, P(54, -7.5), P(86, -4), 1.4, (1, 1, 1, .9 * alpha))    # fil


class Epee:
    """Épée d'arme des ennemis : lame droite 128 px acier gris (gouttière sombre, fil blanc), garde droite noire,
    poignée noire, pommeau rond. Tenue à une main, prise directe."""
    L = 168
    trainee_coul = (.06,)

    def lame(self, seg, d):
        b, t = seg
        return lerp_pt(b, t, .26), t

    def dessiner(self, cr, seg, d, alpha=1.0):
        b, t = seg
        l = dist(b, t)
        if l < 8:
            return
        v = unit(sub(t, b))
        n = (-v[1], v[0])
        k = l / self.L
        P = lambda u, w=0.0: add(add(b, v, u * k), n, w)  # noqa: E731
        cr.set_source_rgba(.07, .07, .08, alpha)
        cr.arc(*P(3), 7, 0, 2 * math.pi)
        cr.fill()
        trait(cr, P(5), P(34), 9, (.07, .07, .08, alpha))
        trait(cr, P(38, -17), P(38, 17), 7, (.07, .07, .08, alpha))
        pts = [P(40, -6), P(150, -5), P(168, 0), P(150, 5), P(40, 6)]
        cr.move_to(*pts[0])
        for q in pts[1:]:
            cr.line_to(*q)
        cr.close_path()
        cr.set_source_rgba(.62, .64, .69, alpha)
        cr.fill_preserve()
        cr.set_source_rgba(.10, .10, .12, alpha)
        cr.set_line_width(1.6)
        cr.stroke()
        trait(cr, P(42), P(140), 2, (.36, .37, .41, alpha))
        trait(cr, P(44, -4.5), P(156, -3.5), 1.4, (1, 1, 1, .85 * alpha))


# =================================================================== pièces
def _ombre_coul(coul, z):
    """Côté éloigné : le héros coloré s'assombrit, l'ennemi noir s'éclaircit en gris (sinon on ne lit pas la profondeur)."""
    k = min(1, max(0, -z / .5))
    if max(coul) < .12:
        return tuple(c + (.30 - c) * .62 * k for c in coul)
    return tuple(c * (1 - .30 * k) for c in coul)


def pieces(sk, coul, arme=None, alpha=1.0, tient=True):
    """Liste (z, fonction de dessin)."""
    d = sk["d"]
    v = sk.get("voie", 0.0)
    out = []
    zs = {1: -.5 * d, 2: .5 * d}                 # 1 = droite, 2 = gauche
    zl = {1: .35 * d, 2: -.35 * d}               # jambe1 = gauche, jambe2 = droite

    def seg(a, b, w, z, zc=None):
        c = _ombre_coul(coul, z)
        out.append((v + z, lambda cr, a=a, b=b, w=w, c=c: trait(cr, sk[a], sk[b], w, (*c, alpha))))

    for i in (1, 2):
        zp = zl[i] + sk.get(f"zj{i}", 0)
        seg("bassin", f"genou{i}", EP, (zl[i] * .8 + zp) / 2 - .001)
        seg(f"genou{i}", f"pied{i}", EP, zp)
        zh = zs[i] + sk.get(f"zm{i}", 0)
        ze = zs[i] * .9 + sk.get(f"zm{i}", 0) * .5
        seg("epaule", f"coude{i}", EP, (zs[i] * .5 + ze) / 2)
        seg(f"coude{i}", f"main{i}", EP, (ze + zh) / 2 + .002)
    c0 = (*coul, alpha)
    out.append((v, lambda cr: (trait(cr, sk["bassin"], sk["epaule"], EP_BUSTE, c0),
                               trait(cr, sk["epaule"], sk["cou"], EP_BUSTE * .8, c0))))

    def tete(cr):
        cr.set_source_rgba(*c0)
        cr.arc(*sk["tete"], LONG["tete"], 0, 2 * math.pi)
        cr.fill()
    out.append((v + .05, tete))
    if arme is not None and sk.get("arme") and tient:
        out += tranches_arme(sk, arme, v + zs[1] + sk.get("zm1", 0), alpha)
    return out


def tranches_arme(sk, arme, z_main, alpha=1.0, n=5):
    """L'arme est découpée en n tranches perpendiculaires à son axe ; chaque tranche a sa profondeur."""
    b, t = sk["arme"]
    l = dist(b, t)
    if l < 4:
        return []
    v = unit(sub(t, b))
    nn = (-v[1], v[0])
    pente = math.sin(math.radians(sk.get("z", 0))) * arme.L / 100 * (1 if sk["d"] > 0 else -1)
    g = sk.get("g", 0)
    out = []
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        um = (u0 + u1) / 2
        z = z_main + (um - g) * pente - .004             # léger biais : la poignée passe SOUS les doigts
        e0 = -60 if i == 0 else 0
        e1 = 60 if i == n - 1 else 0
        p0, p1 = add(b, v, l * u0 - .8 + e0), add(b, v, l * u1 + .8 + e1)
        quad = [add(p0, nn, -40), add(p1, nn, -40), add(p1, nn, 40), add(p0, nn, 40)]
        sombre = min(1, max(0, -(z - sk.get("voie", 0)) / .5)) * .30

        def f(cr, quad=quad, sombre=sombre):
            cr.save()
            cr.move_to(*quad[0])
            for q in quad[1:]:
                cr.line_to(*q)
            cr.close_path()
            cr.clip()
            if sombre > .02:
                cr.push_group()
                arme.dessiner(cr, sk["arme"], sk["d"], alpha)
                cr.set_operator(cairo.OPERATOR_ATOP)
                cr.set_source_rgba(0, 0, 0, sombre)
                cr.paint()
                cr.pop_group_to_source()
                cr.paint()
            else:
                arme.dessiner(cr, sk["arme"], sk["d"], alpha)
            cr.restore()
        out.append((z, f))
    return out


def dessiner_scene(cr, persos, t):
    """persos : [(acteur, couleur, arme|None, tenue(t)->bool)] -> toutes les pièces triées."""
    tout = []
    for i, (a, coul, arme, tenue) in enumerate(persos):
        sk = a.squelette(t)
        for z, f in pieces(sk, coul, arme, tient=tenue(t) if tenue else True):
            tout.append((z, i, f))
    tout.sort(key=lambda q: (q[0], q[1]))
    for _, _, f in tout:
        f(cr)


# =================================================================== traînées
def trainee_membre(cr, acteur, os_, t, duree=.075, seuil=1250, larg=EP):
    """Arc de vitesse derrière un poing / pied rapide (gris qui s'efface), seulement sur les vrais coups."""
    pts = []
    for i in range(int(duree * 360) + 1):
        ti = t - i / 360
        if ti < 0:
            break
        pts.append(acteur.squelette(ti)[os_])
    for i in range(len(pts) - 1, 0, -1):
        v = dist(pts[i], pts[i - 1]) * 360
        f = min(1, max(0, (v - seuil) / 1000))
        if f <= 0:
            continue
        u = i / (len(pts) - 1)
        gris = .15 + .7 * u
        trait(cr, pts[i], pts[i - 1], larg * (1.15 - .8 * u), (gris, gris, gris + .01, f * (1 - u) ** 1.1 * .75))


def trainee_arme(cr, lueur, acteur, arme, t, duree=.09, seuil=900, coul_lueur=None):
    segs = []
    d0 = None
    for i in range(int(duree * 360) + 1):
        ti = t - i / 360
        sk = acteur.squelette(ti) if ti >= 0 else None
        if not sk or not sk["arme"] or (d0 is not None and sk["d"] != d0):
            break
        d0 = sk["d"]
        segs.append(arme.lame(sk["arme"], sk["d"]))
    for i in range(len(segs) - 1, 0, -1):
        (b0, t0), (b1, t1) = segs[i], segs[i - 1]
        v = dist(t0, t1) * 360
        f = min(1, max(0, (v - seuil) / 900))
        if f <= 0:
            continue
        u = i / (len(segs) - 1)
        g = arme.trainee_coul[0] + .75 * u ** .8
        a = f * (1 - u) ** 1.2
        poly(cr, [b0, t0, t1, b1], (g, g, g + .02, a * .8))
        trait(cr, t0, t1, 2.5 + 5 * (1 - u), (1, 1, 1, a))
        if coul_lueur and lueur is not None:
            trait(lueur, t0, t1, 16, (*coul_lueur, a * .9))


# =================================================================== rendu
def rendre10(h, ennemis, ev, sortie, duree, musique, coul_h, armes=None, tenues=None, son=True, dossier=None,
             jusqua=None, morts=(), seed=4, poids_h=.72, projectiles=(), extra=None, coups_membres=(), coups_armes=(),
             coul_e=(.04, .04, .05), cadre=None, zoom_base=1.0, morceau=None):
    """armes / tenues : dict acteur -> objet arme / fonction t->bool. coups_membres : [(acteur, os, t0, t1)] fenêtres
    où une traînée de membre est permise ; coups_armes : [(acteur, t0, t1)]."""
    armes, tenues = armes or {}, tenues or {}
    rng = np.random.default_rng(seed)
    rng_d = np.random.default_rng(seed + 1000)      # hasard du DESSIN séparé : un morceau rendu seul = identique
    sh = h.squelette
    tous = [h] + list(ennemis)
    n_tot = int(round(duree * C.FPS))
    n_img = int(round((jusqua or duree) * C.FPS))
    ts = np.arange(n_tot) / C.FPS

    def proche(t):
        hx = sh(t)["bassin"][0]
        return min(ennemis, key=lambda e: abs(e.squelette(t)["bassin"][0] - hx) + (900 if e.squelette(t)["air"] < -1 else 0))
    if cadre:
        cx = np.array([cadre(t) for t in ts])
    else:
        cx = np.array([poids_h * sh(t)["tete"][0] + (1 - poids_h) * proche(t).squelette(t)["bassin"][0] for t in ts])
    cy = np.array([max(0.0, (C.SOL - 300) - min(a.squelette(t)["tete"][1] for a in tous[:1])) for t in ts])
    cx = gaussian_filter1d(cx, .14 * C.FPS, mode="nearest")
    cy = gaussian_filter1d(cy, .16 * C.FPS, mode="nearest")
    part = M.Particules(rng)
    fum = F.Fumee(rng)
    etinc, effets, chocs = [], [], []
    c_flou, c_lueur, c_ombre = F.Couche(), F.Couche(), F.Couche()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, C.W, C.H)
    cr = cairo.Context(surf)
    f0, f1 = (0, None) if not morceau else morceau
    if morceau:
        n_img = min(n_img, f1)
    vid = M.ecrivain(sortie if not son else sortie + ".v.mp4")
    t_prec = -1.0
    persos = [(h, coul_h, armes.get(h), tenues.get(h))] + [(e, coul_e, armes.get(e), tenues.get(e)) for e in ennemis]
    for f in range(n_img):
        t = f / C.FPS
        dt = 1 / C.FPS
        for e_ in ev:
            if t_prec < e_["t"] <= t:
                p, typ = e_["pt"], e_["typ"]
                k_ = e_.get("f", 1.0)
                if typ == "clang":
                    effets += [(t, "flash", (p, 100 * k_)), (t, "eclat", (p, 160 * k_)), (t, "rayons", (p, 9, 170 * k_))]
                    for _ in range(int(24 * k_)):
                        an = rng.uniform(0, 2 * math.pi)
                        sp = rng.uniform(300, 1100) * k_
                        etinc.append(dict(pos=list(p), vit=[math.cos(an) * sp, math.sin(an) * sp - 200], age=0,
                                          vie=rng.uniform(.18, .4)))
                    chocs.append((t, 10 * k_, p, .03 * k_, 0))
                elif typ == "parade":                      # bloc à mains nues
                    effets += [(t, "eclat", (p, 120 * k_)), (t, "rayons", (p, 7, 140 * k_))]
                    fum.bouffee(p, n=5, force=200, taille=20, vie=.35, gris=.95, alpha=.6, haut=1)
                    chocs.append((t, 8 * k_, p, .02 * k_, 0))
                elif typ == "coup":                         # coup de lame qui entaille
                    effets += [(t, "flash", (p, 150 * k_)), (t, "rayons", (p, 10, 240 * k_)), (t, "eclat", (p, 210 * k_)),
                               (t, "entaille", (p, e_.get("ang", -30), 430 * k_))]
                    part.sang(p, e_.get("dirv", (1, -.4)), n=int(e_.get("sang", 8) * .6 * k_), force=950, cone=.5)
                    chocs.append((t, 20 * k_, p, .06 * k_, e_.get("rot", 0)))
                elif typ == "frappe":                       # poing, pied, genou
                    effets += [(t, "flash", (p, 110 * k_)), (t, "eclat", (p, 170 * k_)), (t, "rayons", (p, 8, 180 * k_))]
                    fum.bouffee(p, n=4, force=220, taille=20, vie=.35, gris=.95, alpha=.5, haut=1)
                    if e_.get("sang"):
                        part.sang(p, e_.get("dirv", (1, -.5)), n=int(e_["sang"]), force=700, cone=.5)
                    chocs.append((t, 14 * k_, p, .04 * k_, e_.get("rot", 0)))
                elif typ == "sol":                          # corps qui s'écrase au sol
                    s_ = (p[0], C.SOL)
                    effets += [(t, "onde", (s_,)), (t, "eclat", (s_, 160 * k_))]
                    fum.bouffee(s_, n=int(22 * k_), force=600 * k_, taille=44, vie=1.0, gris=.6, haut=.35, etal=50, alpha=.7)
                    part.debris(s_, n=int(6 * k_), force=500)
                    chocs.append((t, 22 * k_, p, .05 * k_, 2))
                elif typ == "impact":
                    s_ = (p[0], C.SOL)
                    effets += [(t, "flash", (p, 300)), (t, "rayons", (p, 18, 420)), (t, "entaille", (p, e_.get("ang", -35), 640)),
                               (t, "onde", (s_,)), (t, "eclat", (p, 380))]
                    part.sang(p, (0, -1), n=60, force=1250, cone=1.0)
                    part.debris(s_, n=16, force=880)
                    part.fissure(s_, n=9, larg=250)
                    fum.bouffee(s_, n=40, force=880, taille=58, vie=1.2, gris=.42, haut=.35, etal=60, alpha=.8)
                    chocs.append((t, 42, p, .11, 4))
                elif typ == "giclee":
                    effets += [(t, "flash", (p, 160)), (t, "entaille", (p, e_.get("ang", -30), 620))]
                    part.sang(p, (0, -1), n=int(e_.get("n", 40) * .45), force=1100, cone=1.1)
                    chocs.append((t, 24, p, .07, 2))
                elif typ == "eclair":
                    effets.append((t, "eclat", (p, 90 * k_)))
                elif typ == "gouttes":
                    part.sang(p, e_.get("dirv", (-1, .3)), n=18, force=700, cone=.25)
                elif typ == "poussiere":
                    fum.bouffee(p, n=e_.get("n", 10), force=280, taille=26, vie=.7, gris=.78, alpha=.55)
        for a in tous:
            sk = a.squelette(t)
            if sk["air"] < 5 and rng.random() < .35:
                for pied in ("pied1", "pied2"):
                    p0, p1 = sk[pied], a.squelette(max(0, t - dt))[pied]
                    if abs(p0[0] - p1[0]) * C.FPS > 450 and p0[1] > C.SOL - 30:
                        fum.bouffee((p0[0], C.SOL), n=1, force=140, taille=22, vie=.6, gris=.8, alpha=.45,
                                    dirx=-math.copysign(.7, p0[0] - p1[0]))
        for (qui, m0, m1) in morts:
            if not (m0 < t < min(m1, m0 + 1.2) and rng.random() < .12):
                continue
            ak = qui.squelette(t)
            c = lerp_pt(ak["bassin"], ak["epaule"], rng.uniform(0, 1.1))
            part.taches.append(dict(x=c[0] + rng.normal(0, 18), y=C.SOL + rng.uniform(-6, 10),
                                    l=rng.uniform(14, 34), h=rng.uniform(5, 9), a=.9))
        n_taches = len(part.taches)
        part.maj(dt)
        fum.maj(dt)
        for s_ in part.taches[n_taches:]:            # taches au sol plus petites (moins « flaque géante »)
            s_["l"] *= .5
            s_["h"] *= .75
        if t > duree - .45:                         # boucle : le sol redevient propre avant la reprise
            for s_ in part.taches:
                s_["a"] *= .88
            part.cailloux = [q for q in part.cailloux if rng.random() > .2]
        for s in etinc:
            s["age"] += dt
            s["vit"][1] += 1600 * dt
            s["pos"][0] += s["vit"][0] * dt
            s["pos"][1] += s["vit"][1] * dt
        etinc = [s for s in etinc if s["age"] < s["vie"]]
        t_prec = t
        if f < f0 or (f1 is not None and f >= f1):
            effets = [e for e in effets if t - e[0] < .5]
            continue                                   # simulé (fumée, sang, chocs) mais pas dessiné

        ox = oy = rz = 0.0
        zoom, zc = zoom_base, (cx[f], 1230 - cy[f] * .6)
        for t0, amp, p, z, rr in chocs:
            if t >= t0:
                d_ = t - t0
                k_ = math.exp(-d_ / .15)
                ox += amp * k_ * math.sin(d_ * 97 + amp)
                oy += amp * .7 * k_ * math.cos(d_ * 83 + amp * 2)
                zoom += z * math.exp(-d_ / .16)
                rz += math.radians(rr) * math.exp(-d_ / .2) * math.cos(d_ * 30)
        mat = cairo.Matrix(x0=-zc[0], y0=-zc[1])
        mat = mat.multiply(cairo.Matrix(xx=zoom, yy=zoom))
        mat = mat.multiply(cairo.Matrix.init_rotate(rz))
        mat = mat.multiply(cairo.Matrix(x0=C.W / 2 + ox, y0=1230 + oy))

        cr.identity_matrix()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        cr.save()
        cr.rectangle(0, C.BANDE, C.W, C.H - C.BANDE)
        cr.clip()
        cr.save()
        cr.transform(mat)
        F.decor(cr)
        part.dessiner_sol(cr)
        cr.restore()
        g = c_ombre.debut(mat)
        for a in tous:
            F.ombre_projetee(g, a.squelette(t))
        c_ombre.poser(cr, 2.2, alpha=.26)
        cr.save()
        cr.transform(mat)
        lueur = c_lueur.debut(mat)
        # traînées DERRIÈRE tous les corps (ne recouvrent jamais l'adversaire)
        for (a, os_, t0, t1) in coups_membres:
            if t0 <= t <= t1 + .1:
                trainee_membre(cr, a, os_, t)
        for (a, t0, t1) in coups_armes:
            if t0 <= t <= t1 + .1 and armes.get(a):
                trainee_arme(cr, lueur, a, armes[a], t)
        for pj in projectiles:
            if pj.colle is None and t > pj.t1:
                pj.figer()
            pj.dessiner(cr, lueur, t)
        for a, coul, *_ in persos:
            K.fantomes(cr, a, t, C.dessiner_corps, coul)
        if extra:
            extra(cr, lueur, t, "avant")
        dessiner_scene(cr, persos, t)
        if extra:
            extra(cr, lueur, t, "apres")
        v = K.fantomes(cr, h, t, lambda *a_, **k_: None, coul_h)
        if v > 1300:
            K.lignes_vitesse(cr, sh(t)["bassin"], sub(sh(t)["bassin"], sh(t - .02)["bassin"]), min(1, (v - 1300) / 1200), rng_d)
        part.dessiner(cr)
        for s in etinc:
            v_ = s["vit"]
            n_ = math.hypot(*v_) or 1
            l_ = min(40, n_ * .03)
            u_ = 1 - s["age"] / s["vie"]
            M.trait(cr, s["pos"], (s["pos"][0] - v_[0] / n_ * l_, s["pos"][1] - v_[1] / n_ * l_), 3.2 * u_ + 1,
                    (1, .93, .62, u_))
        for t0, typ, d_ in effets:
            u_ = t - t0
            if typ == "flash":
                M.flash(lueur, d_[0], u_ / .2, d_[1] * .9)
                M.flash(cr, d_[0], u_ / .16, d_[1] * .6)
            elif typ == "rayons":
                M.rayons(cr, d_[0], u_ / .17, d_[1], int(t0 * 1000), d_[2])
            elif typ == "entaille":
                M.entaille(cr, d_[0], d_[1], u_ / .3, d_[2])
            elif typ == "onde":
                M.onde(cr, d_[0], u_ / .45)
            elif typ == "eclat":
                F.eclat(cr, d_[0], u_ / .25, d_[1])
        effets = [e for e in effets if t - e[0] < .5]
        cr.restore()
        g = c_flou.debut(mat)
        fum.dessiner(g)
        c_flou.poser(cr, 3.2)
        c_lueur.poser(cr, 4.0, additif=True, alpha=.5)
        F.vignette(cr, C.BANDE)
        cr.restore()
        M.texte(cr, "my weapon type:", 400, 84)
        vid.stdin.write(surf.get_data())
        if dossier and f % 3 == 0:
            surf.write_to_png(f"{dossier}/i{f:04d}.png")
    vid.stdin.close()
    vid.wait()
    if son:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", sortie + ".v.mp4", "-i", musique, "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{n_img / C.FPS:.3f}",
                        sortie], check=True)
    print(f"{n_img} images -> {sortie}")


def image(persos, t, chemin, cadre_x=540, armes_traces=()):
    """Image fixe de contrôle (sans effets), pour les planches."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, C.W, C.H)
    cr = cairo.Context(surf)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    cr.translate(C.W / 2 - cadre_x, 0)
    F.decor(cr)
    dessiner_scene(cr, persos, t)
    surf.write_to_png(chemin)


def parallele(script, sortie, musique, duree, n=None, extra_args=()):
    """Rendu en n morceaux simultanés (un par cœur), recollés sans réencodage, puis la musique."""
    import os
    import tempfile
    n = n or os.cpu_count()
    nf = int(round(duree * C.FPS))
    bornes = [round(nf * i / n) for i in range(n + 1)]
    tmp = tempfile.mkdtemp()
    procs = []
    for i in range(n):
        out = f"{tmp}/m{i}.mp4"
        procs.append((out, subprocess.Popen(["python3", script, out, "--muet", "--morceau", str(bornes[i]), str(bornes[i + 1]),
                                             *extra_args], stdout=subprocess.DEVNULL)))
    for _, pr in procs:
        assert pr.wait() == 0
    with open(f"{tmp}/liste.txt", "w") as f:
        f.writelines(f"file '{o}'\n" for o, _ in procs)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/liste.txt", "-i", musique,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{nf / C.FPS:.3f}", sortie],
                   check=True)
    print(f"{nf} images en {n} morceaux -> {sortie}")
