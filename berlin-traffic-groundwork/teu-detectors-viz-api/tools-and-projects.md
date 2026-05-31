# Tools & projects for the detector feed

> 🤖 Agent-generated from web research + repo inspection (2026-05-31).

**Executive summary:** the only first-class tooling is **DPS's own** (the blob
browser and a Masterportal chart add-on). Third-party projects that specifically
consume the **TEU detector archive** are scarce and mostly dormant — adjacent
Berlin "traffic data" repos target *count surveys* or *transit*, not this feed. In
practice you write your own `curl` glue (it's a few lines — see
[`torstrasse-live-query.md`](torstrasse-live-query.md)).

## Official — `digitale-plattform-stadtverkehr-berlin` (GitHub org, MIT)

| Repo | What it is | Relevance |
| ---- | ---------- | --------- |
| **`datenablage`** | JS web interface over the Azure blob store (`mdhopendata`) — this *is* the `api.viz.berlin.de/daten/...` browser | Tells you the exact blob URL/list pattern (we used it to reverse the endpoint) |
| **`masterportal-addon-sensor-chart`** | Vue component that charts sensor/detector values on the `viz.berlin.de` Masterportal map | The "live" visual surface; read it to see how the map fetches current values |
| **`masterportal-dps-config`** | Masterportal config for `viz.berlin.de/verkehr-in-berlin` | Map layers, incl. detection layer wiring |
| **`eco-counter`** | Python importer for Berlin's **bike** counting stations | Sibling feed (cycling), not TEU, but same shop |
| **`service-baustellen`**, `baustellen-editor` | Construction/closure feed services | Other DPS data products |

## Adjacent / community (use with care)

| Project | What | State |
| ------- | ---- | ----- |
| [`derhuerst/eco-counter-client`](https://github.com/derhuerst/eco-counter-client) | Node client for Eco-Counter (Berlin **bike** counters, org id 4728) | Cycling, not TEU; maintained-ish |
| [`vizsim/BerlinTrafficCounts`](https://github.com/vizsim/BerlinTrafficCounts) | HTML/Jupyter viz of Berlin **traffic-count surveys 1992–2019** (Verkehrszählungen, via FragDenStaat) | ⚠️ different dataset; dormant (ends 2019) |
| [`funkeinteraktiv/Berlin-Verkehrsdaten`](https://github.com/funkeinteraktiv/Berlin-Verkehrsdaten) | VBB **GTFS** SQL importer | ⚠️ transit, not detectors; unmaintained (2013) |

## What this means for a project

- **Don't shop for a library — shop for the schema.** The `ReadMe.txt` +
  `Stammdaten` are the real "SDK"; access is a list call + file GETs.
- **Minimal stack:** `curl` (list + download) and `tar`/`gzip` (the new-QA monthly
  `.tgz`). No SDK, no key, no auth. CSV is trivially parseable.
- **For live/near-real-time**, study `masterportal-addon-sensor-chart` rather than
  the archive — but note the *open, documented* product is the hourly archive.

## Sources

- [GitHub – digitale-plattform-stadtverkehr-berlin](https://github.com/digitale-plattform-stadtverkehr-berlin)
- [datenablage repo](https://github.com/digitale-plattform-stadtverkehr-berlin/datenablage)
- [derhuerst/eco-counter-client](https://github.com/derhuerst/eco-counter-client)
- [vizsim/BerlinTrafficCounts](https://github.com/vizsim/BerlinTrafficCounts)
- [funkeinteraktiv/Berlin-Verkehrsdaten](https://github.com/funkeinteraktiv/Berlin-Verkehrsdaten)
