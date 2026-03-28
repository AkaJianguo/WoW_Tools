# @Version      : 1.0
# @Author       : Jianguo
# @File         : main.py
# @Time         :2026/3/25 16:18
import time
import signal
import sys
from core.scanner import PaladinScanner
from core.logic_engine import RotationLogic
from core.execution_engine import burst_engine

# --- 2019 Intel MBP 性能调优参数 ---
SCAN_INTERVAL_NORMAL = 0.05  # 平稳期扫描 (20fps)
SCAN_INTERVAL_TURBO = 0.01  # 敲钟后爆发扫描 (100fps)


class WoW_Pilot_Main:
    def __init__(self):
        print("🛡️ 王健国，正在初始化 3.21 圣殿骑士引擎...")
        self.scanner = PaladinScanner()  # 初始化扫描器 (MSS 局部采样)
        self.logic = RotationLogic()  # 初始化 3.21 逻辑引擎
        self.running = True

        # 捕获 Ctrl+C 优雅退出
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum, frame):
        print("\n🛑 正在安全关闭圣光引擎，再见王健国！")
        self.running = False
        sys.exit(0)

    def run(self):
        print("🚀 系统已启动！请切换回游戏界面。")

        while self.running:
            start_ts = time.time()

            # 1. 【感知层】获取当前像素状态
            # 只扫描你在 scanner.py 里定义的 ROI 区域
            game_state = self.scanner.get_current_state()

            # 2. 【决策层】应用 3.21 循环判定
            # 这里的决策会考虑 100% 审计出的“0 圣能敲钟”逻辑
            next_action = self.logic.get_next_action(game_state)

            # 3. 【执行层】触发物理按键
            if next_action:
                # 使用带随机抖动的爆发引擎，瞒天过海
                # duration 建议设为 0.4s-0.6s，确保填满服务器队列
                burst_engine.start_burst(next_action['key'], duration=0.5)

                # 如果刚才打的是“圣洁鸣钟”，临时进入 Turbo 模式
                if next_action['skill'] == "DivineToll":
                    self.turbo_mode = True
                    self.last_turbo_ts = time.time()

            # 4. 【性能平衡】动态休眠逻辑
            # 防止 Intel CPU 持续高频运行导致降频
            elapsed = time.time() - start_ts
            current_interval = SCAN_INTERVAL_NORMAL

            # 检查是否处于敲钟后的爆发期 (2秒内)
            if hasattr(self, 'last_turbo_ts') and (time.time() - self.last_turbo_ts < 2.0):
                current_interval = SCAN_INTERVAL_TURBO

            sleep_time = max(0, current_interval - elapsed)
            time.sleep(sleep_time)


if __name__ == "__main__":
    pilot = WoW_Pilot_Main()
    pilot.run()