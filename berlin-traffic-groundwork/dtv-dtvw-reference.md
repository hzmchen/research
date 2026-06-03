# DTV & DTVw — where to get the values, what they mean

> 🤖 Agent-generated from official sources (web research, June 2026). Endpoints and
> figures were taken from Berlin Senate / Umweltatlas / Open-Data pages; re-verify
> before operational use. Companion to [`01-car.md`](01-car.md) (car/Kfz chapter).

Berlin's network-wide street volumes are published as **DTVw**, and the **DTV**
form is a *derived* product. This file pins down **what each means**, **where to
get it**, **for which years**, **under what status/licence**, and **how valid**
the numbers are — plus the official **DTVw→DTV conversion factors**.

## TL;DR

| | **DTVw** | **DTV** |
| --- | --- | --- |
| German | *durchschnittliche werktägliche Verkehrsstärke* | *durchschnittliche tägliche Verkehrsstärke* |
| English | average **weekday** daily traffic | average daily traffic (**ADT**, all 7 days) |
| Reference days | Mon–Thu, outside school/public holidays (map); Mon–Fri (counters) | Mon–Sun (full week) |
| Unit | vehicles / 24 h (per network segment) | vehicles / 24 h |
| In Berlin this is the… | **native, published** product (Verkehrsmengenkarte) | **derived** product (factor or separate Umweltatlas DTV map) |
| Primary source | `Verkehrsmengen DTVw <year>` (Geoportal/FIS-Broker, WMS/WFS) | `Verkehrsmengen DTV <year> (Umweltatlas)` map, **or** DTVw × factor |
| Relation | always **≥ DTV** (weekends are lighter) | DTVw × **0.91** (Kfz) / **0.82** (Lkw >3.5 t) |

**Key point:** Berlin's traffic-volume map is published in **DTVw**, not DTV.
Standards that require DTV (noise RLS-19 / 16. BImSchV, air 39. BImSchV) are served
either by a *separate* Umweltatlas **DTV** map or by applying the published
conversion factors. Don't assume a Berlin "Verkehrsmenge" is DTV — check which one.

## 1 · Meaning

- **DTVw — average weekday daily traffic.** Vehicles per 24 h on a "normal"
  working day. Berlin derives it from **12-hour roadside counts** (preferably
  Tue/Thu, Pkw vs Lkw ≥3.5 t), extrapolated to a 24 h weekday value using the
  permanent counters (Dauerzählstellen). The **Verkehrsmengenkarte** balances all
  counts to a single reference year. For the map the reference days are
  **Mon–Thu outside Berlin school holidays and public holidays**; the conversion
  methodology uses **Mon–Fri** counts. DTVw is what Berlin's traffic *model* also
  produces (calibrated on the DTVw counts), so it is the city's native planning unit.

- **DTV — average daily traffic (ADT).** Vehicles per 24 h averaged over **all
  seven days** (Mon–Sun). Because weekend volumes are lower than weekdays, **DTV <
  DTVw**. DTV is the unit demanded by **noise** (RLS-19, 16. BImSchV) and **air**
  (39. BImSchV / RL 96/62/EG) regulations, which is the main reason Berlin needs a
  DTV form at all.

- Both are **segment-level network values** (one number per street section), not a
  single-point sensor reading. For live/point counts use the **TEU detectors / VIZ
  Dauerzählstellen** instead (see [`teu-detectors-viz-api/`](teu-detectors-viz-api/)).

## 2 · Where to get DTVw — the native product

**Product:** *Verkehrsmengenkarte* / `Verkehrsmengen DTVw <year>` — Umweltatlas
map **07.01**. Modelled, balanced ("ausgeglichen") weekday volume per main-network
segment, broken out by **Kfz**, **Lkw >3.5 t** (excl. buses), and **bicycle**
(bike as a daytime **DTVw (12 h)**, 07–19 h, on ~1,394 km of cycle network).

