import mss
import numpy as np

class PaladinScanner:
    def __init__(self):
        self.sct = mss.mss()
        
        # --- 影子信号总线坐标 (坐标必须与 JGPilot.lua 中的像素点严格对应) ---
        # 建议游戏模式：窗口化全屏 (Windowed Fullscreen) 以保证 (0,0) 起始点准确
        self.points = {
            "active": (0, 0),    # P1: 总开关 (Blue)
            "burst":  (5, 0),    # P2: 爆发开关 (Red)
            "aoe":    (10, 0),   # P3: AOE模式 (Green)
            "potion": (15, 0),   # P4: 药水开关 (Yellow)
            "hp":     (20, 0),   # P5: 圣能豆子 (Grayscale)
            "proc":   (25, 0),   # P6: 高亮触发 (Cyan)
            "key_st": (30, 0),   # P7: 裁决按键 (Red ID)
            "key_aoe":(35, 0),   # P8: 风暴按键 (Red ID)
            "key_wake":(40, 0),  # P9: 灰烬按键 (Red ID)
            "key_ham": (45, 0),  # P10: 天锤按键 (Red ID)
            "hp_bus": (50, 0)    # P11: 复合血量总线 (RGB)
        }
        
        # 动作条按键映射表 (与 Lua 中的 Encode 函数对应)
        self.id_map = {
            10: "1", 20: "2", 30: "3", 40: "4", 50: "5",
            60: "Q", 70: "E", 80: "R", 90: "F", 100: "G", 110: "V"
        }

    def _get_rgb(self, x, y):
        """抓取像素并转换为原生 Python int，彻底杜绝 NumPy uint8 减法溢出问题"""
        rect = {"top": int(y), "left": int(x), "width": 1, "height": 1}
        # mss 返回 BGRA 格式
        raw = np.array(self.sct.grab(rect))[0, 0, :3]
        # 转换为 RGB 并强制转为 Python int
        return [int(raw[2]), int(raw[1]), int(raw[0])] 

    def _decode_key(self, x, y):
        """解码红色通道中的物理按键 ID"""
        rgb = self._get_rgb(x, y)
        r_val = rgb[0] 
        
        # 过滤黑点 (无技能或识别失败)
        if r_val < 5: return "NONE"
        
        # 寻找 ID 映射中最接近的值
        closest = min(self.id_map.keys(), key=lambda k: abs(k - r_val))
        # 容错范围 5 像素亮度值
        return self.id_map[closest] if abs(closest - r_val) < 5 else "NONE"

    def get_current_state(self):
        """核心：提取所有实时战术数据"""
        try:
            # 批量抓取关键像素点颜色
            active_rgb = self._get_rgb(*self.points["active"])
            burst_rgb  = self._get_rgb(*self.points["burst"])
            aoe_rgb    = self._get_rgb(*self.points["aoe"])
            hp_rgb     = self._get_rgb(*self.points["hp"])
            proc_rgb   = self._get_rgb(*self.points["proc"])
            bus_rgb    = self._get_rgb(*self.points["hp_bus"])

            state = {
                # 状态开关
                "active":     active_rgb[2] > 150,  # 蓝色通道控制激活
                "burst_mode": burst_rgb[0] > 150,   # 红色通道控制爆发
                "aoe_mode":   aoe_rgb[1] > 150,     # 绿色通道控制AOE
                
                # 资源与触发
                "proc_ready": proc_rgb[1] > 150 and proc_rgb[2] > 150, # 青色代表触发
                "holy_power": int((sum(hp_rgb)/3 / 255) * 5 + 0.5),    # 亮度换算圣能 (0-5)
                
                # P11 复合总线解码 (目标血量 / 熔断状态 / 阈值)
                "target_hp":      (bus_rgb[0] / 255) * 100, # R: 目标血量 %
                "melt_active":    bus_rgb[1] > 150,         # G: 熔断开关是否开启
                "melt_threshold": (bus_rgb[2] / 255) * 100, # B: 熔断阈值 %
                
                # 动态按键识别 (Key 名称与逻辑引擎逻辑严格对齐)
                "key_st":     self._decode_key(*self.points["key_st"]),
                "key_aoe":    self._decode_key(*self.points["key_aoe"]),
                "key_wake":   self._decode_key(*self.points["key_wake"]),
                "key_ham":    self._decode_key(*self.points["key_ham"])
            }
            return state

        except Exception as e:
            # 🛡️ 异常护盾：即使抓图失败，也返回一套“安全字典”，防止 main.py 报 NoneType 错误
            # print(f"⚠️ 扫描器感官暂时失灵: {e}")
            return {
                "active": False,
                "burst_mode": False,
                "aoe_mode": False,
                "proc_ready": False,
                "holy_power": 0,
                "target_hp": 100,
                "melt_active": False,
                "melt_threshold": 10,
                "key_st": "NONE", "key_aoe": "NONE", "key_wake": "NONE", "key_ham": "NONE"
            }