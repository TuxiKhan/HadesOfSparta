# KRATOS_MOVESET.md — GoS Kratos moveset & asset inventory → Hades mapping

> **Kaynak:** `C:\mods\model` altındaki çıkarılmış GoS assetleri (Phase 5 ✅,
> extraction log: `C:\mods\model\progress.md`, `_index.json`).
> **Bu dosya telif-güvenlidir:** yalnızca *isimler, yapı ve eşleme kararları* içerir —
> hiçbir oyun baytı, doku, geometri ya da retail offset burada DEĞİLDİR.
> Amaç: çıkarımdan gelen somut GoS hareket/animasyon adlarını Hades silah slotlarına
> bağlayıp (DESIGN.md §4–5) hem Phase 4 (Blades) tasarımını hem de Phase 2 frame-data
> ölçüm hedeflerini isimlendirmek. **Living doc** — ölçüm ilerledikçe güncellenir.

---

## 1. Çıkarılmış kaynak paketler (ne elimizde var)

| Paket | Rol | Doku (PNG) | Geometri blob (Phase 6 hedefi) |
|---|---|---|---|
| `KRATOS_MODEL` | **Base Kratos** (kanonik model) | 13 | `0026_42d68320_CfCm.blob` |
| `KRATOS_MODEL_ARES_ARMOR` | Ares Armor kostümü | 15 | `0028_43390c7c` |
| `KRATOS_MODEL_DEIMOS` | Deimos kostümü | 20 | `0015_24f5f46d` |
| `KRATOS_MODEL_GHOST` | Ghost of Sparta (beyaz) | 13 | `0060_9e20280a` |
| `KRATOS_MODEL_ROBOTOS` | "Robotos" kostümü | 20 | `0075_cc19da55` |
| `KRATOS_MODEL_SPARTAN` | Spartan kostümü | 15 | `0063_9f040b40` |
| `KRATOS_YOUNG` | Genç Kratos (flashback) | 17 | `0046_fcecd373` |
| `KRATOS_ANIMS` | Ana animasyon bankası | — | `0025_29c2bdf7` |
| `DEMO_KRATOS_ANIMS` | Demo/ikinci anim bankası | — | `0146_ad7f7139` |
| `KRATOS_FX` | Efektler (370 FX düğümü) | 47 | `0399_c460a788` |

> **Render pipeline notu (DESIGN §7):** Phase 1–4 için **base `KRATOS_MODEL`** kullanılır;
> kostümler ileride seçenek. Animasyon clip adları Pack formatında **hash'li** (okunabilir
> string değil) — bu yüzden clip-bazlı liste aşağıda değil, canlı ölçümle (Phase 2) ve
> GE-capture ile (Phase 6) eşlenecek.

---

## 2. GoS combat-script modülleri (model paketinden, string-referans)

Bunlar Kratos'un davranış XML'lerinin **adlarıdır** (içerik oyunda derli; sadece referans çıktı).
Hareket ailelerini doğrudan isimlendirirler:

| Modül | Kapsam | Hades eşlemesi (DESIGN §4.1) | Faz |
|---|---|---|---|
| `kratos_blades_scripts.xml` | **Blades of Athena** moveset | `SwordWeapon` ailesi | **4 (öncelik)** |
| `kratos_att_scripts.xml` | Genel saldırı/kombo iskeleti | `SwordWeapon`/`SwordParry` | 4 |
| `kratos_spear_scripts.xml` | **Arms of Sparta — mızrak** | `SpearWeapon` ailesi | 5 |
| `kratos_def_scripts.xml` | Blok / parry / savunma | `SwordParry` (Special) | 4 |
| `kratos_hit_scripts` | Hasar tepkileri (get-hit, launch) | Hades hit-reaction | 4 |
| `kratos_wall_scripts.xml` | Duvar tırmanma | Hades'te yok → **kapsam dışı** | — |
| `kratos_ladder_scripts.xml` | Merdiven | kapsam dışı | — |
| `kratos_ledge_scripts.xml`, `kratos_ledgefree_scripts` | Kenar tutunma | kapsam dışı | — |
| `kratos_sidle_back_scripts` | Dar geçit yan yürüme | kapsam dışı | — |

