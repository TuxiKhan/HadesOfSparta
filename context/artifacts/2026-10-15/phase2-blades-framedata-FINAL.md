# Phase 2 — Blades of Athena frame-data (ilk gerçek ölçüm) · 2026-10-15

> Tracked. Retail bellek adresi YOK (onlar gitignored `research/` + `.ppsspp-dfx/`).
> Video dump'ları kullanıcının makinesinde (`Documents/PPSSPP/PSP/VIDEO/`), repoda değil.
> Sonuç verisi: `data/gos_framedata/blades.json`.

## 1. Neden yöntem değişti (bellek-imleci → video)

Oturum 5'in planı anim-imleci eşiğiyle `watch_value` ölçümüydü.
Bu oturumda iki engel kesinleşti:

1. **`watch_value interval=1` gerçekte ~2 karede bir örnekliyor** (t_s ≈ 32 ms/örnek; 180
   örnek ≈ 5.4 s). Kare-kesin değil.
2. **İmleç monoton değil:** tek □ dokunuşunda değer ±0x260 adımlarla ileri-geri zıpladı ve
   4 s sonra bile idle "park" değerine dönmedi → zaman imleci değil, animasyon-düğümü/
   blend-slot tutamacı gibi davranıyor. Eşik yöntemi güvenilmez.

Ayrıca CPUCore=2 (IR) + ölçüm yükünde duvar saati ≠ oyun saati.

**Çözüm — PPSSPP frame dump:** `Dosya > Kayıt > Görüntü Kaydet` (menü id 40165; FFV1
kayıpsız = 40166) **her emüle edilen vblank için tam bir kare** yazar. Encode sırasında
emülatör ~20 fps'e düşse bile video **oyun-zamanında kare-kesin** (59.94 Hz). Menü komutu
odak gerektirmeden `PostMessage(WM_COMMAND)` ile tetiklendi → `tools/framedata/ppsspp_menu.ps1`.
(Aynı yolla F4 = durum yükleme de çalıştı: `SetForegroundWindow` Windows tarafından
engelleniyor, `PostMessage(WM_KEYDOWN VK_F4)` engellenmiyor.)

## 2. Ölçüm düzeneği

- Sahil kayıt durumu (slot 3 / `StateSlot=2`), boş alan, hedef yok.
- Girdi: ppsspp-dfx `batch_step` (press □/△ 3–4 kare; arka planda).
- **Run 1** (624 kare): tek □ (nötrden) → 4 s bekle → seyrek □×6.
- **Run 2** (1231 kare): □ seri basma ×18 (5 kare arayla) → 7 s → tek △ → 7 s → △ seri ×12.
- Analiz: `tools/framedata/video_metrics.py` — kare başı (a) Kratos bölgesinde gri-seviye
  hareket farkı, (b) HUD bandı dışında "Blades ateş izi" piksel sayısı (turuncu eşik).
  Sınırlar her hareket için kırpılmış kare-kare contact sheet'le **gözle doğrulandı**.
- Kare 0 tanımı = animasyonun görünür ilk değişimi. **Girdi gecikmesi dahil değil**
  (dump'ta girdi işareti yok). "Active" = bıçak izinin görünür uzandığı/süpürdüğü
  kareler — **görsel vekil**, gerçek hitbox değil.
- Tekrarlanabilirlik kontrolü: render her karede benzersiz (0 kopya kare) → oyun 60 fps
  render ediyor; △ iki örnekte ±1 kare içinde aynı.

## 3. Sonuçlar (kare @ 59.94 Hz)

| Hareket | Startup | Active (görsel) | Recovery / sonraki | Toplam | Örnek |
|---|---|---|---|---|---|
| □1 ileri zincir-hamle | **11** (savaş duruşu) · 12 (nötr) · 16 (dönüşlü) | 12–16 | 3 → savaş duruşu | **30** (tek) | 3 |
| □2 ters yatay süpürme | 3–4 | 6–8 | zincirde 16 (seyrek) / 9 (seri) başlangıçtan başlangıca | — | 2 |
| □3 alçak süpürme | 4 (seyrek) / 10 (seri) | 9 | zincirde | — | 2 |
| □4 büyük tepe yayı (bitirici) | 3–4 | 12–15 | ~9 → duruş | dizenin sonu | 2 |
| □5–□10 (sadece sürekli seri basmada) | iz başlangıçları arası 14–22 | 10–21 | — | □1→duruş **195** (~3.25 s) | 1 |
| △1 ağır: çift tepe darbe + alçak takip | **20** | 9 + 7 (2 vuruş, +20..28 / +35..41) | 5 | **47** | 2 (±1) |

Notlar:
- □ dizesi seyrek girdide 4 vuruşta bitiyor (□4 = doğal bitirici); seri basmada 10 vuruşa
  uzuyor (yer-çarpma bitirici). Run 1'de 8 oyun-karesi arayla gelen 6 basıştan 4 vuruş
  çıktı → fazla girdi yutuluyor (tampon/pencere ölçülmedi).
- △ seri basmada ikinci bir ağır vuruşa **zincirlenmiyor**.
- Hades eşleme önerisi (Phase 4 kararı): □1 → `SwordWeapon`, □2/□3 → `SwordWeapon2`,
  □4 → `SwordWeapon3`, △1 → `SwordParry` (Special). Hades 3-vuruşlu kılıç dizesine
  GoS'un 4-vuruşlu temel dizesi doğal oturuyor; □5–10 kapsam dışı/ileride.

## 4. Henüz ölçülmedi (Phase 2 kalanı)

- **Hasar** ve **gerçek hitbox kareleri:** hedef gerek (düşman/kırılabilir obje). Plan:
  düşmanlı kayıtta aynı dump yöntemi + düşman HP'si / orbs sıçraması.
- **Menzil:** dünya-birim; konum alanı (gitignored notlarda) kesinleşince.
- **Kaçış (L+R+analog) / blok-parry penceresi / dash-attack** → `SwordWeaponDash`, `SwordParry`.
- **Girdi gecikmesi** ve **combo-pencere (geç girdi sınırı)**.

## 5. Ortam
PPSSPP 1.20.4 (CPUCore=2), ppsspp-dfx-mcp, ffmpeg 9.0.2 (winget Gyan.FFmpeg — bu oturumda
kuruldu), Python 3.14 stdlib. GoS UCUS98737 v2.00 (kullanıcının kendi dump'ı).

## 6. Honesty note
Ölçüm, analiz ve bu rapor **AI (Claude Code)** yardımıyla üretildi; sınır kareleri
contact sheet'lerden gözle doğrulandı, ±1–2 kare belirsizlik var.
