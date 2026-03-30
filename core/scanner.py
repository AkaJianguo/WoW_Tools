
# @Version      : 1.0
# @Author       : Jianguo
# @File         : scanner.py
# @Time         :2026/3/25 16:01
import mss
import numpy as np


class PaladinScanner:
    def __init__(self):
        self.sct = mss.mss()

        # --- 核心坐标配置 (需根据你的 UI 微调) ---
        # 建议使用截屏工具量取技能图标中心的坐标
        self.roi_config = {
            "hammer_of_light": {"x": 800, "y": 950, "color": [255, 210, 0]},  # 金色高亮
            "divine_toll": {"x": 850, "y": 950, "color": [100, 150, 255]},  # 蓝色图标
            "wings_active": {"x": 750, "y": 800, "color": [255, 200, 50]},  # 翅膀 Buff 图标位置
            "execution_sent": {"x": 900, "y": 800, "color": [200, 100, 50]},  # 处决宣判 Buff 位置
        }

        # 圣能识别区（建议在游戏里用 WA 插件在固定位置显示 5 个色块）
        self.hp_coords = [
            (880, 910), (895, 910), (910, 910), (925, 910), (940, 910)
        ]

    def _get_pixel_color(self, x, y):
        """极速抓取单像素 RGB"""
        # 定义 1x1 的抓取区域
        rect = {"top": int(y), "left": int(x), "width": 1, "height": 1}
        img = np.array(self.sct.grab(rect))
        return img[0, 0, :3][::-1]  # BGRA 转 RGB

    def _is_color_match(self, current, target, threshold=40):
        """判断颜色是否在误差范围内"""
        return np.linalg.norm(current - target) < threshold

    def get_holy_power(self):
        """扫描圣能条，返回 0-5 的整数"""
        count = 0
        for coord in self.hp_coords:
            color = self._get_pixel_color(coord[0], coord[1])
            # 假设有能量时像素较亮 (均值 > 100)
            if np.mean(color) > 100:
                count += 1
        return count

    def get_current_state(self):
        """
        核心数据汇总：输出给 logic_engine.py
        对齐 WCL 0:02-0:05 起手序列
        """
        # 抓取关键状态
        is_hammer_ready = self._is_color_match(
            self._get_pixel_color(self.roi_config["hammer_of_light"]["x"], self.roi_config["hammer_of_light"]["y"]),
            self.roi_config["hammer_of_light"]["color"]
        )

        is_wings_up = self._is_color_match(
            self._get_pixel_color(self.roi_config["wings_active"]["x"], self.roi_config["wings_active"]["y"]),
            self.roi_config["wings_active"]["color"]
        )

        is_exec_up = self._is_color_match(
            self._get_pixel_color(self.roi_config["execution_sent"]["x"], self.roi_config["execution_sent"]["y"]),
            self.roi_config["execution_sent"]["color"]
        )

        return {
            "holy_power": self.get_holy_power(),
            "hammer_of_light_ready": is_hammer_ready,
            "buffs": {
                "avenging_wrath": is_wings_up,
                "execution_sentence": is_exec_up,
                "potion_ready": True  # 简化处理，可增加药水 CD 识别
            },
            "cooldowns": {
                "divine_toll": 0,  # 这里需要你增加图标变灰识别逻辑
                "wake_of_ashes": 0,
                "execution_sentence": 0
            }
        }