# 07 · Private / commercial providers

> 🤖 Agent-generated from web research (May 2026). Pricing/terms change — verify with vendors.

Covers proprietary, paid, or access-gated sources spanning all modes. These fill
the gaps open data leaves — chiefly **real-time congestion / travel time / floating-car
data (FCD)** and **origin–destination / footfall** analytics.

## Executive summary

- **The single biggest reason to go commercial in Berlin is a citywide, real-time,
  road-network travel-time / congestion layer** — which open data does *not* provide
  (open data gives point detectors + periodic DTV maps; see [`01-car.md`](01-car.md)).
- **TomTom** is the most accessible: REST **Traffic API** (real-time flow/incidents) and
  **Traffic Stats** (historical), built on FCD from **600 m+ devices**; freemium tier
  (~50k tile req/day free, then ~$0.08/1k). Its **Traffic Index is a free public benchmark**
  — Berlin **2023: ~22 min per 10 km, ~64 h/yr lost, 2nd-most-congested German city** (after Hamburg).
- **HERE, INRIX, Google Maps Platform, Mapbox** are the other majors — strong coverage,
  but **licensing restricts data storage/derivative use** (esp. Google), and pricing is
  usage-based and can scale fast.
- **Crowd-sourced bias matters:** **Strava Metro** (free to agencies) is dense but
  fitness-skewed; footfall vendors use mobile-SDK panels with their own biases.
- **Brokered/B2B:** the **Mobility Data Space** (Gaia-X) and vendor marketplaces broker
  operator/FCD/telematics data under contract — relevant for freight and shared-mobility
  trip data (see [`02`](02-freight.md), [`06`](06-shared-mobility.md)).
- **Bottom line:** budget for **one FCD/travel-time provider** (TomTom is the easiest
  on-ramp; HERE/INRIX for enterprise depth) and treat everything else as open. Watch
  **licence terms on caching/redistribution**, which are often the real constraint, not price.

## Providers & ratings

### 🔒 TomTom — Traffic API, Traffic Stats, Traffic Index
- **Data:** real-time flow + incidents (Traffic API); historical/analytical (Traffic Stats);
  FCD from 600 m+ devices, 80+ countries. **Traffic Index** = free city congestion benchmark.
- **Access:** developer portal, API keys, **freemium** then pay-as-you-go. Commercial use allowed.
- **Ratings:** Access ★★☆ (easy signup, paid at scale) · Quality ★★★ · Coverage ★★★ ·
  Usability ★★★ (clean REST; permissive enough for apps).

### 🔒 HERE Technologies
- **Data:** real-time + historical traffic, FCD, road attributes; strong automotive/enterprise.
- **Access:** freemium dev tier + enterprise contracts; available via **Mobilithek/MDM** for some feeds.
- **Ratings:** Access ★★☆ · Quality ★★★ · Coverage ★★★ · Usability ★★☆ (enterprise-oriented).

### 🔒 INRIX
- **Data:** traffic, speeds, parking, trip/OD analytics; **TomTom's NA traffic partner**.
- **Access:** mostly enterprise/contract; less self-serve.
- **Ratings:** Access ★☆☆ · Quality ★★★ · Coverage ★★★ · Usability ★★☆.

### 🔒 Google Maps Platform
- **Data:** Routes/Distance Matrix with live traffic, Roads; huge coverage.
- **Access:** API keys, monthly free credit then usage-priced. ⚠️ **Strict terms** — generally
  **no storing/derivative use** of traffic data; display-bound. Poor fit for analytics/storage.
- **Ratings:** Access ★★☆ · Quality ★★★ · Coverage ★★★ · Usability ★★☆ (great API, restrictive licence).

### 🔒 Mapbox
- **Data:** traffic-aware routing, isochrones, movement/telemetry products.
- **Access:** API keys, usage pricing.
- **Ratings:** Access ★★☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★★.

### 🔒/🤝 Strava Metro (cycling/running)
- **Data:** aggregated, de-identified active-travel GPS at segment level.
- **Access:** **free to public agencies/researchers** via application; not open; fitness-biased sample.
- **Ratings:** Access ★☆☆ (gated) · Quality ★★☆ · Coverage ★★★ · Usability ★★☆.

### 🔒 Footfall / location-analytics vendors (pedestrian, retail)
- **Data:** mobile-SDK-derived pedestrian footfall, dwell, OD. Proprietary, privacy-sensitive.
- **Access:** paid. The de-facto option for systematic pedestrian volumes (see [`05`](05-pedestrian.md)).
- **Ratings:** Access ★☆☆ · Quality ★★☆ (panel bias) · Coverage ★★☆ · Usability ★★☆.

### 🏛/🔒 Mobility Data Space + vendor marketplaces (brokered)
- **Data:** operator FCD, telematics, sharing trip data under sovereignty controls (Gaia-X).
- **Access:** membership/contracts. See [`00-platforms.md`](00-platforms.md).
- **Ratings:** Access ★☆☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆.

## Buyer's cheat-sheet

| Need | Best commercial fit | Watch-out |
| ---- | ------------------- | --------- |
| Real-time congestion/travel time | TomTom Traffic API | cost at scale |
| Historical traffic analytics | TomTom Traffic Stats / INRIX | enterprise pricing |
| Free congestion benchmark | TomTom Traffic Index | city-level only, not raw |
| Routing in a consumer app | Google / Mapbox | Google storage limits |
| Cycling desire lines | Strava Metro | fitness bias, gated |
| Pedestrian footfall | Location-analytics vendors | panel bias, privacy |
| Operator/freight microdata | Mobility Data Space | contracts |

## Key insight

Across modes, the **commercial value concentrates in real-time travel-time/FCD and
in trip/OD/footfall** — precisely the two things open Berlin data lacks. For most
projects, **one FCD provider (TomTom as the pragmatic default) covers ~80% of the
commercial need**; the deciding factor is usually **licence terms on storage and
redistribution**, not headline price.

## Sources

- [TomTom – Traffic APIs](https://www.tomtom.com/products/traffic-apis/)
- [TomTom Developer – Traffic API intro](https://developer.tomtom.com/traffic-api/documentation/product-information/introduction)
- [TomTom Developer – Traffic Stats intro](https://developer.tomtom.com/traffic-stats/documentation/product-information/introduction)
- [TomTom Developer – Pricing](https://developer.tomtom.com/pricing)
- [TomTom Traffic Index – Berlin](https://www.tomtom.com/traffic-index/city/berlin)
- [Google Maps Platform – Pricing](https://mapsplatform.google.com/pricing/)
- [INRIX – TomTom strategic partner (press)](https://inrix.com/press-releases/tomtom-selects-inrix-strategic-partner-traffic-fuel-prices/)
- [Mobility Data Space](https://mobility-dataspace.eu/)
