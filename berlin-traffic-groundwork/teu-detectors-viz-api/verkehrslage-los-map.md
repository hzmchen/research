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
  the (frozen) detector archive. **It is genuinely live** (~5-minute cadence) even
  though the TEU detector feed is frozen — see [Liveness](#liveness-how-fresh-and-how-the-map-updates).

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

So the colour = **`los`**, a class derived per link from speed vs free-flow speed.
**Ground truth from the layer's SLD** (`GetStyles`), which maps `los` → colour the
same way for every road category (`strkat_1` ∈ I, II, III, IV, 0):

| `los` | colour (hex) | meaning |
| ----- | ------------ | ------- |
| `0` | red `#FF0000` | jam / heavily congested |
| `1` | orange `#FFC000` | disrupted |
| `2` | green `#00AA00` | flowing |
| `3` | bright green `#00FF00` | free-flow |
| `7` | dark grey `#333333` | special (e.g. closed) |
| *null* | white/grey `#FFFFFF`/`#DDDDDD` | "keine Information" (no data) |

(So the example above — `los:1`, 14.7 km/h vs 30 free-flow — is the **orange
"disrupted"** band, *not* the worst; `los 0` red is the jam class. An earlier draft
mislabelled this.) `traveltime` is the modelled current segment travel time. There
is **no per-feature timestamp**. Full field definitions ↓.

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

## Field definitions (ground truth)

Not inferred — taken from the GeoServer **`DescribeFeatureType`** schema, a real
**`WFS GetFeature`** row, the **SLD**, and the matching **INRIX** data dictionary.

**Rendered layer `mdh:vmzlos-step`** (`DescribeFeatureType`):

| field | type | definition (ground truth) |
| ----- | ---- | ------------------------- |
| `gid` | int | GeoServer feature id |
| `unique_id` | string | segment id (`fromnode_linkid_fromnode`) |
| `from_node`/`to_node` | string | network topology node ids |
| `strkat_1`/`strkat_2` | string | Berlin **Straßenkategorie** (road class I–IV, 0) |
| `closed` | int | segment-closed flag (0/1) |
| `los` | int | level-of-service class — see SLD table above (0=jam … 3=free, 7=special, null=no info) |
| `speedavg` | double | segment average speed [km/h] |
| `freeflowspeed` | double | **free-flow / reference speed** [km/h] |
| `traveltime` | double | current segment travel time |
| `geom` | curve | the road-segment line |

**The source table `mdh:los-vmz` reveals the provenance — it's INRIX XD.** Its
schema and a real row (`WFS GetFeature`):

```
xdsegid:387560184  previousxd:387557165  nextxdsegi:387560263  frc:1
segmentclosed:0  los:3  speed:66  reference:69  average:68  traveltimeminutes:0.499
```

`xdsegid / previousxd / nextxdsegi / frc / speed / reference / average /
traveltimeminutes` are **INRIX XD Traffic / Segment-Speed** field names. INRIX
documents them (docs.inrix.com): for each XD segment INRIX provides the
**`speed`** (current measured speed from live probe data), the **`average`**
(historical typical speed for that day-of-week & hour, 15-min bins), and the
**`reference`** speed — *"the proxy of the free flow or uncongested speed, defined
for the entire day."* So the layer's **`freeflowspeed` = INRIX `reference` speed**
(free-flow proxy); **`frc` = Functional Road Class**; **`traveltimeminutes`** =
segment travel time. The rendered `vmzlos-step` carries the derived `speedavg` /
`freeflowspeed` / `los`; the INRIX source `los-vmz` keeps current `speed`,
historical `average`, and `reference` separately. (A second source table
`mdh:los-rbb` also exists; its schema was not retrievable at query time.)

→ **`freeflowspeed` is not a VMZ invention or a guess: it is INRIX's documented
"reference speed" (free-flow proxy).** Authoritative definitions:
<https://docs.inrix.com/traffic/segmentspeed/> and
<https://inrix.com/blog/reference-speeds-the-backbone-of-better-traffic-intelligence/>.

## Availability on other data platforms

- **daten.berlin.de (Berlin open-data portal): not listed.** A search for
  "Verkehrslage" returns only an unrelated BSR street-cleaning dataset — there is
  **no** Verkehrslage / LOS / FCD dataset on the city portal.
- **Mobilithek / GovData / mCLOUD: not found.** Berlin publishes **closures
  (Baustellen/Sperrungen)** to the Mobilithek as DATEX II, but **not** the
  Verkehrslage/LOS feed. No national-access-point entry surfaced.
- **It *is* retrievable as data — but only from VIZ's own GeoServer, via WFS** (not
  just the rendered WMS): the same `mdh` workspace exposes the features over
  **OGC WFS**, returning full attributes:

  ```bash
  O="https://api.viz.berlin.de/geoserver/mdh/ows"
  # rendered LOS network as GeoJSON features:
  curl -s "$O?service=WFS&version=2.0.0&request=GetFeature&typeNames=mdh:vmzlos-step&count=5&outputFormat=application/json"
  # the INRIX-schema source table:
  curl -s "$O?service=WFS&version=2.0.0&request=GetFeature&typeNames=mdh:los-vmz&count=5&outputFormat=application/json"
  ```

  So "another platform" = **the VIZ GeoServer's WMS (render) + WFS (features)**; it
  is *not* mirrored to Mobilithek, GovData, or daten.berlin.de.

