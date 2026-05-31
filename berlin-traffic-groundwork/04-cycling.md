# 04 · Cycling

> 🤖 Agent-generated from web research (May 2026). Verify figures/endpoints before use.

Covers bicycle traffic: automatic counters, network/infrastructure geodata,
citizen-science, and crowd-sourced flow.

## Executive summary

- **Berlin is unusually data-rich for cycling**, with both *official* and *grassroots*
  sources:
  - **~20 automatic permanent bike counters** (Eco-Counter hardware), directional +
    cross-section, **updated daily (T-1)**, open on `daten.berlin.de`. Programmatically
    reachable via the **Eco-Counter API** (Berlin org ID **4728**, "Verkehrslenkung Berlin").
  - **Cycle-network geodata** — `Radverkehrsnetz` (per Mobility Act MobG BE) and
    `Radverkehrsanlagen` / GPS route tracks — open as **WFS/GeoJSON**.
  - **Modelled volumes:** the **Verkehrsmengenkarte (DTVw)** also includes a **bicycle**
    layer per segment (see [`01-car.md`](01-car.md)).
- **Citizen science / unofficial:** **RADmesser** (Tagesspiegel) — 100 volunteers, Aug–Nov
  2018, **~16,700 overtakes** measured (56% illegally close), open as GeoJSON/CSV keyed to
  the FIS-Broker "Detailnetz". **Berlin zählt Mobilität** — ADFC+DLR citizen **Telraam**
  counters, JSON/CSV.
- **Crowd-sourced flow:** **Strava Metro** (aggregated GPS cycling) — free to public
  agencies but **biased to sport/commute cyclists** and access-gated.
- **Bottom line:** great for **where people cycle** (network + counters + crowd data) and
  **safety context** (overtaking, accidents). Weaker on **complete, unbiased citywide
  volumes** — counters are sparse (~20 sites) and crowd data is self-selected.

## Sources & ratings

### 🏛 Permanent bike counters — VIZ / `daten.berlin.de` (Eco-Counter)
- **What:** ~20 fixed automatic counting stations; **hourly/daily**, by direction and total.
  Map + barometer displays. Org ID **4728** on the Eco-Counter API.
- **Access:** open download (portal) + Eco-Counter API (community client `eco-counter-client`).
  Updated daily to previous day.
- **Ratings:** Access ★★★ · Quality ★★★ (sensor-grade, long series) ·
  Coverage ★★☆ (only ~20 points citywide) · Usability ★★★.

### 🏛 Cycle-network & infrastructure geodata — FIS-Broker / `daten.berlin.de`
- **What:** `Radverkehrsnetz` (WFS), `Radverkehrsanlagen`, **GPS tracks of cycle routes**,
  "Detailnetz" base. The conceptual + physical cycle network.
- **Access:** open **WFS/GeoJSON/GPX**; dl-de/by-2.0.
- **Ratings:** Access ★★★ · Quality ★★☆ (geometry/attribute completeness varies) ·
  Coverage ★★★ (citywide network) · Usability ★★☆ (GIS/OGC).

### 🏛 Verkehrsmengenkarte — bicycle layer (DTVw)
- Modelled **average weekday bicycle volumes** per segment; open WMS/WFS. See [`01-car.md`](01-car.md).
- Ratings: Access ★★★ · Quality ★★☆ (modelled/periodic) · Coverage ★★★ · Usability ★★☆.

### 🤝 RADmesser (Tagesspiegel) — overtaking / safety citizen science
- **What:** open dataset of **overtaking distances** on segments (GeoJSON/CSV, keyed to
  Detailnetz). One-off 2018 campaign; safety-focused, not continuous flow.
- **Access:** open on GitHub (`tagesspiegel/radmesser`).
- **Ratings:** Access ★★★ · Quality ★★☆ (volunteer sample, dated) ·
  Coverage ★★☆ (routes the 100 riders took) · Usability ★★★ (clean GeoJSON).

### 🤝 Berlin zählt Mobilität (ADFC + DLR, Telraam)
- **What:** citizen-operated low-cost **Telraam** sensors counting bikes/cars/peds/trucks;
  community coverage that grows where residents install devices.
- **Access:** open JSON/CSV on `daten.berlin.de`; also Telraam platform.
- **Ratings:** Access ★★★ · Quality ★★☆ (consumer-sensor accuracy, classification limits) ·
  Coverage ★★☆ (opportunistic, resident-driven) · Usability ★★☆.

### 🔒 Strava Metro — crowd-sourced cycling GPS
- **What:** aggregated, de-identified ride GPS at street-segment level; useful for relative
  flow/desire lines.
- **Access:** free to **public agencies/researchers** via application; **not open**; biased
  sample (fitness/commute app users). See [`07-commercial.md`](07-commercial.md).
- **Ratings:** Access ★☆☆ (gated) · Quality ★★☆ (large but biased) · Coverage ★★★ (dense) ·
  Usability ★★☆.

## Access cheat-sheet

| Need | Best source | Format | Live? |
| ---- | ----------- | ------ | ----- |
| Continuous counts at fixed points | Bike counters (Eco-Counter) | CSV/API | ~daily |
| Where the cycle network is | Radverkehrsnetz WFS | WFS/GeoJSON | ❌ |
| Relative flow / desire lines citywide | Strava Metro | GIS export | ❌ (periodic) |
| Safety / overtaking | RADmesser | GeoJSON/CSV | ❌ (2018) |
| Citizen multi-modal counts | Berlin zählt Mobilität | JSON/CSV | ~daily |

## Key insight

Cycling is the mode where **unofficial/citizen data meaningfully extends official
data**: the city gives you precise but **sparse** counters and complete network
geometry, while RADmesser, Telraam and Strava fill in **spatial breadth and
safety** — at the cost of **sampling bias**. A robust picture blends counters
(ground truth) with crowd data (coverage), not either alone.

## Sources

- [VIZ Berlin – Bike Counters (EN)](https://viz.berlin.de/en/traffic-in-berlin/bike-traffic/)
- [derhuerst/eco-counter-client](https://github.com/derhuerst/eco-counter-client)
- [Berlin Open Data – Radverkehrsnetz (WFS)](https://daten.berlin.de/datensaetze/radverkehrsnetz-wfs-086cf065)
- [Berlin Open Data – Radrouten und Radverkehrsanlagen (GPS-Tracks)](https://daten.berlin.de/datensaetze/radrouten-und-radverkehrsanlagen--gps-tracks-fur-die-radrouten-durch-berlin)
- [tagesspiegel/radmesser – opendata](https://github.com/tagesspiegel/radmesser/blob/master/opendata/README.md)
- [Technologiestiftung – Data Dive: Radverkehrsdaten in Berlin](https://lab.technologiestiftung-berlin.de/projects/datadive-cycling/de/)
- [Counting cyclists in Berlin (B. Callander)](https://www.briancallander.com/posts/cycling_in_berlin/counting_cyclists.html)
- [Eco-Counter – Bike & Pedestrian map](https://eco-display-map.eco-counter.com/)
