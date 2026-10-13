--[[ HadesOfSparta / Config.lua
	Tek balans/ayar kaynağı. DESIGN.md §2: "Balance = config." Hiçbir sayı başka
	dosyaya gömülmez; her şey buradan okunur.

	Phase 1 NOTU: Aşağıdaki Blades değerleri PLACEHOLDER'dır. Gerçek GoS sayıları
	Phase 2'de (frame data) ölçülüp buraya yazılacak; dövüş davranışı Phase 4'te
	(Blades + Thera's Bane) uygulanacak. Şimdilik sadece override boru hattını ve
	"ağır vuruş" hissini kanıtlıyoruz.
]]

-- ModUtil mod'u olarak kaydol: global `HadesOfSparta` tablosunu oluşturur/döndürür.
local mod = ModUtil.Mod.Register( "HadesOfSparta" )

mod.Version = "0.1.0-phase1"

mod.Config = {
	-- Konsola/StyxScribe'a yükleme izlerini bas (in-game doğrulaması için).
	Verbose = true,

	-- GoS -> Hades ölçek sabitleri (Phase 2'de doldurulacak; şimdilik nötr).
	Scale = {
		DamageScale = 1.0,   -- GoS hasarını Hades'e çevirme çarpanı (Phase 4)
		RangeScale  = 1.0,   -- menzil/çarpışma çarpanı (Phase 4)
	},

	-- Blades of Athena -> SwordWeapon (Stygius), yerinde override.
	Blades = {
		-- Phase 1 placeholder "ağır vuruş" hissi. Vanilla taban değerler
		-- Blades.lua'da anlık görüntüye alınır; bu çarpanlar ona uygulanır.
		-- Fraction < 1  => daha derin/uzun hit-stop (vuruş daha ağır hisseder).
		HitStopFractionScale = 0.80,
		-- Titreşim payı > 1 => daha güçlü rumble.
		RumbleFractionScale  = 1.50,
	},
}

return mod.Config
