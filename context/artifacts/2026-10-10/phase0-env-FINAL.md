# Phase 0 — Environment setup (FINAL)  ·  2026-10-10

Evidence record. Full detail in `docs/RESEARCH.md`.

## Done & verified
- Project tree + `git init` (branch `main`) at `C:\mods\HadesOfSparta`; `.gitignore` excludes
  all game data / assets / offsets. **No commit yet** (awaiting user request).
- Hades 1 located (Steam, `...\steamapps\common\Hades`), scripts readable, saves located.
- GoS ISO located (`C:\A\mode\...Ghost of Sparta (USA)....iso`), region USA, serial TBD.
- Installed: PPSSPP 1.20.4; `ppsspp-dfx-mcp` 0.1.7 + `deppth2` 0.1.6.7 (project `.venv`);
  universal-modder plugin (enabled).
- ppsspp-dfx MCP registered (user scope) + **health check Connected** (PPSSPP not yet running).
- Hades loaders staged in `research/vendor/extracted/`: modimporter 1.6.1, **ModUtil v2.10.0
  (Hades 1)**, StyxScribe. ModUtil 4.0.1 flagged as Hades II (Hell2Modding) — not used.

## Backup taken (2026-10-10, pre-modimporter)
- `C:\mods\HadesOfSparta_backup\2026-10-10\` — Hades `Content\Scripts` (98 files, 10.3 MB) +
  saves (`Documents\Saved Games\Hades`, 7 files, 1.4 MB). modimporter keeps its own backup too;
  Steam "Verify integrity of game files" is the ultimate restore.

## NOT done (needs user OK / interactive game launch)
- modimporter run against Hades (modifies game files). **User approved; do after relaunch.**
- Hades + StyxScribe REPL round-trip test.
- PPSSPP + GoS boot, remote debugger, live memory read + serial capture.
- Source-verified boon↔slot mapping (read TraitData/WeaponData/HeroData).

## Decisions recorded
- PPSSPP MCP = ppsspp-dfx (Python) over mcp-ppsspp (npm): Node absent, richer surface.
- Hades 1 ModUtil = **v2.10.0**, not repo-latest 4.0.1 (Hades II). Evidence: manifest deps.
