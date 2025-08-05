import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# JSON ファイルのパス
json_path = "click_table_summary.json"

# JSON 読み込み（存在しない場合は空辞書）
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        click_data = json.load(f)
else:
    click_data = {}

stations = ['v.ska2', 'v.sft2', 'v.skd2', 'v.skrd', 'v.skrb', 'v.skrc']
components = ['u', 'n', 'e']

# ヒストグラムのビン幅（横軸の幅）をここで調整してください
bin_width = 0.05  # 例：0.5秒刻み、適宜変更

# --- 差分を計算する関数 ---
def diff(a, b):
    return (a - b) if (a is not None and b is not None) else np.nan

# 観測点ごとの DataFrame を格納する辞書
station_dfs = {}
# 全観測点まとめ用のリスト
all_rows = []

# ===== 観測点ごとの処理 =====
for station in stations:
    rows = []

    for event_name, event_data in click_data.items():
        if station not in event_data:
            continue
        
        station_data = event_data[station]

        # 左クリック raw
        left_u = station_data["left"]["u"]
        left_n = station_data["left"]["n"]
        left_e = station_data["left"]["e"]

        # 右クリック raw
        right_u = station_data["right"]["u"]
        right_n = station_data["right"]["n"]
        right_e = station_data["right"]["e"]

        # 差分計算
        left_un  = diff(left_n, left_u)
        left_ue  = diff(left_e, left_u)
        right_un = diff(right_n, right_u)
        right_ue = diff(right_e, right_u)

        # 観測点ごと用の行（raw + diff 両方）
        rows.append({
            "Event": event_name,
            "left_u": left_u, "left_n": left_n, "left_e": left_e,
            "right_u": right_u, "right_n": right_n, "right_e": right_e,
            "left_n-u": left_un, "left_e-u": left_ue,
            "right_n-u": right_un, "right_e-u": right_ue
        })

        # 全観測点まとめ用の行（stationも含める）
        all_rows.append({
            "Station": station,
            "Event": event_name,
            "left_u": left_u, "left_n": left_n, "left_e": left_e,
            "right_u": right_u, "right_n": right_n, "right_e": right_e,
            "left_n-u": left_un, "left_e-u": left_ue,
            "right_n-u": right_un, "right_e-u": right_ue
        })

    # ---- 観測点ごとの DataFrame ----
    df = pd.DataFrame(rows)
    station_dfs[station] = df

    print(f"\n=== {station} の Δ表（raw + diff）===")
    print(df)

    # ---- CSV で保存 ----
    csv_name = f"delta_{station.replace('.', '_')}.csv"
    df.to_csv(csv_name, index=False)
    print(f"✅ {csv_name} を保存しました")

    # ---- 観測点ごとのヒストグラム ----
    if not df.empty:
        fig, axes = plt.subplots(2, 2, figsize=(10, 6))
        fig.suptitle(f"{station} Δ histogram")

        # 各データ列のリストとタイトル
        hist_params = [
            ("left_n-u",     "Left Click Δ(n-u)",     axes[0, 0]),
            ("left_e-u",     "Left Click Δ(e-u)",     axes[0, 1]),
            ("right_n-u",    "Right Click Δ(n-u)",    axes[1, 0]),
            ("right_e-u",    "Right Click Δ(e-u)",    axes[1, 1]),
        ]

        for col, title, ax in hist_params:
            data = df[col].dropna()
            if data.empty:
                continue
            # ビンのレンジをデータ範囲 + bin_width で計算
            min_edge = np.floor(data.min() / bin_width) * bin_width
            max_edge = np.ceil(data.max() / bin_width) * bin_width
            bins = np.arange(min_edge, max_edge + bin_width, bin_width)

            ax.hist(data, bins=bins, edgecolor='black')
            ax.set_title(title)
            ax.set_xlabel("Time difference [s]")
            ax.set_ylabel("Count")
            ax.set_ylim(0, 25)  # Y軸の上限を固定

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # suptitle 分スペース確保

        # 画像保存
        img_name = f"hist_{station.replace('.', '_')}.png"
        plt.savefig(img_name, dpi=200)
        print(f"📊 {img_name} を保存しました")

        plt.show()

# ===== 6観測点まとめ版 =====
all_df = pd.DataFrame(all_rows)
print("\n=== 全観測点まとめ版 Δ表（raw + diff）===")
print(all_df)

# CSV で保存
all_df.to_csv("all_stations_delta_table.csv", index=False)
print("✅ all_stations_delta_table.csv を保存しました")

# ---- まとめヒストグラム ----
if not all_df.empty:
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle("All Stations Δ histogram")

    hist_params_all = [
        ("left_n-u",  "All Stations Left Δ(n-u)",  axes[0, 0]),
        ("left_e-u",  "All Stations Left Δ(e-u)",  axes[0, 1]),
        ("right_n-u", "All Stations Right Δ(n-u)", axes[1, 0]),
        ("right_e-u", "All Stations Right Δ(e-u)", axes[1, 1]),
    ]

    for col, title, ax in hist_params_all:
        data = all_df[col].dropna()
        if data.empty:
            continue
        min_edge = np.floor(data.min() / bin_width) * bin_width
        max_edge = np.ceil(data.max() / bin_width) * bin_width
        bins = np.arange(min_edge, max_edge + bin_width, bin_width)

        ax.hist(data, bins=bins, edgecolor='black')
        ax.set_title(title)
        ax.set_xlabel("Time difference [s]")
        ax.set_ylabel("Count")
        ax.set_ylim(0, 25)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # まとめヒストグラム保存
    plt.savefig("hist_all_stations.png", dpi=200)
    print("📊 hist_all_stations.png を保存しました")

    plt.show()
