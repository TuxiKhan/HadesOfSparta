# Phase 2 — Blades damage + evade timing · 2026-10-15

> Tracked. Method only — retail addresses/offsets are in gitignored `research/`.
> Data: `data/gos_framedata/blades.json` (damage fields + `evade_roll`).

## 1. Damage oracle
- User-made save state at the start of an encounter (4 undead spear soldiers, early GoS).
- Enemy HP lives in the same **health component type** as Kratos' HP (verified earlier). A
  signature scan for that component type, done **after** loading the state, lists every health
  component; the 4 soldiers are the ones with max HP **20**. (Scanning before the reload found
  stale components from a later moment — those never changed when hit.)
- Per move: reload state → wait until soldiers are in range → input → read all soldier HPs at
  short intervals (batch probes) → per-hit deltas.

## 2. Results (undead soldier, max HP 20)

| Move | Damage | Evidence |
|---|---|---|
| □1 forward thrust | **2** per target (can hit 2 at once) | 3 runs |
| □2 / □3 | **2** each | 1 run (sparse cadence) |
| □4 overhead arc | **2 per tick, 2–4 ticks per target**, area hit (~18 total over 3 soldiers) | 1 run + mash run |
| △1 heavy | **2** (rising blades, first ~18 f) + **6** (main slam, ~+24–29 f) | 2 runs, identical |

⇒ Blades base unit = 2/hit (10 □ hits kill a soldier); the heavy slam = 3×; the finisher's
value comes from multi-tick area damage. Ratios matter for Hades, not the absolute 2/20 —
scaling goes through `Config.lua` `Scale.DamageScale` (Phase 4).

## 3. Evade (L+R + analog), empty arena, frame dump
- Two samples: start → dive (~19 f airborne) → roll + rise → standing: **≈ 36–50 f total**
  (judging "settled" is the uncertainty). Hades target: `SwordWeaponDash`/Rush slot.
- □ pressed right after the roll did **not** produce a distinct dash-attack in GoS.
- Block (L held) is a static stance — no duration to measure. **Parry window and i-frames need
  an incoming enemy attack** → not measured.

## 4. Incident
One run (evade/block attempt #1) was contaminated: the slot-switch + load looked successful in
a screenshot (slot-preview overlay) but the game stayed in the encounter, and combat input not
sent by the tool was recorded (likely the game being played by hand at the same time). Discarded; re-run in the
cleared arena.

## 5. Still open for Phase 2
true hitbox frames (HP-delta timing is ±5 f with batch probes), parry window, evade i-frames,
input latency / late-combo window. All need enemy attacks → a save state where a soldier is
mid-swing at Kratos.

## Honesty note
Measured and written with AI (Claude Code) on the user's own GoS dump.
