"""Data access for workstream A: Earth Engine point series and the NASA POWER API.

Every function returns plain dicts keyed by ISO date ("YYYY-MM-DD") or month ("YYYY-MM").
Earth Engine requests are kept small: one point, a few bands, one year (or one monthly collection) per call.
Raw responses are cached in data/raw/weather/ (git-ignored); finished years are never fetched twice.
"""
import calendar, datetime as dt, json, os, time, urllib.error, urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CACHE_DIR = os.path.join(REPO, "data", "raw", "weather")
FRESH_HOURS = 12          # cache lifetime for series that are still growing
START_YEAR = 1994

GRIDMET = "IDAHO_EPSCOR/GRIDMET"
PRISM_MONTHLY = "OREGONSTATE/PRISM/ANm"        # supersedes AN81m, which stops in 2020
IMERG_MONTHLY = "NASA/GPM_L3/IMERG_MONTHLY_V07"
GRACE = "NASA/GRACE/MASS_GRIDS_V04/MASCON"
SMAP = "NASA/SMAP/SPL4SMGP/008"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_PARAMS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"]

_ee = None


def ee_api():
    """Initialise Earth Engine once, with the caller's own project."""
    global _ee
    if _ee is None:
        project = os.environ.get("EE_PROJECT")
        if not project:
            raise SystemExit("EE_PROJECT is not set. Run: export EE_PROJECT=<your-earth-engine-project>")
        import ee
        ee.Initialize(project=project)
        _ee = ee
    return _ee


def _cached(key, fetch, growing, refresh=False):
    """Return cached JSON for `key`, or call fetch() and store it. `growing` series expire after FRESH_HOURS."""
    path = os.path.join(CACHE_DIR, key + ".json")
    if os.path.exists(path) and not refresh:
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        if not growing or age_h < FRESH_HOURS:
            with open(path) as f:
                return json.load(f)
    data = fetch()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def _point_series(collection_id, bands, lon, lat, scale, start, end, hour_range=None):
    """One getRegion call: [[epoch_ms, band values...], ...] for the pixel under the point. Empty list if no images."""
    ee = ee_api()
    col = ee.ImageCollection(collection_id).filterDate(start, end)
    if hour_range:
        col = col.filter(ee.Filter.calendarRange(hour_range[0], hour_range[1], "hour"))
    try:
        rows = col.select(bands).getRegion(ee.Geometry.Point([lon, lat]), scale).getInfo()
    except ee.EEException as e:          # an empty collection (e.g. first days of a new year) has no bands to select
        print(f"   note: {collection_id} {start}..{end}: {str(e)[:120]}")
        return []
    head = rows[0]
    idx = [head.index("time")] + [head.index(b) for b in bands]
    return [[r[i] for i in idx] for r in rows[1:]]


