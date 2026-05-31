# 06 · Shared / micromobility

> 🤖 Agent-generated from web research (May 2026). Verify feeds/permits before use.

Covers bikeshare, e-scooters, moped-sharing, and carsharing.

## Executive summary

- **The standard is GBFS** (General Bikeshare Feed Specification, MobilityData) — real-time
  vehicle/station availability. The catalogue of feeds worldwide is in
  **`MobilityData/gbfs` `systems.csv`**.
- **Reality in Berlin: feed openness is uneven.** A Technologiestiftung assessment found that
  among bikeshare operators, **only Nextbike and DB (Call a Bike) publish an official,
  documented API**; **Nextbike's GBFS needs no key** (e.g. `api.nextbike.net/maps/gbfs/v1/nextbike_de/gbfs.json`).
  E-scooter/free-float operators (Tier, Lime, Voi, Dott, Bolt) and carsharing (Miles, Sixt
  share) generally **do not expose open public feeds** — their GBFS, where it exists, is
  shared with the city/aggregator under agreement.
- **Aggregation:** **BVG Jelbi** (MaaS, powered by Trafi) integrates Tier, Voi, Lime,
  Nextbike, emmy, Miles, Sixt share, Bolt, Dott, Taxi Berlin — but via a **private MaaS API**,
  not an open feed. **Vianova "Cityscope"** ingests operator data (e-scooter + carsharing)
  for the city's **regulatory/analytics** use — again, not public.
- **Regulation as data:** operators hold a **Sondernutzung permit (§ 11a BerlStrG)**, current
  term **2025-04-01 → 2027-03-31**; the city defines **no-parking zones / Jelbi points** and
  mandates data sharing — useful context and a lever for obtaining feeds.
- **Bottom line:** **live availability is technically everywhere (GBFS) but legally/practically
  gated** except Nextbike/DB. Trip/origin-destination data sits with operators and the city's
  regulator (Vianova/MDS), obtainable only by **agreement**, not open download.

## Sources & ratings

### 🤝/🔒 GBFS feeds (per operator)
- **What:** standardized real-time station/vehicle availability + pricing + geofencing.
- **Nextbike / DB:** **open, documented, key-less** GBFS → Access ★★★ · Quality ★★★ ·
  Coverage ★★☆ (their fleet) · Usability ★★★.
- **Tier / Lime / Voi / Dott / Bolt / Miles / Sixt share:** GBFS exists but **not openly
  published** for Berlin → Access ★☆☆ · Quality ★★★ (when obtained) · Coverage ★★☆ each ·
  Usability ★★★.
- **Discovery:** `MobilityData/gbfs systems.csv` lists known public endpoints.

### 🔒 BVG Jelbi (MaaS, Trafi)
- **What:** unified availability/booking across most Berlin operators. **Private MaaS API**;
  no open data feed. Good as a product, not a data source.
- **Ratings:** Access ★☆☆ · Quality ★★★ · Coverage ★★★ (most operators) · Usability ★☆☆ (closed).

### 🏛/🔒 Vianova Cityscope (city regulator data)
- **What:** platform BVG/Berlin uses to ingest e-scooter + carsharing operator data for
  regulation (parking compliance, distribution). **MDS-style**; not public.
- **Access:** government/regulator only (or via Mobility Data Space agreements).
- **Ratings:** Access ★☆☆ · Quality ★★★ · Coverage ★★★ · Usability ★★☆.

### 🏛 Sharing regulation / permits — SenMVKU
- **What:** **Sondernutzung** framework (§ 11a BerlStrG), permit terms, **no-parking zones**,
  mandatory-parking (Jelbi) points, data-sharing obligations. Geodata of zones partially open.
- **Access:** open pages/PDFs + some geodata; the *operational* data they unlock is gated.
- **Ratings:** Access ★★☆ · Quality ★★☆ · Coverage ★★☆ · Usability ★★☆.

## Access cheat-sheet

| Need | Best source | Open? |
| ---- | ----------- | ----- |
| Live bikeshare availability | Nextbike GBFS | ✅ key-less |
| Live e-scooter/carsharing availability | operator GBFS / Jelbi | ❌ by agreement |
| Trip / OD / utilization | operators or Vianova (city) | ❌ agreement |
| Where vehicles may park | Sondernutzung zones / Jelbi points | partial ✅ |
| Catalogue of feeds | `MobilityData/gbfs` systems.csv | ✅ |

## Key insight

Shared mobility is the clearest case where a **technical standard exists (GBFS)
but governance gates the data**. The city *does* collect rich operator data — but
for **regulation**, via Vianova/agreements, not for the public. A project should
plan to (a) use **Nextbike's open GBFS** directly, and (b) pursue **data-sharing
agreements** (leveraging the Sondernutzung obligations / Mobility Data Space) for
everything else, rather than expecting open downloads.

## Sources

- [MobilityData/gbfs – systems.csv](https://github.com/MobilityData/gbfs/blob/master/systems.csv)
- [nextbike/gbfs documentation](https://github.com/nextbike/gbfs)
- [Technologiestiftung – Assessing open bike sharing data in Berlin](https://lab.technologiestiftung-berlin.de/projects/bike-sharing/en/)
- [Trafi – BVG Jelbi MaaS](https://www.trafi.com/post/bvg-jelbi-world-s-most-extensive-mobility-as-a-service-in-berlin)
- [Vianova – BVG Jelbi e-scooter tender](https://www.vianova.io/blog/mobility-data-platform-vianova-awarded-bvg-jelbi-tender-to-transform-e-scooter-parking-across-berlin)
- [SenMVKU – Stationslose Mikromobilität (Sondernutzung)](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/dienste-und-genehmigungen/stationslose-mikromobilitaet/)
- [Jelbi – Fair parking](https://www.jelbi.de/en/fair-parking/)
