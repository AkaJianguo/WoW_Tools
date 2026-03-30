# @Version      : 1.0
# @Author       : Jianguo
# @File         : picker.py
# @Time         :2026/3/30 15:12
import time
import mss
import numpy as np
from pynput import mouse

# 初始化极速截图
sct = mss.mss()

print("🎯 [校准工具] 启动成功！")
print("操作指南：")
print("1. 将游戏切换至『无边框窗口模式』。")
print("2. 移动鼠标到目标技能图标中心或圣能条位置。")
print("3. 【单击左键】锁定并打印该点的坐标和颜色。")
print("4. 按下 Ctrl+C 退出校准。\n")

def get_pixel_color(x, y):
    """获取指定坐标的 RGB 颜色"""
    # Windows 下 mss 处理高 DPI 缩放较好
    rect = {"top": int(y), "left": int(x), "width": 1, "height": 1}
    img = np.array(sct.grab(rect))
    return img[0, 0, :3][::-1].tolist()  # BGRA -> RGB

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.left:
        color = get_pixel_color(x, y)
        print("-" * 40)
        print(f"📍 坐标: (x={int(x)}, y={int(y)})")
        print(f"🎨 RGB: {color}")
        print(f"📝 建议配置: 'color': {color}")
        print("-" * 40)

# 开启鼠标监听
with mouse.Listener(on_click=on_click) as listener:
    try:
        while True:
            # 这里可以增加一个实时随动显示，如果你需要的话
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 校准结束。")