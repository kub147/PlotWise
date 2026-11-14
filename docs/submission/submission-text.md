# Submission text (draft)

Draft answers for the NASA Space Apps 2026 project form, challenge "Field Shift: Adapting Farms with NASA Data".
The field names below follow earlier Space Apps forms. **Check them against the real form on the Project tab and
adjust lengths**: we could not open the 2026 submission guide from a script.

Items in `[SQUARE BRACKETS]` are missing facts that a team member must fill in. Every number here comes from a file
in this repository; the source is named in [data-and-references.md](data-and-references.md) or next to the number.

## Project name

PlotWise

## High-level summary (short)

PlotWise lets a dryland farmer in western Kansas replay the last 30 years on their own field under different crop
rotations. For each rotation it shows yield, net return, how it held up in dry years and what it does to the soil,
then ranks the rotations by the farmer's own priorities. It reads the field's real crop history from satellite-based
crop maps, drives a soil-water model with NASA and gridded weather data, and checks that model against 24 years of
measured yields from Kansas State University field trials. Every suggestion shows its evidence, its gaps and what to
check locally. The tool does not pick a winner: it shows when the answer depends on what the farmer values.

## Links

- Project demo (video or slides): `[DEMO LINK]`
- Final project (repository): https://github.com/kub147/PlotWise
- Live app: `[LIVE APP LINK — expected https://kub147.github.io/PlotWise/ once GitHub Pages is enabled; confirm it loads]`

## Detailed project description

### The question

> "My field is in wheat–fallow. Should I change the rotation, to what, and what do I risk in a dry year?"

On the High Plains, rain covers only about a third of what the air can evaporate. For a century the answer was to
leave the land bare every second year so the soil could store water for wheat. Farmers are now moving away from that:
in Greeley County, Kansas, fallow fell from 42% of dryland cropland in 2008 to 29% in 2024 (USDA Cropland Data Layer).
The choice is risky. In the Kansas State University trials at Tribune, wheat failed completely in 2002 and 2013 and
sorghum in 2002 and 2012.

### What PlotWise does

The app has five views. A farmer picks a field and moves through them.

1. **My field.** The field outline on an aerial map, the rotation actually practised, what grew there every year
   from 2008 to 2025, the soil and how much water it can hold, how many days a year the ground is bare, an 18-year
   greenness record from Landsat, and a surface-heat image from ECOSTRESS.
2. **What has changed.** Climate trends for that place, each labelled "reliable" or "not reliable" by a standard
   trend test. At Tribune the growing season is warmer (+138 °F·days per decade), the first fall frost comes later,
   and the air is thirstier. Rainfall shows no reliable trend, and the page says so. It also shows regional water
   storage from GRACE (about 7 inches of water lost since 2002) and how the county's fields are farmed.
3. **Rotation replay.** Six rotations are run through every year from 1996 to 2025 on that field's soil and weather.
   Four sliders set the farmer's priorities: net return, holding up in dry years, putting rain to work, and soil.
   The ranking updates at once. Each rotation has a card: why it is suggested, the evidence, what you gain, what you
   risk, what we do not know, and what to check locally. A chart shows the result year by year, with the crop-failure
   years marked. A switch shows the same replay at county-average yields or at well-managed yields.
4. **This season.** Today's soil moisture from SMAP as a percentile for the calendar date (96th percentile at
   Tribune on 10 November 2026). The page states plainly that the model cannot yet project the season from it.
5. **Region.** The same question across 46 counties of western Kansas: what 31,660 fields actually grow, and where
   replacing fallow with a summer crop starts to pay.

A sixth page, **How we know**, shows the validation, the data flow, what we do not claim, and the full evidence
register.

### How it works

- **Field history from space.** Field outlines and the current rotation are derived from eight years of identical
  crop sequences in the USDA Cropland Data Layer. The farmer does not type the rotation in; the tool reads it.
- **A soil-water engine.** A daily soil-water balance runs through every crop and every fallow. Soil water capacity
  comes from the USDA soil survey (SSURGO), daily weather from gridMET and NASA POWER, crop water use from FAO-56.
  Yield follows from the water each crop used, with functions published by Kansas State University.
- **Every rotation in every year.** Each phase of each rotation is started in each year, so a rotation gets the whole
  run of good and bad years rather than one lucky sequence.
