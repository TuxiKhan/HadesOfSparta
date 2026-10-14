"""Shared decoder for PPSSPP GE frame dumps (.ppdmp) — used by ge_mesh.py / ge_textured.py.

Dump container (v6): "PPSSPPGE" | u32 ver | gid | ... | 0x18 u32 cmdCount | 0x1C u32 pushbufSize
| 0x20 u32 cmdCompressedSize | 0x24 zstd(commands) | zstd(pushbuf).
command record = {u8 type; u32 sz; u32 ptr->pushbuf}; types: 1 REGISTERS (GE words),
2 VERTICES, 3 INDICES, 4 CLUT, 0x10 TEXTURE (others ignored here).

GE command IDs follow PPSSPP GPU/ge_constants.h:
  0x12 VERTEXTYPE · 0x04 PRIM · 0x2A/0x2B BONEMATRIX number/data · 0x3A/0x3B WORLDMATRIX
  0x48-0x4B TEXSCALE U/V, TEXOFFSET U/V (uv' = uv*scale + offset)
  0xB8 TEXSIZE0 · 0xC2 TEXMODE (bit0 swizzle) · 0xC3 TEXFORMAT · 0xC5 CLUTFORMAT
(Earlier versions of these scripts read 0x42/0x43 — VIEWPORT scale — as bones and 0x3C/0x3D —
VIEW matrix — as world, so skinning was never applied. Fixed 2026-10-15.)

Vertex transform (hardware order): skinned  p = World · Σ wᵢ·Boneᵢ·v
                                    rigid    p = World · v
pose="bind" skips bones and world -> model/bind-space vertices (what a rig wants).
Stdlib only (Python 3.14 `compression.zstd`).
"""
import struct
from compression import zstd

T_REGISTERS, T_VERTICES, T_INDICES, T_CLUT, T_TEXTURE = 1, 2, 3, 4, 0x10
CSZ = {0: 0, 1: 1, 2: 2, 3: 4}
IDENT = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]


def load(path):
    d = open(path, 'rb').read()
    if d[:8] != b'PPSSPPGE':
        raise ValueError(f"{path}: not a PPSSPP GE dump")
    cc = struct.unpack_from('<I', d, 0x18)[0]
    csz = struct.unpack_from('<I', d, 0x20)[0]
    commands = zstd.ZstdDecompressor().decompress(d[0x24:0x24 + csz])
    zoff = d.find(b'\x28\xb5\x2f\xfd', 0x24 + csz)
    pushbuf = zstd.ZstdDecompressor().decompress(d[zoff:])
    return commands, pushbuf, cc


def records(commands, count):
    for i in range(count):
        o = i * 9
        t = commands[o]
        sz, ptr = struct.unpack_from('<II', commands, o + 1)
        yield t, sz, ptr


def vfmt(vt):
    """Vertex layout from VERTEXTYPE (weights, uv, color, normal, position; each aligned to its size)."""
    tc = vt & 3; col = (vt >> 2) & 7; nrm = (vt >> 5) & 3; pos = (vt >> 7) & 3
    wfmt = (vt >> 9) & 3; idx = (vt >> 11) & 3
    wcnt = ((vt >> 14) & 7) + 1 if wfmt else 0
    morph = ((vt >> 18) & 7) + 1
    through = (vt >> 23) & 1
    csz = {4: 2, 5: 2, 6: 2, 7: 4}.get(col, 0)
    off = 0; align = 1

    def place(sz, cnt):
        nonlocal off, align
        if sz == 0:
            return None
        off = (off + sz - 1) // sz * sz
        o = off; off += sz * cnt; align = max(align, sz)
        return o
    woff = place(CSZ[wfmt], wcnt); toff = place(CSZ[tc], 2); place(csz, 1)
    place(CSZ[nrm], 3); poff = place(CSZ[pos], 3)
    off = (off + align - 1) // align * align
    return dict(stride=off * morph, pos=pos, poff=poff, tc=tc, toff=toff, wfmt=wfmt, wcnt=wcnt,
                woff=woff, idx=idx, through=through, morph=morph)


