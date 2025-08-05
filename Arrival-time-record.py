%matplotlib widget
# Waveform Click Logger with Merge Save (既存JSONに追加)

import readwin32
import numpy as np
import matplotlib.pyplot as plt
from obspy import Stream, Trace, UTCDateTime
import os
import pandas as pd
import json
from collections import defaultdict

# --- 設定 ---
csv_path = "/workspaces/固体地球物理学講座/earthquake_data/earthquake_info@sakurajima/earthquake_info@sakurajima_add.csv"
base_dir = "/workspaces/固体地球物理学講座/earthquake_data/earthquake_info@sakurajima"

# CSV 読み込み
df = pd.read_csv(csv_path, parse_dates=["time"])

# --- 1) 日付で範囲指定する場合 ---
start_date = pd.to_datetime("2025-06-01 00:00:00")
end_date   = pd.to_datetime("2025-07-31 23:59:59")
df_date = df[(df["time"] >= start_date) & (df["time"] <= end_date)]

# --- 2) 行番号で範囲指定する場合（例えば 5 行目から 10 行目まで） ---
# df_index = df.iloc[4:10]  # Python の 0 始まりなので 5 行目はインデックス 4

# ここでは例として「日付範囲で絞り込んだ df_date」を使います
to_iterate = df_date  # 1) の場合
# to_iterate = df_index  # 2) の場合

# events_to_process の動的生成
events_to_process = []
for _, row in to_iterate.iterrows():
    dt = row["time"]
    dir_name = f"{dt.strftime('%Y%m%d_%H%M')}_{row['place'].replace(' ', '_')}"
    datadir = os.path.join(base_dir, dir_name)
    ch_fname = f"03_02_43_{dt.strftime('%Y%m%d')}.euc.ch"
    ch_filepath = os.path.join(datadir, ch_fname)
    events_to_process.append({
        "datadir": datadir,
        "ch_filepath": ch_filepath
    })

# 確認
for ev in events_to_process:
    print(ev)
    
    
stations = ['v.skd2']
components = ['u', 'n', 'e']

# JSONに保存するクリックテーブル
click_table = defaultdict(lambda: defaultdict(lambda: {"left": {c: None for c in components},
                                                       "right": {c: None for c in components}}))

# 新しいイベント分のクリックデータ（まだ保存してない分）
all_click_data = {}
# 表示する全図
figures = []

# === 保存先ディレクトリ ===
save_dir = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/Wave_Check"
os.makedirs(save_dir, exist_ok=True)  # ディレクトリがなければ作成


# === 既存JSONとマージして保存する関数 ===
def save_click_results():
    merged_click_data = {}
    merged_table = {}

    # 既存 clicked_times.json を読み込み
    if os.path.exists("clicked_times.json"):
        with open("clicked_times.json", "r", encoding="utf-8") as f:
            try:
                merged_click_data = json.load(f)
            except json.JSONDecodeError:
                merged_click_data = {}

    # 既存 click_table_summary.json を読み込み
    if os.path.exists("click_table_summary.json"):
        with open("click_table_summary.json", "r", encoding="utf-8") as f:
            try:
                merged_table = json.load(f)
            except json.JSONDecodeError:
                merged_table = {}

    # 新しいイベント分をマージ（既存は残し、同じイベントなら上書き）
    for ev, stations_data in all_click_data.items():
        if ev not in merged_click_data:
            merged_click_data[ev] = {}
        merged_click_data[ev].update(stations_data)

    for ev, stations_data in click_table.items():
        if ev not in merged_table:
            merged_table[ev] = {}
        merged_table[ev].update(stations_data)

    # 上書き保存
    with open("clicked_times.json", "w", encoding="utf-8") as f:
        json.dump(merged_click_data, f, ensure_ascii=False, indent=2)

    with open("click_table_summary.json", "w", encoding="utf-8") as f:
        json.dump(merged_table, f, ensure_ascii=False, indent=2)

    print("✅ 新しいイベントを既存データにマージして保存しました！（clicked_times.json / click_table_summary.json）")


