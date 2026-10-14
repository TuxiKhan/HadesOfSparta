#!/usr/bin/env python3
"""HadesOfSparta — etkileşimli canlı prob sürücüsü (geliştirme aracı).

Hades'i StyxScribe çekirdeğiyle başlatır ve açık tutar. Bir komut dosyasını izler:
dosyaya eklenen her satır oyuna Lua olarak gönderilir (StyxScribeREPL kanalı). Oyunun
`Lua:` çıktısının tamamı bir çıktı dosyasına eklenir. `QUIT` satırı oyunu kapatır.

Kullanım:
    python tools/hades_probe.py --cmd <komut.txt> --out <çıktı.log> [--hades <kök>]
    # başka bir kabuktan:
    echo 'print("X:"..tostring(HadesOfSparta.Active))' >> komut.txt
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

DEFAULT_HADES = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hades")


def main() -> None:
    ap = argparse.ArgumentParser(description="HadesOfSparta interactive live probe")
    ap.add_argument("--hades", default=str(DEFAULT_HADES))
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cmd_path = Path(args.cmd).resolve()
    out_path = Path(args.out).resolve()
    cmd_path.touch()
    out = open(out_path, "a", encoding="utf-8", buffering=1)

    hades = Path(args.hades)
    os.chdir(hades)
    sys.path.insert(0, str(hades))
    from StyxScribe import StyxScribe  # noqa: E402

    scribe = StyxScribe("Hades", "x64", [
        "DebugDraw=true",
        "DebugKeysEnabled=true",
        "RequireFocusToUpdate=false",
    ])

    state = {"active": False, "done": False}

    def on_lua(payload: str) -> None:
        out.write(payload + "\n")

    def on_active() -> None:
        state["active"] = True
        out.write("# LUA ACTIVE\n")

    def pump() -> None:
        pos = cmd_path.stat().st_size  # yalnızca başlatmadan SONRA eklenenler
        while not state["done"]:
            time.sleep(0.5)
            if not state["active"]:
                continue
            size = cmd_path.stat().st_size
            if size <= pos:
                continue
            with open(cmd_path, encoding="utf-8") as f:
                f.seek(pos)
                chunk = f.read()
            pos = size
            for line in chunk.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line == "QUIT":
                    state["done"] = True
                    out.write("# QUIT\n")
                    scribe.Close()
                    return
                out.write(f"> {line}\n")
                scribe.Send("StyxScribeREPL: " + line)

    scribe.AddHook(on_lua, "")
    scribe.AddOnLuaActive(on_active)
    threading.Thread(target=pump, daemon=True).start()
    try:
        scribe.Launch()
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
