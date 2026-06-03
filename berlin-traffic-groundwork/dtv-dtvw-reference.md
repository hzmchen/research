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
| Spatial reference | **cross-section, both directions + all lanes summed** (curb-to-curb); see §7.1 | same |
| In Berlin this is the… | **native, published** product (Verkehrsmengenkarte) | **derived** product (factor or separate Umweltatlas DTV map) |
| Primary source | `Verkehrsmengen DTVw <year>` (Geoportal/FIS-Broker, WMS/WFS) | `Verkehrsmengen DTV <year> (Umweltatlas)` map, **or** DTVw × factor |
| Relation | always **≥ DTV** (weekends are lighter) | DTVw × **0.91** (Kfz) / **0.82** (Lkw >3.5 t) |

**Key point:** Berlin's traffic-volume map is published in **DTVw**, not DTV.
Standards that require DTV (noise RLS-19 / 16. BImSchV, air 39. BImSchV) are served
either by a *separate* Umweltatlas **DTV** map or by applying the published
conversion factors. Don't assume a Berlin "Verkehrsmenge" is DTV — check which one.

## 1 · Meaning

- **DTVw — average weekday daily traffic.** *Exact official definition* (Ergebnisbericht
  2023): "a value **balanced to the year 2023** for Kfz and Lkw traffic on **all Mondays
  to Thursdays (Mo–Do) outside the holiday periods and public holidays**." Vehicles per
  24 h on a normal working day. Holidays count is Berlin **and Brandenburg** (because of
  the strong commuter interlinkage). Berlin derives it from **12 h roadside counts (07–19 h)**
  at intersections/cross-sections, extrapolated to a 24 h weekday value using the permanent
  counters (Dauerzählstellen), then balanced across the network — see §7 for the full chain.
  DTVw is also what Berlin's traffic *model* produces (calibrated on these counts), so it is
  the city's native planning unit.

- **Whole cross-section, both directions, all lanes — not per-direction, not per-lane.**
  The published value is a **Querschnittsbelastung**: the sum over the entire roadway
  (curb-to-curb), both directions and all lanes added together. The Ergebnisbericht states
  the class table as "DTVw (**beide Richtungen zusammen**)" — *both directions together*.
  The *underlying* counts are recorded per direction (Fahrtrichtung FR1/FR2) and per
  movement at nodes, but the segment value you read off the map/WFS is the cross-section
  total. (Grounded: Frankfurter Allee between Buchberger Str. and Atzpodienstr. carries
  ≈ **65,239 Kfz/24h DTVw** — that is the curb-to-curb figure, not one direction.)

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
| Input (Kfz/Lkw map) | ~**3,000** node & cross-section counts (2020–2023) over a **1,318 km** count network; extrapolated & balanced to reference year 2023. (The full DTVw 2023 product incl. the bike layer cites ~5,600 counts.) |
| Value type | **DTVw per cross-section**, both directions summed (vehicles/24 h) |
| Coverage | main road network (segments expected > 10,000 Kfz/24h); the other ~4,096 km are assumed < 10,000 Kfz/24h and not individually counted |
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

Berlin has run citywide motor-traffic counts since **1951** (West Berlin), and
across the whole city since **1993**; a new Verkehrsmengenkarte is compiled
**every 4 years since 2019** (earlier editions were less regular). The edition
years that anchor the official 1991→2023 time series are: **1991, 1993, 1998,
2001, 2004, 2009, 2014, 2019, 2023** (so the current edition is **DTVw 2023**; the
previous is 2019). The **DTV (Umweltatlas)** derivatives trail — **DTV 2014**
confirmed, **DTV 2019** was in preparation as of 2022.

⚠️ Each edition is balanced to its *own* reference year over a *changing* count
network, so **do not sum or directly compare DTVw values across editions** — the
report itself warns against this and uses **Jahresfahrleistung** (annual vehicle-km)
for trend comparison instead. Also note: from **2023 onward the map excludes the
Bundesautobahnen** (federal motorways), whose responsibility passed to the
*Autobahn GmbH des Bundes* on 2021-01-01; motorway data must be requested federally.

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

## 7 · How the number is built — cross-section, "balanced", extrapolation

*(All from the official **Ergebnisbericht Verkehrsmengenkarte DTVw 2023**, Stand
10/2024 — the authoritative methodology source.)*

### 7.1 Cross-section vs direction vs lane

- The published DTVw is a **Querschnittsbelastung** — the **whole roadway,
  curb-to-curb: both directions and all lanes summed** into one vehicles/24 h
  number per segment. Confirmed verbatim in the report's class table heading:
  *"DTVw (beide Richtungen zusammen)"*.
