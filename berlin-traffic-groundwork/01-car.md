# 01 · Car / motorized individual traffic

> 🤖 Agent-generated from web research (May 2026). Verify figures/endpoints before use.

Covers private cars and general motor-vehicle (Kfz) flow: counts, speeds,
congestion, accidents, parking, and the environmental/regulatory layer.

## Executive summary

- **Two complementary official products:** (1) the **detector network** — 240+
  **"Traffic Eye Universal" (TEU)** infrared sensors measuring volume, vehicle
  class (car/truck), and speed, with live + hourly-archived data via DPS/VIZ; and
  (2) the **Verkehrsmengenkarte** — modelled **DTVw** (average weekday daily
  traffic) over the whole main road network, published as map/WMS/WFS by the
  Senate (SenUVK / SenMVKU).
- **Both are open** (dl-de/by-2.0). The detector data is the best *live/temporal*
  source; the DTV map is the best *spatial/network-wide* source. They answer
  different questions.
- **Accidents:** the **Unfallatlas** (Destatis, since 2016) gives geocoded
  injury-accident data including cars — CSV + shapefile, open. Berlin also
  publishes yearly accident CSVs on `daten.berlin.de`.
- **Congestion/floating-car:** the city exposes its own citywide
  **level-of-service (LOS)** layer — VMZ's `vmzlos` network with per-link
  `los`/`speedavg`/`freeflowspeed`/`traveltime`, **publicly reachable** as
  **WMS/WFS** (the red/yellow/green Verkehrslage map; readable via
  `GetFeatureInfo`/`GetFeature`). ⚠️ But it is **INRIX-sourced floating-car data
  with no open licence** (≠ the dl-de/by-2.0 detector archive), rendered-only (no
  bulk/historical export, no timestamp). See the deep dive
  [`teu-detectors-viz-api/verkehrslage-los-map.md`](teu-detectors-viz-api/verkehrslage-los-map.md).
  For **licensed, bulk, or historical** floating-car data you still go
  **commercial** (TomTom, INRIX, HERE — [`07-commercial.md`](07-commercial.md)).
- **Parking** data is **fragmented by district** (some GeoJSON/CSV per Bezirk),
  no unified citywide open inventory.

## Sources & ratings

### 🏛 Traffic detection network (TEU detectors) — DPS/VIZ + daten.berlin.de
- **What:** 240+ fixed locations; per-vehicle counts, classification (Kfz/Lkw),
  speed. **Live** feed at `viz.berlin.de` / `api.viz.berlin.de`; **archive** as
  hourly per-location records on the open-data portal. Historical archive
  **revised in 2025** (re-check documentation for breaks in the series).
- **Format/licence:** CSV/JSON; dl-de/by-2.0.
- **Ratings:** Access ★★★ · Quality ★★★ (authoritative, classified, live) ·
  Coverage ★★☆ (main network only; not every street) · Usability ★★☆.
- 🔬 **Deep dive (with reproducible live queries):** [`teu-detectors-viz-api/`](teu-detectors-viz-api/) — the live OGC **SensorThings/FROST** APIs + the Azure-blob history archive, schema, tools, and a curl-only Torstraße query. ⚠️ **Caveat found:** the infrared **TEU feed is frozen (~2025-07-02)** and the blob archive **ends 2025-06** — Berlin is mid-migration to **thermal cameras** (live, but only 67 sites so far; none on Torstraße). Live ≠ complete right now.
- 🔬 **Single-site deep dive:** [`tc073-deepdive/`](tc073-deepdive/) — every 5-min PKW count & speed for thermal-cam **TC073 (Straße des 17. Juni)**, with time-series/diurnal/statistical graphs and a breaks-&-outliers analysis that separates **real closures** (29 Mar Half-Marathon → zeros) from **measurement artefacts** (a silent May count-doubling, sensor dropouts/outages). Reproducible + gentle-on-API pipeline; raw data not committed.

### 🏛 Verkehrsmengenkarte / DTVw — SenMVKU (Umweltatlas 07.01)
- **What:** modelled **average weekday traffic volume** per network segment;
  breaks out Kfz, **trucks >3.5 t**, buses, motorcycles, **and bicycles**.
  Editions: 2023, 2019, 2014, 2005, 1998 (time series). Conversion factors
  published for deriving DTV/peak-hour values.
- **Access:** open download + **WMS/WFS**; also in FIS-Broker. Updated 2024-12-06.
- **Ratings:** Access ★★★ · Quality ★★☆ (modelled/periodic, not live) ·
  Coverage ★★★ (whole main network, multi-modal volumes) · Usability ★★☆ (GIS).
- 🔬 **Reference:** [`dtv-dtvw-reference.md`](dtv-dtvw-reference.md) — exactly where to get
  **DTVw** vs **DTV**, their meaning, editions/time range, status/licence, the official
  **DTVw→DTV factors** (0.91 Kfz / 0.82 Lkw), and how DTV relates to Berlin's street categories.

### 🏛/🌐 Straßenverkehrsunfälle + Unfallatlas — Destatis / Berlin
- **What:** geocoded **injury accidents** with mode flags (car, bike, motorcycle,
  pedestrian, lorry), date/time, road & light conditions. Unfallatlas covers all
  Germany from 2016; Berlin yearly CSVs (e.g. 2020, 2021) on the portal.
