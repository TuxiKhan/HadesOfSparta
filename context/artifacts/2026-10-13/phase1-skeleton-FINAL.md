# Phase 1 — placeholder Kratos skeleton (FINAL)  ·  2026-10-13

Phase 0 bitti; bu, Phase 1'in ilk dikey dilimi. DESIGN.md §9: Phase 1 = "placeholder
Kratos (Zagreus sprites, Kratos logic)". Asıl Blades dövüşü Phase 4; görsel Phase 3;
ölçülmüş GoS sayıları Phase 2. Bu yüzden Phase 1 KASITLI olarak iskelet + override
boru hattı kanıtıdır, combat reimplementasyonu değildir ("Translate, never rewrite").

## 1. Ne üretildi (repo'da `mod/HadesOfSparta/`)
- `modfile.txt` — `Load Priority 1` (ModUtil/StyxScribe = 0'dan sonra yüklenir), üç
  dosyayı `Scripts/Main.lua`'ya import eder.
- `Config.lua` — tek balans kaynağı. `ModUtil.Mod.Register("HadesOfSparta")` ile global
  mod tablosu + `mod.Config` (Verbose, Scale.{Damage,Range}=1.0 nötr, Blades hit-stop/
  rumble çarpanları). Sayılar PLACEHOLDER; Phase 2'de ölçümle değişecek.
- `HeroKratos.lua` — giriş noktası. `HadesOfSparta.Active=true`, `mod.Log()`, import
  anında + `ModUtil.LoadOnce` içinde yükleme izi basar. Combat reimplementasyonu YOK.
- `Weapons/Blades.lua` — Blades of Athena → `SwordWeapon` ailesini (`SwordWeapon`,
  `SwordWeapon2`, `SwordWeapon3`) YERİNDE override eder. Vanilla değerleri bir kez
  anlık görüntüye alır (`mod._Vanilla`), çarpanları hep bu tabandan MUTLAK uygular →
  `LoadOnce` her çağrıldığında katlanma olmaz. İç silah adları DEĞİŞMEZ.
- `tools/install_mod.py` — `mod/HadesOfSparta` → `<Hades>/Content/Mods/` kopyalar ve
  modimporter'ı `Content/` içinden çalıştırır (`--clean` ile kaldırır).

## 2. Boon-uyumu (projenin kalbi) — korundu
Hiçbir iç silah adı yeniden adlandırılmadı; sadece mevcut `SwordWeapon*` girdilerinin
alanları güncellendi. DESIGN §4.1'e göre boon'lar `WeaponSets.*` içindeki iç ada göre
gate yaptığı için Zeus/Athena/Ares vb. Kratos'un kılıcına ek bağlama olmadan
iliştirilmeye devam eder. (Matrisle fiili doğrulama: Phase 4, `docs/BOON_MATRIX.md`.)

## 3. Statik doğrulama — YAPILDI
- 3 Lua dosyası `luaparser` ile temiz ayrıştı (sözdizimi OK).
- `tools/install_mod.py` çalıştırıldı. modimporter sonucu: **`3 base files import a
  total of 11 mod files`** (önceki 8 + bizim 3). `Scripts/Main.lua` içine enjekte
  edilen importlar 1334–1336, ModUtil (…1332) ve StyxScribe (1333)'tan SONRA — yani
  `Load Priority 1` beklendiği gibi çalıştı, bizim kod çalışırken `ModUtil.*` hazır.
- Oyun içindeki dosyalar mevcut: `Content/Mods/HadesOfSparta/{modfile.txt,Config.lua,
  HeroKratos.lua,Weapons/Blades.lua}`.
- Kullanılan ModUtil 2.10.0 API'leri kaynaktan doğrulandı: `Mod.Register`
  (Main.lua:71), `Table.Copy.Deep` (lua:845), `Table.Merge` (lua:951), `LoadOnce`
  (Main.lua:265).

## 4. CANLI in-game doğrulama — PASS ✅ (2026-10-13 19:00)
`tools/verify_phase1.py` Hades'i StyxScribe çekirdeğiyle (REPL eklentisi YÜKLENMEDEN)
başlattı, kullanıcı bir save yükledi, sürücü problar gönderip `Lua:` çıktısını yakaladı.
Sürücü kendi `scribe.Close()` SIGTERM'i ile çıktı (exit 15 = normal, Phase 0 ile aynı).

Okunan değerler (JSON karar: `pass=true`, tüm kontroller true):
- `HadesOfSparta.Active` → **true**
- `WeaponData.SwordWeapon.HitSimSlowParameters[1].Fraction` → **0.08** (vanilla 0.1 × 0.80)
- `WeaponData.SwordWeapon.HitRumbleParameters[1].RightFraction` → **0.255** (vanilla 0.17 × 1.50)

`game_output.log` (oyun dizini, gitignored — buraya kopyalandı) yükleme zincirini de
doğruluyor:
```
Lua:	HadesOfSparta: Kratos mode loaded (v0.1.0-phase1)        <- boot (import anı)
Lua:	HadesOfSparta: run loaded; Kratos mode active = true     <- save yüklendi (LoadOnce)
Lua:	HadesOfSparta: Blades feel applied to SwordWeapon family -> { SwordWeapon, SwordWeapon2, SwordWeapon3 }
Lua:	HOSP1_ACTIVE:true
Lua:	HOSP1_FRAC:0.08
Lua:	HOSP1_RUMBLE:0.255
```

→ **Phase 1 dikey dilimi uçtan uca kanıtlandı:** mod Hades içinde yükleniyor, `SwordWeapon`
ailesini yerinde override ediyor (iç adlar değişmeden → boon-uyumu korunuyor), ve
Config'teki çarpanlar canlı WeaponData'ya doğru uygulanıyor. Boon matrisi ile fiili
boon-iliştirme testi Phase 4'e planlı (`docs/BOON_MATRIX.md`).

## 5. Geri alma
`python tools/install_mod.py --clean` (modimporter `--clean` + mod klasörünü siler).
Sert geri yükleme: 2026-10-10 `Content/Scripts` yedeği + Steam "verify integrity".

## 6. Notlar
- `luaparser` sadece lint için venv'e kuruldu (gitignored).
- Retail Hades değiştirildi (geri alınabilir) — Phase 0 StyxScribe kurulumu precedent'i.
- Commit kullanıcı isteğine bırakıldı.
