"""Instrumentation : ou part le temps. Sans mesure, aucune optimisation n'est permise.

    from outils.chrono import Chrono
    C = Chrono()
    with C("dessin corps"): ...
    with C("couches flou/lueur"): ...
    C.rapport(n_frames)        # imprime la repartition et l'ecrit dans REGISTRE/TEMPS.csv
"""
import csv
import os
import time
from collections import defaultdict
from contextlib import contextmanager

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "REGISTRE", "TEMPS.csv")


class Chrono:
    def __init__(self, video="?"):
        self.video = video
        self.t = defaultdict(float)
        self.t0 = time.time()

    @contextmanager
    def __call__(self, nom):
        d = time.time()
        try:
            yield
        finally:
            self.t[nom] += time.time() - d

    def rapport(self, n_frames, ecrire=True):
        tot = time.time() - self.t0
        print(f"\n{n_frames} frames en {tot:.1f}s "
              f"({tot / max(1, n_frames) * 1000:.0f} ms/frame)")
        for nom, v in sorted(self.t.items(), key=lambda x: -x[1]):
            print(f"  {v / tot * 100:5.1f}%  {v:7.1f}s  {nom}")
        reste = tot - sum(self.t.values())
        print(f"  {reste / tot * 100:5.1f}%  {reste:7.1f}s  (non mesure)")
        if ecrire:
            os.makedirs(os.path.dirname(CSV), exist_ok=True)
            neuf = not os.path.exists(CSV)
            with open(CSV, "a", newline="") as f:
                w = csv.writer(f)
                if neuf:
                    w.writerow(["date", "video", "frames", "total_s", "ms_par_frame", "postes"])
                w.writerow([time.strftime("%Y-%m-%d %H:%M"), self.video, n_frames,
                            f"{tot:.1f}", f"{tot / max(1, n_frames) * 1000:.0f}",
                            " | ".join(f"{k}={v:.0f}s" for k, v in
                                       sorted(self.t.items(), key=lambda x: -x[1]))])
        return tot
