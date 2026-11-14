# Field Shift: problem statement and example solution

NASA Space Apps 2026, challenge "Field Shift: Adapting Farms with NASA Data".
Team: 5 Geoinformatics students, AGH University of Krakow. Working draft, 2026-11-14.

---

## 1. Problem statement

### Full version

Every year a farmer decides what to plant and in what order (the crop rotation). Until recently they could rely on the experience of previous generations, but conditions are shifting: the growing season is getting longer, hot days are more frequent, rainfall is less predictable, and in many regions groundwater is declining. A rotation that worked for 30 years may no longer be the best one. Changing it is risky, though: a crop that improves the soil may use too much water, have no market, or not fit into the season.

The data that help assess this risk already exist: NASA has been measuring temperature, precipitation, soil moisture, vegetation condition and water storage from space for decades. But these data are scattered across missions, resolutions and formats, and they do not directly answer the farmer's question: **"Is it worth changing the rotation on my field, to what, and what am I risking?"**

Our task is to build a tool that, for a specific field:
1. shows how conditions (climate, water, vegetation) have changed over the last 30 years;
2. highlights periods when the field is bare or the crop is most vulnerable;
3. compares **the current rotation with at least three alternatives** according to the farmer's priorities (water, soil, income);
4. for every suggestion explains **what data it is based on, what we do not know, and what the farmer needs to check themselves or with an advisor**.

The tool supports the farmer; it does not decide for them.

### Short version (for the submission, ~150 words)

Farmers choose crop rotations based on generations of experience, but the conditions behind that experience are shifting: longer and hotter growing seasons, less predictable rain, and declining groundwater. A rotation that worked for decades may no longer be the best choice, yet changing it is risky. A soil-building crop may use too much water, lack a market, or not fit the season.

NASA has observed temperature, precipitation, soil moisture, vegetation and water storage for decades, but these data are scattered across missions, resolutions and formats, and do not directly answer the farmer's question: *should I change my rotation, to what, and what is the risk?*

**Field Shift** turns NASA Earth observations into a field-level profile of changing conditions, finds bare-soil and high-stress windows, and compares the current rotation with alternatives ranked by the farmer's own priorities. Every suggestion shows its evidence, its uncertainty, and what needs local expert review. It supports farmers' judgment; it does not replace it.

---

## 2. Who it is for: example user

**A farmer in western Kansas** (near Garden City, 37.97°N, 100.87°W). Dryland (no irrigation), growing winter wheat in a **wheat–fallow** system: one year of wheat, then the field rests and stores water for the next sowing (fallow typically lasts about 14 months, from harvest in July to sowing in September of the following year). Wells in the Ogallala aquifer in the region are yielding less and less water, so irrigation is not an option for them.

Their questions:
- Does the field have to stay bare for those 14 months? Wind blows the soil away.
- Is it possible to harvest more than one crop in two years without the risk of ending up with nothing in a dry year?
- What would happen if the coming years were like 2011–2012 or 2022?

Why this region for the demo: most of the challenge resources are US-based, and the US has the **Cropland Data Layer** (annual 30 m crop map). From the CDL pixel history we can read the field's current rotation without asking the farmer. The water problem (Ogallala, droughts) makes a strong story for the presentation.

> **To do:** the point above was chosen as a typical location in the region, not as a verified field. The Garden City area is largely irrigated. Before the demo, pick a field that CDL confirms as dryland wheat–fallow (e.g. around Tribune, Greeley County, where K-State runs dryland rotation trials).

---

## 3. Example solution: what the farmer sees

### Step 1. Select a field on the map

Click on the map or draw the field boundary. The app fetches data for that location. For the demo, field data are precomputed.

### Step 2. "Field profile": how conditions have changed

> **The numbers below are real.** They were computed from NASA POWER (daily data 1995–2024) for the point 37.97°N, 100.87°W. ET₀ is an approximation using the Hargreaves method (FAO-56); POWER meteorology has a grid cell of roughly 50 km, so this describes the climate of the area, not of the field itself. Script: `scripts/power_indicators.py`.

| Indicator | 1995–2009 | 2010–2024 | Trend per decade | Is the trend reliable? (Mann-Kendall) |
| :--- | ---: | ---: | ---: | :--- |
| Growing degree days (base 10°C, Apr–Oct) | 2228 | 2355 | +67 | **yes** (p = 0.01) |
| Frost-free days | 192 | 203 | +6.7 | no (p = 0.15) |
| First autumn frost (median Oct 27) | day 297 | day 305 | +5 days | weak signal (p = 0.08) |
| Last spring frost (median Apr 15) | day 105 | day 102 | −1.7 days | no (p = 0.41) |
| Days with Tmax ≥ 35°C | 40 | 47 | +2 | no (p = 0.39) |
| Annual precipitation [mm] | 568 | 533 | −13 | no (p = 0.54) |
| Precipitation Apr–Sep [mm] | 424 | 412 | −7 | no (p = 0.64) |
| Annual ET₀ [mm] | 1276 | 1307 | +14 | no (p = 0.37) |

