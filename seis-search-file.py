import os
import math
import pandas as pd
from datetime import datetime

# ===== 設定 =====
DATA_DIR           = "/workspaces/固体地球物理学講座/earthquake_data"
START_YEAR         = 2011
END_YEAR           = 2022
SAKURAJIMA_LAT     = 31.593
SAKURAJIMA_LON     = 130.657
SEARCH_RADIUS_KM   = 250.0
MIN_MAGNITUDE      = 3.0

# ===== haversine距離計算 =====
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ     = math.radians(lat2 - lat1)
    dλ     = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ===== 1行パース（秒無視・分を度に換算） =====
def parse_fixed_line(line:str):
    if not line.startswith("J"):
        return None
    try:
        # ---- 時刻 ----
        year   = int(line[1:5])
        month  = int(line[5:7])
        day    = int(line[7:9])
        hour   = int(line[9:11])
        minute = int(line[11:13])
        dt = datetime(year, month, day, hour, minute)

        # ---- 緯度（度+分） ----
        lat_deg_str = line[21:24].strip()  # 22–24列目
        lat_min_str = line[24:28].strip()  # 25–28列目 → 4桁（xx.yy）
        lat_deg = int(lat_deg_str) if lat_deg_str else 0
        if len(lat_min_str) == 4:
            # ex: '1984' → 19.84分
            lat_min = float(lat_min_str[:2] + "." + lat_min_str[2:])
        else:
            lat_min = 0.0
        latitude = lat_deg + lat_min / 60.0

        # ---- 経度（度+分） ----
        lon_deg_str = line[32:36].strip()  # 33–35列目
        lon_min_str = line[36:40].strip()  # 37–40列目
        lon_deg = int(lon_deg_str) if lon_deg_str else 0
        if len(lon_min_str) == 4:
            # ex: '1051' → 10.51分
            lon_min = float(lon_min_str[:2] + "." + lon_min_str[2:])
        else:
            lon_min = 0.0
        longitude = lon_deg + lon_min / 60.0

        # ---- 深さ ----
        depth_str = line[44:47].strip()
        depth_km  = int(depth_str) if depth_str else None

        # ---- マグニチュード ----
        mag_str = line[52:54].strip()
        magnitude = float(mag_str) / 10.0 if mag_str else None

        # ---- 地名 ----
        place = line[68:92].strip()

        return {
            "time": dt,
            "latitude": latitude,
            "longitude": longitude,
            "depth_km": depth_km,
            "magnitude": magnitude,
            "place": place
        }
    except Exception:
        return None

# ===== 年次ファイル読み込み =====
def read_year_file(year:int):
    path = os.path.join(DATA_DIR, f"h{year}")
    events=[]
    with open(path, encoding="shift_jis", errors="ignore") as f:
        for line in f:
            ev = parse_fixed_line(line)
            if ev:
                events.append(ev)
    print(f"{year}: {len(events)} parsed")
    return events

# ===== メイン処理 =====
def main():
    all_events=[]
    for yr in range(START_YEAR, END_YEAR+1):
        all_events += read_year_file(yr)
    df = pd.DataFrame(all_events)
    print(f"All parsed: {len(df)}")

    # M>=3 のみ
    df = df[df["magnitude"].notna() & (df["magnitude"] >= MIN_MAGNITUDE)]
    print(f"M>=3: {len(df)}")

    # 距離フィルタ
    df["distance_km"] = df.apply(
        lambda r: haversine(SAKURAJIMA_LAT, SAKURAJIMA_LON, r.latitude, r.longitude),
        axis=1
    )
    df = df[df["distance_km"] <= SEARCH_RADIUS_KM]
    print(f"M>=3 & <=250km: {len(df)}")

    # ソート
    df = df.sort_values("time").reset_index(drop=True)

     # --- マグニチュードだけ文字列にフォーマット ---
    df["magnitude"] = df["magnitude"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
    
    # 保存先を読み込みディレクトリにする
    out = os.path.join(DATA_DIR, "sakurajima_events_2011_2022.csv")

    # CSV保存（緯度経度は%.6f、小数1位のmagnitudeはすでに文字列なのでそのまま）
    df.to_csv(out, index=False, encoding="utf-8-sig", float_format="%.6f")
    print(f"Saved {out} ({len(df)} records)")

if __name__=="__main__":
    main()
