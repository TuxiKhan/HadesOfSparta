--[[ HadesOfSparta / Weapons/Blades.lua
	Blades of Athena -> SwordWeapon (Stygius), YERİNDE override.

	DESIGN.md §4 / §6-5: iç silah adları (`SwordWeapon`, `SwordWeapon2/3`,
	`SwordWeaponDash`, `SwordParry`) DEĞİŞTİRİLMEZ; sadece mevcut girdilerin
	özellikleri güncellenir. Böylece Olympos boon'ları (Zeus/Athena/Ares...) hiçbir
	ek bağlama olmadan Kratos'un bıçaklarına otomatik iliştirilmeye devam eder.

	İki katman:
	  1) Phase 1 "his": Lua WeaponData'daki hit-stop / titreşim (LoadOnce).
	  2) Phase 4 "GoS tabanı": ölçülmüş startup / kilit / hasar, motorun silah
	     özelliklerine (SetWeaponProperty / SetEffectProperty / SetProjectileProperty)
	     MUTLAK olarak yazılır. Hades kahramanı her odada yeniden kurulur
	     (SetupHeroObject -> GatherAndEquipWeapons -> trait'ler), bu yüzden tabanı
	     GatherAndEquipWeapons'ın HEMEN ARDINDAN, trait'ler uygulanmadan ÖNCE yazarız:
	     boon'ların Multiply/Add değişiklikleri Kratos tabanının üstüne biner.
]]

local mod = HadesOfSparta
local config = mod.Config

-- Blades'in devraldığı Hades kılıç ailesi (iç adlar — ASLA yeniden adlandırılmaz).
local SWORD_FAMILY = { "SwordWeapon", "SwordWeapon2", "SwordWeapon3" }

-- ---------------------------------------------------------------------------
-- 1) Phase 1 hissi (Lua WeaponData)
-- ---------------------------------------------------------------------------

-- Vanilla tabanı bir kez sakla ki LoadOnce her çağrıldığında çarpanlar katlanmasın.
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

	if next( base.HitSimSlowParameters ) ~= nil then
		local scaled = ModUtil.Table.Copy.Deep( base.HitSimSlowParameters )
		for _, entry in ipairs( scaled ) do
			if entry.Fraction ~= nil then
				entry.Fraction = entry.Fraction * config.Blades.HitStopFractionScale
			end
		end
		w.HitSimSlowParameters = scaled
	end

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

-- ---------------------------------------------------------------------------
-- 2) Phase 4 GoS tabanı (motor silah özellikleri, oda başına)
-- ---------------------------------------------------------------------------

local function framesToSeconds( frames )
	return frames / config.Scale.Fps * config.Scale.TimeScale
end

-- Config.Blades.Moves -> uygulanacak düz özellik listesi. Saf fonksiyon: motor
-- çağırmaz, böylece REPL'den/doğrulayıcıdan da okunabilir (mod.BladesBaseChanges()).
function mod.BladesBaseChanges()
	local changes = {}
	local function add( kind, weapon, property, value, effect )
		changes[ #changes + 1 ] = { Kind = kind, Weapon = weapon, Property = property, Value = value, Effect = effect }
	end
	for weaponName, move in pairs( config.Blades.Moves ) do
		add( "Weapon", weaponName, "ChargeTime", framesToSeconds( move.ChargeFrames ) )
		local damage = math.floor( move.Damage * config.Scale.DamageScale + 0.5 )
		add( "Projectile", weaponName, "DamageLow", damage )
		add( "Projectile", weaponName, "DamageHigh", damage )
		if move.LockEffect ~= nil then
			add( "Effect", weaponName, "Duration", framesToSeconds( move.LockFrames ), move.LockEffect )
		end
		if move.RecoveryEffect ~= nil then
			add( "Effect", weaponName, "Duration", framesToSeconds( move.RecoveryFrames ), move.RecoveryEffect )
		end
	end
	return changes
end

-- Kahraman SwordWeapon (Stygius) taşıyorsa GoS tabanını mutlak yazar.
function mod.ApplyBladesBase( hero )
	if hero == nil or hero.ObjectId == nil or hero.Weapons == nil or not hero.Weapons.SwordWeapon then
		return false
	end
	local id = hero.ObjectId
	for _, c in ipairs( mod.BladesBaseChanges() ) do
		if c.Kind == "Weapon" then
			SetWeaponProperty({ WeaponName = c.Weapon, DestinationId = id, Property = c.Property, Value = c.Value, ValueChangeType = "Absolute" })
		elseif c.Kind == "Projectile" then
			SetProjectileProperty({ WeaponName = c.Weapon, DestinationId = id, Property = c.Property, Value = c.Value, ValueChangeType = "Absolute" })
		elseif c.Kind == "Effect" then
			SetEffectProperty({ WeaponName = c.Weapon, EffectName = c.Effect, DestinationId = id, Property = c.Property, Value = c.Value, ValueChangeType = "Absolute" })
		end
	end
	mod.BladesBaseAppliedCount = ( mod.BladesBaseAppliedCount or 0 ) + 1
	return true
end

-- Oda başı: SetupHeroObject silahları SJSON tabanından yeniden kurar, sonra
-- trait'leri uygular. Tabanı arada yazıyoruz (boon'lar üstüne biner).
ModUtil.Path.Wrap( "GatherAndEquipWeapons", function( base, currentRun, ... )
	local result = base( currentRun, ... )
	if mod.Active and currentRun ~= nil and mod.ApplyBladesBase( currentRun.Hero ) then
		mod.Log( "Blades GoS base applied (room setup)" )
	end
	return result
end, mod )

-- Evde silah rafından Stygius alınınca: EquipPlayerWeapon silahı SJSON tabanıyla
-- yeniden takar; ardından gelen EquipWeaponUpgrade (aspect) yine üstüne biner.
ModUtil.Path.Wrap( "EquipPlayerWeapon", function( base, weaponData, args, ... )
	local result = base( weaponData, args, ... )
	if mod.Active and weaponData ~= nil and weaponData.Name == "SwordWeapon" then
		if mod.ApplyBladesBase( CurrentRun and CurrentRun.Hero ) then
			mod.Log( "Blades GoS base applied (weapon pickup)" )
		end
	end
	return result
end, mod )
