# @Version      : 1.1 (9800X3D & Win Optimized)
# @Author       : Jianguo
# @File         : execution_engine.py
# @Time         : 2026/03/30
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
        # 9800X3D 性能强劲，可以把轮询线程优先级维持在最高水平
        self.thread = threading.Thread(target=self._send_burst_loop, daemon=True)
        self.thread.start()

    def _send_burst_loop(self):
        """核心执行循环：利用 9800X3D 的响应能力实现超高频模拟"""
        while True:
            # 改用 perf_counter() 获取微秒级精度
            current_time = time.perf_counter()

            if self.is_bursting and current_time < self.burst_end_time:
                if self.target_key:
                    # --- 模拟人类行为的三重随机化（针对 12.0 防检测优化） ---

                    # 1. 模拟按键按下的物理深度感 (18ms - 35ms)
                    # 9800X3D 能让这个区间更稳定地落在目标范围内
                    keyboard.press(self.target_key)
                    time.sleep(random.uniform(0.018, 0.035))
                    keyboard.release(self.target_key)

                    # 2. 模拟手指抬起的间隙 (12ms - 25ms)
                    # 连发频率约等于 20Hz-40Hz，完美对齐服务器 400ms 的法术排队窗
                    time.sleep(random.uniform(0.012, 0.025))

                    # 3. 概率性微小卡顿 (模拟操作干扰)
                    # 9800X3D 的 L3 缓存极大，几乎不会产生系统级掉帧，
                    # 这里的随机卡顿纯粹是为了骗过服务器的特征分析。
                    if random.random() < 0.03:
                        time.sleep(random.uniform(0.04, 0.08))
            else:
                self.is_bursting = False
                # 闲时休眠从 0.1s 压缩到 0.005s
                # 9800X3D 下这几乎不占 CPU，但能让你在 start_burst 调用后几乎瞬间开火
                time.sleep(0.005)

    def start_burst(self, key_char, duration=0.5):
        """
        开启爆发连发模式
        :param key_char: 技能绑定的物理按键
        :param duration: 默认 0.5s，确保在 GCD 结束前能填入多个请求
        """
        if not key_char:
            return

        self.target_key = key_char
        # 统一使用 perf_counter
        self.burst_end_time = time.perf_counter() + duration
        self.is_bursting = True


# 实例化单例模式
burst_engine = BurstLogicEngine()