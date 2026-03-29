# @Version      : 1.2 (Pure Performance)
# @Author       : Jianguo
# @File         : main.py
# @Time         : 2026/3/29
import time
import signal
import sys
from core.scanner import PaladinScanner
from core.logic_engine import RotationLogic
from core.execution_engine import burst_engine

# --- 极致响应参数 ---
# 平稳期 (25Hz)，足以覆盖 1.5s 的 GCD
SCAN_INTERVAL_NORMAL = 0.04  
# 爆发期 (100Hz)，专门捕捉 12.0 圣光之锤的高亮瞬间
SCAN_INTERVAL_TURBO = 0.01   

class WoW_Pilot_Main:
    def __init__(self):
        print("🛡️ [WoW-Pilot] 正在载入圣殿骑士核心...")
        # 直接初始化核心组件，不碰硬盘日志
        self.scanner = PaladinScanner()  # 眼睛：MSS 极速采样
        self.logic = RotationLogic()    # 大脑：3.21 优先级判定
        self.running = True
        self.last_turbo_ts = 0

        # 捕获退出信号
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum, frame):
        print("\n🛑 引擎已关闭。再见，王健国！")
        self.running = False
        sys.exit(0)

    def run(self):
        print("🚀 圣光引擎已启动！请保持游戏处于无边框窗口模式。")

        while self.running:
            start_ts = time.time()

            # 1. 【感知】直接抓取显存像素，不读任何文件
            game_state = self.scanner.get_current_state()

            # 2. 【决策】根据 3.21 循环给出指令
            next_action = self.logic.get_next_action(game_state)

            # 3. 【执行】触发带随机抖动的物理按键
            if next_action:
                burst_engine.start_burst(next_action['key'], duration=0.5)

                # 4. 【Turbo 逻辑】针对圣洁鸣钟的极速响应
                if next_action['skill'] == "DivineToll":
                    self.last_turbo_ts = time.time()

            # --- 动态休眠控制 ---
            elapsed = time.time() - start_ts
            
            # 如果在鸣钟后的 2 秒爆发窗，全速运行 (100fps)
            if (time.time() - self.last_turbo_ts) < 2.0:
                current_interval = SCAN_INTERVAL_TURBO
            else:
                current_interval = SCAN_INTERVAL_NORMAL

            # 这里的计算是为了抵消代码运行本身的耗时
            sleep_time = max(0, current_interval - elapsed)
            time.sleep(sleep_time)

if __name__ == "__main__":
    pilot = WoW_Pilot_Main()
    pilot.run()