- Counts are taken at **Querschnitte** (cross-sections) or **Knotenpunkte**
  (intersections, where turning movements are recorded). Internally each is split
  by **Fahrtrichtung** (FR1/FR2); the segment value is their **sum**.
- It is **not** a per-lane value and **not** a single-direction value. If you need
  one direction, you need the underlying directional count, not the map figure.
- **Grounded contrast:** at the *Oberbaumbrücke* the day-curves are published
  per direction — *FR1 (Richtung West)* and *FR2 (Richtung Ost)* — plus their
  *Querschnitt* sum; the map carries only the Querschnitt. At an outer site like
  *Daumstraße (Haselhorst)* the two directions diverge strongly (morning peak
  inbound, afternoon peak outbound) — yet the DTVw segment value still merges both.

### 7.2 What "balanced" (*ausgeglichen* / *Netzausgleich*) means

Two distinct things hide in the word "balanced":

1. **Balanced to a common reference year.** Counts from **2020–2023** are all
   converted to a single **2023** weekday level (via the Zähljahr factor in §7.3),
   so the whole map is internally consistent for one year even though it was
   measured over four.
2. **Network balancing (*manueller Netzausgleich*).** A final **manual**
   reconciliation step makes the segment values **consistent across the network** —
   conceptually enforcing flow continuity (what enters a node leaves it) and
   plausibility between adjacent segments, and **adjusting or flagging segments
   distorted by roadworks** (*"incl. Baustellen anpassen oder kennzeichnen"*). This
   is why a few individual segment values are smoothed/edited rather than left as
   the raw extrapolated count — it is a modelled product, not raw measurement.

### 7.3 The extrapolation (*Hochrechnung*) chain

A typical input is a **12 h count, 07–19 h, on one weekday**. Three multiplicative
factors turn it into the DTVw, all derived from the **BASt federal permanent
counters + Berlin's own detectors**, computed **separately for Kfz and Lkw**:

```
DTVw = ( Σ s_h  )  ×  f_Woche  ×  f_24h  ×  f_Zähljahr
        └ 7–19h ┘    └─ week ─┘   └ 24h ┘   └ count-year → 2023 ┘
```

| Step | Factor | Turns… into… | Corrects for | Grounded value (Kfz) |
| --- | --- | --- | --- | --- |
| 1 | **f_Woche** (per calendar week) | raw 12 h count → mean **weekday 12 h** of the count year | which week it was measured (season/holidays) | e.g. KW40 2020 ≈ 0.939; COVID-low spring weeks scaled **up** (KW13 2020 ≈ 1.341) |
| 2 | **f_24h** = [0–24]/[7–19] | weekday 12 h → mean **weekday 24 h** | the traffic outside 07–19 h (evening/night) | **1.338** (2020) → **1.362** (2023) — i.e. the 12 h window is ~73 % of the day |
| 3 | **f_Zähljahr** | count-year 24 h → **2023** 24 h | growth/decline since the count year | 2023/2020 = **0.973**, 2023/2021 = **0.950**, 2023/2022 = **1.000** |

Then the **manual Netzausgleich** (§7.2) is applied to produce the final
`DTVw 2023 Kfz` and `DTVw 2023 Lkw` values. Lkw factors differ (e.g. f_24h-Lkw
≈ 1.32–1.35; Zähljahr 2023/2020-Lkw = 0.943) because trucks have a flatter,
peak-less daily curve and a much steeper weekend drop.

**Worked example (schematic, real factors).** A cross-section counted in **2021**
yields **18,000 Kfz** over 07–19 h in calendar week 20 (f_Woche ≈ 0.994):

```
18,000 × 0.994 (week)  = 17,892   (mean weekday 12 h, 2021)
17,892 × 1.358 (24h)   = 24,298   (mean weekday 24 h, 2021)
24,298 × 0.950 (2023/2021) = 23,083  → DTVw 2023 ≈ 23,100 Kfz/24h  (round to hundreds)
```

To then get **DTV** for, say, a noise calc, apply §3's factor:
`23,100 × 0.91 ≈ 21,000 Kfz/24h DTV`. (After the network balancing the published
segment value may differ slightly from this raw chain.)

### 7.4 Why it varies — the variability the factors absorb

The factors exist because raw counts are "Momentaufnahmen" (snapshots) swung by:
**weekday** (Mon–Thu nearly identical; Fri afternoon peaks earlier; **weekends much
lower**, sharply so for Lkw), **season/holidays** (lower in school holidays and
winter), and **one-off events** in 2020–2023 (COVID measures, the 9-/29-€ and
Deutschland-Ticket, fuel-price spikes, ~200 long-running roadworks, protests/strikes).
This is exactly why a DTVw is a *modelled weekday norm*, not "the count on the day".

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
