#!/usr/bin/env python3
"""PPSSPP GE frame dump -> OBJ (untextured). Splits skinned (character) draws from rigid ones.

    python ge_mesh.py <dump.ppdmp> <outdir> [--pose posed|bind]

posed (default): hardware transform (bones + world) -> world-space pose of that frame.
bind: raw vertex positions (no bones/world) -> model/bind space, for rigging.
Writes kratos_skinned_all.obj, kratos_body.obj (Tukey-filtered main cluster), rigid_world.obj.
"""
import argparse, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gedump import draws, body_filter  # noqa: E402


def bbox(V):
    if not V: return None
    return tuple(round(f(v[i] for v in V), 1) for i in range(3) for f in (min, max))


def write_obj(path, ds):
    V = []
    with open(path, 'w') as fh:
        for d in ds:
            b0 = len(V); V.extend(d['verts'])
            for v in d['verts']: fh.write("v %.5f %.5f %.5f\n" % v)
            for a, b, c in d['faces']: fh.write("f %d %d %d\n" % (b0 + a + 1, b0 + b + 1, b0 + c + 1))
    return len(V), sum(len(d['faces']) for d in ds), bbox(V)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump"); ap.add_argument("outdir")
    ap.add_argument("--pose", choices=("posed", "bind"), default="posed")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    ds = list(draws(a.dump, a.pose))
    skin = [d for d in ds if d['skinned']]; rigid = [d for d in ds if not d['skinned']]
    body = body_filter(skin)
    sa = write_obj(os.path.join(a.outdir, 'kratos_skinned_all.obj'), skin)
    sb = write_obj(os.path.join(a.outdir, 'kratos_body.obj'), body)
    write_obj(os.path.join(a.outdir, 'rigid_world.obj'), rigid)
    print(f"[{a.pose}] SKINNED all : {len(skin)} draws -> {sa[0]} verts {sa[1]} tris bbox={sa[2]}")
    print(f"[{a.pose}] KRATOS body : {len(body)} draws -> {sb[0]} verts {sb[1]} tris bbox={sb[2]}")
    print(f"[{a.pose}] RIGID       : {len(rigid)} draws")


if __name__ == '__main__':
    main()
