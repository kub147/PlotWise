"""Field climate indicators from NASA POWER daily data — Field Shift starter script.

Usage:
    python3 power_indicators.py --lat 37.97 --lon -100.87 --start 1995 --end 2024 [--out climate.json]

Downloads T2M_MAX, T2M_MIN and PRECTOTCORR from the POWER API (no key needed) and computes:
GDD (base 10°C, cap 30°C, Apr–Oct), frost dates, days with Tmax >= 35°C, precipitation, ET0 (Hargreaves, FAO-56),
monthly P − ET0 balance, trends per decade and Mann-Kendall p-values. Output: table on screen + JSON.
Note: POWER meteorology has a ~0.5° x 0.625° grid, so this describes the climate of the area, not of the field itself.
Caution: do not use POWER precipitation for trends without a cross-check. At Tribune, KS it shows a drying trend
(-45 mm/decade, 1995-2020) that gridMET does not (+3 mm/decade). Use POWER for temperature, radiation and GDD.
"""
import argparse, json, math, urllib.request, datetime as dt
from statistics import mean, median

def fetch(lat, lon, y0, y1):
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR"
           f"&community=AG&longitude={lon}&latitude={lat}&start={y0}0101&end={y1}1231&format=JSON")
    with urllib.request.urlopen(url, timeout=180) as r:
        return json.load(r)["properties"]["parameter"]

def ra(doy, phi):  # extraterrestrial radiation, FAO-56 eq. 21 [MJ m-2 d-1]
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    de = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(de))))
    return 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(de) + math.cos(phi) * math.cos(de) * math.sin(ws))

def mann_kendall_p(v):
    n = len(v); s = sum((v[j] > v[i]) - (v[j] < v[i]) for i in range(n) for j in range(i + 1, n))
    var = n * (n - 1) * (2 * n + 5) / 18
    z = (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

def slope_per_decade(xs, v):
    mx, my = mean(xs), mean(v)
    return sum((a - mx) * (b - my) for a, b in zip(xs, v)) / sum((a - mx) ** 2 for a in xs) * 10

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True); ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--start", type=int, default=1995); ap.add_argument("--end", type=int, default=2024)
    ap.add_argument("--out", default="climate.json")
    a = ap.parse_args()
    d = fetch(a.lat, a.lon, a.start, a.end); phi = math.radians(a.lat)
    rows = []
    for k in sorted(d["T2M_MAX"]):
        t = dt.date(int(k[:4]), int(k[4:6]), int(k[6:]))
        tx, tn, p = d["T2M_MAX"][k], d["T2M_MIN"][k], d["PRECTOTCORR"][k]
        if min(tx, tn, p) <= -998: continue  # missing value
        et0 = 0.0023 * 0.408 * ra(t.timetuple().tm_yday, phi) * ((tx + tn) / 2 + 17.8) * math.sqrt(max(tx - tn, 0))
        rows.append((t, tx, tn, p, et0))
    years = list(range(a.start, a.end + 1)); Y = {}
    for y in years:
        r = [x for x in rows if x[0].year == y]
        spring = [x[0] for x in r if x[0].month < 7 and x[2] <= 0]
        fall = [x[0] for x in r if x[0].month >= 7 and x[2] <= 0]
        ls = max(spring).timetuple().tm_yday if spring else None
        ff = min(fall).timetuple().tm_yday if fall else None
        gs = [x for x in r if 4 <= x[0].month <= 9]
        Y[y] = dict(precip_mm=sum(x[3] for x in r), precip_apr_sep_mm=sum(x[3] for x in gs),
                    et0_mm=sum(x[4] for x in r), et0_apr_sep_mm=sum(x[4] for x in gs),
                    hot_days_35c=sum(1 for x in r if x[1] >= 35),
                    gdd10_apr_oct=sum(max(0, (min(x[1], 30) + max(x[2], 10)) / 2 - 10) for x in r if 4 <= x[0].month <= 10),
                    last_spring_frost_doy=ls, first_fall_frost_doy=ff,
                    frost_free_days=(ff - ls) if ls and ff else None,
                    heavy_rain_days_25mm=sum(1 for x in r if x[3] >= 25))
    trends = {}
    print("indicator | mean 1st half | mean 2nd half | trend/decade | Mann-Kendall p")
    for key in Y[years[0]]:
        pairs = [(y, Y[y][key]) for y in years if Y[y][key] is not None]
        xs, v = [p[0] for p in pairs], [p[1] for p in pairs]
        if len(v) < 4: continue  # e.g. frost dates at a frost-free site
        h = len(v) // 2
        t = dict(mean_first_half=mean(v[:h]), mean_second_half=mean(v[h:]),
                 slope_per_decade=slope_per_decade(xs, v), mk_p=mann_kendall_p(v))
        trends[key] = t
        print(f"{key} | {t['mean_first_half']:.0f} | {t['mean_second_half']:.0f} | {t['slope_per_decade']:+.1f} | {t['mk_p']:.2f}")
    n = len(years); monthly = []
    for m in range(1, 13):
        r = [x for x in rows if x[0].month == m]
        P, E = sum(x[3] for x in r) / n, sum(x[4] for x in r) / n
        monthly.append(dict(month=m, precip_mm=round(P, 1), et0_mm=round(E, 1), balance_mm=round(P - E, 1)))
    out = dict(lat=a.lat, lon=a.lon, period=[a.start, a.end], source="NASA POWER daily (AG)",
               et0_method="Hargreaves (FAO-56)", yearly=Y, trends=trends, monthly_climatology=monthly,
               driest_seasons=sorted(years, key=lambda y: Y[y]["precip_apr_sep_mm"])[:5])
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    print("saved", a.out)

if __name__ == "__main__":
    main()
