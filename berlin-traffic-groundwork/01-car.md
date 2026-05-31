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
- **Congestion/floating-car** is mostly **commercial** (TomTom, INRIX, HERE) —
  see [`07-commercial.md`](07-commercial.md). The city's own real-time "level of
  service" comes from the detector network.
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

### 🏛 Verkehrsmengenkarte / DTVw — SenMVKU (Umweltatlas 07.01)
- **What:** modelled **average weekday traffic volume** per network segment;
  breaks out Kfz, **trucks >3.5 t**, buses, motorcycles, **and bicycles**.
  Editions: 2023, 2019, 2014, 2005, 1998 (time series). Conversion factors
  published for deriving DTV/peak-hour values.
- **Access:** open download + **WMS/WFS**; also in FIS-Broker. Updated 2024-12-06.
- **Ratings:** Access ★★★ · Quality ★★☆ (modelled/periodic, not live) ·
  Coverage ★★★ (whole main network, multi-modal volumes) · Usability ★★☆ (GIS).

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

### 🏛 Environmental zone / regulation (Umweltzone, vehicle registrations)
- **What:** Berlin's low-emission **Umweltzone** boundary (geodata in
  FIS-Broker); KBA vehicle-registration stats (federal); taxi/Mietwagen
  concession statistics on the portal (PDF). Context layers rather than flow data.
- **Ratings:** Access ★★☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆ (often PDF).

## Access cheat-sheet

| Need | Best source | Format | Live? |
| ---- | ----------- | ------ | ----- |
| Real-time volume/speed at a point | TEU detectors (VIZ) | JSON/CSV | ✅ |
| Network-wide volume per street | Verkehrsmengenkarte DTVw | WMS/WFS | ❌ (periodic) |
| Where crashes happen | Unfallatlas | CSV/SHP | ❌ (yearly) |
| Congestion / travel-time index | TomTom/INRIX/HERE (commercial) | API | ✅ |
| Parking inventory | District GeoJSON/CSV | varies | ❌ |

## Key insight

Berlin gives you **authoritative live point data** (detectors) and
**authoritative periodic network data** (DTV map) for free — but **no open,
citywide, real-time floating-car / travel-time layer**. That gap is exactly what
commercial providers sell, and it's the single most likely reason a project would
need a paid source.

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
