# OpenStreetMap `maxspeed` — the citywide complement

> 🤖 Verified by **live Overpass API calls on 2026-06-02**. The extract's own
> `timestamp_osm_base` was `2026-06-02T11:06Z`; `timestamp_areas_base`
> `2026-05-12`. Re-run the queries below for current values.

OSM is the only source that resolves to a limit for **every** drivable Berlin way —
explicitly for ~95 % of them, and via documented defaults/zones for the rest. It's
what routing engines (OSRM, Valhalla, GraphHopper) actually consume. Trade-off vs. the
[Geoportal layer](fis-broker-tempolimits.md): **mixed provenance** and an **ODbL**
licence (share-alike + attribution) instead of an authoritative, no-attribution source.

## Live coverage (Overpass, 2026-06-02)

| Set (within Berlin `admin_level=4`) | ways | with `maxspeed` | coverage |
| --- | ---: | ---: | ---: |
| **All `highway=*`** (incl. footways, cycleways, paths, service) | 453,346 | 92,795 | 20.5 % |
| **Drivable roads only** (`motorway,trunk,primary,secondary,tertiary,unclassified,residential,living_street`) | **87,992** | **83,436** | **94.8 %** |

The all-highways figure is *not* the interesting number — most of those 453 k ways are
footpaths/cycleways/service ways that don't carry a posted vehicular limit. On the
**drivable** network the explicit-tag coverage is **~94.8 %**, and the remaining ~5 % is
recovered by routers from **default rules** and **`zone:maxspeed`** (see below) — so
*effective* coverage is essentially complete.

## What OSM has that the Geoportal doesn't (and vice-versa)

- ✅ **Default-50 streets**: OSM tags the actual limit on ordinary 50 streets too (or a
  router infers it), so you can read the limit of *any* way. The Geoportal stores **only
  deviations from 50** — see [`fis-broker-tempolimits.md`](fis-broker-tempolimits.md).
- ✅ **Zones**: `maxspeed:type=DE:zone30` / `zone:maxspeed=DE:30` encode area limits and
  their implicit entry/exit semantics.
- ✅ **Conditional limits**: `maxspeed:conditional` for time/weather-dependent limits.
- ⚠️ **No legal "reason" field**: OSM has no equivalent of the Geoportal's `durch_t`
  (Lärmschutz / Schulwegsicherung). `source:maxspeed` records *how the value was
  derived*, not *why it was ordered*.
- ⚠️ **Provenance is mixed**: surveyed signs, `sign`-derived, and bulk/default-inferred
  values coexist; quality varies by district and editor.

## Tagging model (essentials)

| Tag | Use |
| --- | --- |
| `maxspeed=30` | explicit numeric limit in km/h (Germany uses bare numbers = km/h) |
| `maxspeed=DE:urban` / `DE:rural` / `DE:living_street` | **implicit** limit by road category (50 / 100 / walking pace) |
| `zone:maxspeed=DE:30`, `maxspeed:type=DE:zone30` | the way is inside a signed **30 zone** |
| `source:maxspeed=DE:zone30` / `sign` / `survey` | provenance/derivation of the value |
| `maxspeed:conditional=30 @ (22:00-06:00)` | time-restricted limit |
| `maxspeed:hgv`, `maxspeed:forward/backward` | per-class / per-direction limits |

See [`Default speed limits`](https://wiki.openstreetmap.org/wiki/Default_speed_limits)
for how a router fills the untagged ~5 % from `DE:*` categories.

## Reproducible queries

```bash
OVP='https://overpass-api.de/api/interpreter'

# Coverage on the drivable network (counts only — fast, no geometry)
curl -s -A 'research-bot/1.0' -G "$OVP" --data-urlencode 'data=
[out:json][timeout:240];
area["name"="Berlin"]["admin_level"="4"]->.b;
( way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street)$"](area.b); )->.drv;
way.drv["maxspeed"]->.withms;
.drv out count;
.withms out count;'

# Distribution of explicit maxspeed values (pull tags, then tally locally)
curl -s -A 'research-bot/1.0' -G "$OVP" --data-urlencode 'data=
[out:json][timeout:240];
area["name"="Berlin"]["admin_level"="4"]->.b;
way["highway"]["maxspeed"](area.b);
out tags;' | python3 -c '
import sys,json,collections
c=collections.Counter(w["tags"].get("maxspeed") for w in json.load(sys.stdin)["elements"])
[print(f"{k:>14} {n}") for k,n in c.most_common(20)]'
```

Tips: use **`out count`** for coverage ratios (transfers a single number, kind to the
public server); add a `User-Agent`; for heavy/repeated work pull a **Geofabrik Berlin
extract** instead of hammering Overpass.

## Licence

**ODbL 1.0** — free to use, but **share-alike** on derived databases and **attribution**
("© OpenStreetMap contributors") required. This is materially stricter than the
Geoportal's [dl-de/zero-2.0](https://www.govdata.de/dl-de/zero-2-0); pick the source whose
licence fits your downstream product.

## Sources

- [OSM Wiki – Key:maxspeed](https://wiki.openstreetmap.org/wiki/Key:maxspeed) · [DE:Key:maxspeed](https://wiki.openstreetmap.org/wiki/DE:Key:maxspeed) · [DE:Key:source:maxspeed](https://wiki.openstreetmap.org/wiki/DE:Key:source:maxspeed)
- [OSM Wiki – Default speed limits](https://wiki.openstreetmap.org/wiki/Default_speed_limits) · [OSM tags for routing/Maxspeed](https://wiki.openstreetmap.org/wiki/OSM_tags_for_routing/Maxspeed)
- [Overpass API](https://overpass-api.de/) · [Geofabrik Berlin extract](https://download.geofabrik.de/europe/germany/berlin.html)
- [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)
</content>
