import time

class RotationLogic:
    def __init__(self):
        # 预设的基础产豆技能按键 (如果这几个技能也写了宏且带名字，可以改到 scanner 里自动识别)
        self.static_keys = {
            "Judgment": "Q",
            "BladeOfJustice": "E"
        }
        # 内部冷却记录，防止某些瞬间触发的技能在 0.4s 连发期间重叠（可选）
        self.last_wake_time = 0

    def get_next_action(self, s):
        """
        王建国 3.30 终极版 - 圣殿骑士 APL 逻辑
        s: 来自 scanner.py 的实时数据字典
        """
        # 1. 安全出口：总开关没开，脚本保持静默
        if not s['active']:
            return None

        # --- 【智能熔断判定】 ---
        # 满足三个条件：开关开启、目标血量 > 0（有目标）、目标血量 < 你在 UI 设定的阈值
        should_melt = s['melt_active'] and 0 < s['target_hp'] < s['melt_threshold']

        # --- 优先级 1：触发类大招 (圣光之锤 / Hammer of Light) ---
        # 逻辑：这种高亮触发是有时效性的，通常不进熔断，出了必打，伤害最高
        if s['proc_ready'] and s['key_ham'] != "NONE":
            return {"skill": "Hammer of Light", "key": s['key_ham']}

        # --- 优先级 2：长 CD 爆发 (灰烬觉醒 / Wake of Ashes) ---
        # 逻辑：只有当豆子 <= 1 时才考虑点火。
        if s['holy_power'] <= 1 and s['key_wake'] != "NONE":
            # 关键：检查熔断
            if should_melt:
                # 触发熔断，跳过灰烬觉醒，在控制台打印一条淡黄色的记录（可选）
                # print(f"🛑 [熔断] 目标仅剩 {s['target_hp']:.1f}%，节省灰烬觉醒以备下一波。")
                pass 
            else:
                return {"skill": "Wake of Ashes", "key": s['key_wake']}

        # --- 优先级 3：资源消耗 (Spend Holy Power) ---
        # 逻辑：豆子 >= 3 时，根据 Lua 传回的 AOE 信号切换技能
        if s['holy_power'] >= 3:
            # s['aoe_mode'] 是 Lua 自动数怪后传回的信号
            if s['aoe_mode'] and s['key_aoe'] != "NONE":
                return {"skill": "Divine Storm", "key": s['key_aoe']}
            elif s['key_st'] != "NONE":
                return {"skill": "Final Verdict", "key": s['key_st']}

        # --- 优先级 4：资源获取 (Generate Holy Power) ---
        # 逻辑：没豆子打时，优先打公正之剑，其次打审判
        # 提示：如果你的审判也绑了宏，可以让 scanner 识别后改写这里
        if s['holy_power'] < 5:
            # 假设你目前的产豆优先级是：公正之剑 > 审判
            return {"skill": "Generator (BoJ)", "key": self.static_keys["BladeOfJustice"]}

        return None