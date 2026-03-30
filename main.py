import time, ctypes
from core.scanner import PaladinScanner
from core.logic_engine import RotationLogic
from core.execution_engine import burst_engine
from pynput import keyboard

ctypes.WinDLL('winmm').timeBeginPeriod(1) # 开启高精度计时

class JG_Engine:
    def __init__(self):
        self.scanner = PaladinScanner()
        self.logic = RotationLogic()
        # F11 重校准，F12 紧急停止
        self.hk = keyboard.GlobalHotKeys({'<f11>': self.scanner.calibrate})
        self.hk.start()

    def run(self):
        print("🚀 9800X3D 圣殿骑士引擎启动！")
        while True:
            t0 = time.perf_counter()
            state = self.scanner.get_current_state()
            
            if state["active"]:
                action = self.logic.get_next_action(state)
                if action:
                    burst_engine.start_burst(action['key'], duration=0.4)

            # 9800X3D 极致控频：5ms (200Hz)
            t_sleep = 0.005 - (time.perf_counter() - t0)
            if t_sleep > 0: time.sleep(t_sleep)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin(): JG_Engine().run()
    else: print("❌ 请右键以管理员身份运行 PowerShell")