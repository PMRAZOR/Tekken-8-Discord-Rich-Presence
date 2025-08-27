-- Tekken 8 Discord RPC Data Collector

local character_codes = {
    ["aml"] = "Jun",
    ["ant"] = "Jin",
    ["bbn"] = "Raven",
    ["bsn"] = "Steve",
    ["cat"] = "Azucena",
    ["ccn"] = "Jack-8",
    ["cht"] = "Bryan",
    ["cml"] = "Yoshimitsu",
    ["crw"] = "Zafina",
    ["ctr"] = "Claudio",
    ["der"] = "Asuka",
    ["ghp"] = "Leo",
    ["grf"] = "Paul",
    ["grl"] = "Kazuya",
    ["hms"] = "Lili",
    ["hrs"] = "Shaheen",
    ["jly"] = "Leroy",
    ["kal"] = "Nina",
    ["klw"] = "Feng",
    ["kmd"] = "Dragunov",
    ["lon"] = "Victor",
    ["lzd"] = "Lars",
    ["mnt"] = "Alisa",
    ["pgn"] = "King",
    ["pig"] = "Law",
    ["rat"] = "Xiaoyu",
    ["rbt"] = "Kuma",
    ["snk"] = "Hwoarang",
    ["swl"] = "Devil Jin",
    ["ttr"] = "Panda",
    ["wlf"] = "Lee",
    ["zbr"] = "Reina",
    ["dog"] = "Eddy",
    ["cbr"] = "Lidia",
    ["bee"] = "Heihachi",
    ["okm"] = "Clive",
    ["kgr"] = "Anna",
    ["tgr"] = "Fahkumram",
}

local polaris_hud = nil
local player_hud = nil
local last_logged_state = nil
local battle_start_timestamp = nil
local is_in_battle = false
local hook_registered = false

function stateChanged(new_state)
    if not last_logged_state then return true end
    
    return (last_logged_state.game_mode ~= new_state.game_mode or
            last_logged_state.p1_character ~= new_state.p1_character or
            last_logged_state.p2_character ~= new_state.p2_character or
            last_logged_state.in_match ~= new_state.in_match)
end

function getCharacterCodeFromTexture(texture)
    if not texture or not texture:IsValid() then return nil end
    local fullName = texture:GetFullName()
    return string.sub(fullName, -3)
end

function updateHudReferences()
    if not polaris_hud or not polaris_hud:IsValid() then
        polaris_hud = FindFirstOf("WBP_UI_HUD_S2_C")
    end
    
    if polaris_hud and polaris_hud:IsValid() then
        if not player_hud or not player_hud:IsValid() then
            player_hud = polaris_hud.ref_player
        end
        return true
    end
    return false
end

function saveGameState(state)
    local jsonData = string.format(
        '{"in_match":%s,"p1_character":"%s","p2_character":"%s","game_mode":"%s","timestamp":%d}',
        tostring(state.in_match), state.p1_character, state.p2_character, 
        state.game_mode, state.timestamp
    )
    
    local file = io.open("tekken8_discord_rpc.json", "w")
    if file then
        file:write(jsonData)
        file:close()
        
        if stateChanged(state) then
            if state.game_mode == "battle" or state.game_mode == "practice" then
                print("Discord RPC: " .. state.game_mode .. " - " .. state.p1_character .. " vs " .. state.p2_character)
            else
                print("Discord RPC: " .. state.game_mode)
            end
            last_logged_state = state
        end
    end
end

function collectCharacterInfo()
    local p1_char, p2_char = "unknown", "unknown"
    
    if updateHudReferences() and player_hud then
        -- P1
        local p1_icon_widget = player_hud.WBP_UI_HUD_Char_Icon_1P
        if p1_icon_widget and p1_icon_widget:IsValid() then
            local p1_icon = p1_icon_widget.Rep_T_UI_HUD_CH_ICON_L
            if p1_icon and p1_icon:IsValid() then
                local p1_code = getCharacterCodeFromTexture(p1_icon.Brush.ResourceObject)
                if p1_code and character_codes[p1_code] then
                    p1_char = character_codes[p1_code]
                end
            end
        end
        
        -- P2
        local p2_icon_widget = player_hud.WBP_UI_HUD_Char_Icon_2P
        if p2_icon_widget and p2_icon_widget:IsValid() then
            local p2_icon = p2_icon_widget.Rep_T_UI_HUD_CH_ICON_R
            if p2_icon and p2_icon:IsValid() then
                local p2_code = getCharacterCodeFromTexture(p2_icon.Brush.ResourceObject)
                if p2_code and character_codes[p2_code] then
                    p2_char = character_codes[p2_code]
                end
            end
        end
    end
    
    return p1_char, p2_char
end

