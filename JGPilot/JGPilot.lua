-- 1. 数据库初始化 (包含所有开关、按键和熔断设置)
local JGPilotDB = JGPilotDB or { 
    active = false, burst = false, aoe = false, potion = false,
    smart_aoe = true, use_hp_melt = true, hp_threshold = 10,
    keys = { active = "F5", burst = "F6", aoe = "F7", potion = "F8", melt = "F9" } 
}
local key_cache = { ST = "", AOE = "", Wake = "", Hammer = "" }

-- 2. 影子信号灯总线 (P1 - P11)
local function CreateStealthPixel(idx)
    local p = CreateFrame("Frame", nil, UIParent):CreateTexture(nil, "OVERLAY")
    p:SetSize(4, 4)
    p:SetPoint("TOPLEFT", UIParent, "TOPLEFT", (idx-1)*5, 0)
    p:SetColorTexture(0, 0, 0, 1)
    return p
end

local pixels = {
    active = CreateStealthPixel(1), burst = CreateStealthPixel(2),
    aoe = CreateStealthPixel(3),    potion = CreateStealthPixel(4),
    hp = CreateStealthPixel(5),     proc = CreateStealthPixel(6),
    key_st = CreateStealthPixel(7), key_aoe = CreateStealthPixel(8),
    key_wake = CreateStealthPixel(9), key_hammer = CreateStealthPixel(10),
    hp_bus = CreateStealthPixel(11) -- R:当前血量, G:熔断开关, B:熔断阈值
}

-- 3. 【核心】自动数怪逻辑 (扫描可见血条)
local function GetEnemyCount()
    local count = 0
    local nameplates = C_NamePlate.GetNamePlates()
    for _, frame in ipairs(nameplates) do
        local unit = frame.unitToken
        if unit and UnitCanAttack("player", unit) and UnitAffectingCombat(unit) then
            count = count + 1
        end
    end
    return count
end

-- 4. 【核心】宏与按键全槽位智能扫描 (120格地毯式搜索)
local function ScanBindings()
    local targets = { ST = "裁决", AOE = "风暴", Wake = "灰烬", Hammer = "锤子" }
    local found = {}
    for i = 1, 120 do
        local actionType, id = GetActionInfo(i)
        local name = nil
        if actionType == "spell" then 
            local info = C_Spell.GetSpellInfo(id); name = info and info.name
        elseif actionType == "macro" then name = GetActionText(i) end

        if name then
            for tag, keyword in pairs(targets) do
                if string.find(name, keyword) then
                    local binding = (i<=12 and "ACTIONBUTTON"..i) or (i<=24 and "ACTIONBUTTON"..(i-12)) or
                                    (i<=36 and "MULTIBARRIGHTBUTTON"..(i-24)) or (i<=48 and "MULTIBARLEFTBUTTON"..(i-36)) or
                                    (i<=60 and "MULTIBARBOTTOMRIGHTBUTTON"..(i-48)) or (i<=72 and "MULTIBARBOTTOMLEFTBUTTON"..(i-60))
                    if binding then
                        local k = GetBindingKey(binding)
                        if k then found[tag] = k:upper():match("([^%-]+)$") end
                    end
                end
            end
        end
    end
    key_cache = found
end

-- 5. 键盘监听器 (支持物理按键切换 UI 状态)
local listener = CreateFrame("Frame")
listener:SetPropagateKeyboardInput(true)
listener:SetScript("OnKeyDown", function(_, key)
    for type, boundKey in pairs(JGPilotDB.keys) do
        if key == boundKey:upper() then
            if type == "melt" then JGPilotDB.use_hp_melt = not JGPilotDB.use_hp_melt
            else JGPilotDB[type] = not JGPilotDB[type] end
        end
    end
end)

-- 6. UI 面板面板 (160x320)
local f = CreateFrame("Frame", "JGPilotPanel", UIParent, "BackdropTemplate")
f:SetSize(160, 320); f:SetPoint("CENTER"); f:SetMovable(true); f:EnableMouse(true)
f:RegisterForDrag("LeftButton"); f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
f:SetBackdrop({bgFile = "Interface\\ChatFrame\\ChatFrameBackground", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 14, insets = {left=4,right=4,top=4,bottom=4}})
f:SetBackdropColor(0, 0, 0, 0.9)

