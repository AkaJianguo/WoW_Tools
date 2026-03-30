# @Version      : 1.3 (9800X3D Optimized)
# @Author       : Jianguo
# @File         : main.py
# @Time         : 2026/03/30
import time
import signal
import sys
import ctypes
from pathlib import Path

# 导入你的核心模块
try:
    from core.scanner import PaladinScanner
    from core.logic_engine import RotationLogic
    from core.execution_engine import burst_engine
except ImportError as e:
    print(f"❌ 启动失败：模块导入错误 -> {e}")
    print("请确保 core/ 文件夹下有 scanner.py, logic_engine.py 和 execution_engine.py")
    sys.exit(1)

# --- Windows 高精度计时器设置 ---
# 9800X3D 性能极强，我们将系统计时器精度从默认的 15.6ms 提升至 1ms
winmm = ctypes.WinDLL('winmm')
winmm.timeBeginPeriod(1)

# --- 巅峰性能参数 ---
SCAN_INTERVAL_NORMAL = 0.015  # 平稳期扫描 (~66Hz)
SCAN_INTERVAL_TURBO = 0.005  # 爆发期扫描 (200Hz! 专门对齐圣光之锤和 0 圣能鸣钟)


class WoW_Pilot_Main:
    def __init__(self):
        print("🛡️ [WoW-Pilot] 正在初始化 12.0 圣殿骑士引擎 (9800X3D 模式)...")

        # 1. 初始化核心组件
        self.scanner = PaladinScanner()  # 眼睛：基于 MSS 的极速采样
        self.logic = RotationLogic()  # 大脑：3.21 优先级判定
        self.running = True
        self.last_turbo_ts = 0  # 爆发窗记录

        # 2. 捕获退出信号 (Ctrl+C)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum, frame):
        """优雅退出逻辑"""
        print("\n🛑 正在释放资源并关闭圣光引擎...")
        winmm.timeEndPeriod(1)  # 恢复系统计时器精度
        self.running = False
        sys.exit(0)

    def run(self):
        print("🚀 引擎已启动！王健国，准备好统治 WCL 了吗？")
        print(f"💎 当前硬件优化：9800X3D 极速轮询模式开启")
        print("-" * 50)

        while self.running:
            # 记录起始时间用于高精度控频
            loop_start = time.perf_counter()

            # --- 步骤 1：感知 (Perception) ---
            # 抓取当前像素状态：圣能、翅膀 Buff、处决 Buff、技能高亮
            game_state = self.scanner.get_current_state()

            # --- 步骤 2：决策 (Decision) ---
            # 应用 3.21 循环逻辑，返回动作指令 {"skill": "xxx", "key": "x"}
            next_action = self.logic.get_next_action(game_state)

            # --- 步骤 3：执行 (Execution) ---
            if next_action:
                # 触发 0.4s-0.6s 的带随机抖动连发，确保指令进入服务器队列
                burst_engine.start_burst(next_action['key'], duration=0.5)

                # --- 爆发窗逻辑：圣洁鸣钟/翅膀开启/灰烬觉醒 触发 Turbo ---
                if next_action['skill'] in ["DivineToll", "AvengingWrath", "WakeOfAshes"]:
                    self.last_turbo_ts = time.perf_counter()
                    print(f"⚡ 进入爆发窗：{next_action['skill']} 已触发")

            # --- 步骤 4：动态频率控制 (9800X3D 优化) ---
            elapsed = time.perf_counter() - loop_start

            # 判定条件：处决宣判期间或手动设定的 3 秒爆发窗口
            is_in_burst = (time.perf_counter() - self.last_turbo_ts) < 3.0
            is_wings_up = game_state.get('buffs', {}).get('avenging_wrath', False)

            if is_in_burst or is_wings_up:
                current_interval = SCAN_INTERVAL_TURBO
            else:
                current_interval = SCAN_INTERVAL_NORMAL

            # 9800X3D 性能强劲，我们使用忙等 (Busy Wait) 来确保极高精度
            # 这种写法比普通的 time.sleep 更准，且你的 CPU 负载完全扛得住
            target_time = loop_start + current_interval
            while time.perf_counter() < target_time:
                pass  # 毫秒级精准对齐


if __name__ == "__main__":
    # 检查是否以管理员身份运行（模拟按键需要）
    if ctypes.windll.shell32.IsUserAnAdmin():
        pilot = WoW_Pilot_Main()
        pilot.run()
    else:
        print("❌ 错误：请使用『管理员身份』运行终端，否则无法模拟按键。")
        sys.exit(1)