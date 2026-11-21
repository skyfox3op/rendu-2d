"""Moteur v6 : outils de chorégraphie + rendu (armes tenues quelconques, projectiles, durée et musique libres)."""
import math
import os
import subprocess
import sys

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter1d

import arme4 as K
import armes5 as W
import corps3 as C
import effets3 as F
from corps3 import add, lerp_pt, poitrine, sub

import moteur as M  # noqa: E402

REF = "assets/musique_reference.wav"   # non publie : fichier local
DUREE = 7.755
NOIR, GRIS = (.03, .03, .035), (.36, .36, .37)
B = dict(b1=0.093, on0=0.534, b2=0.859, on1=1.184, b3=1.533, on2=1.858, b4=2.183, b5=2.856, on3=3.297,
         b6=3.506, on4=3.831, q1=3.99, b7=4.156, fort=4.83, b9=5.387, b10=5.991, b11=6.571, b12=7.129, final=7.43)


def fab(base, lib):
    def f(nom, **kw):
        p = dict(base)
        p.update(lib[nom])
        p.update(kw)
        return p
    return f


def pres(w, ref):
    return w + 360 * round((ref - w) / 360)


def resoudre(inconnues, erreur, iters=40, tol=.3, pas_max=60):
    for _ in range(iters):
        e0 = np.array(erreur(), float)
        if np.linalg.norm(e0) < tol:
            break
        J = np.zeros((len(e0), len(inconnues)))
        for j, (a, ts, n) in enumerate(inconnues):
            for t in ts:
                a.k(t)[n] += 1e-3
            a.invalider()
            J[:, j] = (np.array(erreur(), float) - e0) / 1e-3
            for t in ts:
                a.k(t)[n] -= 1e-3
            a.invalider()
        pas = np.clip(np.linalg.lstsq(J, -e0, rcond=None)[0], -pas_max, pas_max)
        for j, (a, ts, n) in enumerate(inconnues):
            for t in ts:
                a.k(t)[n] += pas[j]
            a.invalider()
    return float(np.linalg.norm(np.array(erreur(), float)))


def pause(acteur, t, duree, derive=None):
    """Arrêt sur le coup : recopie la clé t à t+duree (légère dérive optionnelle) -> le coup se lit."""
    p = dict(acteur.k(t))
    if derive:
        for k_, v in derive.items():
            p[k_] = p[k_] + v
    acteur.cles.append([t + duree, p, False])
    acteur.invalider()


def vol_balistique(a, mk, t0, t1, x0, x1, air0, air1, haut, rot0, rot1, poses=("vol1", "vol2"), pas=.06, **kw):
    n = max(2, int((t1 - t0) / pas))
    for i in range(1, n):
        u = i / n
        a.cle(t0 + (t1 - t0) * u, **mk(poses[i % len(poses)], x=x0 + (x1 - x0) * u,
                                      air=air0 + (air1 - air0) * u + 4 * haut * u * (1 - u),
                                      rot=rot0 + (rot1 - rot0) * u, **kw))


