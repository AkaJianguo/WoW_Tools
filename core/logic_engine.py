# @Version      : 1.1 (9800X3D & 3.21 APL Optimized)
# @Author       : Jianguo
# @File         : logic_engine.py
# @Time         : 2026/03/30

from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass(slots=True)
class CombatState:
    """全面对齐 12.0 圣殿骑士状态"""
    holy_power: int = 0
    hammer_of_light_ready: bool = False
    target_in_range: bool = True
    
    # 状态字典：由 scanner.py 填充
    buffs: Dict[str, bool] = field(default_factory=lambda: {
        "avenging_wrath": False,
        "execution_sentence": False,
        "potion_ready": True
    })
    
    # 冷却字典：单位为秒 (0 代表就绪)
    cooldowns: Dict[str, float] = field(default_factory=lambda: {
        "divine_toll": 0,
        "wake_of_ashes": 0,
        "execution_sentence": 0,
        "avenging_wrath": 0
    })

class RotationLogic:
    """基于 SimC APL 与 3.21 审计结论的逻辑引擎"""

    def __init__(self, spell_config: Optional[Dict] = None):
        # 优先从 config/spells.json 读取按键，若无则使用默认
        self.keys = spell_config or {
            "HammerOfLight": "1",
            "DivineToll": "2",
            "WakeOfAshes": "3",
            "TemplarsVerdict": "4",
            "AvengingWrath": "5",
            "ExecutionSentence": "6",
            "Judgment": "Q",
            "BladeOfJustice": "E"
        }

    def get_next_action(self, state_dict: Dict) -> Optional[Dict]:
        """
        主入口：将 scanner 的字典转化为决策
        """
        # 1. 结构化数据
        s = CombatState(
            holy_power=state_dict.get('holy_power', 0),
            hammer_of_light_ready=state_dict.get('hammer_of_light_ready', False),
            buffs=state_dict.get('buffs', {}),
            cooldowns=state_dict.get('cooldowns', {})
        )

        if not state_dict.get('target_in_range', True):
            return None

        # --- 2. 3.21 爆发序列核心逻辑 (优先级从高到低) ---

        # A. 资源溢出保护：5 圣能强制泄能
        if s.holy_power >= 5:
            return self._action("TemplarsVerdict")

        # B. 英雄天赋最高优先级：圣光之锤 (Hammer of Light)
        # 条件：高亮触发，且处决宣判已挂上或正在爆发期
        if s.hammer_of_light_ready:
            return self._action("HammerOfLight")

        # C. 爆发启动：复仇之怒 (Avenging Wrath)
        # 审计结论：圣能 >= 3 时开启效果最佳
        if s.holy_power >= 3 and s.cooldowns.get('avenging_wrath', 0) == 0:
            if not s.buffs.get('avenging_wrath'):
                return self._action("AvengingWrath")

        # D. 建立容器：处决宣判 (Execution Sentence)
        # 条件：翅膀已开，圣能 >= 3
        if s.buffs.get('avenging_wrath') and s.cooldowns.get('execution_sentence', 0) == 0:
            if not s.buffs.get('execution_sentence'):
                return self._action("ExecutionSentence")

        # E. 填充容器：灰烬觉醒 (Wake of Ashes)
        # 条件：处决宣判已挂上，这是起手 0:03 秒的核心 Combo
        if s.buffs.get('execution_sentence') and s.cooldowns.get('wake_of_ashes', 0) == 0:
            # 这里逻辑上会触发爆发药水，药水建议绑在灰烬宏里以节省 Python 响应时间
            return self._action("WakeOfAshes")

        # F. 补能核心：圣洁鸣钟 (Divine Toll)
        # 审计结论：0-2 圣能时使用收益最高，防止圣能浪费
        if s.holy_power <= 2 and s.cooldowns.get('divine_toll', 0) == 0:
            return self._action("DivineToll")

        # G. 常规产生技 (Priority Builders)
        if s.holy_power < 3:
            # 这里的顺序可根据 SimC APL 实时调整
            return self._action("BladeOfJustice") if s.cooldowns.get('blade_of_justice', 0) == 0 else self._action("Judgment")

        # H. 保底泄能
        if s.holy_power >= 3:
            return self._action("TemplarsVerdict")

        return None

    def _action(self, skill_name: str) -> Dict:
        return {
            "skill": skill_name,
            "key": self.keys.get(skill_name, "1")
        }