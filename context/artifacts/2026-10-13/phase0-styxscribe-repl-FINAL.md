# Phase 0 — Hades + StyxScribe REPL round-trip — PROVEN (FINAL)  ·  2026-10-13

Closes the last open Phase-0 item (`docs/RESEARCH.md` §8 item 1). Evidence record;
detail folded into RESEARCH.md. **Phase 0 is now complete.**

## 1. What was proven
The Python↔Lua bridge into retail Hades round-trips **both directions**:
- **Lua → Python** (output capture): on boot the game emitted
  `Lua:\tStyxScribe: Lua Refreshed!`, received Python-side.
- **Python → Lua → Python** (the real test): driver sent
  `StyxScribeREPL: print("PONGLUA:"..tostring(2+3))` across the proxy bridge; Lua executed it
  and replied `Lua:\tPONGLUA:5`, caught by a Python hook. **Verdict PASS** (`5` as expected).
- **Live game-state access** (bonus): `print("HEROHP:"..CurrentRun.Hero.Health)` returned
  `HEROHP:50` — so the REPL reaches real run objects, not just arithmetic. Hero.Health=50
  means a run was active in the loaded save.
- Round-trip latency ≈ **0.28 s** (`lua_active_at`→`received_at`). Game closed cleanly
  (driver exit 15 = its own `scribe.Close` SIGTERM; no Hades process left).

## 2. Install done this session (retail Hades modified — user-approved, reversible)
1. Copied mod folders `StyxScribe` + `StyxScribeREPL` → `Content/Mods/` (alongside existing `ModUtil`).
2. Copied `SubsumeHades.py` + `StyxScribe.py` → Hades root (so `x64/Hades.exe` + cwd resolve).
3. Ran `modimporter.exe --game Hades --no-input` **from `Content/`**. Result:
   `3 base files import a total of 8 mod files` —
   - `Scripts/Main.lua`: ModUtil ×5 + `StyxScribe.lua`
   - `Scripts/RoomManager.lua`: `StyxScribeREPL.lua`
   - `StyxScribeScripts/StyxScribeREPL.py` written
   Reversible: `modimporter --clean` from `Content/`; 2026-10-10 backup; Steam verify.

## 3. How the test was driven (reusable)
Driver script (kept in scratchpad): `scratchpad/repl_roundtrip.py`. It uses the **StyxScribe
core only** and deliberately does **not** call `LoadPlugins()` — the `StyxScribeREPL.py` plugin
spawns a `KeyboardThread` that reads `input()` and would `End()` the game on stdin EOF in a
detached process. The Lua-side REPL hook (`"StyxScribeREPL: " → runLua`) is installed by
modimporter regardless, so the core (launch + proxy send + stdout capture) is all that's needed.
Flow: launch → wait for `AddOnLuaActive` (fires once Lua polls, i.e. after the **user loads a
save**) → send probe → hook `PONGLUA:` → write JSON verdict → `Close`.

- Launch is **direct `x64/Hades.exe`** (not via Steam), Steam client running/logged in.
- Args: `DebugDraw=true DebugKeysEnabled=true RequireFocusToUpdate=false`.
- Manual step (by user): load a save so the Lua poll thread starts — the only human-in-loop part.

## 4. Gotchas recorded
- Lua only starts `Polling...` **after a save is loaded** (main menu alone does not poll in
  Hades — matches StyxScribe README).
- Harmless `Error: Failed to process line: 'utf-8' codec can't decode byte 0xfd …` in the log =
  a non-UTF8 engine line; StyxScribe skips engine output (`EXCLUDE_ENGINE`), does not affect Lua channel.
- Do **not** load the REPL python plugin for non-interactive driving (KeyboardThread EOF → End).

## 5. Raw evidence (game_output.log, Hades root, gitignored — never committed)
```
Lua:	StyxScribe: Lua Refreshed!
Lua:	StyxScribe: Lua Refreshed!
Lua:	StyxScribe: Polling...
Lua:	PONGLUA:5
Lua:	HEROHP:50
```