def rendre(h, ennemis, arme, ev, sortie, son=True, dossier=None, jusqua=None, speciaux=(), morts=(), seed=4,
           poids_h=.72, duree=DUREE, musique=REF, projectiles=(), tenue=lambda t: True, coul_h=(.1, .3, .8),
           coul_e=(.04, .04, .05), audio_pret=None, extra=None):
    rng = np.random.default_rng(seed)
    sh = h.squelette
    a = ennemis[0]
    n_tot = int(round(duree * C.FPS))
    n_img = int(round((jusqua or duree) * C.FPS))
    ts = np.arange(n_tot) / C.FPS
    def proche(t):                                   # l'ennemi le plus proche du héros (pour cadrer)
        hx = sh(t)["bassin"][0]
        return min(ennemis, key=lambda e: abs(e.squelette(t)["bassin"][0] - hx) + (900 if e.squelette(t)["air"] < -1 else 0))
    cx = np.array([poids_h * sh(t)["tete"][0] + (1 - poids_h) * proche(t).squelette(t)["bassin"][0] for t in ts])
    cy = np.array([max(0.0, (C.SOL - 300) - sh(t)["tete"][1]) for t in ts])
    cx = gaussian_filter1d(cx, .14 * C.FPS, mode="nearest")
    cy = gaussian_filter1d(cy, .16 * C.FPS, mode="nearest")
    part = M.Particules(rng)
    fum = F.Fumee(rng)
    etinc, effets, chocs = [], [], []
    c_flou, c_lueur, c_ombre = F.Couche(), F.Couche(), F.Couche()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, C.W, C.H)
    cr = cairo.Context(surf)
    vid = M.ecrivain(sortie if not son else sortie + ".v.mp4")
    t_prec = -1.0
    for f in range(n_img):
        t = f / C.FPS
        dt = 1 / C.FPS
        hk = sh(t)
        eks = [e.squelette(t) for e in ennemis]
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
                elif typ == "parade":
                    effets += [(t, "eclat", (p, 120)), (t, "rayons", (p, 7, 140))]
                    fum.bouffee(p, n=5, force=200, taille=20, vie=.35, gris=.95, alpha=.6, haut=1)
                    chocs.append((t, 8, p, .02, 0))
                elif typ == "coup":
                    effets += [(t, "flash", (p, 150 * k_)), (t, "rayons", (p, 10, 240 * k_)), (t, "eclat", (p, 210 * k_)),
                               (t, "entaille", (p, e_.get("ang", -30), 430 * k_))]
                    part.sang(p, e_.get("dirv", (1, -.4)), n=int(12 * k_), force=1050, cone=.55)
                    chocs.append((t, 20 * k_, p, .06 * k_, e_.get("rot", 0)))
                elif typ == "frappe":                       # coup sans lame (pied, talon, hampe)
                    effets += [(t, "flash", (p, 110 * k_)), (t, "eclat", (p, 170 * k_)), (t, "rayons", (p, 8, 180 * k_))]
                    fum.bouffee(p, n=4, force=220, taille=20, vie=.35, gris=.95, alpha=.5, haut=1)
                    chocs.append((t, 14 * k_, p, .04 * k_, 0))
                elif typ == "impact":
                    s_ = (p[0], C.SOL)
                    effets += [(t, "flash", (p, 300)), (t, "rayons", (p, 18, 420)), (t, "entaille", (p, e_.get("ang", -35), 640)),
                               (t, "onde", (s_,)), (t, "eclat", (p, 380))]
                    part.sang(p, (0, -1), n=60, force=1250, cone=1.0)
                    part.debris(s_, n=16, force=880)
                    part.fissure(s_, n=9, larg=250)
                    fum.bouffee(s_, n=40, force=880, taille=58, vie=1.2, gris=.42, haut=.35, etal=60, alpha=.8)
                    chocs.append((t, 42, p, .11, 4))
                elif typ == "giclee":                       # mort différée : explosion de sang
                    effets += [(t, "flash", (p, 160)), (t, "entaille", (p, e_.get("ang", -30), 620))]
                    part.sang(p, (0, -1), n=50, force=1300, cone=1.3)
                    fum.bouffee(p, n=5, force=600, taille=34, vie=.55, coul=(.66, .06, .09), alpha=.18, haut=1)
                    chocs.append((t, 24, p, .07, 2))
                elif typ == "final":
                    effets += [(t, "flash", (p, 150)), (t, "eclat", (p, 300)), (t, "rayons", (p, 14, 260))]
                    fum.bouffee((p[0], C.SOL), n=14, force=520, taille=36, vie=.9, gris=.66, haut=.3, alpha=.5)
                    chocs.append((t, 14, p, .04, 1))
                elif typ == "eclair":                       # reflet discret sur l'arme (fin : pas d'impact dans le vide)
                    effets.append((t, "eclat", (p, 90 * k_)))
                elif typ == "flash_tir":                    # coup de feu (bout du parapluie)
                    effets += [(t, "flash", (p, 120)), (t, "rayons", (p, 10, 150))]
                    fum.bouffee(p, n=6, force=200, taille=20, vie=.5, gris=.7, alpha=.5, haut=1)
                    chocs.append((t, 10, p, .02, 0))
                elif typ == "charge":                       # flèche chargée : lueur qui grossit
                    effets.append((t, "flash", (p, 70)))
                elif typ == "gouttes":                      # secoue le sang de la lame
                    part.sang(p, e_.get("dirv", (-1, .3)), n=18, force=700, cone=.25)
                elif typ == "poussiere":
                    fum.bouffee(p, n=e_.get("n", 10), force=280, taille=26, vie=.7, gris=.78, alpha=.55)
        for sk, who in [(hk, h)] + list(zip(eks, ennemis)):
            if sk["air"] < 5 and rng.random() < .35:
                for pied in ("pied1", "pied2"):
                    p0, p1 = sk[pied], who.squelette(max(0, t - dt))[pied]
                    if abs(p0[0] - p1[0]) * C.FPS > 450 and p0[1] > C.SOL - 30:
                        fum.bouffee((p0[0], C.SOL), n=1, force=140, taille=22, vie=.6, gris=.8, alpha=.45,
                                    dirx=-math.copysign(.7, p0[0] - p1[0]))
        for (qui, m0, m1) in morts:
            if not (m0 < t < m1 and rng.random() < .22):           # flaque SOUS le corps couché
                continue
            ak = qui.squelette(t)
            c = lerp_pt(ak["bassin"], ak["epaule"], rng.uniform(0, 1.1))
            part.taches.append(dict(x=c[0] + rng.normal(0, 18), y=C.SOL + rng.uniform(-6, 10),
                                    l=rng.uniform(14, 34), h=rng.uniform(5, 9), a=.9))
        part.maj(dt)
        fum.maj(dt)
        for s in etinc:
            s["age"] += dt
            s["vit"][1] += 1600 * dt
            s["pos"][0] += s["vit"][0] * dt
            s["pos"][1] += s["vit"][1] * dt
        etinc = [s for s in etinc if s["age"] < s["vie"]]
        t_prec = t

        ox = oy = rz = 0.0
        zoom, zc = 1.0, (cx[f], 1230 - cy[f] * .6)
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
        for ek in eks:
            F.ombre_projetee(g, ek)
        F.ombre_projetee(g, hk)
        c_ombre.poser(cr, 2.2, alpha=.26)
        cr.save()
        cr.transform(mat)
        lueur = c_lueur.debut(mat)
        # la traînée passe DERRIÈRE l'adversaire : elle ne se confond jamais avec son corps
        special = any(t0 < t < t1 for t0, t1 in speciaux)
        tr_ = getattr(arme, "trainee", True)
        if hk["arme"] and tenue(t) and (tr_(t) if callable(tr_) else tr_):
            W.trainee_lame(cr, lueur, h, arme, t, duree=.15 if special else .085, coul_lueur=arme.lueur if special else None)
        for pj in projectiles:
            if pj.colle is None and t > pj.t1:
                pj.figer()
            pj.dessiner(cr, lueur, t)
        for e, ek in zip(ennemis, eks):
            K.fantomes(cr, e, t, C.dessiner_corps, coul_e)
            ob = getattr(e, "objet", None)            # v9 : arme ennemie en main, cachée derrière le corps côté loin
            if ob:
                C.dessiner_heros(cr, ek, coul_e, m1=(lambda ob=ob, ek=ek: ob(cr, ek)) if ek["arme"] else None)
            else:
                C.dessiner_corps(cr, ek, coul_e)
        if extra:
            extra(cr, lueur, t)
        v = K.fantomes(cr, h, t, lambda c_, sk, col, alpha=1: (C.dessiner_corps(c_, sk, col, alpha),
                                                                arme.dessiner_sk(c_, sk, alpha * .7) if tenue(t) else None), coul_h)
        if v > 1300:
            K.lignes_vitesse(cr, hk["bassin"], sub(hk["bassin"], sh(t - .02)["bassin"]), min(1, (v - 1300) / 1200), rng)
        if hasattr(arme, "dessiner_m1"):          # v8 : arme dans une main, cachée derrière le corps côté loin
            C.dessiner_heros(cr, hk, coul_h,
                             m1=(lambda: arme.dessiner_m1(cr, hk)) if hk["arme"] and tenue(t) else None,
                             m2=(lambda: arme.dessiner_m2(cr, hk)) if hasattr(arme, "dessiner_m2") else None)
        else:
            derriere = hk["arme"] and hk["prof"] > .05 and tenue(t)
            if derriere:
                arme.dessiner_sk(cr, hk)
            C.dessiner_corps(cr, hk, coul_h)
            if hk["arme"] and not derriere and tenue(t):
                arme.dessiner_sk(cr, hk)
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
                        sortie], check=True) if not audio_pret else subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", sortie + ".v.mp4", "-i", audio_pret, "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{n_img / C.FPS:.3f}", sortie], check=True)
    print(f"{n_img} images -> {sortie}")


