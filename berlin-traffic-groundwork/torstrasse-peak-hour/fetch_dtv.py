#!/usr/bin/env python3
"""Fetch the official Berlin traffic-volume map values (DTV / DTVw) for the
Torstrasse links around the TE180/TE181 detectors, across all retrievable
editions (Umweltatlas DTV 1993/1998/2005/2009/2014/2019 + native
Verkehrsmengenkarte DTVw 2019/2023), via the gdi.berlin.de WFS.

Output:
  data/dtv_editions_raw.json   - the raw GeoJSON features per edition (bbox query)
  data/dtv_editions.csv        - one row per (edition, link) with the volume value
                                 and the distance of each detector to the link

Gentle: 8 sequential WFS requests with a pause. Idempotent: skips if the CSV
exists (--force to refetch).
"""

import csv
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "data" / "dtv_editions_raw.json"
OUT = HERE / "data" / "dtv_editions.csv"

BBOX = "13.3895,52.5272,13.3950,52.5292"  # lon/lat around TE180+TE181
DETECTORS = {"TE180": (13.39158, 52.52810), "TE181": (13.39407, 52.52857)}

# (edition label, kind, service, layer, volume field, extra fields)
EDITIONS = [
    ("1993", "DTV (Umweltatlas, classed)", "ua_verkehrsmengen_1993",
     "verkehrsmengen1993", "dtv1993", []),
    ("1998", "DTV (Umweltatlas)", "ua_verkehrsmengen_1998",
     "verkehrsmengen1998", "dtv_kfz", ["dtv_lkw"]),
    ("2005", "DTV (Umweltatlas)", "ua_verkehrsmengen_2005",
     "verkehrsmengen2005", "dtv2005", []),
    ("2009", "DTV (Umweltatlas)", "ua_verkehrsmengen_2009",
     "verkehrsmengen2009", "dtv", ["slkw", "llkw"]),
    ("2014", "DTV (Umweltatlas)", "ua_verkehrsmengen_2014",
     "verkehrsmengen_2014", "dtv", ["pkw", "lkw", "lieferwagen"]),
    ("2019", "DTV (Umweltatlas)", "ua_verkehrsmengen_2019",
     "verkehrsmengen_2019", "dtv", ["pkw", "lkw", "lieferwagen"]),
    ("2019", "DTVw (Verkehrsmengenkarte)", "verkehrsmengen_2019",
     "dtvw2019kfz", "dtvw_kfz", ["str_name"]),
    ("2023", "DTVw (Verkehrsmengenkarte)", "verkehrsmengen_2023",
     "dtvw2023kfz", "dtvw_kfz", ["str_name"]),
]


def get(svc: str, layer: str) -> dict:
    url = (f"https://gdi.berlin.de/services/wfs/{svc}?service=WFS&version=2.0.0"
           f"&request=GetFeature&typeNames={svc}:{layer}&bbox={BBOX},EPSG:4326"
           f"&srsName=EPSG:4326&outputFormat=application/json")
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.load(r)


def coords_of(geom: dict):
    if geom["type"] == "LineString":
        return geom["coordinates"]
    if geom["type"] == "MultiLineString":
        return [c for part in geom["coordinates"] for c in part]
    return []


def dist_m(point, coords) -> float:
    """Min distance (m) from point to a polyline's vertices (adequate at 10 m
    vertex spacing)."""
    px, py = point
    best = float("inf")
    for x, y in coords:
        dx = (x - px) * math.cos(math.radians(py)) * 111_320
        dy = (y - py) * 110_540
        best = min(best, math.hypot(dx, dy))
    return best


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        print(f"{OUT} exists - nothing to do (--force to refetch)")
        return
    raw, rows = {}, []
    for label, kind, svc, layer, field, extra in EDITIONS:
        print(f"fetch {svc}:{layer} ...", flush=True)
        fc = get(svc, layer)
        raw[f"{svc}:{layer}"] = fc
        for f in fc["features"]:
            p, coords = f["properties"], coords_of(f["geometry"])
            rows.append({
                "edition": label,
                "kind": kind,
                "layer": f"{svc}:{layer}",
                "link": p.get("link_id") or p.get("code") or p.get("schluessel")
                        or p.get("id"),
                "value": p.get(field),
                "extras": json.dumps({k: p.get(k) for k in extra},
                                     ensure_ascii=False),
                "d_TE180_m": round(dist_m(DETECTORS["TE180"], coords)),
                "d_TE181_m": round(dist_m(DETECTORS["TE181"], coords)),
            })
        time.sleep(1.2)
    RAW.write_text(json.dumps(raw, ensure_ascii=False))
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows) + raw GeoJSON")


if __name__ == "__main__":
    main()