## Licence

**No open licence is published for the Verkehrslage / LOS layer — treat it as
restricted, not open data.** Ground truth:

- The GeoServer capabilities advertise `<Fees>none</Fees>` and
  `<AccessConstraints>none</AccessConstraints>` — but these are **GeoServer's
  default placeholder values**, not an affirmative licence grant.
- The layer is **absent from daten.berlin.de**, so it carries **none** of the
  `dl-de/by-2.0` declaration that the *detector archive* explicitly has. The two
  must not be conflated: the dl-de/by-2.0 grant covers "Verkehrsdetektion", **not**
  the Verkehrslage.
- The underlying data is **INRIX commercial floating-car data**. viz.berlin.de
  states the FCD is "made available in a data-protection-compliant manner by a
  company (here **INRIX**)", and the commuter analyses cite **"INRIX Trips"**; the
  `los-vmz` INRIX-XD schema corroborates. INRIX FCD is contractually licensed and
  generally **not redistributable as open data**.
- **Conclusion:** the WMS/WFS is publicly reachable for *viewing* on viz.berlin.de,
  but there is **no evidence of an open reuse licence**, and the INRIX-sourced
  inputs are proprietary. Any reuse beyond display should be cleared with **VMZ
  Berlin / SenMVKU**; do not assume dl-de/by-2.0. *(I found no explicit terms-of-use
  page for this layer; this is the ground-truth absence, stated as such.)*

## Liveness — how fresh, and how the map updates

**Verdict: it's a near-real-time layer on a ~5-minute cycle, and it is actually
updating (2026), unlike the frozen TEU detector feed.** Evidence from four angles:

**1. How the Masterportal drives it (client side).** In the portal config
(`berlin/config.json`) all three Verkehrslage layers carry
**`"autoRefresh": "300000"`** — the map **re-requests the layer every 300000 ms =
5 minutes**. The layers are also flagged `cache: true`.

**2. Server caching (platform side).** The WMS `GetMap` responses come back with a
**`Date`-only** header (no `Last-Modified`/`Expires`) → rendered **dynamically per
request**. The WMTS/GeoWebCache tiles return **`Cache-Control: max-age=30`** — a
deliberately tiny 30-second cache, the signature of a feed expected to change
constantly. Neither behaves like a static dataset.

**3. The values actually change (empirical).** Querying one fixed segment
(`gid 10435`, Koppenstraße area) across the research session:

| When | los | speedavg | traveltime |
| ---- | --- | -------- | ---------- |
| earlier query | 1 | 14.7 | 31.5 |
| later query | 2 | 15.7 | 29.49 |