| Attribute | Value (current edition: **DTVw 2023**) |
| --- | --- |
| Publisher | SenMVKU — Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt; Abt. VI Verkehrsmanagement, Ref. C |
| Input | ~**5,600** individual counts from recent years, extrapolated/balanced to reference year 2023 |
| Coverage | main road network (+ parts of cycle network); whole city, segment-level |
| Published / updated | **2024-11-22** / **2024-12-06** |
| Licence | **dl-de/zero-2.0** (no attribution required) |
| WMS | `https://gdi.berlin.de/services/wms/verkehrsmengen_2023` (`?service=WMS&request=GetCapabilities`) |
| WFS | `https://gdi.berlin.de/services/wfs/verkehrsmengen_2023` (parallel service name — verify GetCapabilities) |
| Open-data record | [daten.berlin.de — Verkehrsmengen DTVw 2023 [WMS]](https://daten.berlin.de/datensaetze/verkehrsmengen-dtvw-2023-wms-efc1dc7a) |
| Also in | **FIS-Broker / Geoportal** (`gdi.berlin.de`) — *"updated values are provided exclusively in FIS-Broker"* |
| Report | [Ergebnisbericht 2023 (PDF)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsmanagement/verkehrserhebungen/ergebnisbericht-2023.pdf) |

**Access routes, in order of convenience:**
1. **WMS** for a rendered map / `GetFeatureInfo` per segment (quickest look-up).
2. **WFS** for the actual attribute values per segment (analysis/GIS).
3. **FIS-Broker** for the authoritative, most-current copy and metadata.
4. **Ergebnisbericht PDF** + the [Verkehrserhebungen landing page](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsmanagement/verkehrserhebungen/) for methodology and older editions.

## 3 · Where to get DTV — derived two ways

**Option A — the dedicated DTV map.** SenMVKU **Abt. I Umweltpolitik, Ref. C
(Immissionsschutz)** publishes a converted `Verkehrsmengen DTV <year> (Umweltatlas)`
map in **FIS-Broker**, built specifically to feed noise/air calculations (it also
splits Pkw / Lieferwagen / Lkw / Reisebusse / Motorrad / Linienbus, the last from
BVG RBL data). As of the 2022 methodology paper, **DTV 2014** was the published
edition and **DTV 2019** was in preparation — so the DTV map **lags** the DTVw map
by one or more editions. Search FIS-Broker for `Verkehrsmengen DTV`.

**Option B — convert DTVw yourself.** Apply Berlin's official factors (main roads,
status **10/2021**, reviewed every 5 years; computed by TraffGo Road GmbH from the
2017–2019 permanent-counter data):

| Vehicle class | DTVw → DTV factor |
| --- | --- |
| **Kfz** (all motor vehicles) | **× 0.91** |
| **Lkw > 3.5 t** zul. GG | **× 0.82** |

The Lkw factor is lower because commercial traffic drops more sharply at weekends.
Worked example from the official guidance: 30,300 Kfz/24h DTVw × 0.91 ≈ **27,573
Kfz/24h DTV** (round up to full hundreds); 1,500 Lkw DTVw × 0.82 ≈ **1,230 Lkw DTV**.
The factors were tested for dependence on **street type (Verbindungsfunktionsstufe)**
and **load class** — where no significant difference was found, a single citywide
factor is used (hence the simple 0.91 / 0.82 for Hauptverkehrsstraßen).

- Factors & method: [Hinweise und Faktoren zur Umrechnung von Verkehrsmengen (PDF, 04/2022)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsdaten/umrechungsfaktoren-von-verkehrsmengen/hinweise-und-faktoren-zur-umrechnung-von-verkehrsmengen.pdf)
- Full worked example (RLS-19 inputs): [Rechenbeispiel (PDF)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsdaten/umrechungsfaktoren-von-verkehrsmengen/rechenbeispiel.pdf)

## 4 · Time range / editions

The Verkehrsmengenkarte is **periodic (~5-yearly)**, giving a multi-decade time
series. Known editions (map 07.01): **2023, 2019, 2014, 2005, 1998** (older ones
exist as DTV-style historical maps). The **DTV (Umweltatlas)** derivatives trail —
**DTV 2014** confirmed, **DTV 2019** was in preparation as of 2022. Each edition is
balanced to its own reference year, so cross-edition comparison is approximate
(method and network geometry evolve).

## 5 · Status & validity

- **Modelled / balanced, not measured-live.** Values are extrapolated counts
  balanced to a reference year — excellent for *spatial / network-wide* questions,
  not for a specific date/hour (use detectors for that).
- **Currency:** DTVw 2023 is the **current** edition (published Nov 2024). The
  most up-to-date copy lives in **FIS-Broker**, which may carry revisions newer
  than the open-data snapshot.