function updateGameState(game_mode, in_match)
    local p1_char, p2_char = collectCharacterInfo()
    local current_time = os.time()
    
    if (game_mode == "battle" or game_mode == "practice") and in_match then
        if not is_in_battle then
            battle_start_timestamp = current_time
            is_in_battle = true
        end
        current_time = battle_start_timestamp
    else
        is_in_battle = false
        battle_start_timestamp = nil
    end
    
    local state = {
        in_match = in_match or false,
        p1_character = p1_char,
        p2_character = p2_char,
        game_mode = game_mode,
        timestamp = current_time
    }
    
    saveGameState(state)
end

function deleteRPCFile()
    local success = os.remove("tekken8_discord_rpc.json")
    if success then
        print("Discord RPC file deleted")
    else
        print("Failed to delete Discord RPC file (file may not exist)")
    end
end

NotifyOnNewObject("/Script/UMG.UserWidget", function(widget)
    local name = widget:GetFullName()
    
    if string.find(name, "WBP_UI_CharSelect_C") and not string.find(name, "Timer") then
        updateGameState("character_select", false)
    elseif string.find(name, "WBP_UI_StageSelect_C") then
        updateGameState("stage_select", false)
    elseif string.find(name, "WBP_UI_SideSelect_C") then
        updateGameState("side_select", false)
    elseif string.find(name, "WBP_UI_PM_SessionRoom_C") then
        updateGameState("session_room", false)
    elseif string.find(name, "WBP_UI_Practice_S2_C") then
        ExecuteWithDelay(1000, function()
            updateGameState("practice", true)
        end)
    end
end)

-- 메인 메뉴
NotifyOnNewObject("/Script/Polaris.PolarisUMGMainMenu", function()
    updateGameState("main_menu", false)
end)

-- 로딩 화면
NotifyOnNewObject("/Script/Polaris.PolarisUMGMakuai", function(makuai)
    ExecuteWithDelay(1000, function()
        local p1_char, p2_char = "unknown", "unknown"
        
        for i = 1, 2 do
            local character_name_texture
            if i == 1 then
                character_name_texture = makuai.Rep_T_UI_Makuai_Character_Name_L
            else
                character_name_texture = makuai.Rep_T_UI_Makuai_Character_Name_R
            end
            
            if character_name_texture and character_name_texture:IsValid() then
                local material_instance = character_name_texture.Brush.ResourceObject
                local texture = material_instance:K2_GetTextureParameterValue(FName("MainTexture"))
                local char_code = getCharacterCodeFromTexture(texture)
                
                if char_code and character_codes[char_code] then
                    if i == 1 then p1_char = character_codes[char_code]
                    else p2_char = character_codes[char_code] end
                end
            end
        end
        
        local state = {
            in_match = false,
            p1_character = p1_char,
            p2_character = p2_char,
            game_mode = "loading",
            timestamp = os.time()
        }
        saveGameState(state)
    end)
end)

-- 중복 방지
NotifyOnNewObject("/Script/Polaris.PolarisUMGHudGauge", function()
    if hook_registered then return end
    hook_registered = true
    
    RegisterHook("/Game/UI/Widget/HUD/S2/WBP_UI_HUD_Player_S2.WBP_UI_HUD_Player_S2_C:SetZoneChainVisibility", function()
        -- 딜레이를 줘서 한 번만 실행되도록
        ExecuteWithDelay(500, function()
            local p1_char, p2_char = collectCharacterInfo()
            
            if p1_char ~= "unknown" then
                local battle_mode = (p2_char == "unknown") and "practice" or "battle"
                updateGameState(battle_mode, true)
            end
        end)
    end)
end)

NotifyOnNewObject("/Script/Polaris.PolarisUMGResultNew", function()
    is_in_battle = false
    battle_start_timestamp = nil
    
    local state = {
        in_match = false,
        p1_character = last_logged_state and last_logged_state.p1_character or "unknown",
        p2_character = last_logged_state and last_logged_state.p2_character or "unknown",
        game_mode = "result",
        timestamp = os.time()
    }
    saveGameState(state)
end)

-- json 삭제 명령어
-- RegisterConsoleCommandGlobalHandler("rpc_cleanup", {}, function()
--     deleteRPCFile()
--     return "Discord RPC file deleted"
-- end)

-- 상태표시 명령어
RegisterConsoleCommandGlobalHandler("rpc_status", {}, function()
    if last_logged_state then
        return "Current state: " .. last_logged_state.game_mode .. " | " .. last_logged_state.p1_character .. " vs " .. last_logged_state.p2_character
    else
        return "No RPC data available"
    end
end)

-- 이니셜
print("=== Tekken 8 Discord RPC Started ===")
local initialState = {
    in_match = false,
    p1_character = "unknown",
    p2_character = "unknown",
    game_mode = "startup",
    timestamp = os.time()
}
saveGameState(initialState)