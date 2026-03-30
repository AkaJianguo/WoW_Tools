import time
import ctypes
import sys
from pynput import keyboard
from core.scanner import PaladinScanner
from core.logic_engine import RotationLogic
from core.execution_engine import burst_engine

# 1. 开启 Windows 高精度计时 (解决 9800X3D 频率过快导致的计时误差)
ctypes.WinDLL('winmm').timeBeginPeriod(1)

class JG_Engine:
    def __init__(self):
        self.scanner = PaladinScanner()
        self.logic = RotationLogic()
        self.running = True
        # F12 是 Python 层的硬性物理开关，按了之后脚本会进入休眠
        self.hk = keyboard.GlobalHotKeys({'<f12>': self.toggle_run})
        self.hk.start()

    def toggle_run(self):
        self.running = not self.running
        state = "▶️ [继续运行]" if self.running else "⏸️ [脚本暂停]"
        print(f"\n{state}")

    def run(self):
        print("\n" + "="*50)
        print("🛡️ [WoW-Pilot V3.2] 9800X3D 动力引擎已就绪！")
        print("💡 影子协议：左上角对齐 | F12:暂停 | Ctrl+C:关闭")
        print("="*50 + "\n")
        
        last_heartbeat = 0 

        while True:
            # 1. 物理开关判定
            if not self.running:
                time.sleep(0.2)
                continue

            t0 = time.perf_counter()
            
            # 2. 获取全量状态 (带 None 护盾)
            state = self.scanner.get_current_state()
            
            if state is None:
                # 如果扫描器崩溃或没抓到图，跳过这一帧
                time.sleep(0.01)
                continue

            # 3. 动态心跳反馈 (每 3 秒打印一次雷达现状)
            if t0 - last_heartbeat > 3.0:
                is_active = "✅ 激活" if state.get("active") else "💤 等待"
                holy_pwr = state.get("holy_power", 0)
                # 检查按键是否识别为 NONE
                keys_info = f"ST:{state.get('key_st')} AOE:{state.get('key_aoe')} Wake:{state.get('key_wake')}"
                print(f"[雷达] 状态: {is_active} | 豆子: {holy_pwr} | 识别: {keys_info}")
                last_heartbeat = t0

            # 4. 核心逻辑判断
            if state.get("active"):
                action = self.logic.get_next_action(state)
                
                if action:
                    # 获取技能名称和按键
                    skill = action.get("skill", "Unknown")
                    key = action.get("key", "NONE")
                    
                    if key != "NONE":
                        print(f"🔥 执行: {skill} -> [{key}]")
                        
                        # 调用执行引擎
                        # duration 代表按下持续时间，0.4s 对惩戒骑来说很稳
                        burst_engine.start_burst(key, duration=0.4)
                        
                        # --- 🛡️ 强制冷却 (最关键的一行) ---
                        # 防止 9800X3D 瞬间喷出几百个按键，模拟人类 0.5s 的反应间隔
                        # 如果你觉得手感太慢，可以改到 0.3
                        time.sleep(0.5) 
                    else:
                        # 识别到 NONE 时不按键，防止乱按
                        time.sleep(0.1)
                else:
                    # 逻辑引擎判断目前没技能打
                    time.sleep(0.01)

            # 5. 动态控频 (保持 200Hz 扫描频率)
            elapsed = time.perf_counter() - t0
            t_sleep = 0.005 - elapsed
            if t_sleep > 0:
                time.sleep(t_sleep)

if __name__ == "__main__":
    # 必须管理员运行，否则无法往游戏里发指令
    if ctypes.windll.shell32.IsUserAnAdmin():
        try:
            engine = JG_Engine()
            engine.run()
        except KeyboardInterrupt:
            # 退出前关闭计时器
            ctypes.WinDLL('winmm').timeEndPeriod(1)
            print("\n👋 脚本已安全关闭。王建国，下次再战！")
            sys.exit(0)
    else:
        print("\n" + "!"*50)
        print("❌ 错误：请右键点击 PowerShell，选择【以管理员身份运行】！")
        print("!"*50 + "\n")
        input("按回车键退出...")