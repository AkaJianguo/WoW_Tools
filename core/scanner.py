import mss
import numpy as np

class PaladinScanner:
    def __init__(self):
        self.sct = mss.mss()
        # 影子信号总线协议 (坐标 X 轴每 5 像素一个点，锁死 Y=0)
        self.points = {
            "active": (0, 0),    # P1: 总开关
            "burst":  (5, 0),    # P2: 爆发
            "aoe":    (10, 0),   # P3: AOE模式 (智能/手动)
            "potion": (15, 0),   # P4: 药水
            "hp":     (20, 0),   # P5: 圣能
            "proc":   (25, 0),   # P6: 高亮触发
            "k_st":   (30, 0),   # P7: 裁决按键
            "k_aoe":  (35, 0),   # P8: 风暴按键
            "k_wake": (40, 0),   # P9: 灰烬按键
            "k_ham":  (45, 0),   # P10: 锤子按键
            "hp_bus": (50, 0)    # P11: 复合总线 (R:血量, G:熔断开关, B:阈值)
        }
        
        # 按键编码对照表 (必须与 Lua 中的 Encode 函数映射一致)
        self.id_map = {
            10: "1", 20: "2", 30: "3", 40: "4", 50: "5",
            60: "Q", 70: "E", 80: "R", 90: "F", 100: "G", 110: "V"
        }

    def _get_rgb(self, x, y):
        """利用 mss 极速抓取单像素"""
        rect = {"top": int(y), "left": int(x), "width": 1, "height": 1}
        # 转换 BGRA 为 RGB 数组
        img = np.array(self.sct.grab(rect))
        return img[0, 0, :3][::-1]

    def _decode_key(self, x, y):
        """解析红色通道中的按键 ID"""
        rgb = self._get_rgb(x, y)
        r_val = rgb[0]
        if r_val < 5: return "NONE"
        
        # 寻找最接近的编码 ID，允许小范围颜色误差
        closest = min(self.id_map.keys(), key=lambda k: abs(k - r_val))
        return self.id_map[closest] if abs(closest - r_val) < 5 else "NONE"

    def get_current_state(self):
        """一键提取艾泽拉斯所有实时战术数据"""
        # 1. 抓取关键像素
        active_rgb = self._get_rgb(*self.points["active"])
        aoe_rgb    = self._get_rgb(*self.points["aoe"])
        hp_rgb     = self._get_rgb(*self.points["hp"])
        proc_rgb   = self._get_rgb(*self.points["proc"])
        bus_rgb    = self._get_rgb(*self.points["hp_bus"]) # P11 复合总线

        # 2. 组装状态字典
        state = {
            "active":     active_rgb[2] > 150,  # 蓝色通道控制总开关
            "burst_mode": self._get_rgb(*self.points["burst"])[0] > 150,
            "aoe_mode":   aoe_rgb[1] > 150,     # 绿色通道控制 AOE 状态
            "proc_ready": proc_rgb[1] > 150 and proc_rgb[2] > 150, # 青色代表触发
            
            # 圣能：根据灰度亮度还原 (0-255 -> 0-5 豆)
            "holy_power": int((np.mean(hp_rgb) / 255) * 5 + 0.5),
            
            # --- P11 复合解码逻辑 ---
            "target_hp":      (bus_rgb[0] / 255) * 100,  # R通道：目标当前血量 %
            "melt_active":    bus_rgb[1] > 150,          # G通道：熔断开关是否开启
            "melt_threshold": (bus_rgb[2] / 255) * 100,  # B通道：你在 UI 设定的阈值 %
            
            # --- 按键自动识别 ---
            "key_st":     self._decode_key(*self.points["k_st"]),
            "key_aoe":    self._decode_key(*self.points["key_aoe"]),
            "key_wake":   self._decode_key(*self.points["key_wake"]),
            "key_ham":    self._decode_key(*self.points["key_ham"])
        }
        
        return state