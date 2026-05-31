# Masterportal addon widgets & their data

> 🤖 Agent-generated, verified by live calls 2026-05-31 (config + GetCapabilities +
> GetFeatureInfo + SensorThings). dl-de/by-2.0 platform unless noted.

What the custom **Masterportal addon widgets** on `viz.berlin.de` are, and — the
point of this file — **what data each one draws and from where**. Companion to
[`verkehrslage-los-map.md`](verkehrslage-los-map.md) (which showed a *core* WMS
layer is not an addon); here we cover the actual addons.

## Two kinds of addon (important distinction)

- **`gfiTheme`** — a custom **click-popup renderer**. The map layer is an ordinary
  WMS/GeoJSON/SensorThings layer; the addon only changes how a clicked feature's
  info is *displayed* (e.g. draw a chart). **It is not the data source** — it
  renders whatever the bound layer returns.
- **Tool** — a standalone **menu widget** with its own UI and its own bound
  layers (e.g. an origin-destination flow explorer).

So: **addons are presentation; the data still lives in the same open endpoints**
catalogued in `services-internet.json`. The addon code (DPS GitHub org) tells you
*how it's drawn*; the layer's `url` tells you *where the data is*.

## Executive summary

- **6 addons** ship in the DPS Masterportal (+ a `thermiCam-import` backend):
  `sensorChart`, `airpollution`, `complexObject`, `commuterFlows`,
  `economicTransports`, and the **deprecated** `trafficCount`.
- **`sensorChart` is the detector one** — it charts the **SensorThings/FROST**
  feeds (`TEU`, `EcoCounter`, `Wärmebildkamera`/ThermiCam). So the live
  detector data this whole deep dive is about is exactly what this addon
  visualises. See [`api-reference.md`](api-reference.md).
- **The two `Tool` addons expose genuinely distinct datasets** served from VIZ's
  **`euvm`** GeoServer workspace:
  - **`commuterFlows`** → **origin–destination commuter flows with modal split**
    (`car/pt/ride/walk/bike` counts per Wohnort→Arbeitsort), plus MIV/ÖPNV route
    lines. Route geometry rides on **INRIX "XD" segment IDs**.
  - **`economicTransports`** → modelled **commercial-traffic (Wirtschaftsverkehr)**
    routes carrying **`anzahl_kep_trips`** (courier/parcel-like trips per segment).
- **`airpollution`** renders modelled **NO₂ / PM₁₀ / PM₂.₅** street forecasts
  (traffic-linked air quality); **`complexObject`** is a generic popup used for the
  **chargecloud EV-charging** live-status feed.
- **Bottom line:** the addons surface several open datasets *beyond* the detector
  feed — most interestingly **modelled commuter & freight OD flows** (with mode
  split and KEP trip counts) — but they are **rendered WMS/GeoJSON** (per-feature
  via `GetFeatureInfo`), not bulk/downloadable, and the OD layers are **modelled**
  (mixed/commercial provenance), so treat them as indicative, not ground truth.

## The addons & their data

### 🏛 `sensorChart` (gfiTheme, Vue) — live detector charts
- **Bound layers (SensorThings):** `TEU` (`FROST-Server-TEU`), `EcoCounter`
  (`FROST-Server-EcoCounter2`), `Wärmebildkamera` (`FROST-Server-ThermiCam`); each
  loaded with `$select=@iot.id,name,description,properties&$expand=Locations(...)`.
- **Data dimensions:** per-cross-section time series of count & speed × vehicle
  class × 5min/hour/day/week/month/year (see [`api-reference.md`](api-reference.md)).
- **Provenance/state:** 🏛 official; ThermiCam+EcoCounter live, TEU frozen (~2025-07).
- **Ratings:** Access ★★★ · Quality ★★★ · Coverage ★★☆ (detector sites) · Usability ★★★.

### 🏛 `commuterFlows` (Tool) — commuter origin–destination flows
- **Source:** `api.viz.berlin.de/geoserver/euvm/ows` (WMS). Layers: `einpendler`,
  `auspendler`, `pendlerstreckenmiv`, `pendlerstreckenopnv`, plus `fussverkehr_*`
  / `radverkehr_*` start/ziel OD points.
- **Data dimensions (verified):** OD records — `wohnort`/`arbeitsort` (+ Ortsteil/
  Stadt), `richtung` (Ein-/Auspendler), and **mode-split counts** `car, pt, ride,
  walk, bike` (e.g. `car:30, pt:50, ride:20`). MIV route lines carry INRIX `xdsegid`,
  `frc`, `roadname`.
- **Provenance:** 🏛 published by VIZ, but the OD + modal split is **modelled**
  (route geometry on the **INRIX XD** network → commercial-derived inputs). Treat as
  modelled, not measured.
- **Ratings:** Access ★★☆ (open WMS, but rendered/no bulk) · Quality ★★☆ (modelled) ·
  Coverage ★★★ (region-wide OD) · Usability ★★☆ (GetFeatureInfo, not a clean OD matrix).

