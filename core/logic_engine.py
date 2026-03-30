import time

class RotationLogic:
    def __init__(self):
        # 预设的基础技能按键 (如果这几个也写了宏，可以同样通过 scanner 自动识别)
        self.static_keys = {
            "Judgment": "Q",
            "BladeOfJustice": "E",
            "Wings": "5",               # 复仇之怒 (翅膀)
            "ExecutionSentence": "6"    # 处决宣判 (天锤)
        }

    def get_next_action(self, s):
        """
        王建国 3.30 终极圣殿骑士 APL
        s: 来自 scanner.py 的实时复合信号字典
        """
        # 1. 安全出口
        if not s['active']:
            return None

        # --- 【核心：智能熔断状态】 ---
        # 满足：熔断开关开启 + 目标血量 > 0 + 目标血量 < 设定阈值
        should_melt = s['melt_active'] and 0 < s['target_hp'] < s['melt_threshold']

        # --- 优先级 1：触发类大招 (圣光之锤) ---
        # 逻辑：时效性极强的高亮，不进熔断，出了必打。
        if s['proc_ready'] and s['key_ham'] != "NONE":
            return {"skill": "Hammer of Light", "key": s['key_ham']}

        # --- 优先级 2：处决宣判 (天锤) ---
        # 逻辑：3圣能以上 + 爆发开关开 + 非熔断状态
        # 为什么熔断：它需要8秒生效，残血砸下去等于浪费圣能。
        if s['holy_power'] >= 3 and s['burst_mode'] and not should_melt:
            # 这里假设 ES 是固定按键，如果也绑了识别宏，可改为 s['key_es']
            return {"skill": "Execution Sentence", "key": self.static_keys["ExecutionSentence"]}

        # --- 优先级 3：复仇之怒 (翅膀) ---
        # 逻辑：爆发开关开 + 非熔断状态
        # 为什么熔断：20秒的长Buff，为了3秒残血开翅膀会导致下一波断档。
        if s['burst_mode'] and not should_melt:
            return {"skill": "Avenging Wrath", "key": self.static_keys["Wings"]}

        # --- 优先级 4：灰烬觉醒 (点火/产豆) ---
        # 逻辑：豆子 <= 1 + 非熔断状态
        if s['holy_power'] <= 1 and s['key_wake'] != "NONE":
            if should_melt:
                # 记录熔断日志 (可选)
                # print(f"🛑 [熔断] 目标血量 {s['target_hp']:.1f}%，已节省灰烬觉醒。")
                pass 
            else:
                return {"skill": "Wake of Ashes", "key": s['key_wake']}

        # --- 优先级 5：资源消耗 (Spend) ---
        # 逻辑：豆子 >= 3 时，即使熔断也要把豆子打光，不带入脱战。
        if s['holy_power'] >= 3:
            if s['aoe_mode'] and s['key_aoe'] != "NONE":
                return {"skill": "Divine Storm", "key": s['key_aoe']}
            elif s['key_st'] != "NONE":
                return {"skill": "Final Verdict", "key": s['key_st']}

        # --- 优先级 6：常规获取 (Generate) ---
        # 逻辑：公正之剑 > 审判
        if s['holy_power'] < 5:
            # 这里的优先级可以根据你的 12.0 英雄天赋偏好互换
            return {"skill": "Generator (BoJ)", "key": self.static_keys["BladeOfJustice"]}

        return None