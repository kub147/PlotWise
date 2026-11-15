"""Pure calculations for workstream A (no network): daily weather table, precipitation cross-check, climate summary.

Inputs are the dicts returned by fetch.py, so everything here can be tested offline (test_compute.py).
"""
import datetime as dt, math
from statistics import mean, pstdev

TREND_START = 1995
W_M2_TO_MJ_M2_DAY = 0.0864            # 1 W/m2 over 24 h
WIND_10M_TO_2M = 4.87 / math.log(67.8 * 10 - 5.42)   # FAO-56 eq. 47 = 0.748
RELIABLE_P = 0.05                     # a trend is labelled "reliable" when Mann-Kendall p < 0.05
PRODUCTS = ["gridMET", "PRISM", "IMERG", "POWER"]
REFERENCE = "PRISM"                   # station-based; the reference when products disagree (data-sources.md)


# ---------------------------------------------------------------- statistics

def mann_kendall_p(v):
    """Two-sided Mann-Kendall p-value with tie correction."""
    n = len(v)
    if n < 4:
        return None
    s = sum((v[j] > v[i]) - (v[j] < v[i]) for i in range(n) for j in range(i + 1, n))
    ties = {}
    for x in v:
        ties[x] = ties.get(x, 0) + 1
    var = (n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in ties.values())) / 18
    if var <= 0:
        return 1.0
    z = (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def ols_slope(xs, v):
    mx, my = mean(xs), mean(v)
    den = sum((a - mx) ** 2 for a in xs)
    return sum((a - mx) * (b - my) for a, b in zip(xs, v)) / den if den else 0.0


def pearson_r(a, b):
    ma, mb = mean(a), mean(b)
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den if den else None


def trend_row(years, values):
    h = len(values) // 2
    p = mann_kendall_p(values)
    return dict(n_years=len(values), first_year=years[0], last_year=years[-1],
                mean_first_half=round(mean(values[:h]), 2), mean_second_half=round(mean(values[h:]), 2),
                slope_per_decade=round(ols_slope(years, values) * 10, 2),
                mk_p=None if p is None else round(p, 4), reliable=bool(p is not None and p < RELIABLE_P))


def extraterrestrial_radiation(doy, lat_deg):
    """FAO-56 eq. 21, MJ m-2 d-1."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    de = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(de))))
    return 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(de) + math.cos(phi) * math.cos(de) * math.sin(ws))


def hargreaves_eto(tmax, tmin, doy, lat_deg):
    """FAO-56 eq. 52, mm/day. Only used to fill days that gridMET lacks."""
    return 0.0023 * 0.408 * extraterrestrial_radiation(doy, lat_deg) * ((tmax + tmin) / 2 + 17.8) * math.sqrt(max(tmax - tmin, 0))


# ---------------------------------------------------------------- daily weather table

COLUMNS = ["date", "precip_mm", "tmax_c", "tmin_c", "eto_mm", "srad_mj_m2", "wind_m_s"]


def build_daily(gridmet, power, lat, start=dt.date(1994, 1, 1)):
    """Merge gridMET and POWER into one gap-free daily table from `start` to the last gridMET day.

    Primary source per column: precip/tmax/tmin/eto = gridMET; srad/wind = NASA POWER.
    Fallbacks, in order: the other product (unit-converted), then the mean of the nearest valid days
    (precipitation: 0). Returns (rows, fill_counts) where fill_counts[column][source] = number of days.
    """
    if not gridmet:
        raise ValueError("no gridMET data")
    end = dt.date.fromisoformat(max(gridmet))
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    counts = {c: {} for c in COLUMNS[1:]}
    rows = []

    def pick(col, options):
        for source, value in options:
            if value is not None:
                counts[col][source] = counts[col].get(source, 0) + 1
                return value
        return None

    for d in days:
        g, p = gridmet.get(d.isoformat(), {}), power.get(d.isoformat(), {})
        gv = lambda k: g.get(k)
        tmax = pick("tmax_c", [("gridMET", None if gv("tmmx") is None else gv("tmmx") - 273.15), ("NASA POWER", p.get("T2M_MAX"))])
        tmin = pick("tmin_c", [("gridMET", None if gv("tmmn") is None else gv("tmmn") - 273.15), ("NASA POWER", p.get("T2M_MIN"))])
        harg = None if tmax is None or tmin is None else hargreaves_eto(tmax, tmin, d.timetuple().tm_yday, lat)
        rows.append(dict(
            date=d,
            precip_mm=pick("precip_mm", [("gridMET", gv("pr")), ("NASA POWER", p.get("PRECTOTCORR"))]),
            tmax_c=tmax, tmin_c=tmin,
            eto_mm=pick("eto_mm", [("gridMET", gv("eto")), ("Hargreaves (FAO-56) from the temperature columns", harg)]),
            srad_mj_m2=pick("srad_mj_m2", [("NASA POWER", p.get("ALLSKY_SFC_SW_DWN")),
                                           ("gridMET", None if gv("srad") is None else gv("srad") * W_M2_TO_MJ_M2_DAY)]),
            wind_m_s=pick("wind_m_s", [("NASA POWER", p.get("WS2M")),
                                       ("gridMET", None if gv("vs") is None else gv("vs") * WIND_10M_TO_2M)])))

    for col in COLUMNS[1:]:               # last resort, expected to be 0 days
        missing = [i for i, r in enumerate(rows) if r[col] is None]
        for i in missing:
            if col == "precip_mm":
                value = 0.0
            else:
                near = [rows[j][col] for j in (i - 2, i - 1, i + 1, i + 2)
                        if 0 <= j < len(rows) and rows[j][col] is not None and j not in missing]
                if not near:
                    raise ValueError(f"cannot fill {col} on {rows[i]['date']}: no valid neighbouring days")
                value = mean(near)
            rows[i][col] = value
        if missing:
            counts[col]["ASSUMPTION: neighbour mean (precipitation: 0)"] = len(missing)
    for r in rows:
        r["tmax_c"], r["tmin_c"] = max(r["tmax_c"], r["tmin_c"]), min(r["tmax_c"], r["tmin_c"])
        for col in COLUMNS[1:]:
            r[col] = round(max(r[col], 0.0) if col not in ("tmax_c", "tmin_c") else r[col], 2)
    return rows, counts


def check_daily(rows):
    """Raise if the table breaks its contract (consecutive days from 1994-01-01, no missing values)."""
    for a, b in zip(rows, rows[1:]):
        if (b["date"] - a["date"]).days != 1:
            raise ValueError(f"gap between {a['date']} and {b['date']}")
    for r in rows:
        if any(r[c] is None or (isinstance(r[c], float) and math.isnan(r[c])) for c in COLUMNS):
            raise ValueError(f"missing value on {r['date']}")
    if rows[0]["date"] != dt.date(1994, 1, 1):
        raise ValueError("series must start on 1994-01-01")


# ---------------------------------------------------------------- precipitation cross-check

def monthly_from_daily(daily, key):
    """{'YYYY-MM': total} for months in which every day has a value."""
    sums, n = {}, {}
    for iso, rec in daily.items():
        v = rec.get(key)
        if v is None:
            continue
        m = iso[:7]
        sums[m] = sums.get(m, 0.0) + v
        n[m] = n.get(m, 0) + 1
    out = {}
    for m, total in sums.items():
        y, mo = int(m[:4]), int(m[5:])
        days_in_month = (dt.date(y + (mo == 12), mo % 12 + 1, 1) - dt.date(y, mo, 1)).days
        if n[m] == days_in_month:
            out[m] = total
    return out


def yearly_totals(monthly):
    """{year: {'annual': mm, 'apr_sep': mm}} for years with all the months needed."""
    out = {}
    for y in sorted({int(m[:4]) for m in monthly}):
        months = [monthly.get(f"{y}-{mo:02d}") for mo in range(1, 13)]
        rec = {}
        if all(v is not None for v in months):
            rec["annual"] = sum(months)
        if all(v is not None for v in months[3:9]):
            rec["apr_sep"] = sum(months[3:9])
        if rec:
            out[y] = rec
    return out


def precip_crosscheck(gridmet, power, prism_m, imerg_m):
    """Compare four precipitation products at the field, annual and April-September.

    Summary statistics use the years that all four products cover completely, so the rows are comparable.
    The trend is also given for each product's own full record since 1995 (IMERG starts in 1998)."""
    monthly = {"gridMET": monthly_from_daily(gridmet, "pr"), "PRISM": prism_m, "IMERG": imerg_m,
               "POWER": monthly_from_daily(power, "PRECTOTCORR")}
    totals = {k: yearly_totals(v) for k, v in monthly.items()}
    result = dict(reference=REFERENCE, products=PRODUCTS, windows={}, yearly={})
    for window in ("annual", "apr_sep"):
        series = {k: {y: t[window] for y, t in totals[k].items() if window in t and y >= TREND_START} for k in PRODUCTS}
        common = sorted(set.intersection(*(set(s) for s in series.values())))
        rows = []
        for k in PRODUCTS:
            row = dict(product=k)
            if len(common) >= 4:
                v, ref = [series[k][y] for y in common], [series[REFERENCE][y] for y in common]
                p = mann_kendall_p(v)
                r = pearson_r(v, ref)
                row.update(mean_mm=round(mean(v), 1), cv_pct=round(100 * pstdev(v) / mean(v), 1),
                           bias_vs_reference_mm=round(mean(v) - mean(ref), 1),
                           bias_vs_reference_pct=round(100 * (mean(v) - mean(ref)) / mean(ref), 1),
                           r_vs_reference=None if r is None else round(r, 2),
                           slope_mm_per_decade=round(ols_slope(common, v) * 10, 1), mk_p=round(p, 3))
            own = sorted(series[k])
            if len(own) >= 4:
                v = [series[k][y] for y in own]
                row.update(own_period=[own[0], own[-1]], own_slope_mm_per_decade=round(ols_slope(own, v) * 10, 1),
                           own_mk_p=round(mann_kendall_p(v), 3))
            rows.append(row)
        result["windows"][window] = dict(common_years=[common[0], common[-1]] if common else None,
                                         n_common_years=len(common), rows=rows)
        result["yearly"][window] = {k: {str(y): round(v, 1) for y, v in sorted(series[k].items())} for k in PRODUCTS}
    return result


def crosscheck_markdown(cc):
    """The cross-check summary table as Markdown (also readable in a terminal)."""
    f = lambda v, spec="": "–" if v is None else format(v, spec)
    lines = []
    for window, title in (("annual", "Annual precipitation"), ("apr_sep", "April–September precipitation")):
        w = cc["windows"][window]
        span = f"{w['common_years'][0]}–{w['common_years'][1]}, n = {w['n_common_years']}" if w["common_years"] else "no common years"
        lines += [f"**{title}** — years covered by all four products ({span}); bias and r are against {cc['reference']}",
                  "",
                  "| Product | Mean mm | CV % | Bias mm | Bias % | r | Trend mm/decade | MK p | Own record | Trend mm/decade | MK p |",
                  "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: |"]
        for r in w["rows"]:
            own = f"{r['own_period'][0]}–{r['own_period'][1]}" if r.get("own_period") else "–"
            lines.append(f"| {r['product']} | {f(r.get('mean_mm'), '.0f')} | {f(r.get('cv_pct'), '.0f')} | "
                         f"{f(r.get('bias_vs_reference_mm'), '+.0f')} | {f(r.get('bias_vs_reference_pct'), '+.0f')} | "
                         f"{f(r.get('r_vs_reference'), '.2f')} | {f(r.get('slope_mm_per_decade'), '+.0f')} | "
                         f"{f(r.get('mk_p'), '.2f')} | {own} | {f(r.get('own_slope_mm_per_decade'), '+.0f')} | "
                         f"{f(r.get('own_mk_p'), '.2f')} |")
        lines.append("")
    lines.append("Caveat: POWER precipitation comes from a ~50 km reanalysis grid; do not use it for rainfall trends "
                 "(project brief, section 4). The weather CSV takes precipitation from gridMET.")
    return "\n".join(lines)


# ---------------------------------------------------------------- climate summary

def _longest_dry_spell(days):
    best = run = 0
    for r in days:
        run = run + 1 if r["precip_mm"] < 1.0 else 0
        best = max(best, run)
    return best


INDICATORS = [  # key, label, unit, source
    ("gdd10_apr_oct", "Growing degree days (base 10 °C, cap 30 °C), April–October", "°C·day", "NASA POWER"),
    ("hot_days_35c", "Days with Tmax ≥ 35 °C", "days", "NASA POWER"),
    ("last_spring_frost_doy", "Last spring frost (Tmin ≤ 0 °C)", "day of year", "NASA POWER"),
    ("first_fall_frost_doy", "First fall frost (Tmin ≤ 0 °C)", "day of year", "NASA POWER"),
    ("frost_free_days", "Frost-free period", "days", "NASA POWER"),
    ("precip_mm", "Annual precipitation", "mm", "gridMET"),
    ("precip_apr_sep_mm", "April–September precipitation", "mm", "gridMET"),
    ("heavy_rain_days_25mm", "Days with ≥ 25 mm of rain", "days", "gridMET"),
    ("eto_mm", "Annual reference ET", "mm", "gridMET"),
    ("eto_apr_sep_mm", "April–September reference ET", "mm", "gridMET"),
    ("balance_apr_sep_mm", "April–September precipitation minus reference ET", "mm", "gridMET"),
    ("longest_dry_spell_apr_sep", "Longest run of days with < 1 mm, April–September", "days", "gridMET"),
]


def yearly_indicators(rows, power):
    """Per-year indicators. Temperature indicators use NASA POWER (project brief), water indicators the weather table.
    Annual values exist only for complete years; April-September values as soon as the season is complete."""
    by_year = {}
    for r in rows:
        by_year.setdefault(r["date"].year, []).append(r)
    power_by_year = {}
    for iso, p in power.items():
        if p.get("T2M_MAX") is not None and p.get("T2M_MIN") is not None:
            power_by_year.setdefault(int(iso[:4]), []).append((dt.date.fromisoformat(iso), p["T2M_MAX"], p["T2M_MIN"]))
    out = {}
    for y in sorted(by_year):
        if y < TREND_START:
            continue
        days, rec = by_year[y], {}
        complete = len(days) == (dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days
        season = [r for r in days if 4 <= r["date"].month <= 9]
        if complete:
            rec["precip_mm"] = round(sum(r["precip_mm"] for r in days), 1)
            rec["eto_mm"] = round(sum(r["eto_mm"] for r in days), 1)
            rec["heavy_rain_days_25mm"] = sum(1 for r in days if r["precip_mm"] >= 25)
        if len(season) == 183:
            p, e = sum(r["precip_mm"] for r in season), sum(r["eto_mm"] for r in season)
            rec.update(precip_apr_sep_mm=round(p, 1), eto_apr_sep_mm=round(e, 1), balance_apr_sep_mm=round(p - e, 1),
                       longest_dry_spell_apr_sep=_longest_dry_spell(season))
        t = sorted(power_by_year.get(y, []))
        if len(t) == (dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days:
            spring = [d for d, tx, tn in t if d.month < 7 and tn <= 0]
            fall = [d for d, tx, tn in t if d.month >= 7 and tn <= 0]
            ls = max(spring).timetuple().tm_yday if spring else None
            ff = min(fall).timetuple().tm_yday if fall else None
            rec.update(gdd10_apr_oct=round(sum(max(0, (min(tx, 30) + max(tn, 10)) / 2 - 10) for d, tx, tn in t if 4 <= d.month <= 10)),
                       hot_days_35c=sum(1 for d, tx, tn in t if tx >= 35),
                       last_spring_frost_doy=ls, first_fall_frost_doy=ff,
                       frost_free_days=(ff - ls) if ls and ff else None)
        out[y] = rec
    return out


def trend_table(yearly):
    table = []
    for key, label, unit, source in INDICATORS:
        pairs = [(y, rec[key]) for y, rec in sorted(yearly.items()) if rec.get(key) is not None]
        if len(pairs) < 8:
            continue
        row = dict(indicator=key, label=label, unit=unit, source=source)
        row.update(trend_row([p[0] for p in pairs], [p[1] for p in pairs]))
        table.append(row)
    return table


def year_types(yearly):
    """dry / normal / wet from April-September precipitation minus reference ET, split at the terciles."""
    pairs = [(y, rec["balance_apr_sep_mm"]) for y, rec in sorted(yearly.items()) if "balance_apr_sep_mm" in rec]
    v = sorted(p[1] for p in pairs)
    def q(f):                              # linear-interpolated quantile
        pos = f * (len(v) - 1)
        i = int(pos)
        return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (pos - i)
    lo, hi = q(1 / 3), q(2 / 3)
    types = {str(y): ("dry" if b < lo else "wet" if b > hi else "normal") for y, b in pairs}
    method = dict(variable="April–September precipitation minus reference ET (gridMET), mm", split="terciles of all listed years",
                  dry_below_mm=round(lo, 1), wet_above_mm=round(hi, 1), values_mm={str(y): b for y, b in pairs})
    return types, method


def monthly_water_balance(rows):
    """Mean monthly precipitation, reference ET and their difference over the complete years since 1995."""
    by_year = {}
    for r in rows:
        by_year.setdefault(r["date"].year, []).append(r)
    years = [y for y, d in by_year.items() if y >= TREND_START and len(d) >= 365]
    out = []
    for m in range(1, 13):
        p = sum(r["precip_mm"] for y in years for r in by_year[y] if r["date"].month == m) / len(years)
        e = sum(r["eto_mm"] for y in years for r in by_year[y] if r["date"].month == m) / len(years)
        out.append(dict(month=m, precip_mm=round(p, 1), eto_mm=round(e, 1), balance_mm=round(p - e, 1)))
    return dict(period=[min(years), max(years)], months=out)


def grace_summary(grace):
    """Series and linear trend of regional terrestrial water storage (cm of water equivalent)."""
    pts = sorted((dt.date.fromisoformat(k), v) for k, v in grace.items())
    if len(pts) < 12:
        return dict(series=[], note="GRACE series not available")
    x = [d.year + (d.timetuple().tm_yday - 1) / 365.25 for d, _ in pts]
    v = [val for _, val in pts]
    slope = ols_slope(x, v)
    p = mann_kendall_p(v)
    return dict(unit="cm liquid water equivalent, anomaly relative to the 2004–2009 mean",
                period=[pts[0][0].isoformat(), pts[-1][0].isoformat()], n_months=len(pts),
                trend_cm_per_year=round(slope, 3), total_change_cm=round(slope * (x[-1] - x[0]), 1),
                mk_p=round(p, 4), reliable=bool(p < RELIABLE_P),
                note="Regional signal (~300 km mascon): groundwater + soil water + surface water. Never a field value. "
                     "The p-value ignores month-to-month autocorrelation and is therefore optimistic.",
                series=[dict(date=d.isoformat(), lwe_cm=round(val, 2)) for d, val in pts])


def smap_summary(smap, window_days=7):
    """Root-zone soil moisture series and the percentile of the latest value among all values within
    +/- window_days of the same calendar date in every year of the record."""
    pts = sorted((dt.date.fromisoformat(k), v) for k, v in smap.items())
    if not pts:
        return dict(series=[], note="SMAP series not available")
    last_date, last_value = pts[-1]
    doy = last_date.timetuple().tm_yday
    near = [v for d, v in pts if min(abs(d.timetuple().tm_yday - doy), 365 - abs(d.timetuple().tm_yday - doy)) <= window_days]
    below = sum(1 for v in near if v < last_value) + 0.5 * sum(1 for v in near if v == last_value)
    years = {d.year for d, _ in pts}
    return dict(unit="m3/m3, root zone (0–100 cm), SMAP L4 9 km",
                period=[pts[0][0].isoformat(), last_date.isoformat()],
                latest=dict(date=last_date.isoformat(), value=round(last_value, 3),
                            percentile_for_calendar_date=round(100 * below / len(near)),
                            window_days=window_days, n_values=len(near), n_years=len(years)),
                note="One 9 km model-assimilated cell, about 11 years of record: use the percentile and anomalies, "
                     "not the absolute value, and do not read it as a field measurement.",
                series=[dict(date=d.isoformat(), sm_rootzone=round(v, 3)) for d, v in pts])
