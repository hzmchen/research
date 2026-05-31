# Worked example — querying a Torstraße detector (curl only)

> 🤖 Agent-generated; **every command below was actually run on 2026-05-31** and
> the outputs are the real responses. No SDK, no API key, no extra packages —
> just `curl` (+ `tar`/`gzip`, which are standard). dl-de/by-2.0, attribution
> *"Digitale Plattform Stadtverkehr Berlin / Verkehrsdetektion Berlin"*.

## The 8 Torstraße detectors

Filtering the `Stammdaten` on `STRASSE = Torstraße` yields **exactly 8 lane
detectors = 4 cross-sections × 2 lanes** (`Det0/Det1` = `HF1/HF2`, i.e. right lane
/ 2nd-from-right of the main carriageway):

| Cross-section | Detector file (`DET_NAME_ALT`) | New name | Location (POSITION_DETAIL) | Dir. | Lon, Lat (WGS84) |
| ------------- | ------------------------------ | -------- | -------------------------- | ---- | ---------------- |
| **TE180** | `TEU00180_Det0` / `_Det1` | TE180_Det_HF1/2 | btw Tucholskystr. & Borsigstr. (Haus 199) | West | 13.39158, 52.52810 |
| **TE181** | `TEU00181_Det0` / `_Det1` | TE181_Det_HF1/2 | btw Kleine Hamburger Str. & Bergstr. (Haus 178) | Ost | 13.39407, 52.52857 |
| **TE410** | `TEU00410_Det0` / `_Det1` | TE410_Det_HF1/2 | btw Gormannstr. & Alte Schönhauser Str. | Südost | 13.40732, 52.52904 |
| **TE431** | `TEU00431_Det0` / `_Det1` | TE431_Det_HF1/2 | btw Straßburger Str. & Schönhauser Allee | Nordwest | 13.41085, 52.52865 |

(`MQ_ID15`/`DET_ID15` and Excel-serial install dates also present; e.g. TE180 in
service since serial `37671` ≈ 2003-02.)

## Step 1 — list what's available (Azure Blob list API)

```bash
BASE="https://mdhopendata.blob.core.windows.net/verkehrsdetektion"
# top-level: years 2015..2025 + ReadMe.txt + Stammdaten xlsx
curl -s "$BASE/?restype=container&comp=list&delimiter=/" | grep -oE '<Name>[^<]*</Name>'
# the 2025 monthly new-QA archives
curl -s "$BASE/?restype=container&comp=list&delimiter=/&prefix=2025/neue_qualitaetssicherung/Fahrstreifendetektoren/" \
  | grep -oE '<Name>[^<]*</Name>'
#   → detektor_2025_01.tgz … detektor_2025_06.tgz   (latest month at snapshot = June 2025)
```

**Time range available:** 2015 → **2025-06** (hourly values, batched per month).

## Step 2 — pull one detector's data with `curl | tar` (no extra packages)

The new-QA monthly file is a `.tgz` of one CSV per detector. Stream it and extract
just the Torstraße/TE410 right-lane detector:

```bash
URL="$BASE/2025/neue_qualitaetssicherung/Fahrstreifendetektoren/detektor_2025_06.tgz"
curl -s "$URL" | tar -xzO 2025_06/TEU00410_Det0.csv > te410.csv
```

## Step 3 — the data: fields, format, real rows

**Format:** semicolon-delimited CSV, **13 columns**, German header, `NaN` for
missing. Header + sample rows actually returned:

```
Datum (Ortszeit);Stunde des Tages (Ortszeit);qkfz;qpkw;qlkw;vkfz;vpkw;vlkw;ZScore_Det0;ZScore_Det1;ZScore_Det2;Datapoints_Rel;hist_cor
2025-06-08;14;357;352;5;39;39;38;0.00;-0.20;0.00;1.00;0.81
2025-06-19;18;633;619;14;31;31;29;0.00;0.23;0.00;1.00;0.85
```

