import os
import math
import pandas as pd

# ===== 設定 =====
DATA_DIR = "/workspaces/固体地球物理学講座/earthquake_data"
INPUT_CSV = os.path.join(DATA_DIR, "sakurajima_events_2011_present.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "sakurajima_quadrant_top30_with_angle_add.csv")
SAKURAJIMA_LAT = 31.593
SAKURAJIMA_LON = 130.657
MAX_PER_PLACE = 3
TOP_N = 30

# ===== Haversine距離計算 =====
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ     = math.radians(lat2 - lat1)
    dλ     = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ===== 仰角計算 =====
def compute_elevation_angle(depth_km, horizontal_km):
    """水平距離と深さから仰角(度)を計算"""
    if horizontal_km == 0 or pd.isna(horizontal_km):
        return 90.0
    if pd.isna(depth_km):
        return 0.0
    return math.degrees(math.atan2(depth_km, horizontal_km))

# ===== 方位分類 (北/東/南/西) =====
def classify_direction(lat, lon, base_lat, base_lon):
    dlat = lat - base_lat
    dlon = lon - base_lon
    if abs(dlat) >= abs(dlon):
        return "North" if dlat > 0 else "South"
    else:
        return "East" if dlon > 0 else "West"

# ===== 仰角カテゴリ =====
def classify_elevation(angle):
    if angle > 45:
        return "Beneath(>45°)"
    elif angle > 30:
        return "Medium(30°-45°)"
    else:
        return "Beside(≤30°)"

# ===== メイン処理 =====
def main():
    # CSV 読み込み
    df = pd.read_csv(INPUT_CSV, parse_dates=["time"])
    print(f"Loaded {len(df)} records from {INPUT_CSV}")

    # 距離再計算
    df["distance_km"] = df.apply(
        lambda r: haversine(SAKURAJIMA_LAT, SAKURAJIMA_LON, r.latitude, r.longitude),
        axis=1
    )

    # 仰角計算
    df["elevation_angle_deg"] = df.apply(
        lambda r: compute_elevation_angle(r["depth_km"], r["distance_km"]),
        axis=1
    )

    # 仰角カテゴリ
    df["angle_class"] = df["elevation_angle_deg"].apply(classify_elevation)

    # 方位 (北/東/南/西) 分類
    df["direction"] = df.apply(
        lambda r: classify_direction(r["latitude"], r["longitude"], SAKURAJIMA_LAT, SAKURAJIMA_LON),
        axis=1
    )

    # 各方向ごとにフィルタ
    frames = []
    for dir_name in ["North", "East", "South", "West"]:
        sub = df[df["direction"] == dir_name].copy()
        if sub.empty:
            continue
        # マグニチュード降順
        sub = sub.sort_values("magnitude", ascending=False)
        # place ごと最大3件
        sub = sub.groupby("place", group_keys=False).head(MAX_PER_PLACE)
        # direction 内上位 TOP_N 件
        sub = sub.head(TOP_N)
        frames.append(sub)

    result = pd.concat(frames, ignore_index=True)

    # ソート: direction, magnitude 降順
    result = result.sort_values(["direction","magnitude"], ascending=[True, False])

    # 保存
    cols = ["time","latitude","longitude","depth_km","magnitude",
            "distance_km","elevation_angle_deg","angle_class","direction","place"]
    result.to_csv(OUTPUT_CSV, columns=cols, index=False, encoding='utf-8-sig')
    print(f"Saved {OUTPUT_CSV} ({len(result)} records)")

if __name__ == "__main__":
    main()