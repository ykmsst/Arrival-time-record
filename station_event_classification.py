import pandas as pd
import numpy as np
import os
from math import radians, sin, cos, atan2, sqrt, degrees

# === 保存先ディレクトリ ===
output_dir = "/workspaces/固体地球物理学講座/earthquake_data/Arrival_time_checker/classify"
os.makedirs(output_dir, exist_ok=True)  # ディレクトリがなければ作る
output_path = os.path.join(output_dir, "station_event_classification.csv")

# === CSV読み込み ===
events_df = pd.read_csv(os.path.join(output_dir,"earthquake_info@sakurajima_add.csv"), parse_dates=["time"])      # event_id,lat,lon,depth_km
stations_df = pd.read_csv(os.path.join(output_dir,"station_metadata copy.csv"))  # station_name,lat,lon,elevation_m

# === Haversineで距離計算(km) ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球半径(km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# === 方位角(0-360度) ===
def calculate_azimuth(lat1, lon1, lat2, lon2):
    dlon = radians(lon2 - lon1)
    y = sin(dlon) * cos(radians(lat2))
    x = cos(radians(lat1))*sin(radians(lat2)) - sin(radians(lat1))*cos(radians(lat2))*cos(dlon)
    az = degrees(atan2(y, x))
    return (az + 360) % 360

# === 方位分類 ===
def classify_azimuth(deg):
    if deg >= 337.5 or deg < 22.5:
        return "N"
    elif deg < 67.5:
        return "NE"
    elif deg < 112.5:
        return "E"
    elif deg < 157.5:
        return "SE"
    elif deg < 202.5:
        return "S"
    elif deg < 247.5:
        return "SW"
    elif deg < 292.5:
        return "W"
    else:
        return "NW"

# === 仰角分類 ===
def classify_dip(deg):
    if deg > 45:
        return "Beneath"
    elif deg >= 30:
        return "Middle"
    else:
        return "Beside"

# === 計算結果を保存するリスト ===
results = []

# === 全イベント × 全観測点 の組み合わせで計算 ===
for _, e_row in events_df.iterrows():
    dt = e_row["time"]
    place = e_row["place"].replace("/", "_").replace(" ", "_")
    e_lat, e_lon, e_depth = e_row["latitude"], e_row["longitude"], e_row["depth_km"]
    e_id = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}_{dt.hour:02d}{dt.minute:02d}_{place}"

    for _, s_row in stations_df.iterrows():
        st_name = s_row["station_name"]
        st_lat, st_lon = s_row["lat"], s_row["lon"]

        # 平面距離
        horiz_km = haversine(st_lat, st_lon, e_lat, e_lon)
        # 方位角
        az_deg = calculate_azimuth(st_lat, st_lon, e_lat, e_lon)
        az_class = classify_azimuth(az_deg)

        # 仰角
        dip_deg = degrees(atan2(e_depth, horiz_km))
        dip_class = classify_dip(dip_deg)

        results.append([
            e_id, st_name,
            round(az_deg,1), az_class,
            round(horiz_km,1),
            e_depth,
            round(dip_deg,1), dip_class
        ])

# === DataFrame化してCSV出力 ===
out_df = pd.DataFrame(results, columns=[
    "place","station_name",
    "azimuth_deg","azimuth_class",
    "distance_km","depth_km",
    "dip_angle_deg","dip_class"
])
out_df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ station_event_classification.csv を生成しました！")
