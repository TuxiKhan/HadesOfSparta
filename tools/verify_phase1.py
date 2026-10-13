#!/usr/bin/env python3
"""HadesOfSparta — Phase 1 canlı doğrulama sürücüsü.

Hades'i StyxScribe çekirdeğiyle (REPL python eklentisi YÜKLENMEDEN; Phase 0 gotcha:
KeyboardThread EOF -> End) başlatır, Lua aktif olunca (= kullanıcı bir SAVE yükleyince)
problar gönderir, `Lua:` çıktısını yakalar ve JSON kararı yazar.

Doğrulanan:
  HOSP1_ACTIVE  -> HadesOfSparta.Active                                  (beklenen: true)
  HOSP1_FRAC    -> WeaponData.SwordWeapon.HitSimSlowParameters[1].Fraction (beklenen: 0.08)
  HOSP1_RUMBLE  -> WeaponData.SwordWeapon.HitRumbleParameters[1].RightFraction (beklenen ~0.255)

ÖNEMLİ: Bu sürücü Hades'i KENDİSİ başlatmalı (stdout'u ancak başlatan süreç okuyabilir).
Steam'den/elle açılmış bir Hades'e bağlanamaz — önce onu kapat.

Kullanım:
    python tools/verify_phase1.py [--hades <Hades kök>] [--out <json yolu>] [--timeout 180]
Çalışınca: oyun açılır -> bir SAVE yükle -> sürücü otomatik prob gönderir ve kapanır.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_HADES = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hades")

PROBES = [
    ('StyxScribeREPL: print("HOSP1_ACTIVE:"..tostring(HadesOfSparta ~= nil and HadesOfSparta.Active))'),
    ('StyxScribeREPL: print("HOSP1_FRAC:"..tostring(WeaponData.SwordWeapon.HitSimSlowParameters[1].Fraction))'),
    ('StyxScribeREPL: print("HOSP1_RUMBLE:"..tostring(WeaponData.SwordWeapon.HitRumbleParameters[1].RightFraction))'),
]
EXPECT = {"ACTIVE": "true", "FRAC": "0.08", "RUMBLE": "0.255"}
# Sayısal alanlar float karşılaştırmayla (string formatı kırılgan) doğrulanır.
NUMERIC = {"FRAC": 0.08, "RUMBLE": 0.255}
TOL = 1e-4
HOOK_PREFIX = "HOSP1_"


def _check(key: str, got):
    if got is None:
        return False
    if key in NUMERIC:
        try:
            return abs(float(got) - NUMERIC[key]) <= TOL
        except ValueError:
            return False
    return str(got) == EXPECT[key]


def main() -> None:
    ap = argparse.ArgumentParser(description="HadesOfSparta Phase 1 live verifier")
    ap.add_argument("--hades", default=str(DEFAULT_HADES))
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=float, default=180.0)
    args = ap.parse_args()

    hades = Path(args.hades)
    if not (hades / "StyxScribe.py").is_file():
        sys.exit(f"[HATA] StyxScribe.py yok: {hades} (Phase 0 kurulumu gerekli)")

    out_path = Path(args.out) if args.out else (hades / "hosp_phase1_verdict.json")

    # StyxScribe'ı Hades kökünden import et; cwd'yi oraya al (SubsumeHades gibi).
    os.chdir(hades)
    sys.path.insert(0, str(hades))
    from StyxScribe import StyxScribe  # noqa: E402

    scribe = StyxScribe("Hades", "x64", [
        "DebugDraw=true",
        "DebugKeysEnabled=true",
        "RequireFocusToUpdate=false",
    ])

    state = {"sent": False, "results": {}, "start": None, "done": False}

    def collect(payload: str) -> None:
        # payload ör. "ACTIVE:true" (HOOK_PREFIX zaten soyulmuş)
        if ":" not in payload:
            return
        key, _, val = payload.partition(":")
        state["results"][key] = val.strip()
        if len(state["results"]) >= len(EXPECT) and not state["done"]:
            finish()

    def send_probes() -> None:
        if state["sent"]:
            return
        state["sent"] = True
        state["start"] = time.time()
        print(">>> Lua aktif. Problar gönderiliyor...")
        for p in PROBES:
            scribe.Send(p)

    def finish() -> None:
        if state["done"]:
            return
        state["done"] = True
        res = state["results"]
        checks = {k: _check(k, res.get(k)) for k in EXPECT}
        verdict = {
            "phase": 1,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "results": res,
            "expected": EXPECT,
            "checks": checks,
            "pass": all(checks.values()),
        }
        out_path.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        print("=== PHASE 1 VERDICT ===")
        print(json.dumps(verdict, indent=2))
        print(f"(JSON: {out_path})")
        scribe.Close()  # oyunu kapatır + SIGTERM (çıkış kodu 15 normal)

    scribe.AddHook(collect, HOOK_PREFIX)
    scribe.AddOnLuaActive(send_probes)

    print("Hades başlatılıyor. Açılınca bir SAVE yükle (Lua ancak o zaman polling yapar).")
    print(f"Zaman aşımı: {args.timeout}s")

    # Zaman aşımı gözcüsü (ayrı iş parçacığı).
    import threading

    def watchdog() -> None:
        t0 = time.time()
        while not state["done"]:
            time.sleep(1.0)
            if time.time() - t0 > args.timeout:
                print("!!! Zaman aşımı — eldeki sonuçlarla kapanıyor.")
                finish()
                return

    threading.Thread(target=watchdog, daemon=True).start()

    try:
        scribe.Launch()  # bloklar; finish() içinden Close ile biter
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
