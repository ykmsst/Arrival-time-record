import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from matplotlib.ticker import MaxNLocator

# ==== ユーザー設定 ====
json_path = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/Wave_Check/click_table_summary.json"
class_csv = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/classify/station_event_classification.csv"
bin_width = 0.05

# ==== 1) クリックデータ読み込み ====
if not os.path.exists(json_path):
    print(f"Error: JSONファイルが見つかりません: {json_path}", file=sys.stderr)
    sys.exit(1)
with open(json_path, "r", encoding="utf-8") as f:
    click_data = json.load(f)

# ==== 2) 分類CSV読み込み & カラム名リネーム ====
if not os.path.exists(class_csv):
    print(f"Error: 分類CSVが見つかりません: {class_csv}", file=sys.stderr)
    sys.exit(1)
df_class = pd.read_csv(class_csv, encoding="utf-8")
colmap = {}
if "station_name" in df_class.columns: colmap["station_name"] = "Station"
elif "Station" in df_class.columns: colmap["Station"] = "Station"
else: raise KeyError("分類CSVに'station_name'または'Station'がありません")
if "place" in df_class.columns: colmap["place"] = "Event"
elif "Event" in df_class.columns: colmap["Event"] = "Event"
else: raise KeyError("分類CSVに'place'または'Event'がありません")
if "azimuth_class" in df_class.columns: colmap["azimuth_class"] = "AzimuthClass"
elif "AzimuthClass" in df_class.columns: colmap["AzimuthClass"] = "AzimuthClass"
else: raise KeyError("分類CSVに'azimuth_class'または'AzimuthClass'がありません")
if "dip_class" in df_class.columns: colmap["dip_class"] = "DipClass"
elif "DipClass" in df_class.columns: colmap["DipClass"] = "DipClass"
else: raise KeyError("分類CSVに'dip_class'または'DipClass'がありません")
if "depth_km" in df_class.columns:
    colmap["depth_km"] = "Depth"
df_class = df_class.rename(columns=colmap)
df_class = df_class.drop_duplicates(subset=["Station","Event"], keep="first")

# ==== 3) クリック差分の flatten ====
rows = []
for event, ev in click_data.items():
    for station, sd in ev.items():
        lu, ln, le = sd["left"].get("u"), sd["left"].get("n"), sd["left"].get("e")
        ru, rn, re = sd["right"].get("u"), sd["right"].get("n"), sd["right"].get("e")
        def diff(a, b): return (a - b) if (a is not None and b is not None) else np.nan
        rows.append({
            "Station":    station,
            "Event":      event,
            "left_n-u":   diff(ln, lu),
            "left_e-u":   diff(le, lu),
            "right_n-u":  diff(rn, ru),
            "right_e-u":  diff(re, ru),
        })
all_df = pd.DataFrame(rows)
all_df.to_csv("all_stations_delta_table.csv", index=False)

# ==== 4) マージ & 深さ分類追加 ====
merged = pd.merge(
    all_df,
    df_class[["Station","Event","AzimuthClass","DipClass","Depth"]],
    on=["Station","Event"], how="left", validate="m:1"
)

def classify_depth(depth):
    if pd.isna(depth): return np.nan
    if depth < 50: return "0-50km"
    elif depth < 100: return "50-100km"
    else: return "100-km"

merged["DepthClass"] = merged["Depth"].apply(classify_depth)

# ==== 5) 統一レンジでヒストグラム描画関数 ====
def plot_group_hist(df, group_col, prefix):
    params = [
        ("left_n-u",  "Left Δ(n-u)"),
        ("left_e-u",  "Left Δ(e-u)"),
        ("right_n-u", "Right Δ(n-u)"),
        ("right_e-u", "Right Δ(e-u)"),
    ]
    for cls in df[group_col].dropna().unique():
        sub = df[df[group_col] == cls]
        all_vals = []
        for col, _ in params:
            data = sub[col].dropna()
            if not data.empty:
                all_vals.append(data)
        if not all_vals:
            continue
        global_min = min([v.min() for v in all_vals])
        global_max = max([v.max() for v in all_vals])
        mn = np.floor(global_min/bin_width)*bin_width
        mx = np.ceil(global_max/bin_width)*bin_width
        bins = np.arange(mn, mx + bin_width, bin_width)
        counts = [np.histogram(sub[col].dropna(), bins=bins)[0] for col, _ in params]
        ymax = int(np.max([cnt.max() for cnt in counts]))

        fig, axes = plt.subplots(2,2, figsize=(10,6))
        fig.suptitle(f"{group_col} = {cls} histograms", fontsize=16)
        for (col,title), ax in zip(params, axes.flatten()):
            data = sub[col].dropna()
            if data.empty:
                ax.set_visible(False)
                continue
            ax.hist(data, bins=bins, edgecolor="black")
            ax.set_xlim(mn, mx)
            ax.set_ylim(0, ymax)
            ax.set_title(title)
            ax.set_xlabel("Time difference [s]")
            ax.set_ylabel("Count")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        plt.tight_layout(rect=[0,0.03,1,0.95])
        fname = f"{prefix}_{group_col}_{cls}.png".replace(" ","_")
        plt.savefig(fname, dpi=200)
        print(f"📊 {fname} を保存しました")
        plt.close(fig)

# ==== 6) クラス別描画 ====
plot_group_hist(merged, "AzimuthClass", "hist_by_azimuth")
plot_group_hist(merged, "DipClass",     "hist_by_dip")
plot_group_hist(merged, "DepthClass",   "hist_by_depth")
