# Phase 3 prep — GE rip register fix + Pack repack fix · 2026-10-15

> Tracked. No game data; outputs live on the user's machine (`C:\mods\model\_GPU_RIP_v2\`).

## 1. GE rip (tools/rip) — wrong registers → skinning never applied

Checked against PPSSPP `GPU/ge_constants.h` (master):

| Old script read | Is actually | Correct |
|---|---|---|
| `0x3C/0x3D` as world matrix | VIEWMATRIX | WORLDMATRIX `0x3A/0x3B` |
| `0x42/0x43` as bone matrices | VIEWPORT X/Y scale | BONEMATRIX `0x2A/0x2B` |
| `0xC9` as CLUT format | TEXFUNC | CLUTFORMAT `0xC5` |
| — (missing) | TEXSCALE/OFFSET U,V `0x48–0x4B` | now applied |

Evidence in `frame_kratos_scene.ppdmp`: `0x2B` appears 32 604×, `0x42/0x43` 3× each → the bone
palette was never loaded, so "posed" output was really bind-space vertices. This also explains
the old log's "3 different poses gave byte-identical vertices".

Second problem: the Tukey centroid filter keeps several characters at once. Spatial clustering
(`gedump.clusters`) separates them: cluster 0 = a large spiked creature (this was the old
"Kratos"), **cluster 1 = Kratos** (649 draws / 5806 verts / 7 textures; bald, bearded, Blades
on back; front *and* back present), cluster 6 = low-poly Kratos copy (shadow/LOD).

Result: `--pose bind` → clean **T-pose Kratos**; `--pose posed` → full posed body. The earlier
conclusion "a single frame captures only the camera-facing shell; multi-angle capture needed"
was a symptom of this bug and is withdrawn.

Code: `tools/rip/gedump.py` (shared decoder: records, vertex layout, world·Σw·bone, UV
scale/offset, index buffers, clusters), `ge_mesh.py`/`ge_textured.py` rebuilt on it.

## 2. radpack.py resize-repack

Measured on all 10 `*KRATOS*.BIN`: header `0x28` = end of the last blob rounded up to 16, and a
trailer (116–1828 B) follows. Old non-exact repack wrote the file size into `0x28` and dropped
the trailer. Fixed: manifest stores `trailer_hex`; repack re-aligns, sets `0x28`, appends the
trailer. Unmodified extract → resize-repack now matches the original's length, `0x28` and
trailer on all 10 packs (only the original's junk padding bytes differ). Exact `roundtrip`
still SHA-256 identical.

## Honesty note
Found and fixed with AI (Claude Code); verified by renders of the re-ripped mesh and byte
comparisons on the user's own dump.
