# @Version      : 1.0
# @Author       : Jianguo
# @File         : execution_engine.py
# @Time         :2026/3/25 16:02
import time
import random
import threading
from pynput.keyboard import Controller

# 初始化键盘控制器
keyboard = Controller()


class BurstLogicEngine:
    def __init__(self):
        self.is_bursting = False
        self.target_key = None
        self.burst_end_time = 0
        # 守护线程，随主程序启动
        self.thread = threading.Thread(target=self._send_burst_loop, daemon=True)
        self.thread.start()

    def _send_burst_loop(self):
        """核心执行循环：模拟真实人类在高压下的狂按行为"""
        while True:
            if self.is_bursting and time.time() < self.burst_end_time:
                if self.target_key:
                    # --- 模拟人类行为的三重随机化 ---

                    # 1. 模拟按键按下的深度/时长 (20ms - 45ms)
                    keyboard.press(self.target_key)
                    time.sleep(random.uniform(0.02, 0.045))
                    keyboard.release(self.target_key)

                    # 2. 模拟手指抬起准备下一次点击的间隙 (15ms - 40ms)
                    # 这个间隔决定了连发频率，范围在 15Hz-30Hz 左右波动
                    time.sleep(random.uniform(0.015, 0.04))

                    # 3. 概率性微小卡顿 (模拟人手偶尔的疲劳或系统微抖动)
                    if random.random() < 0.05:  # 5% 的几率产生一次稍长的延迟
                        time.sleep(random.uniform(0.05, 0.1))
            else:
                self.is_bursting = False
                # 闲时休眠，降低 CPU 占用，防止你的 Intel MBP 过热
                time.sleep(0.1)

    def start_burst(self, key_char, duration=0.5):
        """
        王健国，调用此函数开启『圣殿骑士』爆发排队模式
        :param key_char: 技能绑定的物理按键
        :param duration: 建议设为 0.5s，正好覆盖一个 GCD 的排队窗
        """
        # 只有当新指令优先级更高或者当前不在爆发时才重置
        self.target_key = key_char
        self.burst_end_time = time.time() + duration
        self.is_bursting = True
        # 调试用（实战时建议注释掉）
        # print(f"🔥 [Stealth Burst] 目标:[{key_char}] 剩余:{duration}s")


# 实例化
burst_engine = BurstLogicEngine()