def f24(d):  # GE matrix/float payload = top 24 bits of a float32
    return struct.unpack('<f', struct.pack('<I', (d & 0xffffff) << 8))[0]


def xform(m, x, y, z):  # 4x3 column-major (PSP): c0=m[0:3] c1=m[3:6] c2=m[6:9] t=m[9:12]
    return (m[0] * x + m[3] * y + m[6] * z + m[9],
            m[1] * x + m[4] * y + m[7] * z + m[10],
            m[2] * x + m[5] * y + m[8] * z + m[11])


def dpos(pb, b, f):
    if f == 3: return struct.unpack_from('<fff', pb, b)
    if f == 2: x, y, z = struct.unpack_from('<hhh', pb, b); return x / 32768, y / 32768, z / 32768
    if f == 1: x, y, z = struct.unpack_from('<bbb', pb, b); return x / 128, y / 128, z / 128
    return 0., 0., 0.


def duv(pb, b, f):
    if f == 3: return struct.unpack_from('<ff', pb, b)
    if f == 2: u, v = struct.unpack_from('<HH', pb, b); return u / 32768, v / 32768
    if f == 1: u, v = struct.unpack_from('<BB', pb, b); return u / 128, v / 128
    return 0., 0.


def dweights(pb, b, wf, wc):
    if wf == 3: return list(struct.unpack_from(f'<{wc}f', pb, b))
    if wf == 2: return [w / 32768 for w in struct.unpack_from(f'<{wc}H', pb, b)]
    if wf == 1: return [pb[b + i] / 128 for i in range(wc)]
    return []


def faces_for(pt, n):
    if pt == 3: return [(i, i + 1, i + 2) for i in range(0, n - n % 3, 3)]
    if pt == 4: return [(s, s + 1, s + 2) if s % 2 == 0 else (s + 1, s, s + 2) for s in range(n - 2)]
    if pt == 5: return [(0, s, s + 1) for s in range(1, n - 1)]
    return []