- **Money.** Yield times the actual Kansas price of that year, minus the Kansas State budget cost for the region, in
  2025 dollars. Money is scored against wheat–fallow on the same field, so the comparison does not depend on land
  rent.
- **Priorities, not a verdict.** Four scores per rotation are combined with the farmer's weights in the browser. The
  engine also tests 5,000 random sets of priorities and reports how often each rotation comes first. At Tribune no
  rotation wins under most priorities, and the app says "it is a close call".

### How we know it is believable

The engine was checked against year-by-year yields measured at the Kansas State University Southwest
Research-Extension Center in Tribune, 1996–2020.

- Sorghum: modelled water use explains about 61% of the year-to-year variation in measured yield (54% leave-one-out).
- Wheat: about 45% with hot days counted, and only about 13% leave-one-out. The app says a single wheat year is a
  rough estimate.
- The model's two lowest years for each crop are the measured crop-failure years.
- For 2008–2015, at well-managed yields, the replay ranks wheat–sorghum–fallow first, wheat–fallow second and
  wheat–corn–fallow last, the same order as the Kansas State large-scale study.

### What we found

- At county-average yields every rotation shows a loss on all eleven demo fields, because the costs include land rent
  and leave out crop insurance and program payments. The app therefore presents the numbers as a comparison, never as
  farm profit.
- The answer changes along 250 km. The gain from replacing fallow with sorghum rises from west to east: about
  −17 USD/acre a year in the driest counties to about +12 in the wettest ones (46 counties, correlation with
  longitude 0.72). At well-managed yields wheat–sorghum–fallow is about −35 USD/acre at Tribune, −2 at Colby and
  +7 at Hays.
- On the same afternoon in late July and August, bare fallow around Tribune was 8 to 10 °F hotter at the surface than
  sorghum (ECOSTRESS, three scenes).
- One rainfall record (NASA POWER) shows a drying trend at Tribune that gridMET, PRISM and GPM IMERG do not show. We
  use POWER for temperature and radiation and do not claim that rain is declining. Cross-checking products is part of
  the method.

### Limits we state in the app

- Gridded weather describes the area, not the single field (2.5 to 30 miles).
- Fields at the same site get almost the same numbers; what differs is their history.
- Wheat is modelled weakly: winterkill, disease, hail and late freezes are not water effects.
- Corn and sunflower have no local trial series; they are the least certain.
- No crop insurance, no government payments, no pests, disease or hail.

### Who it is for and what could come next

It is for a dryland farmer or a crop adviser who wants to see a decision against 30 real years before changing it.
The engine takes weather, soil and a crop table, so it can be run for any water-limited region that has a rotation
trial to check it against. Next steps: a forward run from today's soil moisture for the "This season" view, a
fallow-replacement forage rotation, and a second validation site.

## Space agency data

See [data-and-references.md](data-and-references.md). In one paragraph:

NASA POWER (temperature, radiation, growing degree days, frost dates), NASA GPM IMERG (rainfall cross-check),
NASA GRACE and GRACE-FO (regional water storage), NASA SMAP Level 4 (root-zone soil moisture), NASA/USGS Landsat 5, 7,
8 and 9 (field greenness since 2008), NASA ECOSTRESS (surface temperature), NASA SRTM (slope) and ESA Sentinel-2
(overview image). Together with USDA crop maps, soil survey and statistics, they are fused at field scale: each
dataset has one defined job in the product.

## Use of artificial intelligence

`[TEAM: confirm and complete before submitting. The form must be answered accurately.]`

- The web app (`app/`) was written with Claude Code (Anthropic) under the direction of a team member, who reviewed
  and ran every step. The app's numbers all come from the repository's data files; no figure was generated by an AI
  model.
- `[Other workstreams: say which AI tools were used for pipelines, the engine, documents, images or video, and how.]`
- Trend tests (Mann-Kendall) and the soil-water model are ordinary statistics and process modelling, not machine
  learning.
- No AI-generated images, audio or video are used in the app. `[Confirm for the demo video and slides.]`

## Team

`[TEAM NAME]` — `[MEMBER NAMES AND ROLES: weather and water · fields, soil and vegetation · crops and economics ·
engine and validation · app and story]`

## Tags (if the form asks)

agriculture, crop rotation, drought, soil moisture, dryland farming, decision support, SMAP, GRACE, Landsat,
ECOSTRESS, Kansas