local function CreateBtn(y, key)
    local b = CreateFrame("Button", "JGPilotBtn"..key, f, "UIPanelButtonTemplate")
    b:SetSize(140, 32); b:SetPoint("TOP", f, "TOP", 0, y)
    b:SetScript("OnClick", function() 
        if key == "aoe" then JGPilotDB.smart_aoe = not JGPilotDB.smart_aoe 
        elseif key == "use_hp_melt" then JGPilotDB.use_hp_melt = not JGPilotDB.use_hp_melt
        else JGPilotDB[key] = not JGPilotDB[key] end
    end)
    b:GetFontString():SetFont("Fonts\\ARKai_T.ttf", 11, "OUTLINE")
    return b
end

local b1 = CreateBtn(-35, "active"); local b2 = CreateBtn(-75, "burst")
local b3 = CreateBtn(-115, "aoe"); local b4 = CreateBtn(-155, "potion")
local b5 = CreateBtn(-195, "use_hp_melt")

local slider = CreateFrame("Slider", "JGPilotMeltSlider", f, "OptionsSliderTemplate")
slider:SetPoint("TOP", f, "TOP", 0, -260); slider:SetMinMaxValues(1, 50); slider:SetWidth(130)
slider:SetValueStep(1); slider:SetObeyStepOnDrag(true); slider:SetValue(JGPilotDB.hp_threshold)
_G[slider:GetName()..'Low']:SetText('1%'); _G[slider:GetName()..'High']:SetText('50%')
slider:SetScript("OnValueChanged", function(s, v) JGPilotDB.hp_threshold = math.floor(v) end)

-- 7. 事件绑定与色彩编码
local function Encode(key, p)
    local map = {["1"]=10, ["2"]=20, ["3"]=30, ["4"]=40, ["5"]=50, ["Q"]=60, ["E"]=70, ["R"]=80, ["F"]=90, ["G"]=100, ["V"]=110}
    p:SetColorTexture((map[key or ""] or 0)/255, 0, 0, 1)
end

local e = CreateFrame("Frame")
e:RegisterEvent("PLAYER_ENTERING_WORLD"); e:RegisterEvent("UPDATE_BINDINGS"); e:RegisterEvent("ACTIONBAR_SLOT_CHANGED")
e:SetScript("OnEvent", ScanBindings)

-- 8. 满血版 Update 循环
f:SetScript("OnUpdate", function()
    local enemies = GetEnemyCount()
    local isAOE = JGPilotDB.aoe or (JGPilotDB.smart_aoe and enemies >= 3)
    local hp_max, hp_cur = UnitHealthMax("target"), UnitHealth("target")
    local hp_pct = (hp_max > 0) and (hp_cur / hp_max) or 0

    -- 信号灯同步
    pixels.active:SetColorTexture(0, 0, JGPilotDB.active and 1 or 0, 1)
    pixels.burst:SetColorTexture(JGPilotDB.burst and 1 or 0, 0, 0, 1)
    pixels.aoe:SetColorTexture(0, isAOE and 1 or 0, 0, 1)
    pixels.potion:SetColorTexture(JGPilotDB.potion and 1 or 0, JGPilotDB.potion and 1 or 0, 0, 1)
    pixels.hp:SetColorTexture((UnitPower("player", 9) or 0)/5, (UnitPower("player", 9) or 0)/5, (UnitPower("player", 9) or 0)/5, 1)
    pixels.proc:SetColorTexture(0, (C_Spell.GetSpellOverlayedInfo(431455) and 1 or 0), (C_Spell.GetSpellOverlayedInfo(431455) and 1 or 0), 1)

    Encode(key_cache.ST, pixels.key_st); Encode(key_cache.AOE, pixels.key_aoe)
    Encode(key_cache.Wake, pixels.key_wake); Encode(key_cache.Hammer, pixels.key_hammer)
    pixels.hp_bus:SetColorTexture(hp_pct, JGPilotDB.use_hp_melt and 1 or 0, JGPilotDB.hp_threshold/100, 1)

    -- UI 文字同步
    b1:SetText(string.format("%s[%s]|r 脚本执行", JGPilotDB.active and "|cff00ff00" or "|cffff0000", JGPilotDB.keys.active))
    b2:SetText(string.format("[%s] 爆发开关", JGPilotDB.keys.burst))
    b3:SetText(string.format("[%s] AOE:%s%d怪|r", JGPilotDB.keys.aoe, isAOE and "|cff00ff00" or "|cffffffff", enemies))
    b4:SetText(string.format("[%s] 自动药水", JGPilotDB.keys.potion))
    b5:SetText(string.format("%s[%s]|r 熔断阈值: %d%%", JGPilotDB.use_hp_melt and "|cff00ff00" or "|cffffffff", JGPilotDB.keys.melt, JGPilotDB.hp_threshold))
    _G[slider:GetName()..'Text']:SetText("自动熔断设定")
end)