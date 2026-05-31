# 03 · Public transport

> 🤖 Agent-generated from web research (May 2026). Verify endpoints/limits before use.

Covers U-Bahn, tram, bus (BVG), S-Bahn, and regional rail across the
**VBB** (Verkehrsverbund Berlin-Brandenburg) area.

## Executive summary

- **This is Berlin's best-served data domain — by a wide margin.** VBB publishes
  **official, openly licensed (CC-BY 4.0)** static and real-time feeds:
  - **GTFS static** schedules, refreshed **twice weekly (Wed & Fri)**, on the
    Berlin open-data portal.
  - **GTFS-Realtime** at **`production.gtfsrt.vbb.de`** — **CC-BY 4.0, no auth,
    ~60 req/min** (staging at `staging.gtfsrt.vbb.de`).
- A **HAFAS** backend (HaCon) powers journey planning; community-run
  **transport.rest** wrappers (`v6.vbb.transport.rest`, `v6.bvg.transport.rest`)
  expose clean JSON REST (departures, journeys, nearby vehicles) for free.
- **Ridership context (2024):** BVG ≈ **1.12 bn** passenger journeys (≈2019 record
  level); **S-Bahn Berlin ≈ 456 m** (−3.6% vs 2023, GDL strikes); VBB-wide +2.8%.
  These are in annual reports (**BVG Zahlenspiegel**, PDFs), not feeds.
- **Bottom line:** for schedules and live vehicle/delay data, Berlin is a
  best-in-class open-data city. The only real gaps are **historical RT archives**
  (you must record the live feed yourself) and **fine-grained boarding/occupancy
  counts** (aggregate-only, in PDFs).

## Sources & ratings

### 🏛/🌐 VBB GTFS static — `daten.berlin.de` / `unternehmen.vbb.de`
- **What:** full timetable (stops, routes, trips, calendar) for all VBB operators
  incl. BVG, S-Bahn, regional. Updated **twice weekly**.
- **Licence/format:** **CC-BY 4.0**; standard GTFS zip. No registration.
- **Ratings:** Access ★★★ · Quality ★★★ · Coverage ★★★ (whole VBB area, all PT modes) ·
  Usability ★★★ (GTFS = universal standard).

### 🏛 VBB GTFS-Realtime — `production.gtfsrt.vbb.de`
- **What:** live **trip updates / delays** (and vehicle info) as GTFS-RT protobuf.
- **Access:** **no auth, ~60 requests/min**; CC-BY 4.0. Staging endpoint available.
- **Ratings:** Access ★★★ · Quality ★★★ · Coverage ★★★ · Usability ★★★.
- ⚠️ No official long-term **archive** — capture it yourself for historical analysis.

### 🏛 VBB/BVG HAFAS API (HaCon backend)
- **What:** the production journey-planning API behind official apps; richest query
  surface (routing, real-time positions, messages). Not formally "open" but reachable.
- **Ratings:** Access ★★☆ (semi-public, undocumented) · Quality ★★★ ·
  Coverage ★★★ · Usability ★★☆ (proprietary protocol → use a wrapper).

### 🤝 transport.rest wrappers — `v6.vbb.transport.rest`, `v6.bvg.transport.rest`
- **What:** community (derhuerst) REST/JSON facades over HAFAS: departures,
  arrivals, journeys, stop search, **vehicles in a bounding box**. Also
  `bvg-rest`/`vbb-rest` self-hostable; an **unofficial GTFS-RT** server
  (`berlin-gtfs-rt-server`) polls HAFAS to synthesize a feed.
- **Access:** free public instances; self-host for reliability. No key.
- **Ratings:** Access ★★★ · Quality ★★☆ (depends on upstream) · Coverage ★★★ ·
  Usability ★★★ (clean JSON) — but ⚠️ best-effort uptime; can break on HAFAS changes.

### 🏛 Ridership / performance statistics
- **What:** **BVG Zahlenspiegel** & "BVG in Zahlen" (annual, PDF); S-Bahn press
  releases; VBB press; **Amt für Statistik Berlin-Brandenburg** "Personenverkehr
  mit Bussen und Bahnen". Aggregate journeys, vehicle-km, network size.
- **Access:** open PDFs / statistical tables. Not granular, not live.
- **Ratings:** Access ★★★ · Quality ★★☆ (aggregate) · Coverage ★★☆ · Usability ★☆☆ (PDF).

### 🌐 Fares & geodata
- **What:** VBB also publishes **fare data** and **stop/line geodata**; GTFS already
  carries stop geometry; OSM has rich station detail.
- **Ratings:** Access ★★★ · Quality ★★☆ · Coverage ★★★ · Usability ★★☆.

## Access cheat-sheet

| Need | Best source | Format | Live? |
| ---- | ----------- | ------ | ----- |
| Timetables / network graph | VBB GTFS | GTFS zip | ❌ (2×/week) |
| Live delays / trip updates | VBB GTFS-RT | protobuf | ✅ |
| Easy JSON departures/journeys | transport.rest (`v6.vbb`/`v6.bvg`) | JSON | ✅ |
| Vehicle positions in an area | transport.rest `/radar` | JSON | ✅ |
| Ridership totals | BVG Zahlenspiegel / Stat. office | PDF/tables | ❌ (annual) |

## Key insight

Public transport inverts the citywide pattern: here the **official open feeds are
so good** that the community wrappers exist mainly for *developer convenience*, not
to fill gaps. Plan to **self-host or archive** the RT feed if you need history or
guaranteed uptime — that, plus the absence of open occupancy data, are the only
meaningful limitations.

## Sources

- [Offene Datensätze des VBB](https://unternehmen.vbb.de/digitale-services/datensaetze/)
- [Berlin Open Data – VBB-Fahrplandaten via GTFS](https://daten.berlin.de/datensaetze/vbb-fahrplandaten-via-gtfs)
- [VBB GTFS-Realtime Feed](https://production.gtfsrt.vbb.de/)
- [transport.rest](https://transport.rest/)
- [v6.vbb.transport.rest API docs](https://v6.vbb.transport.rest/api.html)
- [v6.bvg.transport.rest API docs](https://v6.bvg.transport.rest/api.html)
- [derhuerst/berlin-gtfs-rt-server](https://github.com/derhuerst/berlin-gtfs-rt-server)
- [public-transport/state-of-the-open – vbb.md](https://github.com/public-transport/state-of-the-open/blob/master/vbb.md)
- [BVG Zahlenspiegel 2024 (PDF)](https://www.bvg.de/dam/jcr:ac133665-f048-4d1d-b415-e9189d5f3665/BVG-Zahlenspiegel-2024.pdf)
- [VBB – Fahrgastzahlen 2024](https://unternehmen.vbb.de/presse/oepnv-in-berlin-und-brandenburg-auf-hohem-niveau-stabil/)
- [S-Bahn Berlin – Fahrgastzahlen](https://sbahn.berlin/das-unternehmen/presse/pressemitteilungen-pressearchiv/pressemitteilungen/fast-eine-halbe-milliarde-menschen-fahren-mit-der-berliner-s-bahn/)
- [Amt für Statistik Berlin-Brandenburg – Personenverkehr](https://www.statistik-berlin-brandenburg.de/h-i-5-5j/)
