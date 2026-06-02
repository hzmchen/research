# VIZ / DPS and the federal layer for speed limits

> 🤖 Compiled from web research on **2026-06-02**, with a confidence note below.
> Unlike the [Geoportal](fis-broker-tempolimits.md) and [OSM](osm-maxspeed.md)
> files, the VIZ/DATEX II specifics here are **not all confirmed by live calls** —
> see the caveat at the end.

The user asked to include **VIZ**. Short answer: **VIZ does not publish a distinct
live "speed-limit" API** — it is the traffic-information umbrella, and the canonical
static limit data is the **SenMVKU Geoportal `Tempolimits` layer**, which VIZ
re-surfaces cartographically. The *federal* republication path is the **Mobilithek**
national access point as **DATEX II**.

## VIZ / DPS — what it does for limits

- **VIZ** (Verkehrsinformationszentrale des Landes Berlin), run with **VMZ Berlin**, is
  Berlin's official traffic-information centre. Per its own remit it "compiles, analyses
  and processes **static and dynamic** real-time traffic information … and makes it
  available through various channels" using **market-standard, open formats (GeoJSON,
  WFS/WMS, CSV, DATEX II)**.
- Its **own live data** (the part with a dedicated API on `api.viz.berlin.de`) is the
  **dynamic** layer — traffic detection (volume/class/**measured** speed), construction
  & closures, the `vmzlos` Verkehrslage, air quality, flights. See
  [`../01-car.md`](../01-car.md) and [`../teu-detectors-viz-api/`](../teu-detectors-viz-api/).
  **None of those is the legal limit** — the detector "speed" is *measured*, and
  `vmzlos.freeflowspeed` is a congestion *reference*, not a posted limit.
- For the **static** regulatory limit, VIZ's role is **aggregation/display**: the source
  of record is the **SenMVKU Geoportal `Tempolimits`** WFS/WMS. If you want the data, go
  to the Geoportal endpoint directly — it's the same authority's primary publication and
  carries the most permissive licence (dl-de/zero-2.0).

**Takeaway:** treat "VIZ" as *where you see* Berlin's ordered limits on a map, and the
**Geoportal `Tempolimits` WFS** as *where you fetch* them.

## Federal layer — Mobilithek / DATEX II

- The **Mobilithek** (`mobilithek.info`) is Germany's **national access point (NAP)** for
  mobility data, mandated under the EU ITS Directive. It standardises road/traffic data as
  **DATEX II** (the channel navigation/ITS providers consume), merging the former MDM and
  mCLOUD. See [`../00-platforms.md`](../00-platforms.md).
- DATEX II has a **recommended profile for speed limits** under RTTI (Real-Time Traffic
  Information), so static/dynamic limits *can* be expressed and exchanged nationally in a
  standard model. This is the route by which Berlin/Brandenburg road-authority data reaches
  navigation providers in a harmonised form.

## ⚠️ Confidence caveat

- ✅ **High confidence:** VIZ has **no separate open speed-limit API**; the authoritative
  static source is the **Geoportal `Tempolimits`** layer (that part *is* verified live — see
  [`fis-broker-tempolimits.md`](fis-broker-tempolimits.md)).
- ⚠️ **Lower confidence (not verified by a live call here):** that Berlin's *specific*
  ordered-speed-limit dataset is **currently published as a DATEX II feed on the Mobilithek**.
  The Mobilithek and the DATEX II speed-limit *profile* both exist; I did **not** confirm a
  live Berlin `Tempolimits` DATEX II dataset/endpoint on the Mobilithek. If you need the
  DATEX II form, search the Mobilithek catalogue for a Berlin/SenMVKU speed-limit publication
  and verify the endpoint before relying on it.
- The VIZ portal (`viz.berlin.de`) served an auth/redirect wall to the fetch tool, so its
  data-offerings page was not read directly this session; the VIZ description above is from
  the platform survey in [`../00-platforms.md`](../00-platforms.md) and public summaries.

## Sources

- [VIZ Berlin](https://viz.berlin.de/en/) · [DPS – Verkehrsdetektion API](https://api.viz.berlin.de/daten/verkehrsdetektion)
- [Mobilithek](https://mobilithek.info/) · [DATEX II FAQ on the Mobilithek](https://mobilithek.info/blog/faq-bereich-datex-2-in-der-mobilithek)
- [DATEX II – RTTI speed-limits profile](https://docs.datex2.eu/recommended-profiles/rrp/rtti/rtti-670/2-rr-a4-speed-limits/) · [DATEX II NAP map](https://datex2.eu/datex-ii-nap-map/)
- Parent: [`../00-platforms.md`](../00-platforms.md) · [`../01-car.md`](../01-car.md) · [`../teu-detectors-viz-api/`](../teu-detectors-viz-api/)
</content>
