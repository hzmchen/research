# 02 · Truck / freight / logistics

> 🤖 Agent-generated from web research (May 2026). Verify figures/endpoints before use.

Covers heavy goods vehicles (Lkw), commercial transport (Wirtschaftsverkehr),
and courier/parcel (KEP) logistics.

## Executive summary

- **There is no single "Berlin truck flow" open dataset.** Freight data comes from
  three angles that must be combined:
  1. **Federal toll data** (Toll Collect / **BALM** statistics + **Destatis truck-toll
     mileage index**) — excellent for *trends*, but only on **Autobahn/federal trunk
     roads** (in Berlin: A100, A111, A113, A115…), **not surface streets**, and only
     trucks **≥7.5 t**.
  2. **Berlin's own counts** — the **TEU detectors** classify cars vs **trucks**, and
     the **Verkehrsmengenkarte (DTVw)** breaks out **trucks >3.5 t** per network
     segment (see [`01-car.md`](01-car.md)). This is the best *city-street* truck data.
  3. **Studies/concepts** — the **Integriertes Wirtschaftsverkehrskonzept (IWVK)** and
     district reports give modelled/surveyed figures (e.g. KEP volumes), as PDFs, not feeds.
- **KEP (parcel) reality check (from Berlin studies):** ~**2,500 KEP vehicles** deliver
  **>400,000 parcels/day** citywide; Friedrichshain-Kreuzberg alone ~**16,000
  parcels/day on ~200 tours**. These come from reports, not a live API.
- **Bottom line:** trends and network-segment truck shares are **open and free**;
  granular, street-level, real-time freight movement is **not openly available** —
  it lives with operators and commercial telematics providers.

## Sources & ratings

### 🏛 Toll Collect / BALM toll statistics + "Mautverkehr KOMPAKT" / Toll Data Tables
- **What:** distance-based toll for trucks (≥12 t from 2005, lowered to **7.5 t**;
  extended to more roads over time). **BALM** (formerly BAG) publishes toll revenue,
  tolled mileage, and **section traffic per federal-road segment**. Toll table
  maintained by **BASt**.
- **Geography:** federal motorways + trunk roads only → in Berlin, the Autobahn ring,
  not the Kiez streets.
- **Access:** open published tables/reports (PDF/Excel); not a real-time API.
- **Ratings:** Access ★★☆ · Quality ★★★ (census of tolled trucks) ·
  Coverage ★★☆ (Autobahn/≥7.5 t only) · Usability ★★☆ (aggregated tables).

### 🏛 Destatis — Truck-toll mileage index (Lkw-Maut-Fahrleistungsindex)
- **What:** **daily** truck-toll mileage index from 2008 onward; a near-real-time
  economic/freight indicator. National (and broad regional) level.
- **Access:** open via Destatis EXSTAT; CSV/Excel.
- **Ratings:** Access ★★★ · Quality ★★★ · Coverage ★★☆ (national, not city-granular) ·
  Usability ★★★ (clean time series).

### 🏛 Berlin TEU detectors + DTVw truck share — SenMVKU / VIZ
- **What:** truck *classification* at 240+ live detector sites; modelled **truck >3.5 t
  volumes per segment** in the Verkehrsmengenkarte. **Best open city-street truck data.**
- **Access:** open (dl-de/by-2.0); live JSON + WMS/WFS. Details in [`01-car.md`](01-car.md).
- **Ratings:** Access ★★★ · Quality ★★☆ · Coverage ★★☆ (main network) · Usability ★★☆.

### 🏛/📄 IWVK & Wirtschaftsverkehr concepts (Berlin SenMVKU + districts)
- **What:** the **Integrated Commercial Transport Concept** and district studies
  (e.g. Friedrichshain-Kreuzberg "nachhaltiger Wirtschaftsverkehr"); KEP market
  analyses (NOW GmbH, BdKEP). Modelled shares (commercial traffic ≈ ⅓ of urban trips),
  consolidation-center (UCC/Mikro-Hub) scenarios.
- **Access:** open **PDF reports** — context & parameters, not machine-readable feeds.
- **Ratings:** Access ★★☆ · Quality ★★☆ (modelled/survey) · Coverage ★★☆ · Usability ★☆☆ (PDF).

### 🔒 Operator telematics / commercial freight data
- **What:** real fleet GPS/telematics (DHL, parcel carriers, telematics vendors),
  HERE/INRIX truck-flow products. Granular but proprietary.
- **Access:** contracts / Mobility Data Space brokering. See [`07-commercial.md`](07-commercial.md).
- **Ratings:** Access ★☆☆ · Quality ★★★ · Coverage ★★☆ · Usability ★★☆.

## Key insight

For freight, **provenance flips the usual pattern**: the *federal* census-grade data
(toll) is the strongest and freest, but it's **off-street** (Autobahn only). The
moment you need **last-mile / surface-street / parcel** movement — the policy-relevant
part for a city — open data thins out to **modelled studies**, and anything granular
and live is **commercial/operator-held**.

## Sources

- [BALM – Toll statistics (EN)](https://www.balm.bund.de/EN/Topics/HGVTolls/TollStatistics/tollstatistics_node.html)
- [Destatis – Truck toll mileage index (EN)](https://www.destatis.de/EN/Service/EXSTAT/Datensaetze/truck-toll-mileage.html)
- [LKW-Maut – Wikipedia](https://en.wikipedia.org/wiki/LKW-Maut)
- [Toll Collect](https://www.toll-collect.de/en/)
- [SenMVKU – Wirtschaftsverkehr in Berlin](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsplanung/wirtschaftsverkehr/)
- [Friedrichshain-Kreuzberg – nachhaltiger Wirtschaftsverkehr (2025)](https://www.berlin.de/ba-friedrichshain-kreuzberg/aktuelles/pressemitteilungen/2025/pressemitteilung.1595522.php)
- [NOW GmbH – Marktanalyse urbaner Wirtschaftsverkehr (PDF)](https://www.now-gmbh.de/wp-content/uploads/2020/09/now_marktanalyse-urbaner-wirtschaftsverkehr-1.pdf)
- [BdKEP – KEP Studie und Dokumente](https://bdkep.de/bdkep-blog/kep-studie-und-dokumente.html)
