# DESIGN.md — HadesOfSparta

> Living design doc. Decisions here are the referee for both the Hades (Lua/SJSON) side and
> the GoS (measurement/render) side. Status: **Phase 0 — discovery.** Mapping below is a
> *hypothesis* to be verified against Hades source before it is locked.

## 1. Goal

Kratos (GoS: Ghost of Sparta) fully replaces Zagreus as the playable hero inside Hades 1.
Hades keeps its rooms, camera, enemies, and boon/keepsake/Mirror systems. Kratos uses GoS
combat. **Olympian boons must keep attaching to Kratos' weapons** — this is the project's
core constraint.

## 2. Principles (from SkyCraft / universal-modder)

- **Translate, never rewrite.** Express GoS moves *inside* Hades' own weapon / projectile /
  trait systems. If we're reimplementing a Hades mechanic from scratch, the design is wrong —
  stop and ask.
- **Oracles before code.** Every GoS number is *measured* (PPSSPP MCP), not guessed.
- **Evidence log.** `context/artifacts/<date>/<step>-FINAL|PART`. Claims need artifacts.
- **Balance = config.** GoS→Hades damage/scale lives in `Config.lua`, never hardcoded.
- **Each phase ends playable** and with a Turkish report + my approval.

## 3. Architecture

```
[User's GoS ISO] --(PPSSPP + GE capture / format RE)--> tools/extract/  (mesh+skeleton+anim -> glTF)
        v
tools/render/ (Blender bpy, Hades hero angles/scale/light) --> sprite atlas + anim SJSON
        v
tools/pack/ (deppth2) --> Hades .pkg   [built on user's machine, NOT in repo]

[PPSSPP MCP measurement] --> data/gos_framedata/*.json  (numbers only: frames, dmg, range, i-frames)
        v
mod/ (Lua + SJSON, modimporter format)
   HeroKratos.lua · Weapons/{Blades,Spear,Shield}.lua · TherasBane.lua
   Magic.lua · RageOfSparta.lua · Hud.lua · Config.lua
```

Toolchain is pinned in `docs/RESEARCH.md`.

## 4. Boon compatibility — the heart of the project

Hades binds boons (traits) to weapons via internal weapon names and the
Attack / Special / Cast / Dash / Call slots. Strategy: **fit Kratos' weapons onto the existing
slots and, where possible, the existing internal weapon names, then override behavior** — so
Zeus/Athena/Ares/etc. boons auto-attach with no per-boon wiring.

### 4.1 Slot mapping — VERIFIED against source (2026-10-10)

Evidence: `context/artifacts/2026-10-10/phase0-boon-binding-FINAL.md`. **Mechanism confirmed:**
a boon gates on the hitting weapon's **internal name** via `WeaponSets.*`
(e.g. `ZeusWeaponTrait.LegalOnDamageWeapons = WeaponSets.HeroPhysicalWeapons`, `TraitData.lua:771`),
*not* the UI slot. So boons auto-attach **iff Kratos reuses the existing internal weapon names.**
→ **Locked strategy: override the existing weapon entries in place; never mint new names.**

Engine slot names (not the UI labels): **Melee**=Attack, **Secondary**=Special, **Ranged**=Cast,
**Rush**=Dash, **Shout**=Call.

| GoS weapon/action | Hades internal family (override in place) | Slot |
|---|---|---|
| Blades of Athena — light combo | `SwordWeapon` (+ `SwordWeapon2/3`) | Melee |
| Blades — heavy / launcher | `SwordParry` (Special) / `SwordWeaponWave` | Secondary |
| Blades — dash-attack | `SwordWeaponDash` | Rush |
| Arms of Sparta — spear | `SpearWeapon` (+`2/3`), `SpearWeaponThrow` | Melee / Secondary |
| Arms of Sparta — shield | `ShieldWeapon`, `ShieldThrow` (block/parry on Aegis) | Melee / Secondary |
| Evade roll | the `*WeaponDash` / Rush action | Rush |
| 3 magics | `RangedWeapon` (Cast) **or** dedicated key | **open — §6.2** |
| Rage of Sparta | custom resource, **NOT** `Shout`/God Gauge | — |

> Families & members verified in `WeaponSets.lua:131` (`HeroWeaponSets`) and `WeaponData.lua:1676`
> (`SwordWeapon`: `DashWeapon="SwordWeaponDash"`, `SecondaryWeapon="SwordParry"`). Minting new
> weapon names would force edits to every `WeaponSets` list **and** every boon's
> `LegalOnDamageWeapons`/`WeaponNames` — rejected as unmaintainable.

### 4.2 Boon compatibility matrix (test, not assume)

Every Olympian boon × every Kratos weapon, driven from the StyxScribe REPL in a test room:
grant boon → trigger attack → state-dump that the effect applied. Output → `docs/BOON_MATRIX.md`.

## 5. GoS measurement (oracle) — plan

Via ppsspp-dfx MCP: locate Kratos' state struct (pos, HP, magic, rage, active move id, frame
counter). Per move: startup / active / recovery frames, hit count, damage, range, i-frames,
cancel windows. Convert GoS frame rate → Hades time units. Output → `data/gos_framedata/*.json`
(our own numbers). **Retail offsets stay in gitignored `research/` / `.ppsspp-dfx/`.**

## 6. DECISIONS — LOCKED (user, 2026-10-10)

