--[[ HadesOfSparta / Weapons/Blades.lua
	Blades of Athena -> SwordWeapon (Stygius), YERİNDE override.

	DESIGN.md §4 / §5-1: iç silah adları (`SwordWeapon`, `SwordWeapon2/3`,
	`SwordWeaponDash`, `SwordParry`) DEĞİŞTİRİLMEZ; sadece mevcut girdilerin
	alanları güncellenir. Böylece Olympos boon'ları (Zeus/Athena/Ares...) hiçbir
	ek bağlama olmadan Kratos'un kılıcına otomatik iliştirilmeye devam eder.

	Phase 1 KAPSAMI (placeholder): gerçek bir "Kratos combo"su YOK. Sadece
	override boru hattını kanıtlamak ve Blades'in "ağır" dokunuşunu taklit etmek
	için hit-stop (HitSimSlowParameters) ve titreşim (HitRumbleParameters)
	değerlerini Config'teki çarpanlarla ölçekliyoruz. Asıl frame-accurate combo
	Phase 4'te gelecek (önce Phase 2'de GoS'tan ölçülecek).
]]

local mod = HadesOfSparta
local config = mod.Config

-- Blades'in devraldığı Hades kılıç ailesi (iç adlar — ASLA yeniden adlandırılmaz).
local SWORD_FAMILY = { "SwordWeapon", "SwordWeapon2", "SwordWeapon3" }

-- Vanilla tabanı bir kez sakla ki LoadOnce her çağrıldığında çarpanlar katlanmasın.
-- (Mutlak değerler hep orijinal tabandan hesaplanır.)
mod._Vanilla = mod._Vanilla or {}

local function snapshotOnce( weaponName )
	if mod._Vanilla[ weaponName ] ~= nil then return end
	local w = WeaponData and WeaponData[ weaponName ]
	if w == nil then return end
	mod._Vanilla[ weaponName ] = {
		HitSimSlowParameters = ModUtil.Table.Copy.Deep( w.HitSimSlowParameters or {} ),
		HitRumbleParameters  = ModUtil.Table.Copy.Deep( w.HitRumbleParameters  or {} ),
	}
end

-- Taban listeyi çarpanla ölçekleyip hedefe mutlak olarak yazar.
local function applyBladesFeel( weaponName )
	local w = WeaponData and WeaponData[ weaponName ]
	local base = mod._Vanilla[ weaponName ]
	if w == nil or base == nil then return false end

	-- Hit-stop: her girdinin Fraction'ını ölçekle (düşük = daha ağır vuruş).
	if next( base.HitSimSlowParameters ) ~= nil then
		local scaled = ModUtil.Table.Copy.Deep( base.HitSimSlowParameters )
		for _, entry in ipairs( scaled ) do
			if entry.Fraction ~= nil then
				entry.Fraction = entry.Fraction * config.Blades.HitStopFractionScale
			end
		end
		w.HitSimSlowParameters = scaled
	end

	-- Titreşim: RightFraction'ı ölçekle (yüksek = daha güçlü rumble).
	if next( base.HitRumbleParameters ) ~= nil then
		local scaled = ModUtil.Table.Copy.Deep( base.HitRumbleParameters )
		for _, entry in ipairs( scaled ) do
			if entry.RightFraction ~= nil then
				entry.RightFraction = entry.RightFraction * config.Blades.RumbleFractionScale
			end
		end
		w.HitRumbleParameters = scaled
	end

	return true
end

-- Tüm veri yüklendikten sonra (run load) uygula: WeaponData kesinlikle hazırdır.
ModUtil.LoadOnce( function()
	local applied = {}
	for _, name in ipairs( SWORD_FAMILY ) do
		snapshotOnce( name )
		if applyBladesFeel( name ) then
			applied[ #applied + 1 ] = name
		end
	end
	mod.Log( "Blades feel applied to SwordWeapon family -> { "
		.. table.concat( applied, ", " ) .. " }" )
end )
