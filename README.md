# HadesOfSparta

A **merge mod** that makes **Kratos** from *God of War: Ghost of Sparta* (PSP) a playable
character inside **Hades (1)** — Hades' rooms, camera, enemies and boon/Mirror systems are
preserved, but the hero is Kratos and plays with Ghost of Sparta's combat (Blades of Athena,
Arms of Sparta, magic, Rage of Sparta). Olympian boons keep working on Kratos' weapons.

> ⚠️ **Status:** Early development (Phase 0 — discovery & design). Not yet playable.

## What this repo is (and is not)

This repo contains **only code**: Lua/SJSON mod sources, Python converters, and a Blender
render pipeline. It contains **no game files, no ripped assets, no decompiled code, and no
retail memory offsets.** Everything that touches copyrighted content runs **on your own
machine** against **your own** Ghost of Sparta dump and your own Hades installation.

## Requirements (you provide)

- A legally-owned **Hades 1** installation (Steam/Epic, not Windows Store).
- Your own **God of War: Ghost of Sparta** disc image (PSP).
- PPSSPP (PSP emulator), Python 3.14+, Blender, and the Hades modding tools
  (modimporter + ModUtil + StyxScribe). The installer/setup helps you obtain these.

## Install

`install.py --gos-iso <path> --hades <path>` — converts assets and installs the mod on your
machine (runs the extract → render → pack pipeline locally). *(Not implemented yet.)*

## Honesty note

Substantial parts of this project are built with the help of **AI (Claude Code)**.

## Legal

Fan project. Not affiliated with Supergiant Games or Sony/Santa Monica Studio. You must own
both games. See `LICENSE`.
