# rendu-2d — moteur d'animation 2D vectorielle (stickman) + ferme de rendu

Moteur de dessin vectoriel (cairo) qui produit des vidéos 1080×1920 à 60 i/s,
et un découpage du rendu en segments indépendants rendus **en parallèle** sur
GitHub Actions (20 machines), recollés sans réencodage.

## Ce que fait ce dépôt

- `combat/` — le moteur : squelette et poses (`corps3`, `poses4/5`), rendu en
  profondeur pièce par pièce (`prof10`), outils de chorégraphie avec solveur de
  contact (`combat10`), armes (`arme4`, `armes5/6/7/9`), effets (`effets3/10`),
  moteurs de rendu successifs (`moteur6` → `moteur14`), synthèse audio (`audio13`).
- `outils/` — segmentation du rendu, rendu parallèle, mesure de la grille de beats,
  planche de contact, contrôles géométriques, chronométrage.
- `.github/workflows/rendu.yml` — la ferme de rendu.

## Lancer

```bash
pip install -r requirements.txt     # pycairo numpy scipy soundfile
sudo apt-get install libcairo2-dev ffmpeg fonts-inter fonts-dejavu-core
```

Contrôles géométriques (avant tout rendu) :

```bash
python3 outils/controles.py <dump>.json
```

Rendu local, N cœurs :

```bash
python3 outils/rendu_parallele.py videos/<nom>.py out/<nom>.mp4 --n 8
```

Rendu sur la ferme : onglet **Actions** → *rendu* → *Run workflow*.
Le résultat est un artifact `video-finale` : un mp4 **muet**.

## Pas d'audio dans ce dépôt

Aucun fichier audio n'est publié ici, et aucun n'est envoyé à la ferme : les droits
des musiques de référence ne sont pas établis. La ferme rend donc du **muet**, et la
piste son est ajoutée en local, en une commande :

```bash
ffmpeg -y -i rendu_muet.mp4 -i musique.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

`assets/` est vide (et les `*.wav` / `*.mp3` sont ignorés par git) : les fichiers
audio restent locaux. `audio13.musique()` et `base12` attendent un
`musique_22.wav` local ; ils ne sont pas appelés pendant un rendu muet.

## Les chorégraphies ne sont pas publiées

`videos/` est ignoré par git. Le moteur est public, les chorégraphies (la liste des
attaques, le découpage, le timing — le vrai travail) ne le sont pas. Pour faire rendre
une vidéo par la ferme, on ajoute **ce seul fichier**, volontairement :

```bash
git add -f videos/<nom>.py && git commit -m "rendu <nom>" && git push
```

## Un fichier de vidéo doit exposer

```python
DUREE, FPS, MUSIQUE = 21.9, 60, None
def rendre_segment(f0, f1, sortie):   # frames [f0, f1[, sans audio
    ...
```

`prof10.rendre10(...)` accepte déjà `morceau=(f0, f1)` ; les moteurs `moteur12` à
`moteur14` doivent recevoir le même paramètre (6 lignes, voir `outils/segments.py`).

## Licences

- Code : écrit pour ce projet.
- Polices : le moteur appelle les familles système **Inter** et **DejaVu Sans**
  (paquets `fonts-inter`, `fonts-dejavu-core`) ; aucun fichier de police n'est publié ici.
- Aucun asset tiers n'est inclus.
