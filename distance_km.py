import math
import pandas as pd
from io import StringIO

# 桜島の緯度経度
SAKURAJIMA_LAT = 31.593
SAKURAJIMA_LON = 130.657

# 地震データ（CSV形式で読み込み）
data = """time,latitude,longitude,depth_km,magnitude,distance_km,elevation_angle_deg,angle_class,direction,place
2025-07-06 14:07:00,29.3633,129.5117,23,5.5,,,,,NEAR TOKARA ISLANDS
2025-07-03 16:13:00,29.3567,129.5217,20,5.5,,,,,NEAR TOKARA ISLANDS
2025-07-02 15:26:00,29.2567,129.0517,1,5.6,,,,,NEAR TOKARA ISLANDS
2025-04-26 12:06:00,32.5883,130.6333,11,4.2,,,,,KUMAMOTO REGION
2025-04-02 23:04:00,31.045,131.5217,36,6.1,,,,,E OFF OSUMI PEN
2025-03-18 05:00:00,32.4983,130.555,10,4.8,,,,,KUMAMOTO REGION
2025-01-13 21:19:00,31.8283,131.57,36,6.6,,,,,HYUGANADA REGION
2024-12-22 16:56:00,31.9233,130.7317,171,4.7,,,,,SATSUMA PENINSULA REGION
2024-12-17 13:09:00,31.1083,130.36,164,5.2,,,,,W OFF SATSUMA PEN
2024-11-17 21:16:00,29.0633,131.35,80,5.9,,,,,NE OFF AMAMI-OSHIMA ISLAND
2024-09-26 20:35:00,32.685,130.7083,13,3.8,,,,,KUMAMOTO REGION
2024-09-14 08:03:00,29.7667,131.0267,52,5.7,,,,,SE OFF TANEGASHIMA ISLAND
2024-09-10 12:27:00,31.975,130.8767,0,3.1,,,,,SOUTHERN MIYAZAKI PREF
2024-08-08 16:43:00,31.7367,131.7217,31,7.1,,,,,HYUGANADA REGION
2024-04-17 23:14:00,33.2,132.4083,39,6.6,,,,,BUNGO CHANNEL
2024-04-16 07:39:00,29.4567,131.7383,70,5.6,,,,,Tanegashima-southeasternOki
2024-04-08 10:25:00,31.59,131.4767,39,5.1,,,,,E OFF OSUMI PEN
2024-03-19 01:12:00,31.3133,130.6467,124,3.9,,,,,KAGOSHIMA BAY
2023-08-07 03:12:00,30.7667,131.4783,43,5.4,,,,,E OFF OSUMI PEN
2023-05-22 07:20:00,29.7467,129.4517,191,5.4,,,,,NEAR TOKARA ISLANDS
"""

df = pd.read_csv(StringIO(data))

# Haversine 公式で距離を計算する関数（km単位）
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球半径 [km]
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# 各地震の震央距離を計算して新しい列に追加
df['distance_km'] = df.apply(
    lambda row: haversine(SAKURAJIMA_LAT, SAKURAJIMA_LON, row['latitude'], row['longitude']),
    axis=1
)

# 結果を表示
print(df[['time', 'latitude', 'longitude', 'magnitude', 'place', 'distance_km']])

# 必要ならCSVに保存
df.to_csv("earthquake_with_distance.csv", index=False)