It moved between LOS classes and speeds. Within a **69 s** re-poll the values were
*stable* — exactly what you'd expect from a **5-minute** recompute (sub-cycle =
no change; cross-cycle = change). So the map is live, not a frozen snapshot.

**4. How VMZ produces it (upstream).** VMZ Berlin states it **fuses detector data
with floating-car data (FCD) from multiple providers** to "fill gaps in the
detected road network" and compute the **current traffic situation and travel
times**. That is why the LOS network is far denser than the ~276 detector
cross-sections and why it **survives the TEU outage**: FCD, not the frozen
infrared detectors, is doing most of the work. (The road geometry/IDs in related
VIZ layers use the **INRIX "XD"** network — see [`masterportal-addons.md`](masterportal-addons.md) —
consistent with a commercial FCD provider in the mix.)

**Upstream cadence (documented).** VMZ/VIZ descriptions state the sensor network
delivers congestion/speed at ~300 locations **every 5 minutes**, combined with the
state's measurement data to compute a network-wide traffic picture **every ~15
minutes**. So: detectors 5 min → **network-wide LOS recomputed ≈ every 15 min**,
while the Masterportal client re-requests the tiles every 5 min.

**Caveats (confidence).** The *client* refresh (5 min), the *cache* behaviour
(30 s), and the *observed value changes* are verified by API/headers; the ~15-min
network-LOS recompute is from VMZ's own description (secondary source, not an API
field).
There is **no per-feature timestamp / `TIME` dimension and no "Stand" field**, so
you cannot read the age of an individual value from the API; trust it as
"current within minutes" rather than reading an explicit observation time.

## Relation to the rest of this deep dive

- **Different product from the detector archive.** The frozen TEU feed and the
  June-2025 blob archive ([`api-reference.md`](api-reference.md)) are *point
  detector counts/speeds*. `vmzlos` is a *network-wide LOS/travel-time* layer.
  The Verkehrslage map can stay useful even while the detector archive is stale,
  because it is FCD-driven, not detector-driven.
- **It partially fills the "no open real-time travel-time layer" gap** noted in
  [`../01-car.md`](../01-car.md): VMZ *does* expose citywide current
  `los`/`speedavg`/`traveltime` per link, **publicly reachable** as WMS/WFS —
  readable via `GetFeatureInfo`/`GetFeature`. **But "reachable" ≠ "open"**: the
  inputs are **INRIX** (proprietary, no open licence — see Licence above), there's
  no bulk/historical export and no timestamp. So for **licensed, bulk, or
  historical** FCD you still go commercial ([`../07-commercial.md`](../07-commercial.md)).

## Salient docs / sources

- Page: [viz.berlin.de – Verkehrslage](https://viz.berlin.de/verkehr-in-berlin/verkehrslage/)
- WMS: [`api.viz.berlin.de/geoserver/mdh/wms` GetCapabilities](https://api.viz.berlin.de/geoserver/mdh/wms?service=WMS&version=1.1.1&request=GetCapabilities)
- Layer config: [`masterportal-dps-config` services-internet.json](https://github.com/digitale-plattform-stadtverkehr-berlin/masterportal-dps-config/blob/master/resources/services-internet.json)
- Liveness: [`berlin/config.json`](https://github.com/digitale-plattform-stadtverkehr-berlin/masterportal-dps-config/blob/master/berlin/config.json) (`autoRefresh: 300000`); WMTS GWC tiles `Cache-Control: max-age=30`
- FCD fusion / methodology: [VMZ Berlin – Kompetenzbereiche](https://www.vmzberlin.com/kompetenzbereiche/) · [VIZ Berlin – Verkehrsinformation (SenUVK)](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsmanagement/verkehrsinformation/)
- [Masterportal `autoRefresh` layer config](https://www.masterportal.org/) · [OGC WMS](https://www.ogc.org/standard/wms/) · [VMZ Berlin](https://www.vmzberlin.com/)
