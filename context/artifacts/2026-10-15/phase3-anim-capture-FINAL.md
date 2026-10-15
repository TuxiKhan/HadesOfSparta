# Phase 3 — Blades animation capture (FINAL) · 2026-10-15

> Phase 4 (Blades) approved by the user 2026-10-15 ("iyi … onayla"). User asked to *see* the
> Blades with their animation and chain physics → this Phase 3 step. No game data in the repo;
> outputs live in `C:\mods\model\_ANIM\` on the user's machine.

## Method — animation = consecutive GE dumps (no rig, no retarget)
- `tools/rip/capture_anim.py` talks to PPSSPP's WebSocket debugger directly and requests
  `gpu.record.dump` back-to-back while scheduling button presses by dump index. PPSSPP stalls
  emulation while serializing a dump (~1.4 s each), so at **full speed** consecutive requests
  return consecutive rendered frames: the isolated □1 (30 vblanks in Phase 2) spans ~15 dumps
  (GoS renders 30 fps) and bounding boxes / poses change smoothly dump-to-dump. The planned
  "slow PPSSPP down" trick was not needed (ini change reverted).
- `tools/rip/anim_extract.py` decodes every dump with `gedump.py`, auto-picks the hero cluster
  (vertex count window + nearest to previous frame) and writes one posed, textured glTF/OBJ per
  frame. GoS' own skinning + chain simulation is baked into each frame — that *is* the
  "blade physics".
- `ge_textured.run(..., extra_tex=...)` adds selected **rigid** draws inside the hero bbox by
  texture id: `2c5f86` = the Blades' fire-trail ribbon (additive, drawn unskinned).

## Findings
- **Chains:** drawn as part of Kratos' skinned mesh using an additive **FX atlas**
  (128×64: chain links + glow + smoke). Rendered opaque, the atlas showed as black squares around
  the blades; with additive shading the chain/glow appear correctly (e.g. frame 22: thrown blade
  with glowing chain back to the hand). Rule used in Blender: textures ≥30 % black → additive.
- Other rigid groups near Kratos: `270ad7` = water splash ring (excluded), `7cf006` = scenery.
- Through-mode (2D) draws are full-screen post-process blits, not chains.

## Result
- Capture `square_combo` (□×4 at dumps 1/9/17/25, 75 dumps): □1–□4 occupy dumps ~1–34,
  idle afterwards. 41 frames rendered in Blender 5.2 EEVEE (ortho, Hades-like 50° pitch,
  camera follows the body median to cancel GoS root motion) →
  `C:\mods\model\_ANIM\preview\square_combo_{30fps,slowmo}.mp4`, `square_combo.gif`.

## Next (toward Kratos in Hades)
1. Capture △ (SwordParry), dash, idle/run, hit — same tools.
2. Match Hades' hero camera/scale (oracle: Zagreus silhouette height + pivot) and render each
   clip in Hades' hero directions → sprite sheets.
3. Package as Hades animations (deppth/.pkg on the user's machine) replacing Zagreus' sword
   animations only while Kratos mode is active.

## Honesty note
Capture, decoding and rendering done with AI (Claude Code) on the user's own GoS copy.
