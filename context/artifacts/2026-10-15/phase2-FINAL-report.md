# Phase 2 (frame data) — KAPANIŞ RAPORU · 2026-10-15

> DESIGN §9 kapısı: "her faz Türkçe rapor + onayla biter". Bu rapor onay içindir.
> Veri: `data/gos_framedata/blades.json` · Yöntem kanıtları: aynı klasördeki
> `phase2-blades-framedata-FINAL.md`, `phase2-damage-evade-FINAL.md`, ve 2026-10-14
> `phase2-progress-FINAL.md`. Retail adresler yalnızca gitignored `research/`'te.

## 1. Ne ölçüldü (Blades of Athena + savunma)

| Hareket | Startup | Aktif (görsel) | Toplam / zincir | Hasar (asker HP 20) | Hades hedefi |
|---|---|---|---|---|---|
| □1 ileri zincir-hamle | 11 | 12–16 | 30 (tek) | 2 (2 hedefe kadar) | `SwordWeapon` |
| □2 ters süpürme | 3–4 | 6–8 | zincir | 2 | `SwordWeapon2` |
| □3 alçak süpürme | 4 | 9 | zincir | 2 | `SwordWeapon2` |
| □4 tepe yayı (bitirici) | 3–4 | 12–15 | ~9 toparlanma | 2/tick × 2–4, alan | `SwordWeapon3` |
| △1 ağır | 20 | 9 + 7 | 47 | 2 + 6 | `SwordParry` / Special |
| Kaçış (L+R+analog) | ~2 | dalış ~19 | ~45 | — | `SwordWeaponDash` / Rush |
| Blok/deflect (L) | ~4 | dokunuş: isabetten 20→4 kare önce | — | — | `SwordParry` |

Ek: asker mızrağı Kratos'a 5 hasar; □ ile asker 10 vuruşta ölür.

## 2. Yöntemler (yeniden üretilebilir)
- **Zamanlama:** PPSSPP frame dump (emüle kare başına 1 video karesi) + `tools/framedata/video_metrics.py`.
- **Hasar:** düşman sağlık komponentleri (Kratos'unkiyle aynı tip) imza taramasıyla bulunup canlı okundu.
- **Deflect:** kayıt durumundan düşman saldırısı CPU-tick düzeyinde deterministik (2 koşu aynı tick);
  L dokunuşu isabete göre taranıp HP ile doğrulandı + altın deflect efekti görüntüyle.

## 3. Ölçülmeyenler / belirsizlik
- Gerçek hitbox kareleri (görsel iz vekili kullanıldı; HP zamanlaması ±5 kare).
- Menzil (dünya birimi) — Hades'te zaten `Config.lua` `RangeScale` ile ayarlanacak.
- Kaçış dokunulmazlığı yalnızca 1 örnekle "muhtemel".
- Girdi gecikmesi ve geç-kombo penceresi.
- Arms of Sparta (mızrak/kalkan) — Phase 5'te aynı yöntemle.
Bunlar Phase 4 (Blades'i Hades'e taşıma) için engel değil; ±1–2 kare ve oranlar yeterli.

## 4. Öneri
Phase 2'yi **Blades için kapalı** say; Phase 4'e (Blades + Thera's Bane) geç ve bu sayıları
`Config.lua`'ya bağla. Phase 3 (görsel) paralel ilerleyebilir (T-poz Kratos hazır).

## 5. Honesty note
Ölçüm ve rapor AI (Claude Code) yardımıyla, kullanıcının kendi GoS kopyasında yapıldı.
