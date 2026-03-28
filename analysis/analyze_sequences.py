# @Version      : 1.0
# @Author       : Jianguo
# @File         : analyze_sequences.py
# @Time         :2026/3/25 16:00
import json
import pandas as pd
import os

# --- 配置区：定义你的“真按键”清单 ---
# 只有这些 ID 是你 3.21 循环需要通过像素触发的操作
MANUAL_SKILLS = {
    375576: "圣洁鸣钟",
    431398: "圣光之锤 (高亮)",
    427453: "圣光之锤 (基础)",
    383328: "最后审判",
    408385: "强化灰烬觉醒",
    255937: "灰烬觉醒 (基础)",
    53385: "愤怒之锤",
    20271: "审判",
    184575: "公正之剑",
    343527: "处决宣判",
    31884: "复仇之怒"
}

# 需要过滤掉的常见被动/自动触发 ID
PASSIVE_IDS = [1236942, 198137, 431398]  # 注意：有些 ID 既有手动也有自动，这里我们只在逻辑中区分


def run_pure_analysis():
    # 文件路径指向你的 data/reports 目录
    CASTS_FILE = 'reports/report_n4qHgZzwDkA1tWF2_casts_fight-55.json'

    if not os.path.exists(CASTS_FILE):
        print(f"❌ 错误：找不到文件 {CASTS_FILE}")
        return

    print("🚀 启动纯净序列拆解引擎...")

    with open(CASTS_FILE, 'r') as f:
        data = json.load(f)

    events = data.get('events', [])
    df = pd.DataFrame(events)

    # 1. 自动锁定你的 sourceID
    target_sid = df[df['abilityGameID'] == 375576]['sourceID'].value_counts().idxmax()
    print(f"✅ 锁定目标圣骑士 ID: {target_sid}")

    # 2. 【核心过滤】只保留手动按键事件
    # 过滤条件：sourceID 匹配 且 abilityGameID 在我们的手动清单里
    df_manual = df[
        (df['sourceID'] == target_sid) &
        (df['abilityGameID'].isin(MANUAL_SKILLS.keys()))
        ].sort_values('timestamp').reset_index(drop=True)

    # 3. 寻找“圣洁鸣钟”的索引位置
    toll_indices = df_manual[df_manual['abilityGameID'] == 375576].index

    print("-" * 50)
    print(f"📋 王健国，以下是剔除被动触发后的『真·手动连招』：")

    for i, idx in enumerate(toll_indices):
        # 提取敲钟后接下来的 3 个手动按键
        seq = df_manual.iloc[idx + 1: idx + 4]

        skill_names = []
        intervals = []
        last_ts = df_manual.iloc[idx]['timestamp']

        for _, row in seq.iterrows():
            name = MANUAL_SKILLS.get(row['abilityGameID'], f"未知({row['abilityGameID']})")
            skill_names.append(name)
            # 计算 GCD 间隔 (毫秒)
            intervals.append(f"{row['timestamp'] - last_ts}ms")
            last_ts = row['timestamp']

        time_mark = round((df_manual.iloc[idx]['timestamp'] - df_manual.iloc[0]['timestamp']) / 1000, 1)

        # 输出格式：时间戳 | 技能序列 | GCD 间隔
        seq_str = " -> ".join(skill_names)
        gap_str = " | ".join(intervals)
        print(f"组 {i + 1:02} [{time_mark:>5}s]: 敲钟 -> {seq_str}")
        print(f"      └── GCD 间隔: {gap_str}")


if __name__ == "__main__":
    run_pure_analysis()