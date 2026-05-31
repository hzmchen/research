# The Verkehrslage (red/yellow/green) map — data source

> 🤖 Agent-generated, verified by live calls 2026-05-31. Answers: *where does
> [`viz.berlin.de/verkehr-in-berlin/verkehrslage`](https://viz.berlin.de/verkehr-in-berlin/verkehrslage/)
> get its traffic-condition colours, and is it a Masterportal addon?*

## TL;DR

- The red/yellow/green congestion map is a **WMS layer `vmzlos-step`** served from
  **VIZ's own GeoServer**: `https://api.viz.berlin.de/geoserver/mdh/wms`
  (+ a cached **WMTS** variant `verkehrslage_gwc`). `vmzlos` = **VMZ Berlin Level
  Of Service**.
- It is **NOT a Masterportal addon.** It's an ordinary **WMS layer** declared in
  the portal's `services-internet.json` and drawn by **Masterportal core**. The
  *addons* (e.g. `masterportal-addon-sensor-chart`) are separate widgets for the
  detector **point charts**; the Verkehrslage page is the same Masterportal app
  that *can* host addons, but the colour map itself is plain WMS.
- The layer is a **road-network link graph**: each feature is a road segment with
  **`los`** (level-of-service class → the colour), **`speedavg`**,
  **`freeflowspeed`**, **`traveltime`**, plus topology (`from_node`/`to_node`,
  `unique_id`), `strkat_1/2` (road category) and `closed`.
- It is therefore a **travel-time / floating-car-style** product covering a far
  denser network than the 276 TEU detector sites — a *different* data product from
  the (frozen) detector archive. ⚠️ Freshness could not be dated (no `TIME`
  dimension / no published "Stand" timestamp), but the layer returns **populated
  current `los`/`speedavg` values**, i.e. it is not empty/decommissioned.

## The layers (from `services-internet.json`)

| id | name | typ | url | layer |
| -- | ---- | --- | --- | ----- |
| `Verkehrslage` | Verkehrslage | WMS 1.1.1 | `…/geoserver/mdh/wms?` | `vmzlos-step` |
| `Verkehrslage highcontrast` | — | WMS | same | `vmzlos-step-highcontrast` |
| `Verkehrslage-Overview` | Verkehrslage Gesamt | WMS | same | `vmzlos-step-overview` |
| `verkehrslage_gwc` | Verkehrslage | WMTS (GeoWebCache tiles) | `…/geoserver/mdh/gwc/…` | `vmzlos-step` |

GeoServer style is **`los`** (legend `…/geoserver/www/legende_los.png`); the
colour ramp is the LOS class.

## What's behind the colours (real GetFeatureInfo)

The WMS layer is `queryable="1"`, so `GetFeatureInfo` returns the underlying
features. Example responses (queried 2026-05-31, central Berlin):

```json
{"gid":10435,"unique_id":"47550026_47550012.02_47550026",
 "from_node":"47550026","to_node":"47550012","strkat_1":"I","strkat_2":"B",
 "closed":0,"los":1,"speedavg":14.7,"freeflowspeed":30.11,"traveltime":31.5}
{"gid":10437,"...":"...","los":2,"speedavg":23.34,"freeflowspeed":39.67,"traveltime":16.44}
```

So the colour = **`los`**, derived per link from **`speedavg` vs `freeflowspeed`**
(here a link at 14.7 km/h vs 30 free-flow → `los 1`, the most-congested band).
`traveltime` is the modelled current segment travel time. There is **no per-feature
timestamp**.

## Reproduce it with curl

```bash
G="https://api.viz.berlin.de/geoserver/mdh/wms"
# 1) capabilities — confirm the three vmzlos layers
curl -s "$G?service=WMS&version=1.1.1&request=GetCapabilities" | grep -oE '<Name>vmzlos[^<]*</Name>'
# 2) the actual coloured tile the page shows (GetMap → PNG)
curl -s "$G?service=WMS&version=1.1.1&request=GetMap&layers=vmzlos-step&styles=&srs=EPSG:4326\
&bbox=13.38,52.50,13.45,52.54&width=600&height=400&format=image/png&transparent=true" -o verkehrslage.png
# 3) read LOS / speed / travel time at a point (GetFeatureInfo → JSON)
curl -s "$G?service=WMS&version=1.1.1&request=GetFeatureInfo&layers=vmzlos-step\
&query_layers=vmzlos-step&srs=EPSG:4326&info_format=application/json&feature_count=10\
&width=101&height=101&x=50&y=50&bbox=13.410,52.516,13.418,52.524"
```

No key, no addon, no extra packages.

## Where does VMZ get *its* LOS from? (provenance)

`vmzlos` is computed by **VMZ Berlin** (the operator behind VIZ). LOS per link
needs a **current speed for every link of the road graph** — far more links than
the ~276 detector cross-sections — so it is primarily a **floating-car-data /
travel-time** product, with the **TEU/thermal detectors** as one input and
**incident/closure** data (the `Baustellen_OCIT` GeoJSON
`…/daten/baustellen_sperrungen.json`, fed from the non-public **OCIT-C / Concert**
interface) overlaid. This page does not expose the raw FCD; it publishes the
finished LOS network.

## Relation to the rest of this deep dive

- **Different product from the detector archive.** The frozen TEU feed and the
  June-2025 blob archive ([`api-reference.md`](api-reference.md)) are *point
  detector counts/speeds*. `vmzlos` is a *network-wide LOS/travel-time* layer.
  The Verkehrslage map can stay useful even while the detector archive is stale,
  because it is FCD-driven, not detector-driven.
- **It partially fills the "no open real-time travel-time layer" gap** noted in
  [`../01-car.md`](../01-car.md): VMZ *does* publish citywide current
  `los`/`speedavg`/`traveltime` per link, openly, as WMS — readable point-by-point
  via `GetFeatureInfo`. Caveats: it's a **rendered WMS** (no documented bulk
  download, no history, no timestamp), so for **bulk or historical** FCD you would
  still go commercial ([`../07-commercial.md`](../07-commercial.md)).

## Salient docs / sources

- Page: [viz.berlin.de – Verkehrslage](https://viz.berlin.de/verkehr-in-berlin/verkehrslage/)
- WMS: [`api.viz.berlin.de/geoserver/mdh/wms` GetCapabilities](https://api.viz.berlin.de/geoserver/mdh/wms?service=WMS&version=1.1.1&request=GetCapabilities)
- Layer config: [`masterportal-dps-config` services-internet.json](https://github.com/digitale-plattform-stadtverkehr-berlin/masterportal-dps-config/blob/master/resources/services-internet.json)
- [OGC WMS GetFeatureInfo](https://www.ogc.org/standard/wms/) · [VMZ Berlin](https://www.vmzberlin.com/)
