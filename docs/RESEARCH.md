# RESEARCH.md — tool & environment verification

> Phase 0 evidence. Dates absolute. "Bilgi artefakta girmedi ise yok sayılır."
> Last updated: 2026-10-13.

## 1. Detected environment (this machine)

| Thing | Status | Detail |
|-------|--------|--------|
| OS | ✓ | Windows 11 Enterprise LTSC 2024 (10.0.26100) |
| Hades 1 | ✓ installed | Steam app `1145360` → `C:\Program Files (x86)\Steam\steamapps\common\Hades` (layout: `Content/ x64/ x64Vk/ x86/`). Steam build (not Windows Store) → StyxScribe-compatible. |
| Hades saves | ✓ | `C:\Users\Sina\Documents\Saved Games\Hades` (must back up before testing) |
| Hades scripts | ✓ readable | `Content/Scripts/*.lua` are plaintext. Key: `TraitData.lua` (~1 MB), `WeaponData.lua` (437 KB), `HeroData.lua` (297 KB), `EnemyData.lua`, `RoomManager.lua`. `Content/Game/{Weapons,Projectiles,Animations}` present. No `Content/Mods` yet (modimporter not run). |
| GoS disc image | ✓ present | `C:\A\mode\God of War - Ghost of Sparta (USA) (EnFrEs)\God of War - Ghost of Sparta (USA) (En,Fr,Es).iso` (1,747,714,048 B). Region **USA**, serial **`UCUS98737`** — read directly from the ISO's PARAM.SFO 2026-10-10 (no PPSSPP needed). **Path note:** now inside a subfolder (was one level up). **Never committed.** |
| git | ✓ | 2.55.0 |
| Python | ✓ | 3.14.7 (system) + project venv at `.venv` |
| Node.js / npm | ✗ absent | Not needed — chose the Python PPSSPP MCP. |
| Blender | ✗ absent | Deferred to Phase 3 (visual pipeline). Install then. |
| winget | ✓ | used for PPSSPP; choco/scoop absent |

## 2. Installed this session

| Tool | Version | Where | Notes |
|------|---------|-------|-------|
| PPSSPP | 1.20.4 | `C:\Program Files\PPSSPP\PPSSPPWindows64.exe` | via winget; meets ppsspp-dfx-mcp's v1.20.4+ requirement |
| ppsspp-dfx-mcp | 0.1.7 | `.venv` (PyPI) | Python MCP, needs Py 3.14+ (we have it). WebSocket `ws://127.0.0.1:12345`. Registered + **Connected**. |
| deppth2 | 0.1.6.7 | `.venv` (PyPI) | Hades `.pkg` extract/repack (`deppth2 ex/pk`). Replaces writing our own packer. |
| universal-modder | installed+enabled | user scope | Claude Code plugin (mashup-mods skill, publish check). Its bundled `fal` image MCP fails 401 (no token) — irrelevant to us, ignore/disable. |
| Node.js | 22.23.2 (LTS) | winget `OpenJS.NodeJS.22` | Installed 2026-10-13 for REA (needs ≥22.19). PATH updated persistently; npm 10.9.8. (Was absent — PPSSPP MCP picked as Python to avoid it; now present.) |
| REA (`rea-agents`) | 6.4.0 | npm via npx; repo clone `research/vendor/rea/` | "Reverse Engineer Anything" MCP. Registered in Claude Code **local** scope: `cmd /d /c npx -y rea-agents@6.4.0 mcp`. Starts on next Claude restart; **not yet smoke-tested** (auto-mode blocked executing npm-fetched code). Deep native analysis needs a provider (Ghidra/IDA/Hopper) — none yet. Useful for Phase-3 GoS PSP format RE (MIPS). |

Hades-side loaders staged (downloaded, **not yet injected** into the game) under
`research/vendor/extracted/` (gitignored):
- **modimporter 1.6.1** (`modimporter.exe`) — auto-detects Hades 1 vs 2.
- **ModUtil v2.10.0** — the **Hades 1** build (see §3).
- **StyxScribe** (main) — Hades-1 modimporter format; Python side `SubsumeHades.py`; REPL via `>`-prefixed messages, Lua via unprefixed.

## 3. ⚠️ Key gotcha — ModUtil version (Hades 1 vs Hades 2)

- `SGG-Modding/ModUtil` ships **two generations** in the same repo:
  - `v2.x` (v-prefixed, incl. **v2.10.0**): Hades 1, modimporter `modfile.txt`, imports
    `ModUtil.Compat.lua` + `ModUtil.Hades.lua`, **no Hell2Modding/Thunderstore dependency**.
  - `3.x` / `4.x` (incl. **4.0.1**): Hades **II** packaging — `manifest.json` depends on
    `Hell2Modding-Hell2Modding`, `DemonDaemon`, `ENVY` (the Hades II / ReturnOfModding stack).
