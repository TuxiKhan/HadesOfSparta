#!/usr/bin/env python3
"""HadesOfSparta — Lua mod installer (Phase 1).

Repo'da SADECE kod var; bu betik kodu KENDİ makinendeki Hades kurulumuna
kopyalar ve modimporter'ı çalıştırman için hazırlar. Hiçbir oyun dosyası
indirmez/kopyalamaz.

Yaptıkları:
  1) mod/HadesOfSparta  ->  <Hades>/Content/Mods/HadesOfSparta  (kopya)
  2) (bulunabilirse) modimporter'ı  <Hades>/Content  içinden çalıştırır.

Phase 1 kapsamı: sadece Lua mod'u. GoS asset çıkarma/render/pack boru hattı
(install.py --gos-iso) sonraki fazlarda gelecek.

Kullanım:
    python tools/install_mod.py [--hades <Hades kök klasörü>] [--clean]
                                [--modimporter <modimporter.exe>] [--no-import]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOD_SRC = REPO / "mod" / "HadesOfSparta"
MOD_NAME = "HadesOfSparta"

# Hades'i otomatik aramak için tipik Steam yolları (Windows).
STEAM_GUESSES = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hades"),
    Path(r"C:\Program Files\Steam\steamapps\common\Hades"),
]
# Vendor'daki modimporter (gitignored; kullanıcı sağlar).
MODIMPORTER_GUESSES = [
    REPO / "research" / "vendor" / "extracted" / "modimporter-windows" / "modimporter.exe",
]


def find_hades(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not (p / "Content").is_dir():
            sys.exit(f"[HATA] Hades kökü görünmüyor (Content/ yok): {p}")
        return p
    for g in STEAM_GUESSES:
        if (g / "Content").is_dir():
            return g
    sys.exit("[HATA] Hades otomatik bulunamadı. --hades <yol> ile ver.")


def find_modimporter(explicit: str | None, content: Path) -> Path | None:
    cands = ([Path(explicit)] if explicit else []) + MODIMPORTER_GUESSES
    cands.append(content / "modimporter.exe")
    for c in cands:
        if c.is_file():
            return c
    return None


def install(hades: Path, run_import: bool, modimporter: str | None) -> None:
    if not MOD_SRC.is_dir():
        sys.exit(f"[HATA] Mod kaynağı yok: {MOD_SRC}")
    content = hades / "Content"
    dst = content / "Mods" / MOD_NAME
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(MOD_SRC, dst)
    print(f"[OK] Kopyalandı: {MOD_SRC}  ->  {dst}")
    _maybe_import(content, run_import, modimporter)


def clean(hades: Path, run_import: bool, modimporter: str | None) -> None:
    content = hades / "Content"
    dst = content / "Mods" / MOD_NAME
    if dst.exists():
        shutil.rmtree(dst)
        print(f"[OK] Silindi: {dst}")
    else:
        print(f"[bilgi] Zaten yok: {dst}")
    # modimporter --clean, Main.lua'yı tüm mod importlarından arındırır.
    mi = find_modimporter(modimporter, content)
    if run_import and mi:
        print(f"[OK] modimporter --clean çalıştırılıyor ({mi.name}, cwd=Content)...")
        subprocess.run([str(mi), "--game", "Hades", "--clean", "--no-input"],
                       cwd=content, check=False)
    else:
        print(f"    Elle temizle:  cd \"{content}\"  &&  modimporter.exe --game Hades --clean --no-input")


def _maybe_import(content: Path, run_import: bool, modimporter: str | None) -> None:
    mi = find_modimporter(modimporter, content)
    cmd_hint = f'cd "{content}"  &&  modimporter.exe --game Hades --no-input'
    if not run_import:
        print(f"[bilgi] --no-import: modimporter atlandı. Elle:  {cmd_hint}")
        return
    if not mi:
        print(f"[bilgi] modimporter.exe bulunamadı. Elle çalıştır:  {cmd_hint}")
        return
    print(f"[OK] modimporter çalıştırılıyor ({mi.name}, cwd=Content)...")
    subprocess.run([str(mi), "--game", "Hades", "--no-input"], cwd=content, check=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="HadesOfSparta Lua mod installer (Phase 1)")
    ap.add_argument("--hades", help="Hades kök klasörü (Content/ içeren)")
    ap.add_argument("--clean", action="store_true", help="Mod'u kaldır")
    ap.add_argument("--modimporter", help="modimporter.exe yolu")
    ap.add_argument("--no-import", action="store_true",
                    help="modimporter'ı otomatik çalıştırma")
    args = ap.parse_args()

    hades = find_hades(args.hades)
    print(f"[bilgi] Hades: {hades}")
    run_import = not args.no_import
    if args.clean:
        clean(hades, run_import, args.modimporter)
    else:
        install(hades, run_import, args.modimporter)


if __name__ == "__main__":
    main()
