# 05 · Pedestrian

> 🤖 Agent-generated from web research (May 2026). Verify before use.

Covers walking / foot traffic (Fußverkehr).

## Executive summary

- **Pedestrian data is the weakest mode for Berlin.** There is **no dense official
  network of pedestrian counters** comparable to the bike counters or car detectors.
- What exists is **citizen-science and pilot** infrastructure that counts pedestrians
  *alongside* other modes:
  - **Berlin zählt Mobilität** (ADFC + DLR, since 2022) — citizen **Telraam** sensors
    classify pedestrians, bikes, cars, heavy vehicles. Open JSON/CSV on `daten.berlin.de`.
  - **OpenTrafficCount / OpenDataCam** (Technologiestiftung + HTW, CityLAB) — open-source
    ML camera counting cars/bikes/**pedestrians** in real time, privacy-preserving;
    deployed at selected sites as a **pilot/toolkit**, not a permanent citywide feed.
- **Accidents** involving pedestrians are captured in the **Unfallatlas** (see [`01-car.md`](01-car.md)).
- **Footfall (retail/commercial)** is **commercial** (e.g. location-analytics vendors) and
  not openly available for Berlin.
- **Bottom line:** for systematic pedestrian *volumes* you will likely need to **deploy your
  own counting** (Telraam/OpenDataCam are the cheap open paths) or **buy footfall data**.
  Open data gives you safety (accidents) and opportunistic citizen counts only.

## Sources & ratings

### 🤝 Berlin zählt Mobilität (ADFC + DLR, Telraam)
- **What:** citizen Telraam devices; multimodal classification including pedestrians.
  Coverage grows where residents install sensors.
- **Access:** open JSON/CSV (`daten.berlin.de`) + Telraam platform.
- **Ratings:** Access ★★★ · Quality ★★☆ (consumer-sensor; pedestrian classification is the
  hardest class for these devices) · Coverage ★★☆ (opportunistic) · Usability ★★☆.

### 🤝/🏛 OpenTrafficCount / OpenDataCam (Technologiestiftung, HTW, CityLAB)
- **What:** **open-source** ML video counting (cars/bikes/peds) in real time, low-cost,
  GDPR-conscious (no image retention). A **method/toolkit** validated at Berlin sites
  rather than a continuous open dataset.
- **Access:** open-source code; data depends on who runs it.
- **Ratings:** Access ★★☆ (DIY) · Quality ★★☆ · Coverage ★☆☆ (pilot sites) · Usability ★★☆ (build it).

### 🌐 Unfallatlas (pedestrian-involved accidents)
- Geocoded pedestrian injury accidents. Open CSV/SHP. See [`01-car.md`](01-car.md).
- Ratings: Access ★★★ · Quality ★★★ · Coverage ★★★ · Usability ★★★.

### 🔒 Commercial footfall / location analytics
- Mobile-location / SDK-derived pedestrian footfall (retail analytics vendors). Proprietary,
  paid, privacy-sensitive. See [`07-commercial.md`](07-commercial.md).
- Ratings: Access ★☆☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆.

## Key insight

Pedestrians — the largest mode by trip share in inner Berlin — are the **least
instrumented**. The open ecosystem offers **tools to count** (OpenDataCam, Telraam)
far more than **counts to use**. Any pedestrian-volume project should budget for
**primary data collection** rather than expecting a ready citywide feed.

## Sources

- [Berlin Open Data – Berlin zählt Mobilität](https://daten.berlin.de/datensaetze/berlin-zaehlt-mobilitaet)
- [Telraam in Berlin](https://telraam.net/,/case/ich-bin-ein-berliner-telraam-in-berlin)
- [Technologiestiftung – Open Traffic Count](https://www.technologiestiftung-berlin.de/en/projects/open-traffic-count)
- [CityLAB Berlin – Open Traffic Count](https://citylab-berlin.org/en/projects/trafficcount/)
- [OpentrafficCount – Digital Future Berlin](https://www.digital-future.berlin/en/research/projects/opentrafficcount/)
- [Eco-Counter – Why count pedestrians](https://www.eco-counter.com/blog/why-should-you-count-pedestrians)
