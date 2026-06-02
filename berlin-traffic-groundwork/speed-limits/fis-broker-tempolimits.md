# Geoportal `Tempolimits` (FIS-Broker) — the authoritative ordered-limit layer

> 🤖 Verified by **live WFS calls on 2026-06-02**. Counts come from
> `numberMatched` on the live service; re-run the curl commands for current values.

The one **official, open** dataset of Berlin's **legally ordered speed limits**.
Published by the **Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt
(SenMVKU)** through the Berlin Geoportal / FIS-Broker (`gdi.berlin.de`).

## At a glance

| | |
| --- | --- |
| **Title** | Tempolimits (angeordnete zulässige Höchstgeschwindigkeiten) |
| **WFS** | `https://gdi.berlin.de/services/wfs/tempolimits` |
| **WMS** | `https://gdi.berlin.de/services/wms/tempolimits` |
| **Feature type** | `tempolimits:hoechstgeschwindigkeit` |
| **Feature count** (live 2026-06-02) | **29,800** |
| **Geometry** | `MultiLineString`, snapped to the **Detailnetz Berlin** network |
| **CRS** | **EPSG:25833** (ETRS89 / UTM zone 33N) |
| **Reference network** | "Detailnetz Berlin" (linked via `elem_nr`) |
| **Publisher** | SenMVKU (contact in metadata record) |
| **Last revised** | **2025-05-22** · update cadence "as needed" |
| **Licence** | **dl-de/zero-2.0** — public-domain-equivalent, **no attribution required** |
| **Provenance** | reports from the **ordering & executing district authorities** (Bezirke) |

## What it contains — and what it deliberately doesn't

The abstract (verbatim from the live WFS `GetCapabilities`):

> *"Die Geometrien repräsentieren die angeordneten zulässigen Höchstgeschwindigkeiten
> im Berliner Straßennetz als **Ausnahmen vom generellen Tempo 50** (lediglich bei den
> Autobahnen wird auch Tempo 50 dargestellt). … Als Referenznetz wurde das sog.
> 'Detailnetz Berlin' gewählt."*

So:

- ✅ It records **every segment where the ordered limit ≠ 50** (almost all Tempo 30,
  plus a long tail — see below), **with the legal reason and any time restriction**.
- ⚠️ It does **NOT** contain the default-50 streets. A street **absent** from the layer
  ⇒ the StVO default (Tempo 50 in town) applies. You **cannot** read "the limit of an
  arbitrary street" from this layer alone — only *whether it deviates*. (Autobahn 50 is
  the one default shown explicitly.)
- ⚠️ Zone vs. sign nuance: it captures the *ordered* value per Detailnetz segment; it is
  not a sign-by-sign inventory and won't model implicit zone-entry semantics the way OSM's
  `zone:maxspeed` does.

## Fields (live GeoJSON sample, 2026-06-02)

A real feature (`hoechstgeschwindigkeit.1`):

```json
"properties": {
  "gisid": 1,
  "elem_nr": "45620040_45630083.01",
  "wert_ves": 30,
  "zeit_t": null,
  "tag_t": null,
  "durch_t": "angeordnete Verkehrseinschränkung",
  "dann_t": null,
  "dat_t": null
}
```

| Field | Meaning |
| --- | --- |
| `gisid` | internal feature id |
| `elem_nr` | **Detailnetz element number** — the join key to the road-network geometry/attributes (e.g. `45620040_45630083.01`) |
| `wert_ves` | **the ordered limit in km/h** (the value you want): `30`, `20`, `10`, `60`, `80`, … |
| `zeit_t` | time-of-day restriction (e.g. night-only), if the limit is not 24 h |
| `tag_t` | day restriction (which days the limit applies) |
| `durch_t` | **reason for the order** — observed values incl. `angeordnete Verkehrseinschränkung`, `Straßenschäden` (road damage); the official description also lists *Lärmschutz* (noise) and *Schulwegsicherung* (school-route safety) |
| `dann_t` | supplementary note (often null) |
| `dat_t` | date of the ordering (often null in the open extract) |

## Speed-value distribution (live `numberMatched`, 2026-06-02)

| `wert_ves` | segments | share |
| ---: | ---: | ---: |
| **30** | **28,495** | **95.6 %** |
| 60 | 287 | 1.0 % |
| 80 | 235 | 0.8 % |
| 10 | 225 | 0.8 % |
| 20 | 73 | 0.2 % |
| 50 | 47 | 0.2 % |
| 40 | 38 | 0.1 % |
| 70 | 34 | 0.1 % |
| *(other / null)* | ~366 | ~1.2 % |
| **Total** | **29,800** | |

Reading: Berlin's "exceptions to 50" are, in practice, **the Tempo-30 network** — noise/
school/safety 30-zones and 30-stretches dominate; 10–20 are play-streets/road-damage; 60–80
are the few faster arterials/autobahn approaches.

## Reproducible queries (curl-only)

```bash
WFS='https://gdi.berlin.de/services/wfs/tempolimits'

# 1) Capabilities — service title, abstract, feature type
curl -s "$WFS?service=WFS&request=GetCapabilities" | head

# 2) Field schema
curl -s "$WFS?service=WFS&version=2.0.0&request=DescribeFeatureType\
&typeName=tempolimits:hoechstgeschwindigkeit"

# 3) Two sample features as GeoJSON
curl -s "$WFS?service=WFS&version=2.0.0&request=GetFeature\
&typeNames=tempolimits:hoechstgeschwindigkeit&count=2&outputFormat=application/json"

# 4) Total segment count (no geometry transferred)
curl -s "$WFS?service=WFS&version=2.0.0&request=GetFeature\
&typeNames=tempolimits:hoechstgeschwindigkeit&resultType=hits"

# 5) Count by a given limit, e.g. all Tempo-30 segments (CQL filter)
curl -s "$WFS?service=WFS&version=2.0.0&request=GetFeature\
&typeNames=tempolimits:hoechstgeschwindigkeit&resultType=hits&cql_filter=wert_ves=30"
```

Notes: GeoServer here speaks **WFS 2.0.0**; `cql_filter` and `resultType=hits` are
supported. Default output is GML; pass `outputFormat=application/json` for GeoJSON.
Coordinates are **EPSG:25833** — reproject to WGS84 for web maps.

## Sources

- [Berlin Open Data – Tempolimits [WFS]](https://daten.berlin.de/datensaetze/tempolimits-wfs-08198ab7) · [[WMS]](https://daten.berlin.de/datensaetze/tempolimits-wms-e7b13688)
- [Geoportal metadata record](https://gdi.berlin.de/geonetwork/srv/api/records/609fb162-892d-301c-9aa6-331dd44f5a7a)
- [FIS-Broker layer description](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/tempolimits.html)
- Licence: [dl-de/zero-2.0](https://www.govdata.de/dl-de/zero-2-0)
</content>
