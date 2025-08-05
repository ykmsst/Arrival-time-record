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
bin_width = 0.05  # ヒストグラムビン幅
# 出力先フォルダ（絶対パスで指定）
out_dir = os.path.abspath("./output_histograms")
print(f"Output directory: {out_dir}")
os.makedirs(out_dir, exist_ok=True)

json_path = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/Wave_Check/click_table_summary.json"
class_csv = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/classify/station_event_classification.csv"
bin_width = 0.05  # ヒストグラムビン幅
out_dir = "output_histograms"
os.makedirs(out_dir, exist_ok=True)

# ==== 方位分類関数 ====
def classify_azimuth(deg):
    if pd.isna(deg): return np.nan
    deg = deg % 360
    if deg >= 337.5 or deg < 22.5: return "N"
    elif deg < 67.5:  return "NE"
    elif deg < 112.5: return "E"
    elif deg < 157.5: return "SE"
    elif deg < 202.5: return "S"
    elif deg < 247.5: return "SW"
    elif deg < 292.5: return "W"
    else:             return "NW"

# ==== データ読み込み ==== 
if not os.path.exists(json_path): sys.exit(f"Error: JSON not found: {json_path}")
with open(json_path, 'r', encoding='utf-8') as f: click_data = json.load(f)
if not os.path.exists(class_csv): sys.exit(f"Error: CSV not found: {class_csv}")
df_class = pd.read_csv(class_csv)

# ==== カラムリネーム & 重複除去 ====
colmap = {}
# station, event
if 'station_name' in df_class.columns: colmap['station_name']='Station'
elif 'Station' in df_class.columns: colmap['Station']='Station'
if 'place' in df_class.columns:        colmap['place']='Event'
elif 'Event' in df_class.columns:      colmap['Event']='Event'
# 方位角（生）
if 'azimuth_deg' in df_class.columns:    colmap['azimuth_deg']='Azimuth'
elif 'azimuth' in df_class.columns:      colmap['azimuth']='Azimuth'
# 方位クラス
if 'azimuth_class' in df_class.columns:  colmap['azimuth_class']='AzClass'
# 深度
if 'depth' in df_class.columns:          colmap['depth']='Depth'
# 深度クラス
if 'depth_class' in df_class.columns:    colmap['depth_class']='DepthClass'
# 傾斜角
if 'dip' in df_class.columns:            colmap['dip']='Dip'
# 傾斜クラス
if 'dip_class' in df_class.columns:      colmap['dip_class']='DipClass'

if not colmap:
    sys.exit('No columns to rename')

# リネーム実行
print('Column rename map:', colmap)
df_class = df_class.rename(columns=colmap)
print('Renamed df_class columns:', df_class.columns.tolist())
# 重複除去
if 'Station' not in df_class.columns or 'Event' not in df_class.columns:
    sys.exit('Station or Event column missing')
df_class = df_class.drop_duplicates(subset=['Station','Event'], keep='first')
colmap = {}
if 'station_name' in df_class.columns: colmap['station_name']='Station'
elif 'Station' in df_class.columns:     colmap['Station']='Station'
if 'place' in df_class.columns:        colmap['place']='Event'
elif 'Event' in df_class.columns:       colmap['Event']='Event'
if 'azimuth_deg' in df_class.columns:    colmap['azimuth_deg']='Azimuth'
if 'dip' in df_class.columns:           colmap['dip']='Dip'
if 'depth' in df_class.columns:         colmap['depth']='Depth'
if not colmap: sys.exit('No columns to rename')
df_class = df_class.rename(columns=colmap)
df_class = df_class.drop_duplicates(subset=['Station','Event'], keep='first')

# ==== 属性クラス追加 ====
if 'Azimuth' in df_class.columns:
    df_class['AzDir'] = df_class['Azimuth'].apply(classify_azimuth)
if 'Depth' in df_class.columns:
    def classify_depth(d):
        if pd.isna(d): return np.nan
        if d < 50: return '0-50'
        if d < 100: return '50-100'
        return '100+'
    df_class['DepthClass'] = df_class['Depth'].apply(classify_depth)
