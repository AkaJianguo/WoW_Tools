import mss
import numpy as np
from pynput import mouse

def get_pixel_color(x, y):
    """在函数内部初始化 mss，解决线程冲突问题"""
    with mss.mss() as sct:
        # 定义 1x1 像素的抓取区域
        rect = {"top": int(y), "left": int(x), "width": 1, "height": 1}
        img = np.array(sct.grab(rect))
        # mss 返回的是 BGRA，转换为 RGB
        color = img[0, 0, :3][::-1] 
        return color

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.left:
        try:
            color = get_pixel_color(x, y)
            print(f"📍 坐标拾取成功！")
            print(f"   - 屏幕坐标: ({int(x)}, {int(y)})")
            print(f"   - RGB 颜色: {list(color)}")
            print(f"   - 建议代码: np.max(color) > 150  (用于检测亮度)")
            print("-" * 40)
        except Exception as e:
            print(f"❌ 拾取失败: {e}")

def start_picker():
    print("🎯 [JGPilot 坐标拾取器] 已启动")
    print("📢 操作指令：")
    print("1. 请切换到魔兽世界窗口。")
    print("2. 鼠标『左键』点击你想识别的色块（如 JGPilot 插件的小方块）。")
    print("3. 控制台将输出精确的坐标和 RGB 值。")
    print("4. 按 Ctrl+C 或关闭终端退出。")
    print("-" * 50)
    
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

if __name__ == "__main__":
    start_picker()