# Phase 4 (Blades of Athena) — ilk dikey dilim (FINAL) · 2026-10-15

> DESIGN §9: Phase 4 = "Blades + Thera's Bane". Bu rapor **Blades** kısmını kapsar;
> Thera's Bane henüz ölçülmedi (bkz. §6). Veri kaynağı: `data/gos_framedata/blades.json`
> (Phase 2). Canlı karar: `phase4-blades-verdict.json` (aynı klasör).

## 1. Ne yapıldı
- `Config.lua` — Blades artık **ölçülmüş GoS sayıları** + çeviri ölçekleri
  (`Scale.Fps=60`, `TimeScale=1.0`, `DamageScale=6`, `RangeScale=1.0`). `Blades.Moves`
  her Hades iç silahına bir GoS hareketi bağlar (iç adlar değişmez → boon-uyumu).
- `Weapons/Blades.lua` — `mod.BladesBaseChanges()` (saf: Config → özellik listesi) +
  `mod.ApplyBladesBase(hero)` (motor: `SetWeaponProperty` / `SetProjectileProperty` /
  `SetEffectProperty`, hepsi `Absolute`). İki hook:
  - `GatherAndEquipWeapons` sonrası (her oda kurulumu, **trait'lerden önce**) → boon'ların
    Multiply/Add değişiklikleri Kratos tabanının *üstüne* biner.
  - `EquipPlayerWeapon` sonrası (evde raftan Stygius alınınca; aspect ardından gelir).
- Phase 1 hit-stop/rumble hissi korunuyor.
- `modfile.txt` — hedef `Scripts/Main.lua` → **`Scripts/RoomManager.lua`** (bkz. §4).
- `tools/verify_phase4.py` — canlı karar sürücüsü (değerleri Lua tablosundan değil
  **motordan** okur). `tools/hades_probe.py` — etkileşimli canlı prob aracı (dosyaya Lua
  satırı yaz → oyunda çalışır → çıktı log'a).

## 2. GoS → Hades eşlemesi (uygulanan)

| Hades iç silah | GoS hareketi | Startup → ChargeTime | Hasar (GoS×6) | Kilit efekti |
|---|---|---|---|---|
| `SwordWeapon` | □1 ileri zincir-hamle | 11 f → 0.183 s (vanilla 4 f) | 2 → **12** (vanilla 20) | `…CancelableAndLockTrigger` 15 f (aktif) |
| `SwordWeapon2` | □2 ters süpürme (□3 de bu adım) | 4 f → 0.067 s (vanilla 10 f) | 2 → **12** (25) | `…CancelableAndLockTrigger2` 8 f |
| `SwordWeapon3` | □4 tepe yayı (bitirici) | 4 f → 0.067 s (vanilla 0.3 s) | 2×3 tick → **36** (30) | `…AttackCancelable3` 12 f, `…Cancelable3` 21 f |
| `SwordParry` | △1 ağır | 20 f → 0.333 s (vanilla 0.3 s) | 2+6 → **48** (50) | `SwordParryDisableCancelable` 27 f |

- **Kilit = görsel aktif süre**: mash örneklerinin hepsinde sonraki □ tam iz bittiği karede
  başlıyor → en erken zincir anı. Dash ile iptal edilebilir efekte yazıldı.
- **DamageScale = 6** DPS-paritesinden: Stygius 75 hasar / 82 kare ≈ Blades 10 GoS / 63 kare × 5.8.
  Sağlama: △ 48 ≈ vanilla Special 50.
- Bilerek **dokunulmayanlar** (ölçülmedi → vanilla): menzil/arc, `ControlWindow` (kombo
  sıfırlama), sert (iptal edilemez) disable'lar, `SwordWeaponDash` (GoS'ta karşılığı yok),
  `RushWeapon` (GoS kaçışı 45 f; Hades dash'i tüm odaların temposu → değiştirmek oyunu kırar).
- □3 ayrı adım değil: Hades zinciri 3 adımlı; yeni iç ad üretmek boon-uyumunu kırar (DESIGN §4.1).

## 3. CANLI doğrulama — PASS ✅ (2026-10-15 02:43)
`python tools/verify_phase4.py --equip-sword` → kullanıcı save yükledi → Stygius takıldı →
motordan geri okundu (`phase4-blades-verdict.json`, `pass=true`):

```
HOSP4_HASSWORD:true   HOSP4_APPLIED:2   HOSP4_BOONSET:true
CT  SwordWeapon 0.18333  SwordWeapon2 0.06667  SwordWeapon3 0.06667  SwordParry 0.33333
DMG SwordWeapon 12       SwordWeapon2 12       SwordWeapon3 36       SwordParry 48
```
Oda kurulum hook'u da ayrı koşuda log'da görüldü: `HadesOfSparta: Blades GoS base applied (room setup)`.

## 4. Bulunan hata + düzeltme (kayda değer gotcha)
İlk koşularda hook'lar hiç tetiklenmedi (`APPLIED:nil`, hasarlar vanilla 20/25/30/50).
`hades_probe.py` ile canlı teşhis: elle `ApplyBladesBase` → motor değerleri kabul ediyor
(12/48); REPL'den yapılan Wrap çalışıyor; ama import anındaki Wrap kayıp. Sebep:
**`Combat.lua` ve `UpgradeManager.lua`, `Main.lua`'dan SONRA `RoomManager.lua` tarafından
import ediliyor** → `Main.lua`'daki Wrap, fonksiyon yeniden tanımlanınca eziliyor. Çözüm:
modfile hedefi `Scripts/RoomManager.lua`. Ayrıca `GetWeaponProperty` bir getter değil
(argüman tablosunu döndürüyor); doğru okuma `GetWeaponDataValue`.

Küçük not: tek bir `EquipPlayerWeapon` çağrısında taban 2 kez yazıldı (`APPLIED:2`).
Değerler `Absolute` olduğundan zararsız (idempotent); kaynağı (çift wrap?) Phase 4 devamında
incelenecek.

## 5. Ölçülmeyen / açık
- **Elle oynanış hissi testi yapılmadı** — motor değerleri doğrulandı, ama dövüş "hissi"
  (özellikle □1'in 11 f startup'ı ve hızlanan □4) kullanıcının oynayarak onaylaması gerekir.
  Animasyonlar hâlâ Zagreus'un (Phase 3 görsel) → ChargeTime uzayınca charge animasyonu
  son karede bekler.
- Boon matrisi (`docs/BOON_MATRIX.md`, DESIGN §4.2) henüz koşulmadı; şimdilik kanıt:
  iç adlar değişmedi + `WeaponSets.HeroPhysicalWeapons` SwordWeapon'u içeriyor.
- Deflect (GoS L, isabetten 20→4 f önce) Hades'e taşınmadı: Special slotu △'ya ayrıldı,
  Hades'te blok girişi yok → Aegis/kalkan (Phase 5) ile birlikte ele alınmalı.

## 6. Thera's Bane — KAPSAM DIŞI (kullanıcı kararı, 2026-10-15)

Aşağıdaki not tarihsel; Thera's Bane moda eklenmeyecek.

Phase 2'de ölçülmedi (blades.json'da yok). Gerekenler: (a) GoS'ta ölçüm (ateş-bıçak hasar
çarpanı, metre tüketimi/dolumu, zırh kırma), (b) **slot kararı** — Hades'te ikinci bir metre
yok; aday: Cast (`RangedWeapon`) veya God Gauge'siz bir buff durumu. DESIGN §6 kilitli
kararlarına dokunduğu için kullanıcı onayı gerekli.

## 7. Geri alma
`python tools/install_mod.py --clean`. Değerler yalnızca çalışma anında, kahraman
nesnesine yazılır; SJSON/oyun dosyası değişmez.

## 8. Honesty note
Kod, analiz ve doğrulama AI (Claude Code) yardımıyla yapıldı; save yükleme adımı kullanıcıdan.
