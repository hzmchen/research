#!/usr/bin/env python3
"""Worked example: legal speed limits around the TC073 ThermiCam location.

Showcases the Berlin Geoportal `Tempolimits` WFS at the *same* spot the repo's
single-site detector deep dive studies — TC073, Straße des 17. Juni
(52.51376 N, 13.34194 E; see ../../tc073-deepdive/ and
../../teu-detectors-viz-api/thermicam-camera-map.md).

What it does (gentle, one request):
  1. Queries the WFS for every ordered speed-limit segment in a small bbox around
     TC073, asking for GeoJSON in EPSG:4326.
  2. Prints the API spec used, the formats available, a data summary, and the
     limit on / nearest to the detector itself.
  3. Plots the segments coloured by km/h on a static OSM/Carto basemap and writes
     figures/tempolimits_str17juni.png.

Only stdlib + matplotlib + contextily (no pyproj/shapely): Web-Mercator is inlined.

Usage:  python3 query_and_plot.py
"""
import json, math, os, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GEOJSON = os.path.join(HERE, "data", "tempolimits_str17juni.geojson")
PNG = os.path.join(HERE, "figures", "tempolimits_str17juni.png")
OSM_JSON = os.path.join(HERE, "data", "osm_maxspeed_str17juni.json")
OSM_PNG = os.path.join(HERE, "figures", "osm_maxspeed_str17juni.png")
OVERPASS = "https://overpass-api.de/api/interpreter"
DRIVABLE = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
            "living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link")

# --- TC073 location (from thermicam-camera-map.md) ---------------------------
TC073 = (13.34194, 52.51376)  # lon, lat
# bbox ~ 900 m (E-W) x 650 m (N-S) around it
DLON, DLAT = 0.0130, 0.0060
BBOX = (TC073[0] - DLON, TC073[1] - DLAT, TC073[0] + DLON, TC073[1] + DLAT)

# --- WFS spec ----------------------------------------------------------------
WFS = "https://gdi.berlin.de/services/wfs/tempolimits"
TYPENAME = "tempolimits:hoechstgeschwindigkeit"
PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": TYPENAME,
    "outputFormat": "application/json",
    "srsName": "EPSG:4326",
    "cql_filter": "BBOX(geom,{0},{1},{2},{3},'EPSG:4326')".format(*BBOX),
}

# colour per ordered km/h (absent street => default Tempo 50, not in this layer)
COLOR = {10: "#7b1fa2", 20: "#d32f2f", 30: "#f57c00", 40: "#fbc02d",
         50: "#388e3c", 60: "#1976d2", 70: "#0097a7", 80: "#455a64"}


def fetch():
    if os.path.exists(GEOJSON):
        with open(GEOJSON, encoding="utf-8") as fh:
            return json.load(fh)
    url = WFS + "?" + urllib.parse.urlencode(PARAMS)
    req = urllib.request.Request(url, headers={"User-Agent": "research-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    with open(GEOJSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return data


def merc(lon, lat):
    """WGS84 lon/lat -> EPSG:3857 metres (for the contextily basemap)."""
    R = 6378137.0
    x = math.radians(lon) * R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    return x, y


def haversine_m(a, b):
    R = 6371000.0
    dlat = math.radians(b[1] - a[1]); dlon = math.radians(b[0] - a[0])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a[1])) * math.cos(math.radians(b[1]))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def summarise(data):
    feats = data["features"]
    print(f"\n# API spec")
    print(f"  WFS         {WFS}")
    print(f"  feature     {TYPENAME}")
    print(f"  request     GetFeature / WFS 2.0.0")
    print(f"  bbox (CQL)  {PARAMS['cql_filter']}")
    print(f"  formats     application/json (here) | GML 3.2 (default) | WMS image | CSV")
    print(f"  CRS         requested EPSG:4326 (native EPSG:25833)")
    print(f"  licence     dl-de/zero-2.0 (no attribution required)")
    print(f"\n# Result  ({data.get('numberReturned')} segments in bbox)")
    from collections import Counter
    by = Counter((f["properties"]["wert_ves"], f["properties"]["durch_t"]) for f in feats)
    for (v, reason), n in sorted(by.items(), key=lambda kv: (-kv[0][0], -kv[1])):
        print(f"  {n:3d} x  Tempo {v:<3} — {reason}")

    # nearest segment vertex to the detector
    best = (1e9, None)
    for f in feats:
        geom = f["geometry"]
        lines = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for line in lines:
            for lon, lat in line:
                d = haversine_m(TC073, (lon, lat))
                if d < best[0]:
                    best = (d, f["properties"])
    p = best[1]
    print(f"\n# Nearest ordered limit to TC073  ({best[0]:.0f} m away)")
    print(f"  Tempo {p['wert_ves']}  ·  reason: {p['durch_t']}  ·  elem_nr {p['elem_nr']}"
          f"  ·  zeit_t {p['zeit_t']}  ·  tag_t {p['tag_t']}")
    print("  NB: Straße des 17. Juni itself carries NO feature here -> default Tempo 50")
    print("      (the layer stores only the *exceptions* to 50).")
    return feats


