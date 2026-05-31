# 00 · Cross-cutting open-data platforms

> 🤖 Agent-generated from web research (May 2026). Verify endpoints/licences before use.

These are the **distribution platforms** that carry Berlin traffic data across many
modes. Mode-specific datasets are detailed in their own files; this page is the
"where to look first" map.

## Executive summary

- **Start at two places:** the **Berlin Open Data Portal** (`daten.berlin.de`, CKAN-based catalogue) for curated downloads, and the **Digitale Plattform Stadtverkehr / VIZ Berlin** (`viz.berlin.de` + `api.viz.berlin.de`) for the city's own *live* traffic-management data.
- Berlin's traffic detection (≈240+ counting locations) went **open data around 2020–2021** and the historical archive was **reworked in 2025**. Licence is the permissive **dl-de/by-2.0** (attribution only).
- **Geodata** (infrastructure, road network, parking, cycle lanes) lives in the **Geoportal / FIS-Broker** (now `gdi.berlin.de`), served as WMS/WFS/Atom.
- **Federal layer:** the **Mobilithek** (`mobilithek.info`) is Germany's national access point, merging the old **MDM** marketplace and **mCLOUD**; it standardises road/traffic data as **DATEX II**. The **Mobility Data Space** (Gaia-X) is the federated B2B data-sharing community alongside it.
- **Bottom line:** open, permissively licensed, machine-readable data is genuinely available for most modes — the friction is *discovery* (fragmented across ≥5 portals) and *uneven documentation*, not licence cost.

## Platforms

### 🌐 Berlin Open Data Portal — `daten.berlin.de`
- **What:** the city's central CKAN open-data catalogue. The `verkehr` (traffic) group aggregates datasets from many authorities.
- **Notable traffic datasets in the group:** VBB GTFS schedules; traffic-detection locations & measurements; **Radzähldaten** (bike counts, XLSX); **Berlin zählt Mobilität** (citizen Telraam counts, ADFC+DLR, JSON/CSV); **Baustellen/Sperrungen** (closures, JSON, from VIZ); **Straßenverkehrsunfälle** (accident data, CSV); parking inventories (GeoJSON); taxi/Mietwagen statistics (PDF).
- **Access:** fully open, direct download + CKAN API. No registration.
- **Ratings:** Access ★★★ · Quality ★★☆ (mixed: some live JSON, some stale PDFs) · Coverage ★★☆ (broad but patchy per mode) · Usability ★★☆ (formats range JSON↔PDF).

### 🏛 Digitale Plattform Stadtverkehr (DPS) / VIZ Berlin — `viz.berlin.de`, `api.viz.berlin.de`
- **What:** Berlin's official traffic-management & traveller-information platform, run with **VMZ Berlin Betreibergesellschaft**. "DPS Berlin" reorganised this into machine-readable open interfaces usable with free software.
- **Data:** live + archived **traffic detection** (volume, vehicle class car/truck, speed) at 240+ sites; **construction/closures**; **airport flight arrivals/departures** (`api.viz.berlin.de/fluege`); incident feeds via OCIT-C; a **Masterportal** map front-end.
- **Code:** open-source on GitHub org **`digitale-plattform-stadtverkehr-berlin`** (services for flight data, construction/`service-baustellen`, Masterportal config).
- **Licence:** dl-de/by-2.0, attribution "Digitale Plattform Stadtverkehr Berlin / Verkehrsdetektion Berlin".
- **Ratings:** Access ★★★ · Quality ★★★ (authoritative, live) · Coverage ★★☆ (motorized road focus) · Usability ★★☆ (open APIs but sparse central docs; some endpoints internal).

### 🏛 Geoportal Berlin / FIS-Broker — `gdi.berlin.de` (was `fbinter.stadt-berlin.de`)
- **What:** Berlin's spatial data infrastructure. Authoritative **geodata**: road network (Detailnetz), cycle infrastructure, parking, traffic-area maps (Verkehrsmengenkarte / DTV).
- **Access:** open **WMS/WFS/Atom** services + viewer. dl-de/by-2.0 typical.
- **Ratings:** Access ★★★ · Quality ★★★ · Coverage ★★★ (citywide, authoritative geometry) · Usability ★★☆ (OGC services need GIS know-how; legacy portal UX).

### 🏛 Mobilithek (federal) — `mobilithek.info`
- **What:** Germany's **national access point** for mobility data, merging the former **MDM** (Mobility Data Marketplace) and **mCLOUD**. Standardises road/traffic data via **DATEX II (v2 & v3, CEN/TS 16157)**; mandated channel for some EU ITS-Directive datasets.
- **Relevance to Berlin:** the route by which Berlin/Brandenburg road-authority data (closures, detection, parking) is published nationally and to navigation providers.
- **Access:** registration; mix of open + brokered feeds. SOAP/REST + DATEX II XML.
- **Ratings:** Access ★★☆ (registration, B2B-oriented) · Quality ★★★ (standardised) · Coverage ★★☆ (what authorities choose to publish) · Usability ★★☆ (DATEX II is heavy but standard).

### 🏛/🔒 Mobility Data Space (MDS / Gaia-X) — `mobility-dataspace.eu`
- **What:** federated **data-sharing community** (BMV-funded, Gaia-X) for B2B exchange of mobility data with sovereignty controls; linked with the Mobilithek since H1 2025.
- **Relevance:** where *private* mobility data (sharing operators, FCD, etc.) can be brokered under contracts.
- **Ratings:** Access ★☆☆ (membership/contracts) · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆.

### 🏛 GovData — `govdata.de`
- Federal **metadata aggregator**; mirrors Berlin datasets (e.g. Verkehrsdetektion). Useful for discovery, not a primary source. Access ★★★ · Usability ★★☆.

## Key insight

Provenance and licence are *not* the bottleneck for Berlin road/transit data —
**dl-de/by-2.0 and GTFS make most of it freely reusable**. The real cost is
**integration**: stitching together ≥5 portals (`daten.berlin.de`, `viz.berlin.de`,
`gdi.berlin.de`, `mobilithek.info`, `vbb.de`) plus volunteer APIs, each with its
own format (CKAN JSON, DATEX II, GTFS, WFS, XLSX, PDF) and documentation depth.

## Sources

- [Berlin Open Data – Verkehr group](https://daten.berlin.de/datensaetze?groups=verkehr)
- [Berlin Open Data – Verkehrsdetektion Berlin](https://daten.berlin.de/datensaetze/verkehrsdetektion-berlin)
- [Berlin Open Data – Standorte der Verkehrsdetektion](https://daten.berlin.de/datensaetze/standorte-verkehrsdetektion-berlin)
- [VIZ Berlin (Verkehrsinformationszentrale)](https://viz.berlin.de/en/)
- [DPS Berlin – Verkehrsdetektion API](https://api.viz.berlin.de/daten/verkehrsdetektion)
- [GitHub – digitale-plattform-stadtverkehr-berlin](https://github.com/digitale-plattform-stadtverkehr-berlin)
- [Berliner Verkehrsdaten werden OpenData (Ziller, 2020)](https://stefan-ziller.eu/2020/berliner-verkehrsdaten-werden-opendata/)
- [Mobilithek – DATEX II v3](https://mobilithek.info/blog/datex-2-version-3)
- [Mobility Data Space](https://mobility-dataspace.eu/)
- [DATEX II – German Traffic Data Profile](https://repo.datex2.eu/implementations/profile_directory/german-traffic-data-profile)
- [VMZ Berlin – Traffic Information Centers](https://www.vmzberlin.com/en/kompetenzbereiche/traffic-information-centers/)
