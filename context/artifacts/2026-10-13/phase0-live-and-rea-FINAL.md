# Phase 0 — live-memory proof + REA install (FINAL)  ·  2026-10-13

Continues the 2026-10-10 Phase-0 work. Evidence record; detail folded into `docs/RESEARCH.md`.

## 1. GoS live-memory read — PROVEN (closes RESEARCH §8 item 2)

The 2026-10-10 blocker (PPSSPP debugger bound to wildcard/unauthenticated) is resolved: the MCP
respawned with `PPSSPP_DFX_ALLOW_REMOTE_DEBUGGER=1` (DESIGN §6 decision 6) and now connects on
loopback only.

- `ppsspp_session(start, iso=…Ghost of Sparta (USA)….iso, wait_ready=true)` → session up,
  `ws://127.0.0.1:55858/debugger`, **WS connected** (loopback, not wildcard).
- `game_state` → `id=UCUS98737`, `title="God of War®: Ghost of Sparta"`, `version=2.00`,
  running. Matches the serial/region read from PARAM.SFO on 2026-10-10.
- **Live memory read OK:** `read_u32 @0x08804000 = 0x6800CC22`; `read_bytes @0x08804000` =
  `22 CC 00 68 04 00 B0 AF 25 80 80 00 BF 08 04 3C …` — valid MIPS (e.g. `AF B0 00 04` =
  `sw $s0,4($sp)`), i.e. the game's own code. End-to-end read pipeline confirmed.
- Screenshot captured (Options menu) → `.ppsspp-dfx/output/screenshots/` (gitignored; retail
  frame, never committed).
- Session stopped cleanly afterward.

→ Both Phase-0 live checks that needed the emulator are now **done** (serial 2026-10-10,
  memory 2026-10-13). The one remaining §8 item is the Hades+StyxScribe REPL round-trip.

## 2. Tooling — REA ("Reverse Engineer Anything") installed

Requested tool from the two review repos. universal-modder was already installed+enabled
(2026-10-10); REA is the new one.

- **Node.js 22.23.2 (LTS)** installed via winget (`OpenJS.NodeJS.22`) — REA needs
  `^22.19 || ^24.11 || >=26`. winget updated the persistent PATH (effective for new shells /
  after a Claude restart). npm 10.9.8. *(Node was previously absent; PPSSPP MCP was chosen as
  Python precisely to avoid Node — Node is now present for REA.)*
- **Repo cloned** → `research/vendor/rea/` (gitignored, 3409 files). Published on npm as
  `rea-agents` v6.4.0 (`mcpName io.github.morluto/rea`).
- **MCP server registered** (Claude Code, **local** scope → `~/.claude.json` under this
  project, not committed):
  `command=cmd, args=[/d,/c,npx,-y,rea-agents@6.4.0,mcp]` (the Windows wrapper REA's own setup
  uses). First Git-Bash attempt mangled `/d /c` → `D:/ C:/`; re-added with `MSYS_NO_PATHCONV=1`.
- **Not yet verified running.** The auto-mode sandbox denied executing npm-fetched code
  (`[Code from External]`), so `npx rea-agents … --version` / `setup` could not be smoke-tested
  from here. The MCP will fetch + start on the next Claude Code **restart** (needs npx on PATH —
  satisfied) and the user should confirm it appears as a connected `rea` server.

### REA fit for this project
REA's strengths are native-binary (Hopper/Ghidra/IDA) + format analysis, incl. **MIPS** and
firmware/format extraction — directly useful for the **Phase 3 "Format RE" path** (decoding GoS
PSP model/anim archives). Not needed for Hades (Lua scripts are already plaintext). Native deep
analysis needs a provider (Ghidra/IDA/Hopper) configured separately — none installed yet.

## 3. Remaining Phase-0 item (needs interactive game launch)
- Hades + StyxScribe REPL round-trip (Python↔Lua). modimporter+ModUtil already staged
  (2026-10-10). Deferred: launches the retail game; best done with the user present.

## 4. Decisions / notes recorded
- Node install is a system change; justified by the explicit "install REA" request + the
  winget precedent (PPSSPP). REA's own installer policy forbids auto-installing Node, so it was
  done separately, by hand, first.
- No commit made (project still has zero commits; awaiting user request — per 2026-10-10 note).