def plot(feats):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import contextily as cx

    fig, ax = plt.subplots(figsize=(11, 7))
    seen = set()
    for f in feats:
        v = f["properties"]["wert_ves"]
        c = COLOR.get(v, "#000000")
        geom = f["geometry"]
        lines = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for line in lines:
            xs, ys = zip(*(merc(lon, lat) for lon, lat in line))
            ax.plot(xs, ys, color=c, lw=3, solid_capstyle="round",
                    zorder=3, alpha=0.9)
            seen.add(v)

    # the detector
    tx, ty = merc(*TC073)
    ax.plot(tx, ty, marker="*", color="black", markersize=22, zorder=5,
            markeredgecolor="white", markeredgewidth=1.2)
    ax.annotate("TC073 · Straße des 17. Juni\n(ThermiCam — default Tempo 50, no feature)",
                (tx, ty), xytext=(12, 12), textcoords="offset points",
                fontsize=9, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.85))

    bx0, by0 = merc(BBOX[0], BBOX[1]); bx1, by1 = merc(BBOX[2], BBOX[3])
    ax.set_xlim(bx0, bx1); ax.set_ylim(by0, by1)
    ax.set_xticks([]); ax.set_yticks([])
    try:
        cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.CartoDB.Positron,
                       attribution_size=6)
    except Exception as e:  # offline / tile error -> plain background
        print(f"  (basemap skipped: {e})")

    handles = [Line2D([0], [0], color=COLOR[v], lw=3, label=f"Tempo {v}")
               for v in sorted(seen, reverse=True)]
    handles.append(Line2D([0], [0], marker="*", color="black", lw=0,
                          markersize=12, label="TC073 detector"))
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.9,
              title="ordered limit (wert_ves)")
    ax.set_title("Berlin Geoportal `Tempolimits` (WFS) around TC073 / Straße des 17. Juni\n"
                 "ordered speed limits = exceptions to the default Tempo 50",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(PNG, dpi=140, bbox_inches="tight")
    print(f"\nwrote {os.path.relpath(PNG, HERE)}")


# ---------------------------------------------------------------------------
# OSM complement: the same bbox via the Overpass API. Unlike the Geoportal
# layer, OSM tags the default-50 streets too (incl. Straße des 17. Juni itself),
# so it resolves to a limit for *every* drivable way, not just the exceptions.
# ---------------------------------------------------------------------------
OSM_QUERY = (
    "[out:json][timeout:120];"
    'way["highway"~"^(%s)$"](%f,%f,%f,%f);'
    "out geom tags;" % (DRIVABLE, BBOX[1], BBOX[0], BBOX[3], BBOX[2])
)


def fetch_osm():
    if os.path.exists(OSM_JSON):
        with open(OSM_JSON, encoding="utf-8") as fh:
            return json.load(fh)
    body = urllib.parse.urlencode({"data": OSM_QUERY}).encode()
    req = urllib.request.Request(OVERPASS, data=body,
                                 headers={"User-Agent": "research-bot/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    with open(OSM_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return data


def _num(ms):
    """OSM maxspeed string -> int km/h, or None (implicit/untagged/non-numeric)."""
    try:
        return int(str(ms).strip())
    except (TypeError, ValueError):
        return None


def summarise_osm(data):
    from collections import Counter
    ways = data["elements"]
    print(f"\n# OSM complement — Overpass, same bbox")
    print(f"  endpoint    {OVERPASS}")
    print(f"  query       way[highway~drivable]({BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]}); out geom tags;")
    print(f"  licence     ODbL (© OpenStreetMap contributors)")
    by = Counter(w["tags"].get("maxspeed", "<none>") for w in ways)
    tagged = sum(n for k, n in by.items() if k != "<none>")
    print(f"\n  {len(ways)} drivable ways · {tagged} with explicit maxspeed "
          f"({100*tagged/len(ways):.1f}%)")
    for k, n in by.most_common():
        print(f"    {n:3d}  maxspeed={k}")
    s17 = [w for w in ways if "17. Juni" in w["tags"].get("name", "")]
    if s17:
        print(f"\n  Straße des 17. Juni: {len(s17)} ways, "
              f"maxspeed={sorted({w['tags'].get('maxspeed') for w in s17})} "
              f"-> OSM HAS the default-50 the Geoportal omits.")
    return ways


def plot_osm(ways):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import contextily as cx

    fig, ax = plt.subplots(figsize=(11, 7))
    seen = set()
    for w in ways:
        v = _num(w["tags"].get("maxspeed"))
        c = COLOR.get(v, "#9e9e9e")  # grey = implicit/untagged
        geom = w.get("geometry") or []
        if len(geom) < 2:
            continue
        xs, ys = zip(*(merc(p["lon"], p["lat"]) for p in geom))
        ax.plot(xs, ys, color=c, lw=2.4, solid_capstyle="round", zorder=3, alpha=0.9)
        seen.add(v)

    tx, ty = merc(*TC073)
    ax.plot(tx, ty, marker="*", color="black", markersize=22, zorder=5,
            markeredgecolor="white", markeredgewidth=1.2)
    ax.annotate("TC073 · Straße des 17. Juni\n(OSM maxspeed = 50, explicitly tagged)",
                (tx, ty), xytext=(12, 12), textcoords="offset points",
                fontsize=9, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.85))

    bx0, by0 = merc(BBOX[0], BBOX[1]); bx1, by1 = merc(BBOX[2], BBOX[3])
    ax.set_xlim(bx0, bx1); ax.set_ylim(by0, by1)
    ax.set_xticks([]); ax.set_yticks([])
    try:
        cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.CartoDB.Positron,
                       attribution_size=6)
    except Exception as e:
        print(f"  (basemap skipped: {e})")

    order = [v for v in (80, 70, 60, 50, 40, 30, 20, 10) if v in seen]
    handles = [Line2D([0], [0], color=COLOR[v], lw=3, label=f"{v} km/h") for v in order]
    if None in seen:
        handles.append(Line2D([0], [0], color="#9e9e9e", lw=3, label="implicit / untagged"))
    handles.append(Line2D([0], [0], marker="*", color="black", lw=0,
                          markersize=12, label="TC073 detector"))
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.9,
              title="OSM maxspeed")
    ax.set_title("OpenStreetMap `maxspeed` around TC073 / Straße des 17. Juni\n"
                 "every drivable way resolves to a limit — incl. the default-50 arterial",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(OSM_PNG, dpi=140, bbox_inches="tight")
    print(f"\nwrote {os.path.relpath(OSM_PNG, HERE)}")


if __name__ == "__main__":
    data = fetch()
    feats = summarise(data)
    plot(feats)

    osm = fetch_osm()
    ways = summarise_osm(osm)
    plot_osm(ways)
