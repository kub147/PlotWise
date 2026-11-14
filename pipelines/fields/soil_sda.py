"""Soil properties for a field polygon from SSURGO via USDA Soil Data Access (no key needed).

For each field: find the SSURGO map units that intersect the polygon, weight them by intersected area, and for the
dominant component of each map unit read:
  - plant-available water capacity to 150 cm (mm), from horizon awc_r * thickness
  - surface texture, organic matter (%), erodibility factor Kw of the surface horizon
  - hydrologic soil group, component name, representative slope
Returns area-weighted values and the dominant map unit / component name.
"""
import json, urllib.request

SDA = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

def sda(query):
    req = urllib.request.Request(SDA, data=json.dumps({"query": query, "format": "JSON+COLUMNNAME"}).encode(),
                                 headers={"Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req, timeout=120))
    rows = out.get("Table", [])
    return [dict(zip(rows[0], r)) for r in rows[1:]] if rows else []

def mapunit_shares(wkt):
    g = f"geometry::STGeomFromText('{wkt}', 4326)"
    rows = sda(f"SELECT P.mukey, SUM(P.mupolygongeo.STIntersection({g}).STArea()) AS a FROM mupolygon P "
               f"WHERE P.mupolygongeo.STIntersects({g}) = 1 GROUP BY P.mukey")
    total = sum(float(r["a"]) for r in rows) or 1.0
    return {r["mukey"]: float(r["a"]) / total for r in rows}

def mapunit_properties(mukeys):
    keys = ",".join(f"'{k}'" for k in mukeys)
    comp = sda(f"""
    SELECT c.mukey, c.cokey, c.compname, c.comppct_r, c.hydgrp, c.slope_r, m.muname
    FROM component c JOIN mapunit m ON m.mukey = c.mukey
    WHERE c.mukey IN ({keys}) AND c.majcompflag = 'Yes'
    ORDER BY c.mukey, c.comppct_r DESC""")
    dominant = {}
    for r in comp:
        dominant.setdefault(r["mukey"], r)                # first row per mukey = largest component
    cokeys = ",".join(f"'{r['cokey']}'" for r in dominant.values())
    hz = sda(f"""
    SELECT h.cokey, h.hzdept_r, h.hzdepb_r, h.awc_r, h.om_r, h.kwfact, h.sandtotal_r, h.silttotal_r, h.claytotal_r,
           (SELECT TOP 1 tg.texdesc FROM chtexturegrp tg WHERE tg.chkey = h.chkey AND tg.rvindicator = 'Yes') AS texture
    FROM chorizon h WHERE h.cokey IN ({cokeys}) ORDER BY h.cokey, h.hzdept_r""")
    out = {}
    for mukey, c in dominant.items():
        layers = [h for h in hz if h["cokey"] == c["cokey"]]
        awc = 0.0
        for h in layers:
            top, bottom = float(h["hzdept_r"] or 0), min(float(h["hzdepb_r"] or 0), 150.0)
            if bottom > top and h["awc_r"] is not None:
                awc += float(h["awc_r"]) * (bottom - top) * 10      # cm/cm * cm -> mm
        surface = layers[0] if layers else {}
        f = lambda k: float(surface[k]) if surface.get(k) not in (None, "") else None
        out[mukey] = dict(muname=c["muname"], component=c["compname"], hydrologic_group=c["hydgrp"],
                          soil_slope_pct=float(c["slope_r"]) if c["slope_r"] else None, awc_mm=round(awc),
                          texture=surface.get("texture"), organic_matter_pct=f("om_r"), kfactor=f("kwfact"),
                          sand_pct=f("sandtotal_r"), silt_pct=f("silttotal_r"), clay_pct=f("claytotal_r"))
    return out

def field_soil(wkt):
    shares = mapunit_shares(wkt)
    props = mapunit_properties(list(shares))
    top = max(shares, key=shares.get)
    def wmean(k):
        pairs = [(props[m][k], s) for m, s in shares.items() if m in props and props[m][k] is not None]
        w = sum(s for _, s in pairs)
        return round(sum(v * s for v, s in pairs) / w, 2) if w else None
    return dict(awc_mm=round(wmean("awc_mm")), texture=props[top]["texture"], organic_matter_pct=wmean("organic_matter_pct"),
                kfactor=wmean("kfactor"), hydrologic_group=props[top]["hydrologic_group"],
                soil_series=props[top]["component"], soil_map_unit=props[top]["muname"],
                soil_map_unit_share=round(shares[top], 2), clay_pct=wmean("clay_pct"), sand_pct=wmean("sand_pct"),
                soil_source="SSURGO via Soil Data Access; dominant component per map unit, area-weighted")

if __name__ == "__main__":
    # smoke test: a ~800 m square near the K-State Tribune station
    x, y, d = -101.75, 38.47, 0.004
    wkt = f"POLYGON(({x-d} {y-d},{x+d} {y-d},{x+d} {y+d},{x-d} {y+d},{x-d} {y-d}))"
    print(json.dumps(field_soil(wkt), indent=1))