def draws(path, pose="posed"):
    """Yield one dict per triangle draw: skinned, verts, uvs, faces, tex (state tuple or None)."""
    commands, pb, nc = load(path)
    world = IDENT[:]; bones = [IDENT[:] for _ in range(8)]
    wptr = bptr = vtype = 0
    texfmt = texw = texh = swz = 0; cfmt = 3
    uvs_ = [1.0, 1.0, 0.0, 0.0]  # scaleU, scaleV, offU, offV
    last_v = last_i = last_t = last_tsz = last_c = last_csz = 0
    for t, sz, ptr in records(commands, nc):
        if t == T_VERTICES: last_v = ptr
        elif t == T_INDICES: last_i = ptr
        elif t == T_TEXTURE: last_t, last_tsz = ptr, sz
        elif t == T_CLUT: last_c, last_csz = ptr, sz
        elif t != T_REGISTERS: continue
        else:
            for k in range(sz // 4):
                w = struct.unpack_from('<I', pb, ptr + k * 4)[0]; c = w >> 24; d = w & 0xffffff
                if c == 0x12: vtype = d
                elif c == 0x3A: wptr = d
                elif c == 0x3B:
                    if wptr < 12: world[wptr] = f24(d)
                    wptr += 1
                elif c == 0x2A: bptr = d
                elif c == 0x2B:
                    if bptr < 96: bones[bptr // 12][bptr % 12] = f24(d)
                    bptr += 1
                elif 0x48 <= c <= 0x4B: uvs_[c - 0x48] = f24(d)
                elif c == 0xC3: texfmt = d & 0xf
                elif c == 0xB8: texw = d & 0xff; texh = (d >> 8) & 0xff
                elif c == 0xC2: swz = d & 1
                elif c == 0xC5: cfmt = d & 3
                elif c == 0x04:
                    n = w & 0xffff; pt = (w >> 16) & 7
                    if pt not in (3, 4, 5) or n < 3: continue
                    f = vfmt(vtype)
                    if f['through'] or f['poff'] is None or f['stride'] == 0: continue
                    st = f['stride']
                    if f['idx']:
                        isz = {1: 1, 2: 2, 3: 4}[f['idx']]
                        if last_i + isz * n > len(pb): continue
                        order = ([pb[last_i + j] for j in range(n)] if isz == 1 else
                                 [struct.unpack_from('<H', pb, last_i + j * isz)[0] for j in range(n)])
                    else:
                        order = list(range(n))
                    nv = max(order) + 1
                    if last_v + st * nv > len(pb): continue
                    V = []; UV = []
                    for vi in range(nv):
                        bb = last_v + vi * st
                        x, y, z = dpos(pb, bb + f['poff'], f['pos'])
                        if pose == "posed":
                            if f['wcnt']:
                                ws = dweights(pb, bb + f['woff'], f['wfmt'], f['wcnt'])
                                px = py = pz = 0.
                                for bi, wv in enumerate(ws):
                                    if wv:
                                        tx, ty, tz = xform(bones[bi], x, y, z)
                                        px += wv * tx; py += wv * ty; pz += wv * tz
                                x, y, z = px, py, pz
                            x, y, z = xform(world, x, y, z)
                        V.append((x, y, z))
                        if f['toff'] is not None:
                            u, v = duv(pb, bb + f['toff'], f['tc'])
                            UV.append((u * uvs_[0] + uvs_[2], v * uvs_[1] + uvs_[3]))
                        else:
                            UV.append((0., 0.))
                    if not all(abs(q) < 1e6 for v in V for q in v): continue
                    fl = faces_for(pt, n)
                    fl = [(order[a], order[b], order[c2]) for a, b, c2 in fl]
                    tex = None
                    if texw <= 11 and texh <= 11 and last_tsz:
                        tex = (last_t, last_tsz, 1 << texw, 1 << texh, texfmt, swz,
                               last_c if last_csz else 0, last_csz, cfmt)
                    yield dict(skinned=f['wcnt'] > 0, verts=V, uvs=UV, faces=fl, tex=tex, pb=pb)


def centroid(d):
    V = d['verts']
    return tuple(sum(v[i] for v in V) / len(V) for i in range(3))


def clusters(ds, radius=4.0):
    """Group draws whose centroids chain within `radius` (posed space). Returns lists of draw
    indices, largest first. Separate characters in one frame land in separate clusters —
    pick the hero by size/visual check (see ge_textured.py --list)."""
    cs = [centroid(d) for d in ds]
    par = list(range(len(ds)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    grid = {}
    for i, c in enumerate(cs):
        grid.setdefault(tuple(int(x // radius) for x in c), []).append(i)
    r2 = radius * radius
    for k, ids in grid.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        for i in ids:
                            if i < j and sum((a - b) ** 2 for a, b in zip(cs[i], cs[j])) < r2:
                                par[find(i)] = find(j)
    groups = {}
    for i in range(len(ds)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def describe(ds, idx):
    V = [v for i in idx for v in ds[i]['verts']]
    bb = [(min(v[a] for v in V), max(v[a] for v in V)) for a in range(3)]
    ntex = len({ds[i]['tex'][0] for i in idx if ds[i]['tex']})
    return f"{len(idx)} draws, {len(V)} verts, {ntex} textures, size " + \
        "x".join(f"{hi - lo:.1f}" for lo, hi in bb)


def body_filter(ds):
    """Tukey fence on draw centroids -> main cluster. Kept for ge_mesh.py's quick overview;
    it cannot separate two characters in one frame — prefer clusters()."""
    if not ds: return []
    cs = [tuple(sum(v[i] for v in d['verts']) / len(d['verts']) for i in range(3)) for d in ds]

    def fence(a):
        s = sorted(a); n = len(s); q1 = s[n // 4]; q3 = s[3 * n // 4]; r = q3 - q1
        return q1 - 1.5 * r, q3 + 1.5 * r
    fs = [fence([c[i] for c in cs]) for i in range(3)]
    return [d for d, c in zip(ds, cs) if all(fs[i][0] <= c[i] <= fs[i][1] for i in range(3))]
