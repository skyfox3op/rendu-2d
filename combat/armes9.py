"""v9 : la dague longue fine (style « Needle ») et l'épée longue des ennemis. Dessinées dans la main (dessiner_m1)."""
import math

from corps3 import add, dist, sub, trait, unit


def _lame(cr, base, pointe, v, n, larg, coul, liseré, alpha):
    pts = [add(base, n, larg), add(pointe, v, -22), pointe, add(base, n, -larg)]
    cr.move_to(*pts[0])
    for q in pts[1:]:
        cr.line_to(*q)
    cr.close_path()
    cr.set_source_rgba(*coul, alpha)
    cr.fill_preserve()
    cr.set_source_rgba(*liseré, alpha)
    cr.set_line_width(1.6)
    cr.stroke()


class Dague:
    """Dague longue et fine : lame très étroite acier clair avec gorge centrale, petite garde droite en laiton,
    poignée de cuir enroulé, pommeau rond. Tenue près de la garde (g≈.12) ; w = direction de la pointe."""
    L, g0, deux = 160, .12, False
    lueur = (.85, .93, 1.0)
    trainee_coul = (.12, .14, .18)
    COUPS = ()

    def lame(self, seg, d):
        b, t = seg
        return add(b, unit(sub(t, b)), 34), t

    def trainee(self, t):
        return any(c - .11 < t < c + .04 for c in self.COUPS)

    def dessiner_m1(self, cr, sk, alpha=1.0):
        if not sk["arme"] or dist(*sk["arme"]) < 10:
            return
        b, t = sk["arme"]
        v = unit(sub(t, b))
        n = (-v[1], v[0])
        g = add(b, v, 30)
        trait(cr, b, g, 7, (.32, .2, .1, alpha))                       # cuir
        for k in range(4):
            p = add(b, v, 6 + 6 * k)
            trait(cr, add(p, n, -3.5), add(add(p, n, 3.5), v, 3), 1.2, (.18, .1, .05, alpha))
        cr.set_source_rgba(.62, .5, .22, alpha)
        cr.arc(*b, 5.5, 0, 2 * math.pi)
        cr.fill()
        trait(cr, add(g, n, -13), add(g, n, 13), 5, (.68, .55, .24, alpha))   # garde laiton
        _lame(cr, add(g, v, 3), t, v, n, 2.6, (.8, .84, .9), (.2, .22, .28), alpha)
        trait(cr, add(g, v, 8), add(t, v, -30), 1.0, (.98, .99, 1, .9 * alpha))

    def dessiner_sk(self, cr, sk, alpha=1.0):
        self.dessiner_m1(cr, sk, alpha)


class Epee:
    """Épée longue des ennemis : lame large acier sombre, garde en croix noire, poignée longue, pommeau."""
    L, g0, deux = 210, .1, False
    lueur = (1.0, .9, .7)
    trainee_coul = (.05, .05, .06)

    def lame(self, seg, d):
        b, t = seg
        return add(b, unit(sub(t, b)), 40), t

    def dessiner_m1(self, cr, sk, alpha=1.0):
        if not sk["arme"] or dist(*sk["arme"]) < 10:
            return
        self.dessiner_seg(cr, sk["arme"], alpha)

    def dessiner_seg(self, cr, seg, alpha=1.0):
        b, t = seg
        v = unit(sub(t, b))
        n = (-v[1], v[0])
        g = add(b, v, 36)
        trait(cr, b, g, 8, (.06, .06, .07, alpha))
        cr.set_source_rgba(.06, .06, .07, alpha)
        cr.arc(*b, 7, 0, 2 * math.pi)
        cr.fill()
        trait(cr, add(g, n, -20), add(g, n, 20), 7, (.06, .06, .07, alpha))
        _lame(cr, add(g, v, 3), t, v, n, 6, (.46, .49, .54), (.08, .08, .1), alpha)
        trait(cr, add(g, v, 8), add(t, v, -30), 1.3, (.8, .82, .86, .7 * alpha))