### 🏛 `economicTransports` (Tool) — commercial / KEP traffic routes
- **Source:** `…/geoserver/euvm/ows` (WMS). Layers: `wv_strecken`, `wv_start`,
  `wv_ziel` (Wirtschaftsverkehr); shown as "Strecken KEP-ähnlicher-Verkehre".
- **Data dimensions (verified):** road segments with `roadname`, `frc`, and
  **`anzahl_kep_trips`** (modelled courier/parcel-like trips per segment, e.g. 93 on
  Koppenstraße). Complements the freight survey gap noted in [`../02-freight.md`](../02-freight.md).
- **Provenance:** 🏛 VIZ, **modelled** commercial-traffic estimates.
- **Ratings:** Access ★★☆ · Quality ★★☆ (modelled) · Coverage ★★☆ · Usability ★★☆.

### 🏛 `airpollution` (gfiTheme) — traffic-linked air-quality forecast
- **Source:** `…/geoserver/mdh/ows` (WMS). Layers: `umwelt_lines_no2 / _pm10 /
  _pm2_5` (street-line forecasts) and `inwt_wmst_*` (station points), as
  "Luftschadstoff-Prognose NO₂/PM₁₀/PM₂.₅" at street and LOR (planning-area) level.
- **Data dimensions:** modelled pollutant concentration per street/area (forecast).
- **Provenance:** 🏛 modelled (traffic-emissions model).
- **Ratings:** Access ★★★ (open WMS) · Quality ★★☆ (modelled forecast) · Coverage ★★★ · Usability ★★☆.

### 🏛 `complexObject` (gfiTheme) — generic structured popup
- **Bound layer:** `Ladestationen` — chargecloud EV-charging live status
  (`…/e-infoplattform/chargecloud/lade-standort/geojsondps`). A reusable popup theme
  for nested/structured feature attributes (here: charger availability).
- ⚠️ The chargecloud endpoint returned `{message, statusCode}` (empty/guarded) when
  queried, so live fields couldn't be captured — verify separately.
- **Ratings:** Access ★★☆ · Quality ★★☆ (unverified at query time) · Coverage ★★☆ · Usability ★★☆.

### 🪦 `trafficCount` (gfiTheme) — **DEPRECATED**
- The standard Masterportal Eco-Counter/Zählstellen popup; superseded by
  `sensorChart`. A related custom `verkehrsstaerken` theme is still bound to a
  "Verkehrsdetektion – Tagesmittel" WMS (`mdh/wms`, detector daily-mean volumes).
- **Ratings:** n/a (retired) — use `sensorChart`.

## Addon → repo → data, at a glance

| Addon (kind) | DPS repo | Bound data | Endpoint |
| ------------ | -------- | ---------- | -------- |
| sensorChart (gfiTheme) | `masterportal-addon-sensor-chart` | detector time series | `FROST-Server-{TEU,EcoCounter2,ThermiCam}` |
| commuterFlows (Tool) | `masterportal-addon-commuter-flows` | commuter OD + mode split | `geoserver/euvm/ows` |
| economicTransports (Tool) | `masterportal-addon-economic-transports` | KEP/freight trip routes | `geoserver/euvm/ows` |
| airpollution (gfiTheme) | `masterportal-addon-airpollution` | NO₂/PM forecasts | `geoserver/mdh/ows` |
| complexObject (gfiTheme) | `masterportal-addon-complex-object` | chargecloud EV status | `e-infoplattform/chargecloud/…` |
| trafficCount (gfiTheme) | `masterportal-addon-traffic-count` ⚠️dep. | (was) counter popups | — |

## Key insight

The addons confirm a pattern: **`viz.berlin.de` is a thin Masterportal presentation
layer over many open endpoints**, and the *interesting* addon-only data is **not**
the detectors (those are the open SensorThings feeds the `sensorChart` just draws)
— it's the **modelled OD products in the `euvm` workspace**: commuter flows *with
modal split* and commercial/KEP trip volumes per segment. Those partly fill gaps
that open *measured* data leaves (freight in [`../02-freight.md`](../02-freight.md),
pedestrian OD in [`../05-pedestrian.md`](../05-pedestrian.md)) — but they are
**modelled, rendered (WMS GetFeatureInfo), and not bulk-downloadable**, with INRIX
inputs in the mix, so use them as indicative context, not authoritative counts.

## Sources

- [DPS GitHub org (addon repos)](https://github.com/orgs/digitale-plattform-stadtverkehr-berlin/repositories)
- [`masterportal-dps-config` – services-internet.json](https://github.com/digitale-plattform-stadtverkehr-berlin/masterportal-dps-config/blob/master/resources/services-internet.json)
- euvm WMS GetCapabilities: `https://api.viz.berlin.de/geoserver/euvm/ows?service=WMS&request=GetCapabilities`
- mdh WMS GetCapabilities: `https://api.viz.berlin.de/geoserver/mdh/wms?service=WMS&request=GetCapabilities`
- SensorThings detail: [`api-reference.md`](api-reference.md) · Verkehrslage: [`verkehrslage-los-map.md`](verkehrslage-los-map.md)
