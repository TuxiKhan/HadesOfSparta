# HadesOfSparta

A **merge mod** that makes **Kratos** from *God of War: Ghost of Sparta* (PSP) a playable
character inside **Hades (1)** — Hades' rooms, camera, enemies and boon/Mirror systems are
preserved, but the hero is Kratos and plays with Ghost of Sparta's combat (Blades of Athena,
Arms of Sparta, magic, Rage of Sparta). Olympian boons keep working on Kratos' weapons.

> ⚠️ **Status:** Early development. **Phase 1 ✅** — placeholder Kratos skeleton loads &
> overrides Stygius in place (boon-compat preserved), live-verified in game. **Phase 2 🔄** —
> GoS player struct located & verified live (HP/orbs/magic/position) via a CWCheat-seeded
> MCP pointer-chase; first Blades frame data (□ string + △ heavy timings) measured from
> PPSSPP frame dumps → `data/gos_framedata/blades.json`: Blades timings, damage, evade and
> deflect window — Phase 2 done for Blades.
> **Phase 4 🔄** — Blades of Athena live in Hades: measured GoS startup / combo lock / damage
> are written onto Stygius (`SwordWeapon` family) every room, *before* boons apply, so boons
> stack on top; engine readback PASS (`tools/verify_phase4.py`). Thera's Bane still to do.
> **Phase 3 (visual) 🔄 started early** — textured Kratos mesh (posed + T-pose) rips from a PPSSPP
> GE dump on your machine; skeleton/animation/render still to do. Plan position: `docs/DESIGN.md` §9.1.
> Not yet playable as Kratos.

## What this repo is (and is not)

This repo contains **only code**: Lua/SJSON mod sources, Python converters/analysis tools, and (planned) a Blender
render pipeline. It contains **no game files, no ripped assets, no decompiled code, and no
retail memory offsets.** Everything that touches copyrighted content runs **on your own
machine** against **your own** Ghost of Sparta dump and your own Hades installation.

## Requirements (you provide)

- A legally-owned **Hades 1** installation (Steam/Epic, not Windows Store).
- Your own **God of War: Ghost of Sparta** disc image (PSP).
- PPSSPP (PSP emulator), Python 3.14+, ffmpeg, Blender, and the Hades modding tools
  (modimporter + ModUtil + StyxScribe). The installer/setup helps you obtain these.

## Install

Today (Lua mod only): `python tools/install_mod.py [--hades <path>]` copies `mod/HadesOfSparta`
into Hades and runs modimporter (`--clean` removes it).

Planned: `install.py --gos-iso <path> --hades <path>` — converts assets and installs the mod on
your machine (runs the extract → render → pack pipeline locally). *(Not implemented yet.)*

## Honesty note

Substantial parts of this project are built with the help of **AI (Claude Code)**.

## Legal

Fan project. Not affiliated with Supergiant Games or Sony/Santa Monica Studio. You must own
both games. See `LICENSE`.
