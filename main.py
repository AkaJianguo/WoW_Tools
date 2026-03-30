import time
import ctypes
from pynput import keyboard
from core.scanner import PaladinScanner
from core.logic_engine import RotationLogic
from core.execution_engine import burst_engine

# 1. 开启 Windows 高精度计时
ctypes.WinDLL('winmm').timeBeginPeriod(1)

class JG_Engine:
    def __init__(self):
        self.scanner = PaladinScanner()
        self.logic = RotationLogic()
        self.running = True
        self.hk = keyboard.GlobalHotKeys({'<f12>': self.toggle_run})
        self.hk.start()

    def toggle_run(self):
        self.running = not self.running
        state = "▶️ [继续运行]" if self.running else "⏸️ [脚本暂停]"
        print(f"\n{state}")

    def run(self):
        print("🛡️ [WoW-Pilot V3.1] 9800X3D 动力引擎已启动！")
        print("💡 影子协议：锁死坐标 (0,0) | 模式：自动按键识别")
        
        last_heartbeat = 0 # 用于控制输出频率

        while True:
            if self.running:
                t0 = time.perf_counter()
                
                # 获取全量状态（包含自动识别的按键）
                state = self.scanner.get_current_state()
                
                # --- 新增：心跳反馈（每 3 秒打印一次，让你心里有底） ---
                if t0 - last_heartbeat > 3.0:
                    mode = "✅ 激活" if state["active"] else "💤 等待"
                    # 这里显示识别出的按键，方便你对齐
                    keys = f"裁决:{state.get('key_st')} 风暴:{state.get('key_aoe')} 灰烬:{state.get('key_wake')}"
                    print(f"[心跳] 状态: {mode} | 豆子: {state['holy_power']} | 识别: {keys}")
                    last_heartbeat = t0

                if state["active"]:
                    action = self.logic.get_next_action(state)
                    if action:
                        # --- 新增：技能日志，让你看到脚本在打什么 ---
                        print(f"🔥 执行: {action['skill']} -> [{action['key']}]")
                        
                        # 注意：如果你的 execution_engine 里函数名改成了 start，这里也要跟着改
                        # 这里沿用你代码里的 start_burst
                        burst_engine.start_burst(action['key'], duration=0.4)

                # 动态控频 (5ms)
                elapsed = time.perf_counter() - t0
                t_sleep = 0.005 - elapsed
                if t_sleep > 0:
                    time.sleep(t_sleep)
            else:
                time.sleep(0.1)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        try:
            JG_Engine().run()
        except KeyboardInterrupt:
            print("\n👋 脚本已手动关闭，战神辛苦了！")
    else:
        print("❌ 错误：请以管理员身份运行 PowerShell！")