if 'Dip' in df_class.columns:
    df_class['DipClass'] = df_class['Dip']

# ==== クリック差分 Flatten ====
stations = ['v.ska2','v.sft2','v.skd2','v.skrd','v.skrb','v.skrc']
def diff(a,b): return (a-b) if (a is not None and b is not None) else np.nan
rows=[]
for evt, ev in click_data.items():
    for st, sd in ev.items():
        if st not in stations: continue
        lu, ln, le = sd['left'].get('u'), sd['left'].get('n'), sd['left'].get('e')
        ru, rn, re = sd['right'].get('u'), sd['right'].get('n'), sd['right'].get('e')
        rows.append({'Station':st,'Event':evt,
                     'left_n-u': diff(ln, lu),'left_e-u': diff(le, lu),
                     'right_n-u': diff(rn, ru),'right_e-u': diff(re, ru)})
all_df = pd.DataFrame(rows)
all_df.to_csv('all_stations_delta_table.csv', index=False)

# ==== マージ ====
extras = [c for c in ['AzDir','DepthClass','DipClass'] if c in df_class.columns]
if not extras: sys.exit('No classification columns found')
merged = pd.merge(all_df, df_class[['Station','Event'] + extras], on=['Station','Event'], how='left', validate='m:1')

# ==== ヒストグラム描画関数 ====
params = [('left_n-u','Left Δ(n-u)'),('left_e-u','Left Δ(e-u)'),
          ('right_n-u','Right Δ(n-u)'),('right_e-u','Right Δ(e-u)')]
def plot_hist(df, title_pref, fname):
    vals = [df[col].dropna() for col,_ in params]
    vals = [v for v in vals if not v.empty]
    mn = min(v.min() for v in vals)
    mx = max(v.max() for v in vals)
    mn, mx = np.floor(mn/bin_width)*bin_width, np.ceil(mx/bin_width)*bin_width
    bins = np.arange(mn, mx+bin_width, bin_width)
    counts = [np.histogram(df[col].dropna(), bins=bins)[0] for col,_ in params]
    ymax = int(max(cnt.max() for cnt in counts))
    
    fig, axes = plt.subplots(2,2, figsize=(10,6))
    fig.suptitle(title_pref, fontsize=14)
    for (col,ttl), ax in zip(params, axes.flatten()):
        data = df[col].dropna()
        if data.empty:
            ax.set_visible(False)
            continue
        ax.hist(data, bins=bins, edgecolor='black')
        ax.set_xlim(mn, mx)
        ax.set_ylim(0, ymax)
        ax.set_title(ttl)
        ax.set_xlabel('Time diff [s]')
        ax.set_ylabel('Count')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.tight_layout(rect=[0,0.03,1,0.95])
    out_path = os.path.join(out_dir, fname)
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")

# ==== 各方位ごとに深度クラス・仰角クラスをプロット ====
if 'AzDir' in merged.columns:
    for direction in merged['AzDir'].dropna().unique():
        sub = merged[merged['AzDir']==direction]
        print(f"Processing direction: {direction}")
        # 深度クラス別
        if 'DepthClass' in sub.columns:
            for dcls in sub['DepthClass'].dropna().unique():
                df_sub = sub[sub['DepthClass']==dcls]
                print(f" - DepthClass: {dcls}, n={len(df_sub)}")
                if not df_sub.empty:
                    plot_hist(df_sub, f"Az={direction} Depth={dcls}", f"hist_Az_{direction}_Depth_{dcls}.png")
        # 仰角クラス別
        if 'DipClass' in sub.columns:
            for icls in sub['DipClass'].dropna().unique():
                df_sub = sub[sub['DipClass']==icls]
                print(f" - DipClass: {icls}, n={len(df_sub)}")
                if not df_sub.empty:
                    plot_hist(df_sub, f"Az={direction} Dip={icls}", f"hist_Az_{direction}_Dip_{icls}.png")
