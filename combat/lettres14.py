"""v14 — les LETTRES du titre « my weapon type: » comme armes : métriques, emplacements, dessin de glyphes."""
import math

import cairo

from corps3 import add, dist, lerp_pt, sub, unit

W, BANDE = 1080, 560
TXT, EM, YB = "my weapon type:", 84, 400
_s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8)
_c = cairo.Context(_s)
_M = {}


def _font(cr, em):
    cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(em)


def met(ch):
    if ch not in _M:
        _font(_c, 100)
        e = _c.text_extents(ch)
        _M[ch] = (e.x_bearing, e.y_bearing, e.width, e.height, e.x_advance)
    return _M[ch]


def slots():
    _font(_c, EM)
    e = _c.text_extents(TXT)
    x0 = W / 2 - e.width / 2 - e.x_bearing
    out = []
    for i, ch in enumerate(TXT):
        adv = _c.text_extents(TXT[:i] + "|").x_advance - _c.text_extents("|").x_advance
        xb, yb, w, h, a = [v * EM / 100 for v in met(ch)]
        if ch == " ":
            out.append(dict(ch=ch, x=x0 + adv, cx=x0 + adv + a / 2, cy=YB - 24, h=40, w=a, adv=a))
        else:
            out.append(dict(ch=ch, x=x0 + adv, cx=x0 + adv + xb + w / 2, cy=YB + yb + h / 2, h=h, w=w, adv=a))
    return out


def glyphe_c(cr, ch, c, haut, ang, coul, alpha=1.0):
    xb, yb, w, h, _ = met(ch)
    s = haut / h
    cr.save()
    cr.translate(*c)
    cr.rotate(ang)
    cr.scale(s, s)
    cr.translate(-(xb + w / 2), -(yb + h / 2))
    _font(cr, 100)
    cr.move_to(0, 0)
    cr.text_path(ch)
    cr.set_source_rgba(*coul, alpha)
    cr.fill()
    cr.restore()


def glyphe_seg(cr, ch, A, B, la, lb, miroir, coul, alpha=1.0):
    xb, yb, w, h, _ = met(ch)
    pa = (xb + la[0] * w, yb + la[1] * h)
    pb = (xb + lb[0] * w, yb + lb[1] * h)
    vl, vw = sub(pb, pa), sub(B, A)
    s = math.hypot(*vw) / math.hypot(*vl)
    cr.save()
    cr.translate(*A)
    cr.rotate(math.atan2(vw[1], vw[0]))
    if miroir:
        cr.scale(1, -1)
    cr.rotate(-math.atan2(vl[1], vl[0]))
    cr.scale(s, s)
    cr.translate(-pa[0], -pa[1])
    _font(cr, 100)
    cr.move_to(0, 0)
    cr.text_path(ch)
    cr.set_source_rgba(*coul, alpha)
    cr.fill()
    cr.restore()


# lettres tenues : L = longueur en main, g = position de la main, la/lb = points du glyphe (fraction de la boîte)
LET = {"t": dict(L=175, g=.14, la=(.45, 0), lb=(.45, 1)),      # épée : main en haut du t, barre = garde, pied = pointe
       "p": dict(L=205, g=.06, la=(.14, 1), lb=(.14, 0)),      # marteau : main en bas de la hampe, panse = tête
       "y": dict(L=185, g=.10, la=(.30, 1), lb=(.5, 0))}       # lance-pierre : main sur la queue, fourche en haut
R_O = 65


def seg_main(sk, ch, k=1.0):
    cfg = LET[ch]
    a0, a1 = sk["arme"]
    v = unit(sub(a1, a0))
    m = sk["main1"]
    L = cfg["L"] * k
    return add(m, v, -L * cfg["g"]), add(m, v, L * (1 - cfg["g"]))


def _n(sk, A, B):
    v = unit(sub(B, A))
    return v, (-v[1] * sk["d"], v[0] * sk["d"])


def tete_p(sk, k=1.0):
    A, B = seg_main(sk, "p", k)
    v, n = _n(sk, A, B)
    L = dist(A, B)
    return add(add(A, v, .64 * L), n, .36 * L)


def centre_main(sk, ch, k=1.0):
    if ch == "o":
        return add(sk["main1"], (sk["d"] * 8 * k, 0))
    A, B = seg_main(sk, ch, k)
    if ch == "p":
        v, n = _n(sk, A, B)
        return add(lerp_pt(A, B, .5), n, .28 * dist(A, B))
    return lerp_pt(A, B, .5)


def dessine_main(cr, sk, ch, k, coul):
    if ch == "o":
        glyphe_c(cr, "o", centre_main(sk, "o", k), 2 * R_O * k, 0, coul)
        return
    A, B = seg_main(sk, ch, k)
    glyphe_seg(cr, ch, A, B, LET[ch]["la"], LET[ch]["lb"], sk["d"] < 0, coul)
