#!/usr/bin/env python3
"""HadesOfSparta — Phase 4 (Blades) canlı doğrulama sürücüsü.

verify_phase1.py ile aynı düzen: Hades'i StyxScribe çekirdeğiyle başlatır, Lua aktif
olunca (= kullanıcı bir SAVE yükleyince) birkaç saniye bekler (oda kurulumu +
GatherAndEquipWeapons bitsin), sonra MOTORDAN (Lua tablosundan değil) kahramanın
silah özelliklerini geri okur ve JSON kararı yazar.

Doğrulanan (Config.lua Phase 4 değerleri; Fps 60, DamageScale 6):
  HASSWORD      kahramanda SwordWeapon (Stygius) takılı                -> true
  APPLIED       mod.BladesBaseAppliedCount >= 1 (taban en az 1 kez yazıldı)
  CT_<silah>    GetWeaponDataValue ChargeTime (□1 11f, □2 4f, □4 4f, △ 20f)
  DMG_<silah>   GetProjectileProperty DamageLow (□1 12, □2 12, □4 36, △ 48)
  BOONSET       WeaponSets.HeroPhysicalWeapons hâlâ "SwordWeapon" içeriyor (boon-uyumu)

NOT: Stygius'ta aspect/boon varsa (ör. Arthur aspect'i) trait'ler tabanın ÜSTÜNE
biner ve CT/DMG beklenenden sapabilir — bu tasarım gereğidir; temiz test için
ev (House) içinde, aspect'siz Stygius ile save yükle.

Kullanım:
    python tools/verify_phase4.py [--hades <Hades kök>] [--out <json>] [--timeout 240]
                                  [--equip-sword]

--equip-sword: probelardan önce Stygius'u silah rafından alınmış gibi takar
(EquipPlayerWeapon + EquipWeaponUpgrade; mod'un EquipPlayerWeapon hook'unu da test
eder). Save'deki seçili silahı DEĞİŞTİRİR — evde raftan başka silah alarak geri alınır.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

DEFAULT_HADES = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hades")
HOOK_PREFIX = "HOSP4_"
SETTLE_SECONDS = 10.0

FPS = 60.0
EXPECT_NUM = {
    "CT_SwordWeapon": 11 / FPS,
    "CT_SwordWeapon2": 4 / FPS,
    "CT_SwordWeapon3": 4 / FPS,
    "CT_SwordParry": 20 / FPS,
    "DMG_SwordWeapon": 12,
    "DMG_SwordWeapon2": 12,
    "DMG_SwordWeapon3": 36,
    "DMG_SwordParry": 48,
}
EXPECT_STR = {"HASSWORD": "true", "BOONSET": "true"}
TOL = 1e-3


def _lua(expr_key: str, expr: str) -> str:
    return f'StyxScribeREPL: print("{HOOK_PREFIX}{expr_key}:"..tostring({expr}))'


EQUIP_CMD = ("StyxScribeREPL: UnequipWeaponUpgrade(); EquipPlayerWeapon(WeaponData.SwordWeapon); "
             "EquipWeaponUpgrade(CurrentRun.Hero)")


def build_probes() -> list[str]:
    hero = "CurrentRun.Hero"
    p = [
        _lua("HASSWORD", f"{hero}.Weapons.SwordWeapon == true"),
        _lua("APPLIED", "HadesOfSparta.BladesBaseAppliedCount"),
        _lua("BOONSET", 'Contains(WeaponSets.HeroPhysicalWeapons, "SwordWeapon")'),
    ]
    for w in ("SwordWeapon", "SwordWeapon2", "SwordWeapon3", "SwordParry"):
        p.append(_lua(f"CT_{w}",
                      f'GetWeaponDataValue({{ Id = {hero}.ObjectId, WeaponName = "{w}", Property = "ChargeTime" }})'))
        p.append(_lua(f"DMG_{w}",
                      f'GetProjectileProperty({{ Id = {hero}.ObjectId, WeaponName = "{w}", Property = "DamageLow" }})'))
    return p


def check(res: dict) -> dict:
    out = {}
    for k, v in EXPECT_STR.items():
        out[k] = res.get(k) == v
    for k, v in EXPECT_NUM.items():
        try:
            out[k] = abs(float(res.get(k)) - v) <= TOL
        except (TypeError, ValueError):
            out[k] = False
    try:
        out["APPLIED"] = int(float(res.get("APPLIED"))) >= 1
    except (TypeError, ValueError):
        out["APPLIED"] = False
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="HadesOfSparta Phase 4 live verifier")
    ap.add_argument("--hades", default=str(DEFAULT_HADES))
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--equip-sword", action="store_true")
    args = ap.parse_args()

    hades = Path(args.hades)
    if not (hades / "StyxScribe.py").is_file():
        sys.exit(f"[HATA] StyxScribe.py yok: {hades} (Phase 0 kurulumu gerekli)")
    out_path = Path(args.out) if args.out else (hades / "hosp_phase4_verdict.json")

    os.chdir(hades)
    sys.path.insert(0, str(hades))
    from StyxScribe import StyxScribe  # noqa: E402

    scribe = StyxScribe("Hades", "x64", [
        "DebugDraw=true",
        "DebugKeysEnabled=true",
        "RequireFocusToUpdate=false",
    ])

    probes = build_probes()
    n_expected = len(probes)
    state = {"sent": False, "results": {}, "done": False}

    def finish() -> None:
        if state["done"]:
            return
        state["done"] = True
        res = state["results"]
        checks = check(res)
        verdict = {
            "phase": 4,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "results": res,
            "expected": {**EXPECT_STR, **{k: round(v, 5) for k, v in EXPECT_NUM.items()}, "APPLIED": ">=1"},
            "checks": checks,
            "pass": all(checks.values()),
        }
        out_path.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        print("=== PHASE 4 VERDICT ===")
        print(json.dumps(verdict, indent=2))
        print(f"(JSON: {out_path})")
        scribe.Close()

    def collect(payload: str) -> None:
        if ":" not in payload:
            return
        key, _, val = payload.partition(":")
        state["results"][key] = val.strip()
        if len(state["results"]) >= n_expected:
            finish()

    def send_probes_later() -> None:
        if state["sent"]:
            return
        state["sent"] = True
        print(f">>> Lua aktif. Oda kurulumu için {SETTLE_SECONDS:.0f}s bekleniyor...")

        def go() -> None:
            time.sleep(SETTLE_SECONDS)
            if args.equip_sword:
                print(">>> Stygius takılıyor...")
                scribe.Send(EQUIP_CMD)
                time.sleep(2.0)
            print(">>> Problar gönderiliyor...")
            for p in probes:
                scribe.Send(p)

        threading.Thread(target=go, daemon=True).start()

    def watchdog() -> None:
        t0 = time.time()
        while not state["done"]:
            time.sleep(1.0)
            if time.time() - t0 > args.timeout:
                print("!!! Zaman aşımı — eldeki sonuçlarla kapanıyor.")
                finish()
                return

    scribe.AddHook(collect, HOOK_PREFIX)
    scribe.AddOnLuaActive(send_probes_later)
    threading.Thread(target=watchdog, daemon=True).start()

    print("Hades başlatılıyor. Açılınca Stygius'lu bir SAVE yükle.")
    print(f"Zaman aşımı: {args.timeout}s")
    try:
        scribe.Launch()
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