def saut(acteur, mk, nom_air, t0, t1, x0, x1, haut, pose_sol="garde", rot0=0, rot1=0, **kw):
    """Saut naturel : flexion d'appel, extension, groupé en l'air, réception amortie (pas un perso déplacé à la main)."""
    acc = dict(t=34, c1=86, j1=-26, c2=30, j2=-70)
    acteur.cle(t0 - .07, **mk(pose_sol, x=x0, rot=rot0, **{**kw, **acc}))
    acteur.cle(t0, **mk(pose_sol, x=x0 + (x1 - x0) * .05, air=8, rot=rot0, **{**kw, "t": 4, "c1": 30, "j1": 10, "c2": -20, "j2": -30}))
    acteur.cle((t0 + t1) / 2, **mk(nom_air, x=(x0 + x1) / 2, air=haut, rot=(rot0 + rot1) / 2, **kw))
    acteur.cle(t1, **mk(pose_sol, x=x1, air=0, rot=rot1, **{**kw, "t": 10, "c1": 50, "j1": -20, "c2": -30, "j2": -50}))
    acteur.cle(t1 + .08, **mk(pose_sol, x=x1 + (x1 - x0) * .04, rot=rot1, **{**kw, **acc}))


def plongee(acteur, mk, nom, t0, t1, p0, p1, n=4, **kw):
    """Piqué propre : trajectoire RECTILIGNE à vitesse constante (clés régulières sur la droite), corps aligné."""
    for i in range(n + 1):
        u = i / n
        acteur.cle(t0 + (t1 - t0) * u, **mk(nom, x=p0[0] + (p1[0] - p0[0]) * u, air=p0[1] + (p1[1] - p0[1]) * u, **kw))