def _utc_date(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date()


def _tag(lon, lat):
    return f"{lon:.4f}_{lat:.4f}"


def gridmet_daily(lon, lat, today=None, refresh=False):
    """gridMET daily, one request per year. Values in native units:
    pr mm, tmmx/tmmn K, eto mm (grass reference), srad W/m2, vs m/s at 10 m."""
    today = today or dt.date.today()
    bands = ["pr", "tmmx", "tmmn", "eto", "srad", "vs"]
    out = {}
    for y in range(START_YEAR, today.year + 1):
        rows = _cached(f"{_tag(lon, lat)}/gridmet_{y}",
                       lambda y=y: _point_series(GRIDMET, bands, lon, lat, 4000, f"{y}-01-01", f"{y + 1}-01-01"),
                       growing=(y >= today.year - 1 and today < dt.date(y + 1, 3, 1)), refresh=refresh)
        for r in rows:
            out[_utc_date(r[0]).isoformat()] = dict(zip(bands, r[1:]))
    return out


def gridmet_daily_points(points, today=None, refresh=False):
    """gridMET daily for many points at once: one request per year for all points together.

    points: list of (id, lon, lat). Returns {id: {date: {band: value}}} in the same units as gridmet_daily().
    getRegion over a MultiPoint returns one row per pixel and day; each point takes the pixel nearest to it."""
    import hashlib
    today = today or dt.date.today()
    bands = ["pr", "tmmx", "tmmn", "eto", "srad", "vs"]
    tag = f"points_{len(points)}_" + hashlib.md5(repr(sorted(points)).encode()).hexdigest()[:8]

    def fetch_year(y):
        ee = ee_api()
        col = ee.ImageCollection(GRIDMET).filterDate(f"{y}-01-01", f"{y + 1}-01-01").select(bands)
        rows = col.getRegion(ee.Geometry.MultiPoint([[lon, lat] for _, lon, lat in points]), 4000).getInfo()
        idx = [rows[0].index(k) for k in ["longitude", "latitude", "time"] + bands]
        return [[r[i] for i in idx] for r in rows[1:]]

    out = {pid: {} for pid, _, _ in points}
    for y in range(START_YEAR, today.year + 1):
        rows = _cached(f"{tag}/gridmet_{y}", lambda y=y: fetch_year(y),
                       growing=(y >= today.year - 1 and today < dt.date(y + 1, 3, 1)), refresh=refresh)
        pixels = {(r[0], r[1]) for r in rows}
        nearest = {}                                   # point id -> its pixel
        for pid, lon, lat in points:
            if pixels:
                px = min(pixels, key=lambda p: (p[0] - lon) ** 2 + (p[1] - lat) ** 2)
                if abs(px[0] - lon) > 0.05 or abs(px[1] - lat) > 0.05:
                    raise SystemExit(f"gridMET {y}: no pixel within 0.05 degrees of {pid} ({lon}, {lat})")
                nearest[px] = nearest.get(px, []) + [pid]
        for r in rows:
            for pid in nearest.get((r[0], r[1]), []):
                out[pid][_utc_date(r[2]).isoformat()] = dict(zip(bands, r[3:]))
        print(f"   gridMET {y}: {len(rows)} rows for {len(points)} points", flush=True)
    return out


def prism_monthly(lon, lat, refresh=False):
    """PRISM monthly precipitation, mm. One request. The collection mixes AN81 and AN91 releases; if a month
    appears twice the later image in the collection is kept and the number of such months is reported."""
    rows = _cached(f"{_tag(lon, lat)}/prism_anm_monthly",
                   lambda: _point_series(PRISM_MONTHLY, ["ppt"], lon, lat, 4000, f"{START_YEAR}-01-01", "2100-01-01"),
                   growing=True, refresh=refresh)
    out, repeated = {}, 0
    for t, v in rows:
        if v is None:
            continue
        m = _utc_date(t).isoformat()[:7]
        repeated += m in out
        out[m] = v
    if repeated:
        print(f"   note: PRISM has {repeated} months with more than one image; the later one is used")
    return out


def imerg_monthly(lon, lat, refresh=False):
    """GPM IMERG V07 monthly precipitation, converted from mm/hr to mm per month. One request. Starts 1998-01."""
    rows = _cached(f"{_tag(lon, lat)}/imerg_monthly_1998",
                   lambda: _point_series(IMERG_MONTHLY, ["precipitation"], lon, lat, 11000, "1998-01-01", "2100-01-01"),
                   growing=True, refresh=refresh)
    out = {}
    for t, v in rows:
        if v is None:
            continue
        d = _utc_date(t)
        out[d.isoformat()[:7]] = v * 24 * calendar.monthrange(d.year, d.month)[1]
    return out


def grace_monthly(lon, lat, refresh=False):
    """GRACE / GRACE-FO JPL mascon liquid-water-equivalent thickness anomaly, cm. One request. Regional (~300 km)."""
    rows = _cached(f"{_tag(lon, lat)}/grace",
                   lambda: _point_series(GRACE, ["lwe_thickness"], lon, lat, 55000, "2002-01-01", "2100-01-01"),
                   growing=True, refresh=refresh)
    return {_utc_date(t).isoformat(): v for t, v in rows if v is not None}


def smap_daily(lon, lat, today=None, refresh=False):
    """SMAP L4 root-zone soil moisture (m3/m3), the first 3-hourly field of each UTC day. One request per year."""
    today = today or dt.date.today()
    out = {}
    for y in range(2015, today.year + 1):
        rows = _cached(f"{_tag(lon, lat)}/smap_{y}",
                       lambda y=y: _point_series(SMAP, ["sm_rootzone"], lon, lat, 9000, f"{y}-01-01", f"{y + 1}-01-01",
                                                 hour_range=(0, 2)),
                       growing=(y >= today.year), refresh=refresh)
        for t, v in rows:
            if v is not None:
                out[_utc_date(t).isoformat()] = v
    return out


def power_daily(lon, lat, today=None, refresh=False):
    """NASA POWER daily (AG community): T2M_MAX/T2M_MIN degC, PRECTOTCORR mm/day, ALLSKY_SFC_SW_DWN MJ/m2/day,
    WS2M m/s. Missing values (-999) are returned as None. One HTTP request, no key."""
    today = today or dt.date.today()

    def fetch():
        last_error = None
        for back in range(1, 11):        # the API rejects end dates it does not have yet
            end = today - dt.timedelta(days=back)
            url = (f"{POWER_URL}?parameters={','.join(POWER_PARAMS)}&community=AG&longitude={lon}&latitude={lat}"
                   f"&start={START_YEAR}0101&end={end:%Y%m%d}&format=JSON")
            try:
                with urllib.request.urlopen(url, timeout=300) as r:
                    return json.load(r)["properties"]["parameter"]
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code not in (400, 422):
                    time.sleep(5)
        raise SystemExit(f"NASA POWER request failed: {last_error}")

    raw = _cached(f"{_tag(lon, lat)}/power", fetch, growing=True, refresh=refresh)
    out = {}
    for k in raw[POWER_PARAMS[0]]:
        iso = f"{k[:4]}-{k[4:6]}-{k[6:]}"
        out[iso] = {p: (None if raw[p].get(k) is None or raw[p][k] <= -900 else raw[p][k]) for p in POWER_PARAMS}
    return out
