"""v8 : bibliothèque de POSITIONS (sprint Naruto, dash, salto, tornade, scorpion, high kick, projeté, relevé ninja…)
+ VÉRIFICATEUR de chorégraphie (chaque coup déclaré touché / paré / esquivé est mesuré sur les squelettes)."""
import math

from corps3 import EP, add, dist, lerp_pt, sub, unit
from lib7 import A, AB, B, CORPS, COUL_E, course, ennemi, fab, mort, pause, plongee, pres, resoudre, roulade, saut  # noqa: F401
from moteur7 import vol_balistique

# ---------------------------------------------------------------- poses de positions (corps seulement)
P8 = {
    "naruto1": dict(t=56, h=-34, b1=-112, a1=-104, b2=-118, a2=-110, c1=78, j1=-6, c2=-58, j2=-30),
    "naruto2": dict(t=56, h=-34, b1=-112, a1=-104, b2=-118, a2=-110, c1=-58, j1=-30, c2=78, j2=-6),
    "dash": dict(t=58, h=-30, b1=-80, a1=-60, b2=-100, a2=-90, c1=104, j1=-10, c2=-66, j2=-86),
    "groupe": dict(t=40, h=20, b1=70, a1=20, b2=70, a2=20, c1=124, j1=10, c2=116, j2=4),
    "tornade": dict(t=-6, h=-10, b1=96, a1=100, b2=-80, a2=-100, c1=96, j1=96, c2=40, j2=-50),
    "scorpion": dict(t=30, h=-26, c1=4, j1=0, c2=-128, j2=-206),
    "high_kick": dict(t=-28, h=-6, b1=40, a1=100, b2=-60, a2=-100, c1=172, j1=176, c2=-6, j2=-8),
    "kick_arme": dict(t=6, h=-6, b1=50, a1=110, b2=-40, a2=-90, c1=118, j1=-10, c2=-10, j2=-14),
    "accroupi": dict(t=46, h=-22, c1=100, j1=-30, c2=-36, j2=-96),
    "glisse": dict(rot=-40, t=-20, h=-10, c1=96, j1=96, c2=20, j2=-60),
    "plat": dict(rot=-90, t=0, h=-4, b1=176, a1=184, b2=8, a2=4, c1=6, j1=2, c2=-6, j2=-10),
    "dos_groupe": dict(rot=-130, t=20, h=10, b1=170, a1=200, b2=170, a2=200, c1=130, j1=20, c2=120, j2=10),
    "detente": dict(rot=-30, t=-10, h=-10, b1=60, a1=40, b2=60, a2=40, c1=60, j1=50, c2=40, j2=30),
    "reception": dict(t=40, h=-16, c1=100, j1=-26, c2=-14, j2=-90),
    "vol1": dict(t=-40, h=-30, b1=150, a1=190, b2=-90, a2=-130, c1=40, j1=70, c2=-30, j2=-10),
    "vol2": dict(t=-30, h=-20, b1=170, a1=200, b2=-70, a2=-110, c1=60, j1=90, c2=-10, j2=20),
}
# ennemis : attaques avec ARMEMENT visible (on voit venir le coup)
EA = dict(A)
EA.update({k: v for k, v in P8.items()})
EA.update({
    "arme_poing": dict(t=-8, h=-4, b1=-40, a1=70, b2=60, a2=130, c1=40, j1=-6, c2=-34, j2=-46),
    "jab": dict(t=18, h=-6, b1=90, a1=90, b2=40, a2=128, c1=46, j1=-2, c2=-36, j2=-48),
    "cross": dict(t=28, h=-8, b1=86, a1=88, b2=50, a2=130, c1=56, j1=0, c2=-44, j2=-58),
    "arme_pied": dict(t=-8, h=-6, b1=60, a1=130, b2=-40, a2=-80, c1=112, j1=-20, c2=-6, j2=-10),
    "pied_haut": dict(t=-30, h=-8, b1=60, a1=130, b2=-50, a2=-90, c1=118, j1=124, c2=-8, j2=-12),
    "saut_pied": dict(t=-20, h=-10, b1=120, a1=150, b2=-60, a2=-30, c1=95, j1=95, c2=40, j2=-40),
    "sonne": dict(t=-26, h=-30, b1=30, a1=90, b2=10, a2=60, c1=20, j1=-10, c2=-40, j2=-50),
    "genoux": dict(t=30, h=10, b1=20, a1=10, b2=-10, a2=0, c1=40, j1=-90, c2=0, j2=-92),
    "oreilles": dict(t=20, h=12, b1=140, a1=230, b2=140, a2=230, c1=30, j1=-8, c2=-22, j2=-40),
    "ramasse": dict(t=70, h=-30, b1=70, a1=50, b2=40, a2=20, c1=90, j1=-40, c2=-20, j2=-80),
})


