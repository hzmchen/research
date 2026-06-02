#!/usr/bin/env python3
"""Static location map for the TE180 cross-section on Torstraße.

Draws TE180 (the studied site) as a star on a CartoDB-Positron basemap, with the
other three Torstraße TEU cross-sections (TE181, TE410, TE431) shown faintly for
corridor context. Coordinates for TE180 are read from data/te180_meta.json when
present (written by fetch.py); otherwise the documented WGS84 fix is used.

Only stdlib + matplotlib + contextily (Web-Mercator inlined), mirroring
../speed-limits/str17juni-example/query_and_plot.py. One network call (basemap
tiles); skips gracefully to a plain background if offline.

Usage:  python3 map.py
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "data", "te180_meta.json")
PNG  = os.path.join(HERE, "figures", "00_location_map.png")

# Documented Torstraße TEU cross-sections (lon, lat, direction) — see
# ../teu-detectors-viz-api/torstrasse-live-query.md. TE180 is overwritten from
# meta.json if available.
SITES = {
    "TE180": (13.39157593, 52.52809909, "West"),   # studied site
    "TE181": (13.39407,     52.52857,    "Ost"),
    "TE410": (13.40732,     52.52904,    "Südost"),
    "TE431": (13.41085,     52.52865,    "Nordwest"),
}

def merc(lon, lat):
    """WGS84 lon/lat -> EPSG:3857 metres."""
    R = 6378137.0
    x = math.radians(lon) * R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    return x, y

def load_te180():
    if os.path.exists(META):
        try:
            m = json.load(open(META))
            c = m["site_meta"]["coordinates"]
            if c:
                return float(c[0]), float(c[1])
        except Exception:
            pass
    return SITES["TE180"][0], SITES["TE180"][1]

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import contextily as cx

    lon180, lat180 = load_te180()
    SITES["TE180"] = (lon180, lat180, "West")

    lons = [v[0] for v in SITES.values()]; lats = [v[1] for v in SITES.values()]
    pad_lon, pad_lat = 0.0045, 0.0022
    bbox = (min(lons) - pad_lon, min(lats) - pad_lat,
            max(lons) + pad_lon, max(lats) + pad_lat)

    fig, ax = plt.subplots(figsize=(11, 6))

    # sibling cross-sections (context)
    for name, (lo, la, dr) in SITES.items():
        if name == "TE180":
            continue
        x, y = merc(lo, la)
        ax.plot(x, y, marker="o", color="#1976d2", markersize=8, zorder=4,
                markeredgecolor="white", markeredgewidth=1.0)
        ax.annotate(f"{name}\n({dr})", (x, y), xytext=(8, -4),
                    textcoords="offset points", fontsize=8, color="#0d3c61",
                    zorder=6, bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                        ec="#1976d2", alpha=0.8))

    # the studied site
    x180, y180 = merc(lon180, lat180)
    ax.plot(x180, y180, marker="*", color="#d62728", markersize=26, zorder=5,
            markeredgecolor="white", markeredgewidth=1.4)
    ax.annotate("TE180 · Torstraße (West)\nbtw Tucholskystr. & Borsigstr. (Haus 199)",
                (x180, y180), xytext=(12, 12), textcoords="offset points",
                fontsize=9.5, fontweight="bold", zorder=7,
                bbox=dict(boxstyle="round,pad=0.3", fc="#fff3f3", ec="#d62728",
                          alpha=0.92))

    bx0, by0 = merc(bbox[0], bbox[1]); bx1, by1 = merc(bbox[2], bbox[3])
    ax.set_xlim(bx0, bx1); ax.set_ylim(by0, by1)
    ax.set_xticks([]); ax.set_yticks([])
    try:
        cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.CartoDB.Positron,
                       attribution_size=6)
    except Exception as e:
        print(f"  (basemap skipped: {e})")

    handles = [
        Line2D([0], [0], marker="*", color="#d62728", lw=0, markersize=16,
               markeredgecolor="white", label="TE180 (studied)"),
        Line2D([0], [0], marker="o", color="#1976d2", lw=0, markersize=9,
               markeredgecolor="white", label="other Torstraße TEU cross-sections"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.92)
    ax.set_title("TE180 infrared (TEU) detector on Torstraße, Berlin-Mitte\n"
                 f"cross-section TE180 @ {lat180:.5f} N, {lon180:.5f} E  ·  "
                 "Richtung West", fontsize=11)
    fig.tight_layout()
    fig.savefig(PNG, dpi=140, bbox_inches="tight")
    print(f"wrote {os.path.relpath(PNG, HERE)}")

if __name__ == "__main__":
    main()
