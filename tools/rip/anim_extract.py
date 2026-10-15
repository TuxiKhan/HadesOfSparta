#!/usr/bin/env python3
"""Consecutive GE dumps (capture_anim.py) -> one posed, textured Kratos mesh per frame.

    python tools/rip/anim_extract.py <capture_dir> <out_dir> [--first N --last M]
        [--min-verts 4500 --max-verts 9000]

For each fNNNN.ppdmp the hero cluster is picked automatically: a skinned cluster whose vertex
count is in [min,max], nearest to the previous frame's pick (first frame: the largest such).
Writes <out_dir>/fNNNN/{kratos_textured.obj,kratos.gltf,textures/} and <out_dir>/frames.json
(cluster, verts, centroid, bbox per frame). --extra-tex adds rigid draws by texture id (default
2c5f86 = the Blades' additive fire trail, which is how GoS PSP draws the thrown blades' link —
no separate chain mesh exists in the GE stream). Outputs contain game data -> keep outside repo.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gedump import draws, clusters  # noqa: E402
from ge_textured import run  # noqa: E402


def pick_cluster(dump: str, prev, lo: int, hi: int):
    posed = [d for d in draws(dump, "posed") if d['skinned']]
    best = None
    for k, idx in enumerate(clusters(posed)):
        V = [v for i in idx for v in posed[i]['verts']]
        if not (lo <= len(V) <= hi):
            continue
        c = tuple(sum(v[a] for v in V) / len(V) for a in range(3))
        bb = [(min(v[a] for v in V), max(v[a] for v in V)) for a in range(3)]
        score = len(V) if prev is None else -sum((c[a] - prev[a]) ** 2 for a in range(3))
        if best is None or score > best[0]:
            best = (score, k, len(V), c, bb)
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("capture"); ap.add_argument("out")
    ap.add_argument("--first", type=int, default=0); ap.add_argument("--last", type=int, default=10**6)
    ap.add_argument("--min-verts", type=int, default=4500); ap.add_argument("--max-verts", type=int, default=9000)
    ap.add_argument("--extra-tex", default="2c5f86",
                    help="comma list of rigid-draw texture ids to keep (default: Blades fire trail)")
    a = ap.parse_args()
    cap, out = Path(a.capture), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frames, prev = [], None
    for p in sorted(cap.glob("f*.ppdmp")):
        i = int(p.stem[1:])
        if not (a.first <= i <= a.last):
            continue
        best = pick_cluster(str(p), prev, a.min_verts, a.max_verts)
        if best is None:
            print(f"{p.name}: no hero cluster"); continue
        _, k, nv, c, bb = best
        prev = c
        with contextlib.redirect_stdout(io.StringIO()):
            run(str(p), str(out / p.stem), "posed", k, tuple(filter(None, a.extra_tex.split(","))))
        frames.append({"frame": i, "cluster": k, "verts": nv, "centroid": c, "bbox": bb})
        print(f"{p.name}: cluster {k} verts {nv} size " +
              "x".join(f"{hi_ - lo_:.1f}" for lo_, hi_ in bb), flush=True)
    (out / "frames.json").write_text(json.dumps(frames, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
