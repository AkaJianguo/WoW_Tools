# @Version      : 1.0
# @Author       : Jianguo
# @File         : analyze_321.py
# @Time         :2026/3/25 16:00
import json
import pandas as pd
from pathlib import Path

# --- 配置区 ---
CASTS_FILE = 'reports/report_n4qHgZzwDkA1tWF2_casts_fight-55.json'
RES_FILE = 'reports/report_n4qHgZzwDkA1tWF2_resources_fight-55.json'
SPELL_DIVINE_TOLL = 375576  # 圣洁鸣钟
SPELL_WAKE_OF_ASHES = 255937  # 灰烬觉醒 (用于定位惩戒骑)
RESOURCE_HOLY_POWER = 9  # WCL 中 9 代表圣能


def analyze_logic():
    print("🚀 正在启动 3.21 循环逻辑审计 (Intel MBP 加速模式)...")

    # 1. 加载 JSON 数据
    try:
        with open(CASTS_FILE, 'r') as f:
            casts_data = json.load(f)['events']
        with open(RES_FILE, 'r') as f:
            res_data = json.load(f)['events']
    except FileNotFoundError:
        print("❌ 错误：找不到 JSON 文件，请检查 reports/ 目录下的文件名。")
        return

    df_casts = pd.DataFrame(casts_data)
    df_res = pd.DataFrame(res_data)

    # 2. 自动锁定 sourceID：寻找施放“灰烬觉醒”次数最多的玩家
    paladin_stats = df_casts[df_casts['abilityGameID'] == SPELL_WAKE_OF_ASHES]['sourceID'].value_counts()
    if paladin_stats.empty:
        print("❌ 错误：在 log 中未找到惩戒骑特征技能。")
        return

    target_sid = paladin_stats.idxmax()
    print(f"✅ 已锁定核心惩戒骑 SourceID: {target_sid}")

    # 3. 提取该玩家的专项数据
    p_casts = df_casts[df_casts['sourceID'] == target_sid].copy()
    p_res = df_res[df_res['sourceID'] == target_sid].copy()

    # 4. 逻辑审计：针对“圣洁鸣钟”在圣能 <= 2 时释放的判定
    tolls = p_casts[p_casts['abilityGameID'] == SPELL_DIVINE_TOLL].copy()

    audit_results = []
    for _, row in tolls.iterrows():
        ts = row['timestamp']
        # 寻找释放瞬间前最后一次圣能记录
        prior_res = p_res[p_res['timestamp'] <= ts].sort_values('timestamp', ascending=False)

        if not prior_res.empty:
            current_hp = prior_res.iloc[0].get('resourceAmount', 0)
            # 3.21 核心判定逻辑
            is_valid = (current_hp <= 2)
            audit_results.append({
                "战斗时间(s)": round((ts - df_casts['timestamp'].min()) / 1000, 2),
                "释放前圣能": current_hp,
                "判定结果": "✅ 合规" if is_valid else "❌ 资源溢出"
            })

    # 5. 输出汇总报告
    report_df = pd.DataFrame(audit_results)
    success_rate = (report_df['释放前圣能'] <= 2).mean() * 100

    print("\n" + "=" * 40)
    print(f"📊 3.21 循环实战审计报告 (Fight 55)")
    print("=" * 40)
    print(report_df.to_string(index=False))
    print("-" * 40)
    print(f"🎯 逻辑符合度 (圣能 <= 2): {success_rate:.2f}%")
    print(f"💡 建议：{'继续保持，逻辑完美' if success_rate > 90 else '建议检查 3.21 配置中的优先级顺序'}")
    print("=" * 40)


if __name__ == "__main__":
    analyze_logic()