- **Decision (evidence-based, not assumed): use ModUtil v2.10.0 for Hades 1.** The repo
  default/latest (4.0.1) is the wrong game. The Hades II one is flagged
  `_DO_NOT_USE_HADES2.txt` in vendor.
- This is exactly the "don't confuse with Hades II's Hell2Modding/ReturnOfModding chain"
  warning from the brief — confirmed real.

## 4. PPSSPP MCP choice

- Candidates: `mcp-ppsspp` (npm, Node 22+) vs `ppsspp-dfx-mcp` (PyPI, Py 3.14+).
- **Chose `ppsspp-dfx-mcp`**: Node absent + Py 3.14 present; richer surface (session
  lifecycle, memory r/w, disassembly, breakpoints, input automation, screenshots, replay).
- Config lives in `.ppsspp-dfx/config/` (`project.yaml`, `addresses.yaml`) — gitignored.
  Registered at **user scope** (session cwd is `C:\A\mode`, project is `C:\mods\HadesOfSparta`).
- Health check: **Connected** with PPSSPP not yet running. Live memory tools need PPSSPP
  running + WebSocket debugger enabled + GoS booted. May need a Claude Code restart for the
  MCP tools to load into the session.

## 5. Boon↔weapon binding — VERIFIED (2026-10-10)

Done. Full evidence: `context/artifacts/2026-10-10/phase0-boon-binding-FINAL.md`; mapping locked
in DESIGN.md §4.1. Core finding: boons gate on the hitting weapon's **internal name** via
`WeaponSets.*` (`ZeusWeaponTrait.LegalOnDamageWeapons = WeaponSets.HeroPhysicalWeapons`,
`TraitData.lua:771`), not the UI slot → Kratos must **reuse existing weapon names and override in
place**. Engine slot names: Melee/Secondary/Ranged/Rush/Shout.

## 6. ⚠️ PPSSPP debugger security (found 2026-10-10)

`ppsspp-dfx` refuses to connect: the running PPSSPP debugger (port 52959) is bound to the
**wildcard address and is unauthenticated** — any reachable host can read/write emulated memory
and inject input. PPSSPP binds `INADDR_ANY` unconditionally (no `ppsspp.ini` fix). Options:
(1) OS firewall rule → restrict the port to loopback (safe, system change); (2) env
`PPSSPP_DFX_ALLOW_REMOTE_DEBUGGER=1` to accept the risk on this offline box. **RESOLVED
(DESIGN §6 dec. 6): option 2 chosen, env set; verified working 2026-10-13 — the MCP now drives
PPSSPP over loopback `127.0.0.1` only.**

## 7. Loader install — DONE (2026-10-10)

modimporter + **ModUtil v2.10.0** installed and verified. Gotcha learned: this modimporter
resolves `Mods/` and `Scripts/` **relative to its working directory**, and the modfile targets
`Scripts/Main.lua` → it must be run **from inside `Content/`** (mods live in `Content/Mods/<mod>/`),
*not* from the game root. Result: `Content/Scripts/Main.lua` now `Import`s the 5 ModUtil files
(`1 base file imports 5 mod files`). Uninstall: `modimporter --clean` (from `Content/`).

## 8. Phase-0 items — ALL DONE

1. ~~Launch Hades + StyxScribe, confirm the Python↔Lua REPL round-trips.~~ **✅ DONE 2026-10-13.**
   StyxScribe+StyxScribeREPL installed into retail Hades (modimporter, `3 base files / 8 mod
   files`); driver launched Hades directly, user loaded a save, probe
   `print("PONGLUA:"..(2+3))` round-tripped → `PONGLUA:5` (PASS), and live `CurrentRun.Hero.Health`
   → `50`. Evidence: `context/artifacts/2026-10-13/phase0-styxscribe-repl-FINAL.md`.
2. ~~Boot GoS via MCP and prove a **live memory read**.~~ **✅ DONE 2026-10-13.** MCP respawned
   with `PPSSPP_DFX_ALLOW_REMOTE_DEBUGGER=1`, connected on loopback; `read_u32/read_bytes`
   @`0x08804000` returned valid MIPS code; `game_state` = UCUS98737 / v2.00. Evidence:
   `context/artifacts/2026-10-13/phase0-live-and-rea-FINAL.md`.

→ **Phase 0 (discovery) complete.** Both game-side toolchains (Hades Lua REPL, GoS live memory)
  are proven end-to-end. Next gate: Phase 1 (placeholder Kratos — DESIGN §9).

## Sources
- https://github.com/SGG-Modding/modimporter (1.6.1 release assets)
- https://github.com/SGG-Modding/ModUtil (tags v2.x vs 3.x/4.x; manifest.json deps)
- https://github.com/SGG-Modding/StyxScribe
- https://github.com/weituotian/ppsspp-dfx-mcp (install/config templates)
- https://pypi.org/project/ppsspp-dfx-mcp/ · https://pypi.org/project/deppth2/