1. **Session root → relaunch `claude` inside `C:\mods\HadesOfSparta`.** Future sessions run in
   the project folder (also respawns the MCP so decision 6 takes effect).
2. **Magic = out of scope for now.** If it is ever required, it binds to **Cast (`RangedWeapon`)**
   — replacing Bloodstone Cast — so Cast boons auto-apply. No dedicated magic bar unless revisited.
3. **Bow / Fists / Rail → deferred to a later release.** In Kratos mode they stay as-is / unused
   for now; not adapted this cycle.
4. **modimporter → RUN. ✅ DONE** (2026-10-10): ModUtil v2.10.0 staged in `Content/Mods/ModUtil`,
   modimporter run **from `Content/`**, `Scripts/Main.lua` now imports the 5 ModUtil files.
   Uninstall = `modimporter --clean`; hard restore = `Content/Scripts` backup + Steam verify.
5. **One weapon per run; GoS weapons replace Hades weapons in place, added over time.** Kratos
   equips a single weapon per run (Hades' model kept). Each GoS weapon *overrides the behavior of
   one Hades weapon family*, rolled out across phases:
   - Blades of Athena → **`SwordWeapon`** (Stygius) — Phase 1 onward.
   - Arms of Sparta spear → **`SpearWeapon`** (Varatha) — later phase.
   - Arms of Sparta shield → **`ShieldWeapon`** (Aegis) — later phase.
   (No in-run weapon-switch system — stays faithful to "translate, never rewrite.")
6. **PPSSPP debugger security → risk accepted (offline box). ✅ env set**: MCP re-registered
   (user scope) with `PPSSPP_DFX_ALLOW_REMOTE_DEBUGGER=1`. Effective after the MCP respawns
   (i.e. on the decision-1 relaunch).

## 7. Visual pipeline — capture-method spike (Phase 3)

Two candidate capture paths, decided by a small timed spike, not up front:
- **A. GE frame capture:** position Kratos in a neutral area, trigger moves via MCP input/
  memory, capture skinned mesh + bone matrices from PPSSPP's GE debugger (or RenderDoc under
  D3D11/Vulkan).
- **B. Format RE:** decode GoS's model/animation archive via Ghidra + memory reads.
  (`mogaika/god_of_war_browser` is PS2/PS3/Vita GoW1-2 only — no PSP GoS support — but useful
  for format ideas.)
Oracle for the render: automated Kratos-vs-Zagreus silhouette-height / pivot comparison.
Budget risk: a single Hades hero attack is hundreds of frames × directions — prioritize an
animation list and measure disk/VRAM before committing.

## 8. Risk table

| Risk | Impact | Mitigation |
|---|---|---|
| Trait system enumerates weapons in a way our override can't hook | breaks boon-compat (core) | verify in `TraitData.lua`/`WeaponData.lua` in Phase 0 *before* building |
| ModUtil/modimporter drift vs current Steam Hades build | mod won't load | pinned versions in RESEARCH.md; empirical modimporter run is the gate |
| GoS state struct / move ids hard to locate in memory | blocks measurement oracle | ppsspp-dfx disassembly + breakpoints; log the search in `research/` |
| Sprite frame-count explosion | disk/VRAM blowup, slow renders | prioritized anim list + measured budget in Phase 3 spike |
| PSP GoS model/anim format undocumented | visual pipeline stalls | spike picks GE-capture vs format-RE by measured speed |
| Accidentally shipping game data / offsets | legal / takedown | strict `.gitignore` + publish check every push |

## 9. Phase gates

0 discovery · 1 placeholder Kratos (Zagreus sprites, Kratos logic) · 2 frame data · 3 visual
spike · 4 Blades + Thera's Bane · 5 Arms of Sparta · 6 magic + Rage · 7 polish & release.
Each ends playable, with a Turkish report, and waits for approval.

**Status:** Phase 0 ✅ · Phase 1 ✅ (live-verified 2026-10-13: `SwordWeapon` family overridden
in place, boon-names untouched, in-game readback PASS). **Phase 2 🔄 in progress (2026-10-14):**
the precondition — locating the GoS player struct — is **DONE**. After 3 sessions of failed
*blind* discovery, a **CWCheat-seed + MCP pointer-chase** cracked it: the player stat struct is
pointer-indirect, and **orbs (5× HUD match), current/max HP (damage + regen), magic and position**
are verified live. The per-move animation state was also located but is a *playback cursor*, not a
discrete move-id — so frame-data extraction (startup/active/recovery → `data/gos_framedata/*.json`)
is the next focused step (cursor-threshold or behavioral/screenshot method). `Config.lua` Blades
values stay placeholder until then. Retail addresses live only in gitignored `research/` +
`.ppsspp-dfx/`. Evidence: `context/artifacts/2026-10-14/phase2-progress-FINAL.md`.
**2026-10-15:** first real frame data — the anim cursor proved unusable as a timer, so the
oracle switched to **PPSSPP frame dumps** (one video frame per emulated vblank → game-time
exact) + `tools/framedata/video_metrics.py`. Blades □1–□4 (+ extended □5–10) and △1
startup / visual-active / recovery are in `data/gos_framedata/blades.json`. Still open:
damage, true hitbox frames, range, dodge/parry/dash. Evidence:
`context/artifacts/2026-10-15/phase2-blades-framedata-FINAL.md`.