**What the tool tells the farmer (in plain language):**
- "The season is getting warmer: accumulated heat is increasing, and this is a reliable signal. The frost-free window is getting longer, especially in autumn, but the data still fluctuate here."
- "Precipitation shows no clear trend. However, **in every month of the year potential evaporation exceeds precipitation** (on average precipitation covers about 43% of ET₀). Water is the main constraint on this field."
- "The driest seasons (Apr–Sep) in the last 30 years: **2011 (233 mm), 2022 (244 mm), 2012 (257 mm)**. The wettest: 1996, 2016, 2015 (about 560 mm). A good year gets more than twice as much rain as a bad one, so a strategy has to survive a bad year."

**Seasonal chart (water balance, 1995–2024 average):**

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
| :--- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| Precipitation [mm] | 11 | 12 | 32 | 47 | 77 | 84 | 90 | 77 | 43 | 43 | 16 | 18 |
| ET₀ [mm] | 32 | 45 | 84 | 121 | 164 | 188 | 198 | 172 | 129 | 83 | 46 | 30 |
| Balance [mm] | −21 | −32 | −52 | −74 | −87 | −104 | −108 | −95 | −86 | −40 | −30 | −12 |

In the app we overlay:
- **NDVI from MODIS or Sentinel-2** for the field (via GEE). Periods with NDVI below about 0.3 = bare field. In wheat–fallow this is a long band from July to autumn of the following year.
- **SMAP soil moisture anomalies** (since 2015): was the soil wetter or drier than usual before sowing in a given year.
- **Terrain slope from SRTM**: where on the field water erosion may be higher.
- **CDL**: current rotation read from history (e.g. "wheat in 2016, 2018, 2020, 2022; fallow in between").

### Step 3. The farmer sets priorities

Sliders: water saving, soil protection and improvement, nitrogen, income, safety in a dry year. Plus constraints: "no irrigation", "no drill for…", "I have cattle, forage is useful".

### Step 4. Strategy comparison

> **Note:** the strategies and scores below are **placeholders**. The crop descriptions are general (based on knowledge of the dry Great Plains), and every claim must be backed by a source before the hackathon, e.g. K-State Research and Extension publications or FAO. The 1–5 scores are set by hand for now to illustrate the mechanism. In the final version the engine computes them from the crop trait table and the field indicators.

**S0. Current: winter wheat – fallow (2 years)**
- *Why it is included:* it is the baseline; this is how the farmer manages the field today (CDL).
- *Benefits:* safest in a dry year, because fallow stores water for the wheat.
- *Weaknesses:* one crop in two years; a long bare-soil period (NDVI), which promotes wind erosion and loss of organic matter.
- *Gap:* how much water fallow actually stores on this field. Satellites cannot measure this; it needs field measurements or the farmer's knowledge.

**S1. Wheat – sorghum – fallow (3 years)**
- *Why:* the season is getting longer (GDD increasing, p = 0.01), so a spring crop fits between wheat and fallow. Sorghum tolerates drought well.
- *Benefits:* two crops in three years instead of one in two; shorter bare-soil period.
- *Risks:* in a year like 2011 sorghum may fail; less water is left for the wheat.
- *Check locally:* local sorghum market (USDA AMS Market News), equipment.

**S2. Wheat – sorghum – "flexible" forage cover crop in place of fallow**
- *Why:* the farmer indicated they have cattle and that soil is a priority. The cover crop is sown **only when soil moisture before sowing (SMAP) is above normal**. In a dry year the field stays fallow.
- *Benefits:* soil cover, forage, and the decision depends on that year's data.
- *Risks:* the cover crop uses water that the next wheat crop may need. SMAP resolution is on the order of kilometres, so the threshold must be calibrated against field measurements.
- *Check locally:* moisture threshold, species, seed cost.

**S3. Wheat – legume (e.g. pea) – fallow**
- *Why:* priority "nitrogen and soil". Legumes fix nitrogen from the air, so the following crop needs less fertiliser.
- *Benefits:* less fertiliser, breaks cereal disease and weed cycles.
- *Risks:* sensitive to heat during flowering (days ≥ 35°C), uncertain market.
- *Check locally:* varieties, buyers, sowing date.

**Multi-criteria scoring** (1 = poor, 5 = good; placeholder scores):

| Criterion | S0 | S1 | S2 | S3 |
| :--- | :-: | :-: | :-: | :-: |
| Water (use, risk of shortage) | 5 | 3 | 3 | 4 |
| Soil (cover, erosion, organic matter) | 1 | 3 | 4 | 3 |
| Nitrogen | 1 | 1 | 2 | 4 |
| Income | 2 | 4 | 4 | 3 |
| Safety in a dry year | 5 | 3 | 3 | 3 |

