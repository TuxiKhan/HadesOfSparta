--[[ HadesOfSparta / Config.lua
	Tek balans/ayar kaynağı. DESIGN.md §2: "Balance = config." Hiçbir sayı başka
	dosyaya gömülmez; her şey buradan okunur.

	Phase 4: Blades değerleri artık ÖLÇÜLMÜŞ GoS sayılarıdır
	(data/gos_framedata/blades.json, Phase 2). Burada yalnızca (a) bu ham sayılar ve
	(b) GoS -> Hades çeviri ölçekleri durur. Uygulama: Weapons/Blades.lua.
]]

-- ModUtil mod'u olarak kaydol: global `HadesOfSparta` tablosunu oluşturur/döndürür.
local mod = ModUtil.Mod.Register( "HadesOfSparta" )

mod.Version = "0.4.0-phase4"

mod.Config = {
	-- Konsola/StyxScribe'a yükleme izlerini bas (in-game doğrulaması için).
	Verbose = true,

	-- GoS -> Hades çeviri sabitleri.
	Scale = {
		-- GoS ölçüm kare hızı (blades.json source.measured_fps ≈ 59.94 -> 60).
		Fps = 60,
		-- Zaman çarpanı: 1.0 = GoS kare sayıları birebir. (<1 => daha hızlı Kratos.)
		TimeScale = 1.0,
		-- GoS hasar birimi -> Hades hasarı. DPS-paritesi ile türetildi:
		--   Stygius dizisi (vanilla): 20+25+30 = 75 hasar / 82 kare  (≈0.915/kare)
		--   Blades dizisi (□1,□2,□4): 2+2+6 = 10 GoS hasar / 63 kare (startup+kilit)
		--   0.915 × 63 / 10 ≈ 5.8  -> 6.  Sağlama: △ (2+6)×6 = 48 ≈ vanilla Special 50.
		DamageScale = 6.0,
		-- Menzil ölçülmedi (blades.json range=null) -> Hades vanilla menzili korunur.
		RangeScale  = 1.0,
	},

	-- Blades of Athena -> SwordWeapon (Stygius) ailesi, yerinde override.
	Blades = {
		-- Phase 1 "ağır vuruş" hissi (Lua WeaponData, vanilla tabana göre çarpan).
		-- Fraction < 1  => daha derin/uzun hit-stop.  Rumble > 1 => daha güçlü titreşim.
		HitStopFractionScale = 0.80,
		RumbleFractionScale  = 1.50,

		-- Hades iç silahı -> GoS hareketi (KRATOS_MOVESET.md §5). Hades'in 3 adımlı
		-- zinciri GoS'un 4 vuruşlu □ dizisini taşır: □2/□3 neredeyse aynı (startup 4,
		-- aktif 8–9) olduğundan SwordWeapon2 ikisini temsil eder; □4 bitirici.
		-- Alanlar (hepsi GoS karesi, blades.json'dan):
		--   ChargeFrames  : startup (girdi -> vuruş). Hades ChargeTime'a çevrilir.
		--   Damage        : vuruş başına GoS hasarı (çok-tick/çok-vuruş toplamı).
		--   LockFrames    : saldırı kilidi = görsel aktif süre. Kanıt: mash örneklerinde
		--                   sonraki □ her zaman iz bittiği karede başlıyor (en erken zincir).
		--                   Hades'te dash ile iptal edilebilir (Cancelable) efekte yazılır.
		--   RecoveryFrames: (opsiyonel) girdi yoksa hareket kilidi = aktif + toparlanma.
		-- Ölçülmeyen alanlar (iptal-penceresi/ControlWindow, menzil) Hades vanilla kalır.
		Moves = {
			SwordWeapon = {               -- □1 ileri zincir-hamle
				Gos = "square_1",
				ChargeFrames = 11,
				Damage = 2,
				LockFrames = 15,
				LockEffect = "SwordDisableCancelableAndLockTrigger",
			},
			SwordWeapon2 = {              -- □2 ters süpürme (□3 alçak süpürme de bu adım)
				Gos = "square_2",
				ChargeFrames = 4,
				Damage = 2,
				LockFrames = 8,
				LockEffect = "SwordDisableCancelableAndLockTrigger2",
			},
			SwordWeapon3 = {              -- □4 tepe yayı (bitirici)
				Gos = "square_4",
				ChargeFrames = 4,
				Damage = 2 * 3,           -- 2/tick × 2–4 tick/hedef -> ortalama 3
				LockFrames = 12,
				LockEffect = "SwordDisableAttackCancelable3",
				RecoveryFrames = 12 + 9,  -- aktif + toparlanma (dizi sonu, settled)
				RecoveryEffect = "SwordDisableCancelable3",
			},
			SwordParry = {                -- △1 ağır (çift yükselen bıçak + ana darbe)
				Gos = "triangle_1",
				ChargeFrames = 20,
				Damage = 2 + 6,           -- iki vuruş tek Hades patlamasında toplanır
				RecoveryFrames = 47 - 20, -- toplam 47 - startup 20
				RecoveryEffect = "SwordParryDisableCancelable",
			},
		},
	},
}

return mod.Config