> Kapsam-dışı modüller (wall/ladder/ledge/sidle) Hades oda tasarımında karşılığı olmayan
> GoS-platform mekanikleri — DESIGN §2 "translate, never rewrite" gereği **taşınmaz**.

---

## 3. Çıkarılan animasyon-state token'ları (base model, okunabilir)

Pack binary'sinden okunabilen state adları. Frame-data (Phase 2) ve sprite-render (Phase 6)
için **isimlendirilmiş hedef** listesi:

**Combat / Blades**
- `sblade_main` — Blades ana düğümü (silah kökü)
- `blades_switch_ground`, `blades_switch_air` — silah çıkarma (yerde/havada)
- `bladesback` — Blades'i sırta alma
- `atten`, `aratten` — saldırı giriş/varyant (att-enter)
- `launch` — havaya fırlatma (launcher) → Hades Special adayı

**Savunma / tepki**
- `def_block_parry` — blok→parry
- `gethit`, `gethit_vo`, `gethitvo`, `g_hit` — hasar alma (+ ses)

**Navigasyon / idle**
- `nav_idle_combat` — dövüş idle (silah çekili bekleme)
- `nav_jump_block` — zıplama/blok geçişi
- `swim_dash_idle` — yüzme (kapsam dışı sahne)
- `sidlefront_idle`, `sidlefront_lookl(_en)`, `sidlefront_lookr(_en)` — yan geçit (kapsam dışı)

**Arms of Sparta (Phase 5 için)**
- `os_spear`, `os_shield` — mızrak / kalkan ("Olympus Spartan" silahları)
- `wpn_shieldenter`, `wpn_shieldblockfall`, `wpn_shielddiveexit` — kalkan giriş/blok/dalış

**Grapple (GoS sahne mekaniği — kapsam dışı)**
- `rope_grab`, `grapple_attach`, `grapple_attach_e`

---

## 4. İskelet (rig) — joint adları

Base model bind-skeleton'undan okunabilen temiz joint'ler (humanoid; C=merkez, L=sol, R=sağ):

```
EXP_C1_Pelvis1
EXP_C1_Spine1  EXP_C1_Spine2  EXP_C1_Spine3
EXP_L1_Clav1   EXP_L1_Arm1
EXP_R1_Clav1   EXP_R1_Arm1  EXP_R1_Arm2  EXP_R1_Hand1
```

