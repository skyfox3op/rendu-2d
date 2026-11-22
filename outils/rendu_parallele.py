"""Rendu local multi-processus : N segments, N coeurs, recollage, audio.

    python3 outils/rendu_parallele.py videos/dague.py out/dague_v11.mp4 --n 8

Le fichier video doit exposer :
    DUREE, FPS, MUSIQUE  et  rendre_segment(f0, f1, sortie)
"""
import argparse
import importlib.util
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in (_RACINE, os.path.join(_RACINE, "combat"), os.path.join(_RACINE, "videos")):
    if _d not in sys.path:
        sys.path.insert(0, _d)
from outils import segments as S  # noqa: E402

_MOD = None


def _charger(chemin):
    global _MOD
    if _MOD is None:
        spec = importlib.util.spec_from_file_location("video", chemin)
        _MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MOD)
    return _MOD


def _job(args):
    chemin, i, f0, f1, tmp = args
    m = _charger(chemin)
    t0 = time.time()
    sortie = f"{tmp}/seg{i:03d}.mp4"
    m.rendre_segment(f0, f1, sortie)
    return i, sortie, f1 - f0, time.time() - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("sortie")
    p.add_argument("--n", type=int, default=os.cpu_count())
    p.add_argument("--muet", action="store_true")
    p.add_argument("--segment", type=int, default=None,
                   help="ne rendre QUE ce segment (ferme de rendu) -> _segments/segNNN.mp4")
    a = p.parse_args()

    m = _charger(a.video)
    fps = getattr(m, "FPS", 60)
    n_frames = int(round(m.DUREE * fps))
    tmp = "_segments"
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(os.path.dirname(a.sortie) or ".", exist_ok=True)

    plan = S.plan_segments(n_frames, a.n, fps)
    if a.segment is not None:                      # un seul segment : mode ferme de rendu
        i, f0, f1 = plan[a.segment]
        _, sortie, nf, dt = _job((a.video, i, f0, f1, tmp))
        print(f"seg {i:03d}: frames {f0}-{f1} en {dt:.1f}s "
              f"({dt / max(1, nf) * 1000:.0f} ms/frame) -> {sortie}")
        return
    print(f"{n_frames} frames · {len(plan)} segments · {a.n} processus")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.n) as ex:
        res = sorted(ex.map(_job, [(a.video, i, f0, f1, tmp) for i, f0, f1 in plan]))
    t_dessin = time.time() - t0
    for i, _, nf, dt in res:
        print(f"  seg {i:03d}: {nf} frames en {dt:5.1f}s ({dt / max(1, nf) * 1000:4.0f} ms/frame)")

    t1 = time.time()
    muet = S.recoller([s for _, s, _, _ in res], f"{tmp}/muet.mp4")
    if a.muet:
        os.replace(muet, a.sortie)
    else:
        S.finaliser(muet, getattr(m, "MUSIQUE"), a.sortie, n_frames / fps)
    print(f"dessin {t_dessin:.0f}s · montage {time.time() - t1:.0f}s · "
          f"TOTAL {time.time() - t0:.0f}s -> {a.sortie}")


if __name__ == "__main__":
    main()