- **Licence:** DTVw 2023 is **dl-de/zero-2.0** (public-domain-style). Older
  editions may be dl-de/**by**-2.0 — check each record.
- **Unit trap:** confirm DTVw vs DTV before using a value in a regulation that
  fixes one of them. A DTVw figure is ~10 % higher than the corresponding Kfz DTV.
- **Class definitions:** "Lkw" here means **>3.5 t zulässiges Gesamtgewicht**
  (RLS-19 splits light/heavy); bicycle volume is a **12 h** daytime DTVw, not 24 h.

## 6 · DTV in context — Berlin's street categories (Kat 0–IV)

A DTV/DTVw figure is most useful read **against the function of the street that
carries it**. Berlin classifies its **übergeordnetes Straßennetz** ("StEP-Netz",
published with the **StEP Mobilität und Verkehr**) into **Verbindungsfunktions­stufen**
(connection-function levels) **0–IV**, following the FGSV **RIN 2008** guideline.
This network is ~**1,500 km** of Berlin's ~**5,350 km** total; the Senate (SenMVKU
Abt. IV) owns levels 0–IV, while the remaining **Nebennetz** is the **districts'**
(Bezirke) responsibility. The classification is geometry that the
Verkehrsmengenkarte hangs its volumes on, so **every DTVw segment can be joined to
its category** (Geoportal layer `strnetz`, WFS `https://gdi.berlin.de/services/wfs/strnetz`).

| Stufe | Berlin name (RIN name) | Function — what it connects | Typical examples |
| --- | --- | --- | --- |
| **0** | kontinentale Straßenverbindung | between metropolitan regions | A 10 ring (only a few km in Berlin, Karow/Buch) |
| **I** | großräumige Straßenverbindung | Oberzentren ↔ historische Mitte / City West | city motorways (Stadtautobahn), B1/B2/B5/B96a |
| **II** | übergeordnete Straßenverbindung | district main centres, airports/rail/ports → level I | Landsberger Allee, Tempelhofer Damm |
| **III** | örtliche Straßenverbindung | Ortsteile / minor centres ↔ main centres | Groß-Ziethener Str., Königsheideweg |
| **IV** | Ergänzungsstraßen | access to residential/commercial/industrial areas, tram/bus corridors | Wilhelminenhofstr., Montanstr. |

**How DTV relates to the categories — and the trap:**

- **Category is assigned by *function*, not by volume.** Under RIN 2008 the level
  follows the centres a road connects (via the StEP Zentren hierarchy), so DTV is
  **not** the primary criterion. A high-category road *usually* carries high DTV,
  but the mapping is correlational, not definitional.
- **Volume appears only as a *supplementary* criterion.** Older/secondary guidance
  cites indicative bands — e.g. **Kat II ≳ 50,000 Kfz/Tag**, **Kat III ≳ 25,000
  Kfz/Tag** — but the current official classification note (SenMVKU, 10/2025)
  defines the levels by function and does **not** list DTV thresholds. Treat those
  numbers as rules-of-thumb, not cut-offs.
- **The two datasets share a network, so cross them deliberately:** join the
  **DTVw** value (Verkehrsmengenkarte 07.01) to the **Verbindungsfunktionsstufe**
  (`strnetz`) to get "volume by road class" — useful for prioritising, screening,
  or sanity-checking a segment's category against what it actually carries.
- **Mind the discrepancies the Senate itself flags:** some heavily-loaded streets
  sit in residential settings (function ≠ measured load), and category can change
  on yearly updates (roads enter/leave the übergeordnetes Netz). Always pair a DTV
  value with the *edition* of both the volume map and the network classification.
- **Different "category" systems exist — don't conflate them.** The
  Verbindungsfunktionsstufe (0–IV, planning/RIN) is distinct from the **RLS-19
  road-type classes** ("Stadtstraße/Gemeindestraße >10,000 Kfz/24h" etc.) used to
  pick noise/peak-hour factors when converting DTV. The conversion-factor study
  (§3) tested whether DTVw→DTV factors differ by Verbindungsfunktionsstufe; finding
  no significant split, it kept a single citywide factor.

Deeper street-network/legal-attribute material lives in
[`speed-limits/`](speed-limits/); the network geometry itself is the
**Detailnetz** referenced in [`00-platforms.md`](00-platforms.md).

## Sources

- [daten.berlin.de — Verkehrsmengen DTVw 2023 [WMS]](https://daten.berlin.de/datensaetze/verkehrsmengen-dtvw-2023-wms-efc1dc7a)
- [SenMVKU — Verkehrserhebungen (Verkehrsmengenkarte)](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsmanagement/verkehrserhebungen/)
- [Ergebnisbericht Verkehrsmengenkarte DTVw 2023 (PDF)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsmanagement/verkehrserhebungen/ergebnisbericht-2023.pdf)
- [Umweltatlas — Verkehrsmengen / Traffic Volumes ADT (map 07.01)](https://www.berlin.de/umweltatlas/en/traffic-noise/traffic-volumes/)
- [Hinweise und Faktoren zur Umrechnung von Verkehrsmengen (PDF, 04/2022)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsdaten/umrechungsfaktoren-von-verkehrsmengen/hinweise-und-faktoren-zur-umrechnung-von-verkehrsmengen.pdf)
- [Rechenbeispiel zur Umrechnung DTVw→DTV (PDF)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsdaten/umrechungsfaktoren-von-verkehrsmengen/rechenbeispiel.pdf)
- [Geoportal Berlin (gdi.berlin.de) — WMS/WFS services & FIS-Broker](https://gdi.berlin.de/)
- [SenMVKU — Berliner Straßennetz, Erläuterung zur Klassifizierung (PDF, 10/2025)](https://www.berlin.de/sen/uvk/_assets/verkehr/verkehrsplanung/strassen-und-kfz-verkehr/uebergeordnetes-strassennetz/berliner-strassennetz-klassifizierung.pdf)
- [SenMVKU — Übergeordnetes Straßennetz (StEP-Netz) landing page](https://www.berlin.de/sen/uvk/mobilitaet-und-verkehr/verkehrsplanung/strassen-und-kfz-verkehr/uebergeordnetes-strassennetz/)
- [Wikipedia — Übergeordnetes Straßennetz von Berlin](https://de.wikipedia.org/wiki/%C3%9Cbergeordnetes_Stra%C3%9Fennetz_von_Berlin)