# ---------------------------------------------------------------- positions
def naruto(a, mk, t0, t1, x0, x1, pas=.1, **kw):
    """Sprint Naruto : buste couché vers l'avant, bras tendus derrière, grandes foulées."""
    n = max(1, int(round((t1 - t0) / pas)))
    for i in range(n + 1):
        u = i / n
        a.cle(t0 + (t1 - t0) * u, **mk("naruto1" if i % 2 == 0 else "naruto2", x=x0 + (x1 - x0) * u, air=6 * (i % 2), **kw))


def dash(a, mk, t0, t1, x0, x1, nom="dash", **kw):
    """Dash : départ bas, trajet très rapide (images fantômes automatiques), freinage en appui."""
    a.cle(t0, **mk(nom, x=x0, **kw))
    a.cle(t0 + (t1 - t0) * .5, **mk(nom, x=x0 + (x1 - x0) * .62, air=4, **kw))
    a.cle(t1, **mk(nom, x=x1, **kw))


def salto(a, mk, t0, t1, x0, x1, haut, avant, rot0=0, pose_sol="garde", d=1, **kw):
    """Salto avant (rot +360) ou arrière (rot -360) : appel fléchi, groupé, réception amortie."""
    r1 = rot0 + (360 if avant else -360)
    saut(a, mk, "groupe", t0, t1, x0, x1, haut, pose_sol=pose_sol, rot0=rot0, rot1=r1, d=d, **kw)
    a.cle(t0 + (t1 - t0) * .25, **mk("groupe", x=x0 + (x1 - x0) * .25, air=haut * .75, rot=rot0 + (r1 - rot0) * .25, d=d, **kw))
    a.cle(t0 + (t1 - t0) * .75, **mk("groupe", x=x0 + (x1 - x0) * .75, air=haut * .75, rot=rot0 + (r1 - rot0) * .75, d=d, **kw))
    return r1


def tornade(a, mk, t0, t1, x0, x1, haut, d_fin, demi=3, nom="tornade", **kw):
    """Tornade : saut + demi-tours (le perso se retourne à chaque demi-tour), jambe d'attaque tendue."""
    d = d_fin * (-1) ** demi
    a.cle(t0, **mk("accroupi", x=x0, d=d, **kw))
    for i in range(demi + 1):
        u = (i + .5) / (demi + 1)
        tt = t0 + (t1 - t0) * u
        a.cle(tt, coupe=i > 0, **mk(nom, x=x0 + (x1 - x0) * u, air=haut * 4 * u * (1 - u) + 20, d=d, **kw))
        d = -d


def projete(a, mk, t, x, dx, d, haut=90, duree=.4, rot0=0, **kw):
    """Projeté au sol (non mortel) : vol, choc dos au sol, glissade. Retourne le x d'arrivée."""
    sens = 1 if dx * d < 0 else -1
    r1 = rot0 - 90 * sens
    vol_balistique(a, mk, t, t + duree, x, x + dx, 0, 0, haut, rot0, r1, d=d, **kw)
    a.cle(t + duree, **mk("plat", x=x + dx, rot=r1, d=d, **kw))
    a.cle(t + duree + .07, **mk("plat", x=x + dx * 1.07, air=12, rot=r1 - 3, d=d, **kw))
    a.cle(t + duree + .2, **mk("plat", x=x + dx * 1.12, rot=r1, d=d, **kw))
    return x + dx * 1.12, r1


def releve_ninja(a, mk, t0, x, d, rot0=-90, pose="garde", **kw):
    """Kip-up : dos au sol -> genoux à la poitrine -> détente des jambes -> debout. Dure 0.42 s."""
    s = 1 if rot0 < 0 else -1
    a.cle(t0, **mk("plat", x=x, rot=rot0, d=d, **kw))
    a.cle(t0 + .12, **mk("dos_groupe", x=x, rot=rot0 - 40 * s, d=d, **kw))
    a.cle(t0 + .24, **mk("detente", x=x + 30 * d, air=70, rot=rot0 + 60 * s, d=d, **kw))
    a.cle(t0 + .34, **mk("reception", x=x + 50 * d, rot=0, d=d, **kw))
    a.cle(t0 + .44, **mk(pose, x=x + 56 * d, d=d, **kw))
    return x + 56 * d


# ---------------------------------------------------------------- vérificateur
def segments(sk):
    s = [("bassin", "epaule"), ("epaule", "cou"), ("epaule", "coude1"), ("coude1", "main1"), ("epaule", "coude2"),
         ("coude2", "main2"), ("bassin", "genou1"), ("genou1", "pied1"), ("bassin", "genou2"), ("genou2", "pied2")]
    return [(sk[a], sk[b]) for a, b in s] + [(sk["tete"], sk["tete"])]


def d_seg(p, a, b):
    ab = sub(b, a)
    l2 = ab[0] ** 2 + ab[1] ** 2
    u = 0 if l2 < 1e-9 else max(0, min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / l2))
    return dist(p, add(a, ab, u))


