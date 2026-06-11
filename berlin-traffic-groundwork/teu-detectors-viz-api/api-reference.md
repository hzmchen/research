# API reference — VIZ / DPS Verkehrsdetektion

> 🤖 Agent-generated; verified by live calls 2026-05-31 (snapshot). dl-de/by-2.0,
> attribution *"Digitale Plattform Stadtverkehr Berlin / Verkehrsdetektion Berlin"*.

## What the TEU detectors are

**TEU = "Traffic Eye Universal"** — passive-infrared roadside detectors at **240+
locations** on Berlin's main road network, measuring vehicle **count**,
**classification** (car vs truck), and **speed** per lane. (Per SenUVK, the fleet
is being upgraded to ~250 thermal-imaging cameras, but the open data model below is
unchanged.) Detectors are grouped into **Messquerschnitte** (directional
measurement cross-sections); a cross-section's value exists only when *all* its
lane detectors have a valid hour.

## Interfaces: 3 live SensorThings servers + 1 history blob

The VIZ platform exposes detection through open, anonymous **OGC SensorThings
(Fraunhofer FROST)** servers, plus an Azure-blob history store. **Which vehicle
server is live changed with the infrared→thermal migration** — verified
2026-05-31:

| Endpoint (`/v1.1/`) | Data | Things | Newest obs | State |
| --- | --- | --- | --- | --- |
| `…/FROST-Server-ThermiCam` | **thermal cams, multimodal** (PKW/LKW/Lieferwagen/Krad/**Fahrrad/Fußgänger**), 5-min + aggregates | **67** | **2026-05-31** | ✅ live |
| `…/FROST-Server-TEU` | **legacy infrared**, KFZ/PKW/LKW, 5-min + aggregates | 276 | ~2025-07-02 | ⛔ frozen |
| `…/FROST-Server-EcoCounter2` | bike counters | 24 | 2026-05-30 | ✅ live |
| `mdhopendata.blob…/verkehrsdetektion/` | curated **hourly** history (TEU era) | — | ends 2025-06 | 🟡 not extended |

➡️ **For current vehicle data use `ThermiCam`** (but only 67 sites exist so far).
`TEU` is the richest *historical* live record but is no longer updating. For clean
long time series use the blob archive. See [`README.md`](README.md#why-is-the-data-old--the-endpoints-stale)
for why TEU/the archive stopped.

### SensorThings entity model (all three servers)

Standard STA; **anonymous GET**, OData query params, also MQTT. Entities: `Things`
(one per measurement cross-section), `Datastreams` (per Thing: count/speed × each
vehicle class × 5min/Stunde/Tag/Woche/Monat/Jahr), `Observations`, `Locations`,
`ObservedProperties`, `Sensors`, `FeaturesOfInterest`.

```bash
# --- LIVE vehicle data today: ThermiCam ---
B="https://api.viz.berlin.de/FROST-Server-ThermiCam/v1.1"
curl -s "$B/"                                  # service doc (entity list)
curl -s "$B/Things?\$count=true&\$top=5"       # 67 camera sites
# pick a Thing, list its 5-min datastreams, read newest observations:
curl -s "$B/Things(9)/Datastreams?\$select=@iot.id,name"
curl -s "$B/Datastreams(<id>)/Observations?\$orderby=phenomenonTime desc&\$top=3&\$select=phenomenonTime,result"

# --- LEGACY (frozen, but documents the TEU era): TEU ---
T="https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
curl -s "$T/Things?\$filter=name eq 'TE410'&\$expand=Datastreams(\$select=@iot.id,name)"
curl -s "$T/Datastreams(19225)/Observations?\$orderby=phenomenonTime desc&\$top=3&\$select=phenomenonTime,result"
```

`Observation.phenomenonTime` is an ISO-8601 **interval** (e.g.
`2025-07-01T12:30:00Z/2025-07-01T12:35:00Z`); `result` is the value (count, or
km/h for speed datastreams). **Sensor health varies widely** — on both servers
many Things last reported months ago; always check the newest `phenomenonTime`
before trusting a stream.

> 📄 SensorThings spec: <https://docs.ogc.org/is/18-088/18-088.html> · FROST docs:
> <https://fraunhoferiosb.github.io/FROST-Server/>

### Datastream anatomy — why one site has hundreds of datastreams

A single Thing exposes **many** datastreams (ThermiCam 216–648, median **432**; TEU
72–144, median **108**). They are the **cross-product of four dimensions** — a
datastream name reads as **`{measure} {class} {interval} - {spatial unit}`**:

| Dimension | Values | Count |
| --- | --- | --- |
| **Measure** | `Anzahl` (count) · `Geschwindigkeit` (speed) | 2 |
| **Time aggregation** | `5 Minuten` · `Stunde` · `Tag` · `Woche` · `Monat` · `Jahr` | 6 |
| **Vehicle class** | ThermiCam: `PKW`, `LKW mit/ohne Anhänger`, `Lieferwagen`, `Krad`, `Bus`, `Fahrrad`, `Fußgänger` (+`KFZ`) ≈ 9 · TEU: `KFZ`, `PKW`, `LKW` = 3 | 3 or ~9 |
| **Spatial unit** | `Messquerschnitt` (whole cross-section) + per-lane, e.g. `HFB 1. Spur von rechts` | varies (lanes) |

So the per-site total factors as **classes × measures × intervals × spatial units**:

```
ThermiCam:  9 × 2 × 6 = 108 per spatial unit  →  432 = 108 × 4 (cross-section + 3 lanes)
TEU:        3 × 2 × 6 =  36 per spatial unit  →  108 =  36 × 3
```

The count varies per site only by **how many lanes it resolves** (216 = 2 units,
432 = 4, 648 = 6). Two caveats: the **5-minute** stream is the raw feed and the
hour→year levels are **server-side rollups** of it (mostly redundant), and many
class/lane streams (e.g. `Bus`, or `Fußgänger` speed on a car road) exist in the
schema but are near-empty.

**Example query** — count a site's datastreams and sample their names (the
`$expand($count=true;$top=0)` trick returns the count without the bodies):

```bash
B="https://api.viz.berlin.de/FROST-Server-ThermiCam/v1.1"
# how many datastreams does TC023 have?
curl -s "$B/Things?\$filter=name eq 'TC023'&\$select=name&\$expand=Datastreams(\$count=true;\$top=0)"
# sample the first 3 names + units:
curl -s "$B/Things?\$filter=name eq 'TC023'&\$select=name&\$expand=Datastreams(\$select=name,unitOfMeasurement;\$top=3)"
```

**Actual return value** (second query, abridged):

```json
{
  "value": [
    {
      "name": "TC023",
      "Datastreams@iot.count": 432,
      "Datastreams": [
        { "name": "Anzahl Fußgänger 5 Minuten -  Messquerschnitt",
          "unitOfMeasurement": { "name": "Verkehrsstärke", "symbol": "Fußgänger/5 Minuten", "definition": null } },
        { "name": "Anzahl Fußgänger Stunde -  Messquerschnitt",
          "unitOfMeasurement": { "name": "Verkehrsstärke", "symbol": "Fußgänger/Stunde", "definition": null } },
        { "name": "Anzahl Fußgänger Tag -  Messquerschnitt",
          "unitOfMeasurement": { "name": "Verkehrsstärke", "symbol": "Fußgänger/Tag", "definition": null } }
      ],
      "Datastreams@iot.nextLink": ".../Things(21)/Datastreams?$top=3&$skip=3&..."
    }
  ]
}
```

The `unitOfMeasurement.symbol` (`Fußgänger/5 Minuten`) encodes the class + interval;
speed streams instead read `Geschwindigkeit … - …` with a km/h unit. See
[`thermicam-teu-staleness.md`](thermicam-teu-staleness.md) for per-site datastream
counts and the inferred observation volume.

## The history endpoint is an Azure Blob container

`https://api.viz.berlin.de/daten/verkehrsdetektion` is an HTML page whose
`browser.js` simply lists an Azure blob container:

```
AZURE_DOMAIN = https://mdhopendata.blob.core.windows.net/
container     = verkehrsdetektion
```

List it with the standard **Azure "List Blobs"** REST API (anonymous read):

```bash
# top-level "folders" (BlobPrefix) — delimiter makes it directory-like
curl -s "https://mdhopendata.blob.core.windows.net/verkehrsdetektion/?restype=container&comp=list&delimiter=/" \
  | grep -oE '<Name>[^<]*</Name>'

# browse into a path with &prefix=
curl -s "https://mdhopendata.blob.core.windows.net/verkehrsdetektion/?restype=container&comp=list&delimiter=/&prefix=2025/"
```

The response is XML (`/EnumerationResults/Blobs/Blob/Name`). Any blob is then a
plain `GET`:

```bash
curl -s "https://mdhopendata.blob.core.windows.net/verkehrsdetektion/ReadMe.txt"
```

> 📄 The canonical schema documentation is the **`ReadMe.txt`** sitting in the
> container root — read it first.

## Container layout (snapshot 2026-05-31)

```
verkehrsdetektion/
├── ReadMe.txt                                  ← schema / field docs
├── Stammdaten_Verkehrsdetektion_2022_07_20.xlsx ← detector ↔ street/coords map
├── 2015/ … 2024/
│   ├── alte_qualitaetssicherung/
│   │   ├── Fahrstreifendetektoren/             ← per-lane detector CSVs (det_val_hr_YYYY_MM.csv.gz)
│   │   └── Messquerschnitte/                   ← aggregated cross-section CSVs (mq_hr_YYYY_MM.csv.gz)
│   └── neue_qualitaetssicherung/               ← ⚠️ exists only from 2023!
│       └── Fahrstreifendetektoren/
│           └── detektoren_YYYY_MM.tgz          ← monthly archive, 1 CSV per detector
└── 2025/
    └── neue_qualitaetssicherung/Fahrstreifendetektoren/detektor_2025_01..06.tgz
```

⚠️ **Corrections from actually listing the container (2026-06-11):** the
neue-QS folders exist **only for 2023-2025** (2015-2022 carry alte QS alone);
the tgz stem is `detektoren_` in 2023/24 but `detektor_` in 2025; and the
neue-QS CSV schema varies — 2023/24 files use the long header (`Datum
(Ortszeit);…`) with a `Vollständigkeit` (0-100) quality field, 2025 files the
short header with `Datapoints_Rel` (0-1). See
[`../torstrasse-peak-hour/fetch_neuqa.py`](../torstrasse-peak-hour/fetch_neuqa.py)
for a parser handling all variants.

- **Time range:** **2015 → 2025-06** at the snapshot (no 2026 folder yet; latest
  monthly archive = `detektor_2025_06.tgz`). The open archive is **hourly,
  batched monthly** — treat it as *recent history*, not a real-time feed.
- **Granularity:** one row per **(detector, date, hour)**, local time.

## Schema

### Stammdaten (master data) — single sheet `Stammdaten_TEU_20220720`, 582 detectors

Columns: `MQ_KURZNAME, DET_NAME_ALT, DET_NAME_NEU, DET_ID15, MQ_ID15, STRASSE,
POSITION, POS_DETAIL, RICHTUNG, SPUR, annotation, LÄNGE (WGS84), BREITE (WGS84),
INBETRIEBNAHME, ABBAUDATUM, DEINSTALLIERT, KOMMENTAR`.

- `DET_NAME_ALT` (e.g. `TEU00410_Det0`) = the **filename** used inside the new-QA
  archives. `MQ_KURZNAME` (e.g. `TE410`) groups lanes into a cross-section.
- `STRASSE` is the street to filter on (e.g. `Torstraße`); coordinates are WGS84.
- Dates like `INBETRIEBNAHME` are **Excel serial numbers** (e.g. `39802` ≈ 2008-12).

### Neue Qualitätssicherung — per-detector CSV (what we query below)

Semicolon-delimited, 13 columns, German header:

| Field | Meaning |
| ----- | ------- |
| `Datum (Ortszeit)` | local date `YYYY-MM-DD` |
| `Stunde des Tages (Ortszeit)` | hour `0`–`23` (`8` = 08:00–08:59) |
| `qkfz` | count, all motor vehicles (Kfz) in the hour |
| `qpkw` | count, cars (Pkw) |
| `qlkw` | count, trucks (Lkw) |
| `vkfz` / `vpkw` / `vlkw` | mean speed [km/h] for Kfz / Pkw / Lkw |
| `ZScore_Det0/1/2` | normalised correlation of `qkfz` to each lane detector |
| `Datapoints_Rel` | completeness of the underlying intervals (0–1) |
| `hist_cor` | correlation of `qkfz` to the expected day/hour average |
| missing hours | encoded as `NaN` |

### Alte Qualitätssicherung — per-lane + cross-section CSVs

Detector fields: `detid_15, tag, stunde, qualitaet, q_kfz_det_hr, v_kfz_det_hr,
q_pkw_det_hr, v_pkw_det_hr, q_lkw_det_hr, v_lkw_det_hr`. Cross-section files use the
same shape with `mq_name` and `*_mq_hr` columns. `qualitaet` is the share of valid
intervals; **hours below 75 % validity are dropped** (so absence ≠ zero traffic).

## Quality caveats (from the ReadMe + observed)

- `q_kfz` may differ slightly from `q_pkw + q_lkw` (rounding in the method).
- A cross-section value needs **all** member detectors valid for that hour.
- **Historical data was reworked in 2025** — expect series breaks vs older pulls.
- **Duplicate-row gotcha** in new-QA files (NaN placeholder + value row per valid
  hour) — see [`torstrasse-live-query.md`](torstrasse-live-query.md).

## Sources

- [DPS – Verkehrsdetektion (file browser + ReadMe.txt)](https://api.viz.berlin.de/daten/verkehrsdetektion)
- [Berlin Open Data – Verkehrsdetektion Berlin](https://daten.berlin.de/datensaetze/verkehrsdetektion-berlin)
- [Berlin Open Data – Standorte der Verkehrsdetektion](https://daten.berlin.de/datensaetze/standorte-verkehrsdetektion-berlin)
- [Azure Blob – List Blobs REST API](https://learn.microsoft.com/rest/api/storageservices/list-blobs)
- [SenUVK press – new data & technology (2021)](https://www.berlin.de/sen/uvk/presse/pressemitteilungen/2021/pressemitteilung.1131619.php)
