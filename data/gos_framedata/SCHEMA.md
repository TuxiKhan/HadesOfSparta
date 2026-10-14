# data/gos_framedata — şema (Phase 2)

Bu klasör SADECE bizim türettiğimiz sayıları içerir (GoS'tan ölçülmüş frame/hasar/menzil
değerleri). **Retail bellek offset'leri burada DEĞİL** — onlar gitignored `research/` ve
`.ppsspp-dfx/`'te kalır. Her dosya tek bir GoS silahını/eylem setini tanımlar.

## Dosya adlandırma
`<silah>.json` — ör. `blades.json`, `spear.json`, `shield.json`.

## JSON şeması
```jsonc
{
  "weapon": "blades_of_athena",
  "hades_target_family": "SwordWeapon",   // DESIGN §5: yerinde override hedefi
  "source": {
    "game": "God of War: Ghost of Sparta",
    "serial": "UCUS98737",
    "measured_fps": 60,                    // GoS iç mantık frame hızı (doğrulanacak)
    "method": "ppsspp-dfx memory + frame counter; bkz. research/phase2-method"
  },
  "moves": [
    {
      "id": "light_1",                     // combo adımı / eylem adı
      "input": "Square",
      "startup_frames": 0,                 // input -> ilk aktif/hit frame
      "active_frames": 0,                  // hitbox aktif süre
      "recovery_frames": 0,                // son aktif -> tekrar kontrol
      "hits": 1,
      "damage": 0,                         // GoS iç hasar birimi (ham)
      "range": 0.0,                        // ölçülen menzil (birim: belgelenecek)
      "iframes": null,                     // varsa [start,end] frame
      "cancel_window": null,               // varsa frame aralığı
      "notes": ""
    }
  ],
  "frame_to_seconds": 0.0,                 // 1 frame kaç saniye (1/measured_fps)
  "hades_time_note": "Hades süreleri saniye cinsinden; dönüşüm Phase 4'te uygulanır"
}
```

## Ek alanlar (blades.json ile eklendi, 2026-10-15)
- `source.frame_zero` / `source.active_definition`: kare-0 ve "active" tanımı (ölçüm yöntemine bağlı).
- `total_frames_isolated`: tek basışta ilk anim karesi → duruşa dönüş.
- `samples`: ham örnekler (dump kare indeksleri; `trail` = görünür bıçak izi penceresi).
- `active_windows_relative`: çok-vuruşlu hareketlerde kare-0'a göre [başla, bitir] listesi.
- `trail_windows`, `trail_start_intervals_frames`: tek örnekli uzun dizeler için.

## Alan notları
- `damage`/`range` ham GoS birimidir; Hades'e ölçekleme `mod/.../Config.lua` `Scale.*`
  üzerinden Phase 4'te yapılır (DESIGN §2: "Balance = config").
- `startup/active/recovery` GoS frame sayacından ölçülür; saniyeye `frame_to_seconds`
  ile çevrilir.
- Eksik/ölçülememiş alan `null` bırakılır — "Bilgi artefakta girmedi ise yok sayılır."