| Farmer's weights | S0 | S1 | S2 | S3 | Result |
| :--- | :-: | :-: | :-: | :-: | :--- |
| **A. "I save water and soil"** (water 30%, soil 25%, nitrogen 10%, income 20%, drought 15%) | 3.00 | 3.00 | 3.35 | **3.40** | S3 and S2 almost tied → the tool says: **"result uncertain, depends on assumptions; talk to an advisor"** |
| **B. "I need income"** (water 20%, soil 20%, nitrogen 5%, income 40%, drought 15%) | 2.80 | 3.30 | **3.55** | 3.25 | S2 clearly ahead |

Takeaway for the presentation: **changing the weights changes the ranking**, and the tool shows this instead of pretending there is a single "best" answer.

### Step 5. "What if"

Scenario slider: "precipitation −15%", "+1.5°C". The engine recomputes the water balance and heat days, and the cards show which strategies lose the most. Simplest version: replace years in the data with the driest years on record (2011, 2012, 2022) and recompute the ranking.

---

## 4. How it works

```
NASA POWER (daily climate)   ┐
GPM IMERG (precipitation)    │
SMAP (soil moisture)         │   GEE + Python        field indicators      scoring engine      app
MODIS / Sentinel-2 (NDVI)    ├──► clip to field ────► (GDD, frost dates, ──► rules + crop ─────► Flask + Leaflet
SRTM (slope)                 │   common grid          water balance,       trait table +       strategy cards
CDL (crop history)           │   and time axis        bare-soil windows,   farmer weights +    seasonal chart
SoilGrids / SSURGO (soil)    │                        anomalies, trends)   sensitivity         sliders
GRACE (groundwater)          ┘                                                   │
                                                                                 ▼
                                                                   LLM: card text in plain language
                                                                   (only from the numbers it receives)
```

Where AI/ML comes in (the challenge asks about this):
- **trends and their reliability:** Mann-Kendall (as in the table above);
- **year types:** K-Means on season features (precipitation, ET₀, heat) → "dry / normal / wet"; strategies are scored separately for each type;
- **bare-soil and stress windows:** thresholds and smoothing of the NDVI time series, optionally clustering of field NDVI profiles;
- **LLM:** only translates numbers and scores into card text. It does not invent facts; every number in the text comes from the engine.

What we **do not** do: a yield model. In 48 h there is nothing to validate it against, and it is hard to explain honestly.

---

## 5. Team roles: 5 people with a GIS background

We all have similar skills, so we split the work **by data and layers**, not by specialisation. We lack agronomic knowledge, so **one person owns agronomy from the start** and makes sure every claim has a source.

| Person | Owns | Output |
| :--- | :--- | :--- |
| 1. **Climate and water** | NASA POWER, GPM, GRACE; indicators, trends, year types (starter script already exists) | `climate.json` per field |
| 2. **Field and vegetation** | GEE: NDVI (MODIS, Sentinel-2), bare-soil windows, CDL (current rotation), SRTM | `field.json` + map layers |
| 3. **Soil and agronomy** | SMAP, SoilGrids/SSURGO; **crop trait table with sources**; strategy rules; contact with an advisor | `crops.csv` + `rules.md` |
| 4. **App** | Flask + Leaflet + charts; field profile, sliders, cards | working demo |
| 5. **Engine and story** | multi-criteria scoring, weight sensitivity, LLM for cards; slides, video, submission text | ranking + presentation |

We agree on the data format between people in the first hour (field names, units, ISO dates), so that 1, 2 and 3 can work in parallel with 4 and 5.

**How to cover the missing agronomist:**
- before the hackathon, contact someone from the **University of Agriculture in Krakow** (agriculture faculty) and ask for 15 minutes of questions about rotations in dry climates;
- sources for the crop table: FAO-56 (Kc coefficients, stage lengths), FAO GAEZ (crop climate requirements), K-State Research and Extension (rotations on the dry Great Plains);
- every card has a "Check locally" section. This is not a weakness; the challenge explicitly asks for it.

---

## 6. What is verified and what is not

| Item | Status |
| :--- | :--- |
| Climate indicator table (section 3, step 2) | computed from NASA POWER 1995–2024; ET₀ is a Hargreaves approximation |
| Problem statement, challenge requirements | from the challenge page (as of 2026-11-14) |
| Typical wheat–fallow rotation in western Kansas, fallow length | general knowledge, **confirm with a source** |
| Strategy descriptions S1–S3 (benefits, risks) | general knowledge, **confirm every sentence with a source** |
| 1–5 scores and weights | **placeholders**, to be replaced by engine output |
| Example point (Garden City) | **not verified** as a dryland field; choose a field confirmed by CDL |
| Space Apps 2026 judging criteria and submission format | **not checked**, see the rules |
