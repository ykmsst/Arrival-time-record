import os
import pandas as pd

# ===== Windows の実行フォルダ設定 =====
# フォルダパスを r"…" でエスケープせずにそのまま指定します
DATA_DIR   = r"C:\Users\yukim\OneDrive\デスクトップ\固体地球物理学講座\桜島トモグラフィー\地震情報\earthquake_info@sakurajima"
INPUT_CSV  = os.path.join(DATA_DIR, "sakurajima_quadrant_top30_with_angle_add.csv")
OUTPUT_DIR = DATA_DIR  # 同じディレクトリ内にサブフォルダを作成
SORTED_CSV    = os.path.join(OUTPUT_DIR, "sakurajima_quadrant_top30_sorted.csv")



# ===== メイン処理 =====
def main():
    # ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # CSV 読み込み
    df = pd.read_csv(INPUT_CSV, parse_dates=["time"])

    # 日付順ソート
    df_sorted = df.sort_values("time").reset_index(drop=True)

    # ソート済みCSV 保存
    df_sorted.to_csv(SORTED_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved sorted CSV: {SORTED_CSV} ({len(df_sorted)} records)")

    # 各イベントごとにフォルダ生成
    for _, row in df_sorted.iterrows():
        dt = row["time"]
        place = row["place"].replace("/", "_").replace(" ", "_")
        # フォルダ名: YYYYMMDD_PLACE
        folder_name = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}_{dt.hour:02d}{dt.minute:02d}_{place}"
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
    print(f"Created folders under: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
