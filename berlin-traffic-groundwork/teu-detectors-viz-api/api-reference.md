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

## Two interfaces: live (SensorThings) + history (blob)

The VIZ platform exposes the detectors through **two** open, anonymous interfaces:

| | Live / near-real-time | Curated history |
| --- | --- | --- |
| Tech | **OGC SensorThings API** (Fraunhofer **FROST** server) | **Azure Blob** container |
| Base | `https://api.viz.berlin.de/FROST-Server-TEU/v1.1/` | `https://mdhopendata.blob.core.windows.net/verkehrsdetektion/` |
| Resolution | **5 min** (+ hour/day/week/month/year aggregates) | hourly |
| Latency | minutes (current to ~2025-07-02 at snapshot) | monthly batch (ends 2025-06) |
| Use it for | "now", live maps, sub-hourly analysis | clean long time series |

Sibling FROST servers on the same host: **`FROST-Server-EcoCounter2`** (bike
counters) and **`FROST-Server-ThermiCam`** (the thermal cameras now replacing the
infrared TEUs). All are wired into the public `viz.berlin.de` Masterportal config.

### Live: OGC SensorThings (FROST) — `FROST-Server-TEU/v1.1`

Standard SensorThings entity model; **anonymous GET**, OData query params, also
MQTT. Key entities: `Things` (one per cross-section, **276** of them),
`Datastreams` (per Thing: count/speed × KFZ/PKW/LKW × 5min/Stunde/Tag/Woche/
Monat/Jahr), `Observations`, `Locations`, `ObservedProperties`.

```bash
B="https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
curl -s "$B/"                                            # service doc (entity list)
curl -s "$B/Things?\$count=true&\$top=1"                 # 276 cross-sections
curl -s "$B/Things?\$filter=name eq 'TE410'\
&\$expand=Datastreams(\$select=@iot.id,name)"            # one sensor's datastreams
# latest 5-min vehicle counts for datastream 19225 (TE410, "Anzahl KFZ 5 Minuten"):
curl -s "$B/Datastreams(19225)/Observations?\$orderby=phenomenonTime desc&\$top=3&\$select=phenomenonTime,result"
```

`Observation.phenomenonTime` is an ISO-8601 **interval** (e.g.
`2025-07-01T12:30:00Z/2025-07-01T12:35:00Z`); `result` is the value (count, or
km/h for speed datastreams). Sensor health varies — some Things' last observation
is months old (matching the offline detectors seen in the archive).

> 📄 SensorThings spec: <https://docs.ogc.org/is/18-088/18-088.html> · FROST docs:
> <https://fraunhoferiosb.github.io/FROST-Server/>

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
│   │   ├── Fahrstreifendetektoren/             ← per-lane detector CSVs
│   │   └── Messquerschnitte/                   ← aggregated cross-section CSVs
│   └── neue_qualitaetssicherung/
│       └── Fahrstreifendetektoren/
│           └── detektor_YYYY_MM.tgz            ← monthly archive, 1 CSV per detector
└── 2025/
    └── neue_qualitaetssicherung/Fahrstreifendetektoren/detektor_2025_01..06.tgz
```

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
