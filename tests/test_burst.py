# @Version      : 1.0
# @Author       : Jianguo
# @File         : test_burst.py
# @Time         :2026/3/25 16:09

import time
import sys
import os

# 1. 确保脚本能跨文件夹找到 core 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.execution_engine import burst_engine
except ImportError:
    print("❌ 错误：找不到 core/execution_engine.py。")
    print("请确保你已经编写了执行引擎，否则测试无法运行。")
    sys.exit(1)


def run_pressure_test():
    print("🧪 [WoW-Pilot 压力测试] 启动！")
    print("=" * 50)
    print("📢 指令：")
    print("1. 请立刻在 Windows 任务栏打开一个空的『记事本』。")
    print("2. 点击记事本，确保光标正在闪烁。")
    print("3. 5 秒后，脚本将模拟『圣光之锤』的 1.0 秒极速爆发。")
    print("=" * 50)

    # 倒计时，给你切换窗口的时间
    for i in range(5, 0, -1):
        print(f"⏳ 倒计时: {i}...")
        time.sleep(1)

    print("\n🔥 开始连发！模拟按键: '1' (持续 1.0s)...")

    # 调用你的执行引擎
    # 模拟在 1.0 秒内疯狂按 '1'
    start_time = time.time()
    burst_engine.start_burst('1', duration=1.0)
    end_time = time.time()

    print(f"\n✅ 测试结束。执行总耗时: {end_time - start_time:.4f}s")
    print("=" * 50)
    print("🔍 审计结果说明：")
    print("- 频率检查：统计记事本里有几个 '1'。如果有 30-50 个，说明你的输出频率极高。")
    print("- 随机性检查：看 '1' 之间的间距。如果间距完全一样，会被封号；如果有快有慢，说明你的随机抖动算法完美。")
    print("- 系统负载：如果测试期间你的鼠标移动卡顿，请调低 execution_engine 里的连发频率。")


if __name__ == "__main__":
    run_pressure_test()