- **Format/licence:** CSV + Shapefile; open (interactive map at unfallatlas.statistikportal.de).
- **Ratings:** Access ★★★ · Quality ★★★ (national standard, geocoded) ·
  Coverage ★★★ (all injury accidents) · Usability ★★★ (clean CSV/SHP; well-used by analysts).

### 🌐 Parking (Parkraum) — district datasets
- **What:** parking-space inventories and ticket-machine (PSA) locations,
  published **per Bezirk** (e.g. Charlottenburg-Wilmersdorf GeoJSON, Pankow PSA
  XLSX/CSV). No unified citywide live availability feed in open data.
- **Ratings:** Access ★★☆ · Quality ★★☆ · Coverage ★☆☆ (district-patchwork) ·
  Usability ★★☆.

### 🏛/🌐 Legal speed limits (Tempolimits) — SenMVKU Geoportal + OSM
- **What:** the **posted/ordered** limit of a street (≠ the *measured* speed in the
  detector feeds or the `vmzlos` free-flow reference). Authoritative open source is
  SenMVKU's **`Tempolimits` WFS/WMS** in the Geoportal (`gdi.berlin.de`,
  `tempolimits:hoechstgeschwindigkeit`, **29,800 segments**, dl-de/**zero**-2.0) — but it
  stores **only deviations from the default 50** (95.6 % are Tempo 30). **OSM `maxspeed`**
  is the citywide complement (~94.8 % of drivable ways tagged; ODbL).
- 🔬 **Deep dive:** [`speed-limits/`](speed-limits/) — live WFS/Overpass verification,
  full schema, speed-value distribution, reproducible queries, and the VIZ/DATEX II story.
- **Ratings:** Access ★★★ · Quality ★★★ (Geoportal authoritative) · Coverage ★★☆
  (Geoportal = exceptions only; OSM fills the rest) · Usability ★★☆ (OGC/GIS).

### 🏛 Environmental zone / regulation (Umweltzone, vehicle registrations)
- **What:** Berlin's low-emission **Umweltzone** boundary (geodata in
  FIS-Broker); KBA vehicle-registration stats (federal); taxi/Mietwagen
  concession statistics on the portal (PDF). Context layers rather than flow data.
- **Ratings:** Access ★★☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆ (often PDF).

## Access cheat-sheet

| Need | Best source | Format | Live? |
| ---- | ----------- | ------ | ----- |
| Real-time volume/speed at a point | TEU detectors (VIZ) | JSON/CSV | ✅ |
| Legal/posted speed limit of a street | Geoportal `Tempolimits` WFS (+ OSM `maxspeed` to fill default-50) | WFS/WMS · OSM | ❌ (static) |
| Network-wide volume per street | Verkehrsmengenkarte DTVw | WMS/WFS | ❌ (periodic) |
| Where crashes happen | Unfallatlas | CSV/SHP | ❌ (yearly) |
| Current congestion / LOS / link speed (public, but INRIX-sourced, no open licence) | VMZ `vmzlos` Verkehrslage | WMS/WFS (+GetFeatureInfo) | ✅ (rendered; no history) |
| Bulk/historical floating-car & travel-time | TomTom/INRIX/HERE (commercial) | API | ✅ |
| Parking inventory | District GeoJSON/CSV | varies | ❌ |

## Key insight

Berlin gives you **authoritative live point data** (detectors) and
**authoritative periodic network data** (DTV map) for free — and, via VMZ's
**`vmzlos` Verkehrslage WMS/WFS**, a citywide **current LOS / travel-time** layer is
**publicly reachable**. But that layer is **INRIX-sourced floating-car data with no
open licence** (don't conflate it with the dl-de/by-2.0 detector archive), rendered
only, with no bulk/historical export or timestamp. So what's still *not* openly &
reusably available is **licensed, bulk, historical floating-car data** — that gap is
what commercial providers (TomTom, INRIX, HERE) sell and the most likely reason to pay.

## Sources

- [SenMVKU – Verkehrserhebungen (Verkehrsmengenkarte)](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsmanagement/verkehrserhebungen/)
- [Berlin.de – Traffic data (EN)](https://www.berlin.de/sen/uvk/en/mobility-and-transport/traffic-data/)
- [Berlin Open Data – Verkehrsmengen DTVw 2023 (WMS)](https://daten.berlin.de/datensaetze/verkehrsmengen-dtvw-2023-wms-efc1dc7a)
- [Umweltatlas – Traffic Volumes ADT (EN)](https://www.berlin.de/umweltatlas/en/traffic-noise/traffic-volumes/)
- [Berlin Open Data – Verkehrsdetektion Berlin](https://daten.berlin.de/datensaetze/verkehrsdetektion-berlin)
- [DPS – Verkehrsdetektion API](https://api.viz.berlin.de/daten/verkehrsdetektion)
- [Unfallatlas (Destatis)](https://unfallatlas.statistikportal.de/?BL=BE)
- [data.europa.eu – Berlin road accidents 2021](https://data.europa.eu/data/datasets/3530c81b-a649-4056-85ef-9ecf1da7f1f7?locale=en)
- [Umrechnungsfaktoren von Verkehrsmengen (PDF)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsdaten/umrechungsfaktoren-von-verkehrsmengen/hinweise-und-faktoren-zur-umrechnung-von-verkehrsmengen.pdf)