Reading the busiest hour we saw (`2025-06-19 18:00`): **633** motor vehicles
(`qkfz`) — **619 cars** + **14 trucks** — at mean **31 km/h** (`vkfz`), data
completeness `Datapoints_Rel = 1.00`. Field meanings are in
[`api-reference.md`](api-reference.md#schema).

## Step 4 — ⚠️ the duplicate-row gotcha (proven)

For every hour that has a valid reading, the file also carries an all-`NaN`
placeholder row for the same `(Datum, Stunde)`:

```
2025-06-02;10;NaN;NaN;NaN;NaN;NaN;NaN;NaN;NaN;NaN;0.00;NaN     ← placeholder
2025-06-02;10;390;354;36;40;40;40;0.00;-0.20;0.00;0.33;0.78    ← real values
```

In this single file (June 2025, `TEU00410_Det0`): **1133 data rows** but only
**715 distinct hours** — **418** of them duplicated, and **all 418** are exactly
one `NaN` + one value row. **Always dedupe on `(Datum, Stunde)` and keep the
non-`NaN` row** (e.g. sort so values beat `NaN`, or filter `qkfz != NaN`).

## Step 5 — a real daily profile (deduped)

Hourly `qkfz` for **TEU00410_Det0**, **Sunday 2025-06-08** (a fully-covered day),
straight from `te410.csv`:

```
2025-06-08 TEU00410_Det0 — qkfz/h (cars+trucks), mean speed vkfz
  00  q=278  v=37  ############################
  02  q=209  v=45  #####################
  04  q=160  v=46  ################
  06  q=128  v=44  #############
  08  q=123  v=41  ############
  10  q=205  v=40  #####################
  12  q=333  v=39  ##################################
  14  q=357  v=39  ####################################   ← afternoon peak
  16  q=280  v=40  ############################
  17  q=340  v=39  ##################################
  18  q=286  v=40  #############################
  20  q=256  v=40  ##########################
  22  q=235  v=41  ########################
```

A believable **Sunday** shape: low morning, afternoon peak ~14:00, speeds 37–48
km/h in the 50-zone, trucks a few % of flow. (Full 24 rows are in the CSV.)

## Step 6 — reality check on coverage/quality

Across all **8** Torstraße detectors in June 2025, valid (non-`NaN`) hours were
**very uneven**:

| Detector | valid hours (of ~720) | usable? |
| -------- | --------------------- | ------- |
| TEU00181_Det1 | 573 | ✅ |
| TEU00410_Det0 | 418 | ✅ |
| TEU00410_Det1 | 418 | ✅ |
| TEU00181_Det0 | 5 | ❌ effectively offline |
| TEU00180_Det0 / _Det1 | 1 | ❌ |
| TEU00431_Det0 / _Det1 | 1 | ❌ |

**Only 3 of 8 lane detectors delivered usable June-2025 data.** Even good days can
contain implausible single-hour spikes/dropouts at the lane level. **Takeaway:**
treat individual lane detectors as *frequently gappy*, prefer aggregating to the
**cross-section (Messquerschnitt)** level and across redundant lanes, and always
gate on `Datapoints_Rel`/`qualitaet` before trusting an hour.

## Step 7 — is there a LIVE feed for Torstraße? (No — and why)

The 8 Torstraße detectors live on the **legacy** `FROST-Server-TEU` SensorThings
server. TE410 is `Thing(179)`; its 5-minute KFZ-count datastream is `19225`:

```bash
B="https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
curl -s "$B/Datastreams(19225)/Observations?\$orderby=phenomenonTime desc&\$top=3&\$select=phenomenonTime,result"
```

Real response (queried **2026-05-31**): newest =
**`2025-07-01T12:30:00Z/…12:35:00Z`, result 110**. That's **~10 months old** — the
TEU feed is **frozen**, not live.

**Latest observation per Torstraße cross-section (queried 2026-05-31):**

| Cross-section | Latest TEU observation | Age |
| ------------- | ---------------------- | --- |
| TE181 | 2025-07-02 10:05Z | ~10 mo |
| TE410 | 2025-07-01 12:35Z | ~10 mo |
| TE180 | 2025-04-13 09:55Z | ~13 mo |
| TE431 | 2024-04-29 13:25Z | ~2 yr |

**Why no current data:** the legacy infrared TEU network is being decommissioned
in favour of **thermal cameras** (`FROST-Server-ThermiCam`, live to **2026-05-31**),
but **ThermiCam covers only 67 sites and none on Torstraße** — confirmed:

```bash
TC="https://api.viz.berlin.de/FROST-Server-ThermiCam/v1.1"
curl -s "$TC/Things?\$top=100&\$select=name,description" | grep -i torstr   # → no match
```

So **Torstraße currently has no live detector at all**; the freshest data is
**2025-07-02** (frozen TEU SensorThings) or **June 2025** (blob archive). For a
*currently-live* example you'd query a ThermiCam site instead, e.g. `TC013`
(Hauptstraße) or `TC009` (Frankfurter Allee), which reported within the hour.
Full reasoning: [`README.md`](README.md#why-is-the-data-old--the-endpoints-stale).

## Recap (what the API gave us)

- **Fields:** date, hour (local), counts `qkfz/qpkw/qlkw`, speeds `vkfz/vpkw/vlkw`,
  QA (`ZScore_*`, `Datapoints_Rel`, `hist_cor`); `NaN` = missing.
- **Format:** `;`-CSV, one row per (detector, date, hour); new-QA delivered as
  monthly `.tgz` of per-detector CSVs.
- **Time range (Torstraße):** archive 2015 → 2025-06 (hourly); legacy TEU
  SensorThings to ~2025-07-02 then **frozen**; **no thermal-camera (live) coverage
  on Torstraße yet**. Citywide live vehicle data exists only at the 67 ThermiCam
  sites (5-min, current to 2026-05-31).
- **Access:** anonymous — Azure-blob list + GET for history (`curl`+`tar`),
  SensorThings GET for live/legacy (`curl`); no key, no extra packages.

## Sources / docs

- [DPS file browser + `ReadMe.txt`](https://api.viz.berlin.de/daten/verkehrsdetektion)
- [Berlin Open Data – Verkehrsdetektion Berlin](https://daten.berlin.de/datensaetze/verkehrsdetektion-berlin)
- [Azure Blob – List Blobs REST API](https://learn.microsoft.com/rest/api/storageservices/list-blobs)
- Schema details: [`api-reference.md`](api-reference.md) · tools: [`tools-and-projects.md`](tools-and-projects.md)
