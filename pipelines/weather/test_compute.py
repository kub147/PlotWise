"""Offline tests for the weather pipeline (no Earth Engine, no network): python3 pipelines/weather/test_compute.py

Synthetic weather only checks the plumbing: file contract, gap filling, units, statistics. It says nothing about Tribune.
"""
import csv, datetime as dt, math, os, random, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compute, fetch, run

TODAY = dt.date(2026, 11, 14)


def synthetic():
    rng = random.Random(1)
    gridmet, power, smap = {}, {}, {}
    d = dt.date(1994, 1, 1)
    while d <= TODAY - dt.timedelta(days=2):
        season = math.sin(2 * math.pi * (d.timetuple().tm_yday - 105) / 365)
        tx, tn = 18 + 14 * season + rng.gauss(0, 3), 2 + 13 * season + rng.gauss(0, 3)
        pr = rng.expovariate(1 / 6) if rng.random() < 0.18 else 0.0
        gridmet[d.isoformat()] = dict(pr=pr, tmmx=tx + 273.15, tmmn=tn + 273.15, eto=max(0.3, 4 + 3.5 * season),
                                      srad=200 + 110 * season, vs=5.0)
        late = d > TODAY - dt.timedelta(days=30)            # POWER radiation lags behind
        power[d.isoformat()] = dict(T2M_MAX=tx + 0.5, T2M_MIN=tn + 0.5, PRECTOTCORR=pr * 0.8,
                                    ALLSKY_SFC_SW_DWN=None if late else 17 + 9 * season, WS2M=None if late else 3.5)
        if d >= dt.date(2015, 4, 1):
            smap[d.isoformat()] = 0.2 + 0.05 * season + rng.gauss(0, 0.01)
        d += dt.timedelta(days=1)
    del gridmet["2003-07-04"]                               # a missing gridMET day must be filled from POWER
    monthly = compute.monthly_from_daily(gridmet, "pr")
    prism = {m: v * 1.02 for m, v in monthly.items()}
    imerg = {m: v * 1.1 for m, v in monthly.items() if m >= "2000-06" and m <= "2026-06"}
    grace = {f"{y}-{m:02d}-01": -0.8 * (y + m / 12 - 2002) + math.sin(m) for y in range(2002, 2025) for m in range(1, 13)}
    return gridmet, power, prism, imerg, grace, smap


def test_all():
    gridmet, power, prism, imerg, grace, smap = synthetic()

    # statistics
    assert compute.mann_kendall_p(list(range(30))) < 0.001
    assert compute.mann_kendall_p([1, 1, 1, 1, 1]) == 1.0
    assert abs(compute.ols_slope([0, 1, 2, 3], [1, 3, 5, 7]) - 2) < 1e-9
    assert abs(compute.WIND_10M_TO_2M - 0.748) < 0.001
    assert 40 < compute.extraterrestrial_radiation(172, 38.47) < 43      # FAO-56 table 2.6: ~41.6 at 38N in June

    # daily table
    rows, counts = compute.build_daily(gridmet, power, 38.47)
    compute.check_daily(rows)
    assert rows[-1]["date"] == TODAY - dt.timedelta(days=2)
    assert counts["precip_mm"]["NASA POWER"] == 1 and counts["eto_mm"]["Hargreaves (FAO-56) from the temperature columns"] == 1
    assert counts["srad_mj_m2"]["gridMET"] == 28 and counts["wind_m_s"]["gridMET"] == 28
    assert abs(rows[-1]["wind_m_s"] - 5.0 * 0.748) < 0.01
    assert abs(rows[-1]["srad_mj_m2"] - gridmet[rows[-1]["date"].isoformat()]["srad"] * 0.0864) < 0.01
    assert all(r["tmax_c"] >= r["tmin_c"] and r["precip_mm"] >= 0 for r in rows)

    # cross-check
    cc = compute.precip_crosscheck(gridmet, power, prism, imerg)
    annual = {r["product"]: r for r in cc["windows"]["annual"]["rows"]}
    assert cc["windows"]["annual"]["common_years"] == [2001, 2025]       # IMERG starts mid-2000; 2026 is incomplete
    assert annual["PRISM"]["bias_vs_reference_mm"] == 0
    assert -23 < annual["POWER"]["bias_vs_reference_pct"] < -20 and 7 < annual["IMERG"]["bias_vs_reference_pct"] < 9
    assert annual["gridMET"]["own_period"][0] == 1995
    table = compute.crosscheck_markdown(cc)
    assert table.count("| gridMET |") == 2 and "IMERG" in table

    # climate summary
    yearly = compute.yearly_indicators(rows, power)
    assert "precip_mm" not in yearly[2026] and "balance_apr_sep_mm" in yearly[2026]
    trends = compute.trend_table(yearly)
    assert {t["indicator"] for t in trends} >= {"gdd10_apr_oct", "precip_apr_sep_mm", "eto_mm", "longest_dry_spell_apr_sep"}
    types, method = compute.year_types(yearly)
    n = len(types)
    assert n == 32 and abs(list(types.values()).count("dry") - n / 3) <= 1 and set(types.values()) == {"dry", "normal", "wet"}
    mwb = compute.monthly_water_balance(rows)
    assert len(mwb["months"]) == 12 and mwb["period"] == [1995, 2025]
    g = compute.grace_summary(grace)
    assert abs(g["trend_cm_per_year"] + 0.8) < 0.02 and g["reliable"]
    s = compute.smap_summary(smap)
    assert 0 <= s["latest"]["percentile_for_calendar_date"] <= 100 and s["latest"]["n_values"] > 100

    # end to end with the fetchers replaced: files on disk match the contract
    with tempfile.TemporaryDirectory() as tmp:
        run.PROCESSED = tmp
        fetch.gridmet_daily = lambda lon, lat, **k: gridmet
        fetch.power_daily = lambda lon, lat, **k: power
        fetch.prism_monthly = lambda lon, lat, **k: prism
        fetch.imerg_monthly = lambda lon, lat, **k: imerg
        fetch.grace_monthly = lambda lon, lat, **k: grace
        fetch.smap_daily = lambda lon, lat, **k: smap
        field = run.load_fields()[0]
        gm, pw, cc = run.crosscheck(field, False)
        run.write_sources([run.build(field, gm, pw, cc, False)])
        with open(os.path.join(tmp, "weather", "ks071-001.csv")) as f:
            table = list(csv.reader(f))
        assert table[0] == ["date", "precip_mm", "tmax_c", "tmin_c", "eto_mm", "srad_mj_m2", "wind_m_s"]
        assert table[1][0] == "1994-01-01" and len(table) - 1 == (TODAY - dt.timedelta(days=2) - dt.date(1994, 1, 1)).days + 1
        assert all(len(r) == 7 and all(c != "" for c in r) for r in table)
        import json
        with open(os.path.join(tmp, "climate", "ks071-001.json")) as f:
            climate = json.load(f)
        for key in ("trends", "year_types", "monthly_water_balance", "grace", "smap", "precip_crosscheck"):
            assert key in climate
        assert os.path.exists(os.path.join(tmp, "weather", "sources.md"))
    print("all offline tests passed")


if __name__ == "__main__":
    test_all()
