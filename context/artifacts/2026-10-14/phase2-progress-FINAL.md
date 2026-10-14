# Phase 2 — GoS frame-data ölçüm temeli (PROGRESS / FINAL) · 2026-10-14

> Bu dosya repo'da (tracked). **Retail GoS bellek adresleri BURADA DEĞİL** — onlar
> gitignored `research/phase2-memory-notes.md` ve `.ppsspp-dfx/config/addresses.yaml`'te
> kalır (DESIGN §5: "Retail offsets stay in gitignored research/"). Burada sadece *yöntem*
> ve *doğrulama sonucu* nitel olarak anlatılır.

## 0. Bağlam

DESIGN §9: Phase 2 = "frame data" (GoS hareketlerinin startup/active/recovery/hasar/menzil
sayılarını ölçüp `data/gos_framedata/*.json`'a yazmak; Config.lua placeholder'larını
gerçek ölçümlerle değiştirmek). Ölçüm oracle'ı: PPSSPP-dfx MCP ile canlı bellek.

Phase 2'nin ön koşulu: GoS oyuncu struct'ını (HP, orbs, magic, pozisyon, animasyon durumu)
bellekte **bulmak**. Önceki 3 RE oturumu (13–14 Ekim) bunu *kör* diff/scan ile denedi ve
başaramadı — scanner "unknown initial value" desteklemiyor, bellek-diff animasyon kemik
paleti gürültüsünde boğuluyordu. Oturum 3 sonucu: "adres bul (MCP-dışı) → MCP ile ölç" iş
bölümü; CWCheat DB'sinden tohumlamak önerildi.

## 1. Yöntem — CWCheat-seed + MCP pointer-chase (DUVAR KIRILDI)

Kullanıcı kararı: doğrulanmış topluluk CWCheat kodlarını tohum alıp MCP ile doğrulamak.

1. UCUS98737 (USA) v2.00 için tam CWCheat listesi web'den toplandı (kaynak aşağıda).
2. **Kod yapısı çözümlendi** → statların **pointer-dolaylı** olduğu ortaya çıktı: sabit bir
   "pointer tutucu" global adres, oyuncu stat-struct'ının canlı adresini tutuyor; HP/MP/orbs
   bu struct içinde sabit offset'lerde. (Önceki oturumların doğrudan okumaları bu yüzden HP
   gibi davranmamıştı.)
3. Kritik avantaj: kodlar **bilinen hedef değerler** veriyor (magic full = 200.0f;
   orbs max = 999999). Scanner'ın istediği "tohum değer" artık elde — kör tarama gereği kalktı.
4. Pointer taze deref edilip struct offset'leri **canlı HUD ile karşılaştırılarak** doğrulandı.

(Tüm ham adresler/offset'ler → gitignored `research/` + `.ppsspp-dfx/`.)

## 2. Doğrulanan alanlar (canlı, slot-0 save + Scylla dövüşü + sakin sahil)

| Alan | Doğrulama kanıtı | Durum |
|---|---|---|
| **Orbs** | HUD 331 → 397 → 451 → 476 → 1125; her değer pointer-chase ile **birebir** (5×) | ✅ KESİN |
| **Current HP** | boss hasarı 100.0 → 79.0; sakin alanda regen 79.0 → 100.0 (float) | ✅ KESİN |
| **Max HP** | 100.0f sabit | ✅ KESİN |
| **Magic (MP)** | float; erken oyunda 0, tam = 200.0f (CWCheat ile uyumlu) | ✓ aday |
| **Pozisyon X/Y/Z** | float üçlüsü; Kratos hareketinde değişti | ✓ aday |

**Adresleme reçetesi** (gitignored config'te): `base = deref(sabit_tutucu)` her ölçümde taze;
`orbs/HP/MP = base (veya alt-component) + sabit offset`. Pointer-tutucu stabil bölgede
(PSP'de ASLR yok → oturumlar arası stabil).

## 3. Animasyon-state alanı — bulundu, ama "oynatma imleci" (ayrık move-id değil)

Frame-data'nın çekirdeği per-move animasyon durumudur. Write-breakpoint/diff aviyla
(kemik matris-paleti gürültüsü hariç tutularak) **tek temiz attack-korelasyonlu alan** bulundu
(oyuncu entity'sinin bir alt-komponen­tinde). Karakterizasyon:

- idle ve attack'ta **her kare ilerleyen** bir **animasyon-veri oynatma imleci** (ham RAM
  pointer değil; bir id/handle alanı). Her animasyon farklı değer aralığında; attack aralığı
  idle aralığından yüksek.
- ⇒ **Ayrık "move-id enum" DEĞİL.** Temiz move kimliği için her animasyonun imleç-aralığını
  haritalamak gerekir — bu, sessions 2–3'ün işaret ettiği "churny animasyon sistemi" zorluğu.
- Yine de kullanılabilir: attack aralığına giriş/çıkış = **move-sınırı oracle'ı** (eşikle).

## 4. Frame-data'ya giden iki pratik yol (sonraki odaklı adım)

1. **İmleç-eşiği (ucuz, memory):** anim-imleci eşik-üstündeyken "saldırı aktif" kabul;
   `wait_frames(1)` döngüsünde giriş/çıkış kareleri = startup..recovery toplam süresi.
   Ön iş: idle loop + her combo adımının imleç-aralığını haritala (≈1 oturum).
2. **Davranışsal (screenshot):** `wait_frames(1)` + ekran görüntüsüyle input→bıçak-aktif
   (startup), aktif süre, recovery kareleri; vuruş-anı için kırılabilir obje yanında
   **orbs sıçraması** = hitbox-aktif oracle'ı. Memory-RE'siz, en kesin görünüm; context-pahalı.

## 5. Durum

- **Stat struct KESİN** (HP/orbs/MP/pozisyon) — Phase 2'nin ön koşulu tamam; 3 oturumluk
  kör-keşif duvarı kırıldı.
- **Anim-state alanı bulundu**, semantiği (imleç) belgelendi.
- **Frame-data çıkarımı** (startup/active/recovery → `data/gos_framedata/blades.json`) henüz
  YAPILMADI — yöntem netleşti, sonraki odaklı oturuma kaldı.
- `Config.lua` Blades değerleri hâlâ placeholder (Phase 2 bitince gerçek sayılarla değişecek).

## 6. Araçlar / ortam

- PPSSPP 1.20.4, CPUCore=2 (IR Interpreter — breakpoint'ler için), FastMemoryAccess kapalı.
- ppsspp-dfx-mcp 0.1.7; loopback `127.0.0.1`.
- GoS UCUS98737 v2.00 (kullanıcının kendi dump'ı; repo'ya asla girmez).

## 7. Kaynak

- almarsguides — God of War: Ghost of Sparta (USA) CWCheat:
  https://almarsguides.com/retro/walkthroughs/psp/games/godofwarghostofsparta/cwcheat/usa/

## 8. Honesty note

Bu oturumun bellek-RE'si ve raporu **AI (Claude Code)** yardımıyla üretildi. Tüm ölçümler
kullanıcının kendi GoS dump'ına karşı kendi makinesinde yapıldı; hiçbir retail adres/oyun
verisi repo'ya girmedi.