# === 1つの図に対してイベントハンドラを設定する関数 ===
def setup_event_handlers(fig, axes, cursor_annotations, fixed_annotations,
                         left_click_times, right_click_times,
                         event_id, station):
    def on_mouse_move(evt):
        for i, ax in enumerate(axes):
            if evt.inaxes == ax:
                x, y = evt.xdata, evt.ydata
                if x is not None and y is not None:
                    cursor_annotations[i].xy = (x, y)
                    cursor_annotations[i].set_text(f"{x:.3f} s")
                    cursor_annotations[i].set_visible(True)
                else:
                    cursor_annotations[i].set_visible(False)
            else:
                cursor_annotations[i].set_visible(False)
        fig.canvas.draw_idle()

    def on_click(evt):
        for i, ax in enumerate(axes):
            if evt.inaxes == ax:
                x, y = evt.xdata, evt.ydata
                if x is not None and y is not None:
                    comp = components[i]
                    # 左クリック (1)
                    if evt.button == 1 and len(left_click_times[comp]) < 1:
                        left_click_times[comp].append(round(x, 3))
                        click_table[event_id][station]["left"][comp] = round(x, 3)
                    # 右クリック (3)
                    elif evt.button == 3 and len(right_click_times[comp]) < 1:
                        right_click_times[comp].append(round(x, 3))
                        click_table[event_id][station]["right"][comp] = round(x, 3)
                    else:
                        return
                    ann = ax.annotate(f"{x:.3f} s", xy=(x, y), xytext=(20, 20),
                                      textcoords='offset points', fontsize=9,
                                      bbox=dict(boxstyle="round", fc="lightyellow"),
                                      arrowprops=dict(arrowstyle="->"))
                    fixed_annotations.append(ann)
                fig.canvas.draw_idle()

    def on_key(evt):
        key = evt.key
        # Deleteで注釈削除
        if key == 'delete':
            for ann in fixed_annotations:
                ann.remove()
            fixed_annotations.clear()
            fig.canvas.draw_idle()
        # ←→↑↓で時間軸操作
        elif key in ['right', 'left', 'up', 'down']:
            base_ax = axes[0]
            xmin, xmax = base_ax.get_xlim()
            x_range = xmax - xmin
            if key == 'right':
                base_ax.set_xlim(xmin + x_range * 0.1, xmax + x_range * 0.1)
            elif key == 'left':
                base_ax.set_xlim(xmin - x_range * 0.1, xmax - x_range * 0.1)
            elif key == 'up':
                center = (xmin + xmax) / 2
                new_range = x_range / 1.2
                base_ax.set_xlim(center - new_range / 2, center + new_range / 2)
            elif key == 'down':
                center = (xmin + xmax) / 2
                new_range = x_range * 1.2
                base_ax.set_xlim(center - new_range / 2, center + new_range / 2)
            fig.canvas.draw_idle()
        # Shift+↑↓ で振幅拡大縮小（y=0基準）
        elif key in ['shift+up', 'shift+down']:
            ax = evt.inaxes
            if ax in axes:
                ymin, ymax = ax.get_ylim()
                y_center = 0
                y_range = ymax - ymin
                scale = 1/1.2 if key == 'shift+up' else 1.2
                new_range = y_range * scale
                new_ymin = y_center - new_range / 2
                new_ymax = y_center + new_range / 2
                ax.set_ylim(new_ymin, new_ymax)
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)


# === メイン処理 ===
for event in events_to_process:
    datadir = event['datadir']
    ch_filepath = event['ch_filepath']
    event_id = os.path.basename(datadir)

    try:
        filedata = readwin32.ReadWin32(os.path.join(datadir, '*cnt'), ch=ch_filepath)
    except Exception as e:
        print(f"Error loading event {event_id}: {e}")
        continue

    all_click_data[event_id] = {}

    for station in stations:
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 6), sharex=True)
        fig.suptitle(f"Event: {event_id} | Station: {station}", fontsize=14)
        figures.append((fig, axes))

        waveform_data = {}
        sampling_rates = {}
        minlen = float('inf')

        for comp in components:
            key = f"{station}.{comp}"
            try:
                data, sr = filedata.get_data(key)
                waveform_data[comp] = data
                sampling_rates[comp] = sr
                minlen = min(minlen, len(data))
            except:
                waveform_data[comp] = None

        if minlen == float('inf'):
            plt.close(fig)
            continue

        t = np.arange(minlen) / list(sampling_rates.values())[0]

        cursor_annotations = []
        fixed_annotations = []

        left_click_times = {comp: [] for comp in components}
        right_click_times = {comp: [] for comp in components}

        for i, comp in enumerate(components):
            ax = axes[i]
            if waveform_data[comp] is not None:
                ax.plot(t, waveform_data[comp][:minlen], color='black')
                ax.set_ylabel(comp.upper())
                ax.grid(True)
            else:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)

            annotation = ax.annotate('', xy=(0, 0), xytext=(20, 20),
                                     textcoords='offset points', fontsize=9,
                                     bbox=dict(boxstyle="round", fc="w"),
                                     arrowprops=dict(arrowstyle="->"))
            annotation.set_visible(False)
            cursor_annotations.append(annotation)

        # イベントハンドラ設定
        setup_event_handlers(fig, axes, cursor_annotations, fixed_annotations,
                             left_click_times, right_click_times,
                             event_id, station)

        # 保存対象のクリックデータを格納
        all_click_data[event_id][station] = {
            "left": left_click_times,
            "right": right_click_times
        }

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# すべての図を表示
for fig, _ in figures:
    fig.show()

print("\n💡 クリックが終わったら `save_click_results()` を実行すると、既存JSONにマージして保存されます。")
