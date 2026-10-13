--[[ HadesOfSparta / HeroKratos.lua
	Giriş noktası + "Kratos modu" işaretleyicisi.

	Phase 1'de burada combat REIMPLEMENTASYONU YOK (DESIGN.md §2: "Translate,
	never rewrite"). Sadece:
	  1) mod'un gerçekten Hades içinde yüklendiğini gözlemlenebilir kılar
	     (StyxScribe ile `Lua:` kanalından okunabilen print),
	  2) ileri fazların dallanacağı `HadesOfSparta.Active` bayrağını kurar.
]]

local mod = HadesOfSparta            -- Config.lua'daki ModUtil.Mod.Register ile kuruldu
local config = mod.Config

-- Kratos modu etkin. Sonraki fazlar (Blades/Spear/Shield, Magic, Rage) buna dallanır.
mod.Active = true

-- Yardımcı: StyxScribe kuruluysa `Lua:` kanalından, değilse normal log'dan görünür.
function mod.Log( msg )
	if config.Verbose then
		print( "HadesOfSparta: " .. tostring( msg ) )
	end
end

-- Import anında (oyun açılışında) bir kez bas: mod'un yüklendiğinin kanıtı.
mod.Log( "Kratos mode loaded (v" .. tostring( mod.Version ) .. ")" )

-- Bir run içine girildiğinde de doğrula — bu noktada tüm oyun verisi hazırdır,
-- Blades override'ının uygulandığı an da budur (bkz. Weapons/Blades.lua).
ModUtil.LoadOnce( function()
	mod.Log( "run loaded; Kratos mode active = " .. tostring( mod.Active ) )
end )
