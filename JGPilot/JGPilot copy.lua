-- JGPilot V51.0 王建国 12.0【午夜】全技能工业版
JGPilotDB = JGPilotDB or { active = false }
local keys = { ST="NONE", AOE="NONE", Wake="NONE", Hammer="NONE", Jud="NONE", HoW="NONE", Toll="NONE", Wings="NONE" }

-- 扩展颜色映射表（确保 Z, X, C, V, Q, E, R, F, G, ~ 全覆盖）
local color_map = {
    ["1"]=10,["2"]=20,["3"]=30,["4"]=40,["5"]=50,
    ["Q"]=60,["W"]=70,["E"]=80,["R"]=90,["T"]=100,
    ["A"]=110,["S"]=120,["D"]=130,["F"]=140,["G"]=150,
    ["Z"]=160,["X"]=170,["C"]=180,["V"]=190,["B"]=200,
    ["~"]=210,["NONE"]=0
}

-- 核心：物理热键抓取
local function ScanPhysicalHotKey(slot)
    local barPrefixes = {"ActionButton", "MultiBarBottomLeftButton", "MultiBarBottomRightButton", "MultiBarRightButton", "MultiBarLeftButton", "MultiBar5Button", "MultiBar6Button"}
    for _, prefix in ipairs(barPrefixes) do
        for i = 1, 12 do
            local btn = _G[prefix..i]
            if btn and btn.action == slot then
                local hotkey = _G[prefix..i.."HotKey"]
                local text = hotkey and hotkey:GetText()
                if text and text ~= "" and text ~= RANGE_INDICATOR then
                    return text:upper():match("([^%-]+)$") -- 提取主键位
                end
                local k = GetBindingKey(prefix:upper()..i) or GetBindingKey("CLICK "..prefix..i..":LeftButton")
                if k then return k:upper():match("([^%-]+)$") end
            end
        end
    end
    return nil
end

-- 扫描逻辑
local function ExecuteScan()
    print("|cff00ff00[JGPilot]|r 正在校准 12.0 全技能链路...")
    -- 目标技能关键字映射
    local targets = {
        ["最终审判"]="ST", ["裁决"]="ST", 
        ["神圣风暴"]="AOE", 
        ["灰烬觉醒"]="Wake", 
        ["天锤"]="Hammer",
        ["审判"]="Jud",
        ["愤怒之锤"]="HoW",
        ["圣洁鸣钟"]="Toll",
        ["复仇之怒"]="Wings", ["征伐"]="Wings"
    }
    local res = { ST="NONE", AOE="NONE", Wake="NONE", Hammer="NONE", Jud="NONE", HoW="NONE", Toll="NONE", Wings="NONE" }

    for i = 1, 144 do
        local aType, id = GetActionInfo(i)
        if aType then
            local name = (aType == "spell") and C_Spell.GetSpellName(id) or GetActionText(i)
            if not name and aType == "macro" then
                local body = GetMacroBody(id)
                if body then
                    for k, _ in pairs(targets) do if body:find(k) then name = k break end end
                end
            end

            if name then
                for k, tag in pairs(targets) do
                    if name:find(k) then
                        local key = ScanPhysicalHotKey(i)
                        if key then
                            res[tag] = key
                            print(string.format("  |cff00ff00[锁定]|r %s -> 按键:|cffff0000%s|r", name, key))
                        end
                    end
                end
            end
        end
    end
    keys = res
    print("|cff00ff00[JGPilot]|r 全技能对齐完成。")
end

SLASH_JGPILOT1 = "/jgp"; SlashCmdList["JGPILOT"] = ExecuteScan

-- 像素渲染（这里需要增加像素位，供 Python 识别更多技能）
local function CreatePix(i)
    local f = CreateFrame("Frame", nil, UIParent); f:SetFrameStrata("TOOLTIP")
    local t = f:CreateTexture(nil, "OVERLAY"); t:SetSize(4, 4)
    t:SetPoint("TOPLEFT", (i-1)*5, 0); t:SetColorTexture(0, 0, 0, 1)
    return f, t
end
local px_frames, px = {}, {}
for i=1, 15 do px_frames[i], px[i] = CreatePix(i) end

local f = CreateFrame("Frame")
f:SetScript("OnUpdate", function()
    -- P1-P6: 基础信号与圣能
    local pwr = UnitPower("player", 9) or 0
    px[1]:SetColorTexture(0, 0, JGPilotDB.active and 1 or 0, 1) -- 开关
    px[5]:SetColorTexture(pwr/5, pwr/5, pwr/5, 1)             -- 圣能

    -- P7-P15: 技能按键信号 (按颜色值传递给 Agent)
    local function E(k, p) p:SetColorTexture((color_map[k] or 0)/255, 0, 0, 1) end
    E(keys.ST, px[7]);    E(keys.AOE, px[8]);   E(keys.Wake, px[9])
    E(keys.Hammer, px[10]); E(keys.Jud, px[11]);  E(keys.HoW, px[12])
    E(keys.Toll, px[13]);   E(keys.Wings, px[14])
end)