def d_corps(p, sk):
    """Distance du point à la SURFACE du corps (épaisseur des membres, tête ronde)."""
    best = 1e9
    for a, b in segments(sk):
        r = 30 if a == b else (EP / 2 + 4)
        best = min(best, d_seg(p, a, b) - r)
    return best


class Verif:
    """Les mesures sont DIFFÉRÉES : évaluées dans rapport(), quand toutes les clés de la chorégraphie existent
    (sinon une clé ajoutée plus tard peut changer la trajectoire après la mesure)."""
    def __init__(self):
        self.lignes = []
        self.differe = []

    def __getattribute__(self, nom):
        if nom in ("touche", "pare", "esquive", "choc"):
            f = object.__getattribute__(self, nom)
            return lambda *a, **k: object.__getattribute__(self, "differe").append(lambda: f(*a, **k))
        return object.__getattribute__(self, nom)

    def touche(self, t, nom, pt, cible, tol=25):
        e = d_corps(pt(t), cible.squelette(t))
        self.lignes.append((t, nom, "touché", e, e <= tol))

    def pare(self, t, nom, pt, seg_def, tol=25):
        a, b = seg_def(t)
        e = d_seg(pt(t), a, b)
        self.lignes.append((t, nom, "paré", e, e <= tol))

    def esquive(self, t0, t1, nom, pt, cible, marge=20):
        e = min(d_corps(pt(t0 + (t1 - t0) * i / 24), cible.squelette(t0 + (t1 - t0) * i / 24)) for i in range(25))
        self.lignes.append((t1, nom, "esquivé", e, e >= marge))

    def choc(self, t, nom, pa, pb, v_min=300):
        """Lames qui se rencontrent : contact (< 25 px) ET les DEUX lames en mouvement juste avant (pas d'impact figé)."""
        e = dist(pa(t), pb(t))
        va = dist(pa(t), pa(t - .08)) / .08
        vb = dist(pb(t), pb(t - .08)) / .08
        self.lignes.append((t, nom, "choc", e, e <= 25))
        self.lignes.append((t, nom + " (2 lames bougent)", "vitesse", min(va, vb), min(va, vb) >= v_min))

    def retournements(self, a, duree, ecart=.45, maxi=6):
        """Pas de perso qui glitche : peu de demi-tours, jamais deux à moins de `ecart` s."""
        flips, d0 = [], a.squelette(0)["d"]
        for f in range(1, int(duree * 60)):
            d = a.squelette(f / 60)["d"]
            if d != d0:
                flips.append(f / 60)
                d0 = d
        serre = min((b - a_ for a_, b in zip(flips, flips[1:])), default=9)
        self.lignes.append((duree, f"{a.nom} : {len(flips)} demi-tours", "retournements", serre, len(flips) <= maxi and serre >= ecart))

    def armement(self, a, t_coup, t_arme, nom):
        ok = t_coup - t_arme >= .15
        self.lignes.append((t_coup, nom + " (armé)", "visible", t_coup - t_arme, ok))

    def globaux(self, acteurs, duree, libres=()):
        """Téléportations (bassin > 2600 px/s hors fenêtres libres) et corps qui se traversent (> 0.12 s)."""
        n = int(duree * 60)
        for a in acteurs:
            for f in range(1, n):
                t = f / 60
                p_ = a.pose(t)
                if any(t0 <= t <= t1 for t0, t1 in libres) or abs(((p_["rot"] + 180) % 360) - 180) > 20 or p_["air"] > 10:
                    continue
                v = abs(a.squelette(t)["bassin"][0] - a.squelette(t - 1 / 60)["bassin"][0]) * 60
                if v > 2600:
                    self.lignes.append((t, f"{a.nom} vitesse", "téléport", v, False))
                    break
        for i, a in enumerate(acteurs):
            for b in acteurs[i + 1:]:
                run = 0
                for f in range(n):
                    t = f / 60
                    sa, sb = a.squelette(t), b.squelette(t)
                    debout = sa["air"] < 30 and sb["air"] < 30 and abs(sa["tete"][1] - sb["tete"][1]) < 60
                    if debout and abs(sa["bassin"][0] - sb["bassin"][0]) < 34 and sa["tete"][1] < 1400 and sb["tete"][1] < 1400:
                        run += 1
                        if run == 8:
                            self.lignes.append((t, f"{a.nom}/{b.nom}", "superposés", 0, False))
                    else:
                        run = 0

    def rapport(self):
        for f in self.differe:
            f()
        self.differe = []
        self.lignes.sort(key=lambda l_: l_[0])
        ok = all(l_[4] for l_ in self.lignes)
        out = [f"{'t':>6}  {'action':38s} {'issue':10s} {'mesure':>7}  ok"]
        for t, nom, iss, e, b in self.lignes:
            out.append(f"{t:6.2f}  {nom:38s} {iss:10s} {e:7.1f}  {'✔' if b else '✘'}")
        return ok, "\n".join(out)