> Standart RAD-engine humanoid adlandırması. GE-capture bone-matrix paleti bu joint'lere
> kalibre edilecek (render pivot/scale oracle'ı için). Tam hiyerarşi geometri blob'u
> (`0026_…`) veya dump'taki per-draw bone paletinden netleşir.
>
> **2026-10-15:** düzeltilmiş GE rip (`tools/rip/gedump.py`, `ge_textured.py --pose bind`)
> Kratos'u **T-pozda** (bind uzayı; 5806 vertex, 7 doku) veriyor — rig için doğrudan taban.
> Önceki rip'ler register hatası yüzünden yanlış karakterdi (bkz. DESIGN §7).

---

## 5. Hades slot eşlemesi — Blades (Phase 4) hedef tablosu

DESIGN §4.1 kilitli strateji: **iç silah adları yerinde override** (yeni ad üretme → boon-compat).

| GoS Blades hareketi | Çıkarılan iz | Hades iç silah (override) | Slot |
|---|---|---|---|
| Hafif kombo (L1→L2→L3) | `atten`/`aratten`, `kratos_blades_scripts` | `SwordWeapon`, `SwordWeapon2`, `SwordWeapon3` | Melee |
| Ağır / launcher | `launch` | `SwordParry` (Special) / `SwordWeaponWave` | Secondary |
| Dash-attack | — | `SwordWeaponDash` | Rush |
| Blok→parry | `def_block_parry` | `SwordParry` | Secondary |
| Hasar tepkisi | `gethit*`, `kratos_hit_scripts` | Hades hit-reaction (dokunma) | — |

---

## 6. Phase 2 frame-data ölçüm hedefleri (bu dokümandan beslenir)

`data/gos_framedata/SCHEMA.md` formatında ölçülecek, **adı artık belli** hareketler
(ölçüm yöntemi: `research/phase2-memory-notes.md` → anim-cursor eşiği + `wait_frames`):

1. **`blades_light_1/2/3`** (`atten`/kombo) — startup / active / recovery / hasar / menzil / combo-pencere.
2. **`blades_launcher`** (`launch`) — startup / active / i-frame?.
3. **`block_parry`** (`def_block_parry`) — parry penceresi (kaç kare).
4. **`dash_attack`** — Rush slotu için.

Her ölçüm → `data/gos_framedata/blades.json` (ham sayılar). Config.lua'daki Blades
placeholder'ları ancak bu ölçümlerden sonra gerçek değerlerle değişir.

---

### 6.1 Ölçüm durumu (2026-10-15)
Yöntem anim-imleci yerine **PPSSPP frame dump + video metrikleri** oldu (imleç monoton
değil; `watch_value` ~2 karede bir örnekliyor). Ölçülen (görsel-active vekili, ±1–2 kare):

| Hareket | Startup | Active | Toplam / zincir | Hasar | Hades adayı |
|---|---|---|---|---|---|
| □1 ileri zincir-hamle | 11 | 12–16 | 30 (tek) | 2 (2 hedef) | `SwordWeapon` |
| □2 ters süpürme | 3–4 | 6–8 | zincir | 2 | `SwordWeapon2` |
| □3 alçak süpürme | 4 | 9 | zincir | 2 | `SwordWeapon2` |
| □4 tepe yayı (bitirici) | 3–4 | 12–15 | ~9 recovery | 2/tick × 2–4, alan | `SwordWeapon3` |
| □5–10 (sürekli seri) | — | — | □1→duruş 195 | — | kapsam dışı |
| △1 ağır (2 vuruş) | 20 | 9 + 7 | 47 | 2 + 6 | `SwordParry` |
| Kaçış (L+R+analog) | 2 | dalış ~19 | ~45 | — | `SwordWeaponDash` / Rush |

Referans düşman: ölümsüz mızraklı asker, maks HP 20 (□ ile 10 vuruşta ölür).
Kalan: gerçek hitbox kareleri, menzil, `def_block_parry` penceresi, kaçış i-frame'leri (gelen saldırı gerekir).
Kaynak: `data/gos_framedata/blades.json`, `context/artifacts/2026-10-15/phase2-blades-framedata-FINAL.md`.

---

## 7. Değişiklik günlüğü
- **2026-10-14:** Doküman oluşturuldu. `C:\mods\model` Phase-5 çıkarımından combat-script
  modülleri, animasyon-state token'ları, iskelet joint'leri ve kostüm/geometri envanteri
  telif-güvenli biçimde repoya alındı; Blades (Phase 4) slot eşlemesi + Phase 2 frame-data
  hedefleri isimlendirildi.
- **2026-10-15:** §6.1 — ilk ölçülen Blades frame-data (□1–4, □5–10, △1) eklendi.
- **2026-10-15:** §4 — düzeltilmiş GE rip ile T-pose Kratos notu.
- **2026-10-15:** Phase 4 — §5 eşlemesi uygulandı: □1→`SwordWeapon`, □2(+□3)→`SwordWeapon2`,
  □4→`SwordWeapon3`, △1→`SwordParry`. Deflect ve dash-attack bu turda taşınmadı
  (bkz. `context/artifacts/2026-10-15/phase4-blades-FINAL.md`).
