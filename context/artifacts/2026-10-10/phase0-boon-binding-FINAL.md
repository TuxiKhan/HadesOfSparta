# Phase 0 — Boon↔weapon binding model (FINAL, source-verified)  ·  2026-10-10

Evidence for DESIGN.md §4. Read from the live Steam Hades source (read-only, not copied):
`...\steamapps\common\Hades\Content\Scripts\{WeaponSets,WeaponData,TraitData,HeroData}.lua`.

## 1. How Hades binds a boon (trait) to a weapon — the mechanism

Verified on the Zeus Attack boon `ZeusWeaponTrait` (`TraitData.lua:763`):

```lua
ZeusWeaponTrait = {
    Slot = "Melee",                                  -- UI slot (see §3)
    AddOnDamageWeapons   = { "ChainLightning" },     -- effect added on hit
    LegalOnDamageWeapons = WeaponSets.HeroPhysicalWeapons,   -- <-- THE gate
    PropertyChanges = { { WeaponName = "SwordWeapon", WeaponProperty="FireFx", ... }, ... },
}
```

- **`LegalOnDamageWeapons = WeaponSets.*`** is the real gate: the boon's effect fires only
  when the hit comes from a weapon whose **internal name** is in that set.
- **`PropertyChanges[].WeaponName`** apply per-weapon tweaks (VFX, damage) keyed by the same
  internal names; a name that doesn't exist simply no-ops.
- Cast/projectile boons gate on `WeaponSets.HeroNonPhysicalWeapons = { "RangedWeapon" }`
  (`TraitData.lua:324`, etc.).

**Consequence (locks the whole project):** boons find weapons **by internal weapon name**, via
the `WeaponSets` lists — *not* by the UI slot alone. So auto-attach works **iff Kratos' weapons
keep the existing internal names** (`SwordWeapon`, `SpearWeapon`, `ShieldWeapon`, `RangedWeapon`,
… and their members). → **Strategy = override the existing weapon entries in place**, never mint
new weapon names. New names would force edits to every `WeaponSets` list *and* every boon's
`LegalOnDamageWeapons` / `WeaponNames` — unmaintainable.

## 2. The weapon families (what "override in place" must cover)

`WeaponData.lua` `SwordWeapon` (`:1676`) shows the linkage fields:
`DashWeapon = "SwordWeaponDash"`, `SecondaryWeapon = "SwordParry"`; combo steps are
`SwordWeapon2/3`. `WeaponSets.HeroWeaponSets` (`WeaponSets.lua:131`) enumerates each family:

| Base (Attack) | Combo | Dash (Rush) | Special (Secondary) | GoS target |
|---|---|---|---|---|
| `SwordWeapon` (Stygius) | `SwordWeapon2/3`, `SwordWeaponWave` | `SwordWeaponDash` | `SwordParry` | Blades of Athena |
| `SpearWeapon` (Varatha) | `SpearWeapon2/3`, spins | `SpearWeaponDash` | `SpearWeaponThrow` | Arms of Sparta — spear |
| `ShieldWeapon` (Aegis) | `ShieldWeaponRush` | `ShieldWeaponDash` | `ShieldThrow` | Arms of Sparta — shield |
| `BowWeapon`, `GunWeapon`, `FistWeapon` | … | …`Dash` | `BowSplitShot`/`GunGrenadeToss`/`FistWeaponSpecial` | Bow/Rail/Fists — OPEN |
| `RangedWeapon` | — | — | — | Cast → magic (OPEN, DESIGN §6.2) |

Key `WeaponSets` gates a boon can use: `HeroPhysicalWeapons` (the 6 base melee), `HeroMeleeRangeWeapons`,
`HeroDashWeapons`, `HeroSecondaryWeapons`, `HeroNonPhysicalWeapons` (= RangedWeapon / Cast).

## 3. Slot name correction (brief used UI names; source uses engine names)

`TraitData.lua` `Slot` values (verified counts): **Melee**=Attack, **Secondary**=Special,
**Ranged**=Cast, **Rush**=Dash, **Shout**=Call (God Gauge). The brief's "Attack/Special/Cast/
Dash/Call" are the UI labels for these same five.

## 4. Design tension surfaced (needs user decision — DESIGN §6)

Hades equips **one** weapon family per run; GoS Kratos wields Blades **+** spear/shield **+**
magic **simultaneously** with live switching. Mapping Blades→Sword, spear→Spear, shield→Shield
as *simultaneous* contradicts Hades' one-weapon model. Options in DESIGN.md §6.5.

## 5. GoS disc identity (verified, non-interactive)

Read straight from the ISO (no PPSSPP needed): **serial `UCUS98737`**, region **USA**
(`DISC_ID`/`DISC_VERSION`/`TITLE` present in PARAM.SFO). ISO size 1,747,714,048 bytes.
**Path correction:** ISO now lives at
`C:\A\mode\God of War - Ghost of Sparta (USA) (EnFrEs)\God of War - Ghost of Sparta (USA) (En,Fr,Es).iso`
(a subfolder — memory/earlier notes had it one level up).

## 6. PPSSPP live-memory read — BLOCKED on a security decision

`ppsspp-dfx` MCP health = ok (v0.1.7). `ppsspp_session(start)` **refused**: a PPSSPP debugger
(pid 17380, port 52959) is bound to the **wildcard address, unauthenticated** — any host on the
network could read/write emulated memory and inject input. PPSSPP binds `INADDR_ANY`
unconditionally, so no `ppsspp.ini` setting fixes it. Two ways forward (user picks):
1. **OS firewall rule** restricting the PPSSPP debugger port(s) to loopback (safe; a system change).
2. Set env **`PPSSPP_DFX_ALLOW_REMOTE_DEBUGGER=1`** to accept the risk (fast; offline/single-player).
Until resolved, the "GoS memory readable" Phase-0 check is open.
