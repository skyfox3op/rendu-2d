"""Poses v5 : héros à l'épée fine (HF), héros à la faux (HX), adversaire à mains nues (A)."""
from poses4 import A as A4, AB

BASE_H = dict(x=300, air=0, t=10, h=-6, b1=50, a1=100, b2=40, a2=120, c1=34, j1=-2, c2=-28, j2=-40,
              w=110, g=.1, rot=0, z=0, d=1, deux=False, tient=True)
HFB = dict(BASE_H, g=.1, deux=False)
HXB = dict(BASE_H, g=.58, deux=True, w=150)
DEPART = dict(t=40, h=-26, c1=96, j1=-30, c2=-62, j2=-74, b2=64, a2=30)
CORPS = {   # poses de corps communes (les armes ajoutent w/g)
    "garde": dict(t=8, h=-6, b1=70, a1=110, b2=-36, a2=-110, c1=40, j1=-6, c2=-34, j2=-46),
    "depart": dict(DEPART, b1=-120, a1=-150),
    "fente": dict(t=30, h=-14, b1=92, a1=92, b2=-60, a2=-100, c1=92, j1=10, c2=-62, j2=-72),
    "moulinet": dict(t=6, h=-6, b1=78, a1=100, b2=-36, a2=-110, c1=36, j1=-4, c2=-30, j2=-42),
    "glisse": dict(rot=-40, t=-20, h=-10, b1=150, a1=172, b2=-60, a2=-20, c1=96, j1=96, c2=20, j2=-60),
    "taille_montante": dict(t=-14, h=-16, b1=170, a1=184, b2=-50, a2=-40, c1=60, j1=-30, c2=-40, j2=-70),
    "salto": dict(t=30, h=10, b1=120, a1=150, b2=100, a2=130, c1=110, j1=20, c2=95, j2=-5),
    "reception": dict(t=42, h=-14, b1=-40, a1=-60, b2=62, a2=30, c1=102, j1=-24, c2=-10, j2=-88),
    "traversee": dict(t=36, h=-12, b1=100, a1=96, b2=-70, a2=-60, c1=98, j1=-20, c2=-52, j2=-88),
    "parade": dict(t=6, h=-10, b1=58, a1=150, b2=-36, a2=-100, c1=40, j1=-10, c2=-34, j2=-50),
    "recul": dict(t=-14, h=-8, b1=60, a1=130, b2=-30, a2=-90, c1=10, j1=-10, c2=-40, j2=-50),
    "saut": dict(t=8, h=-10, b1=150, a1=172, b2=100, a2=140, c1=110, j1=20, c2=95, j2=-5),
    "pique": dict(t=62, h=-24, b1=104, a1=100, b2=-70, a2=-60, c1=-10, j1=-40, c2=-46, j2=-80),
    "coup_pied": dict(t=-22, h=-8, b1=40, a1=90, b2=-40, a2=-80, c1=100, j1=100, c2=-20, j2=-30),
    "chiburi": dict(t=12, h=-4, b1=40, a1=12, b2=-20, a2=-10, c1=30, j1=-2, c2=-28, j2=-36),
    "dos": dict(t=4, h=-4, b1=-20, a1=-50, b2=-16, a2=-6, c1=20, j1=4, c2=-20, j2=-14),
    "marche1": dict(t=10, h=2, b1=60, a1=100, b2=24, a2=40, c1=30, j1=-2, c2=-24, j2=-40),
    "marche2": dict(t=10, h=2, b1=50, a1=96, b2=-20, a2=-5, c1=-24, j1=-40, c2=30, j2=-2),
    # faux
    "garde_x": dict(t=10, h=-6, b1=40, a1=80, c1=40, j1=-6, c2=-34, j2=-46),
    "arme_x": dict(t=-14, h=-8, b1=-30, a1=-50, c1=34, j1=-6, c2=-40, j2=-50),
    "fauche": dict(t=30, h=-10, b1=100, a1=96, c1=86, j1=8, c2=-56, j2=-66),
    "parade_x": dict(t=-6, h=-10, b1=150, a1=172, c1=44, j1=-16, c2=-36, j2=-56),
    "talon_x": dict(t=22, h=-8, b1=80, a1=90, c1=60, j1=0, c2=-44, j2=-60),
    "crochet": dict(t=40, h=-14, b1=96, a1=92, c1=92, j1=6, c2=-60, j2=-70),
    "tirer": dict(t=-24, h=-10, b1=30, a1=60, c1=20, j1=-20, c2=-50, j2=-40),
    "tour_x": dict(t=16, h=-8, b1=92, a1=92, c1=50, j1=-8, c2=-40, j2=-56),
    "souleve": dict(t=-12, h=-14, b1=170, a1=180, c1=40, j1=-10, c2=-36, j2=-50),
    "recolte": dict(t=52, h=-10, b1=110, a1=100, c1=100, j1=-20, c2=-40, j2=-88),
    "epaule": dict(t=4, h=-6, b1=160, a1=30, b2=-16, a2=-6, c1=22, j1=6, c2=-22, j2=-12),
}
A = dict(A4)
A.update({
    "genoux": dict(t=30, h=10, b1=20, a1=10, b2=-10, a2=0, c1=40, j1=-90, c2=0, j2=-92),
    "chute_avant": dict(t=64, h=30, b1=40, a1=30, b2=30, a2=20, c1=40, j1=-80, c2=10, j2=-80),
    "face": dict(rot=90, t=0, h=10, b1=170, a1=176, b2=150, a2=170, c1=4, j1=2, c2=-6, j2=-8),
    "regard_haut": dict(t=-20, h=-40, b1=60, a1=130, b2=40, a2=120, c1=34, j1=-6, c2=-30, j2=-40),
    "recule_pas": dict(t=-6, h=-4, b1=60, a1=135, b2=40, a2=125, c1=10, j1=-8, c2=-40, j2=-50),
    "saut_pied": dict(t=-20, h=-10, b1=120, a1=150, b2=-60, a2=-30, c1=95, j1=95, c2=40, j2=-40),
    "sprint1": dict(t=34, h=-14, b1=-50, a1=-10, b2=60, a2=100, c1=70, j1=10, c2=-60, j2=-20),
    "sprint2": dict(t=34, h=-14, b1=60, a1=100, b2=-50, a2=-10, c1=-60, j1=-20, c2=70, j2=10),
    "salto_arr": dict(t=30, h=10, b1=120, a1=150, b2=100, a2=130, c1=110, j1=20, c2=95, j2=-5),
})
