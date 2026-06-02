#!/usr/bin/env python3
"""Idempotent, gentle fetch of TE180 PKW (car) 5-minute cross-section data.

Pulls count (Anzahl) and speed (Geschwindigkeit) for the PKW class at the
Messquerschnitt level from the Berlin VIZ/DPS **legacy TEU** FROST (OGC
SensorThings) server, merges them onto the 5-minute interval-start timestamp,
and writes a tidy CSV to data/te180_pkw_5min.csv.

TE180 is one of the 8 Torstraße infrared (Traffic Eye Universal) lane detectors
(cross-section TE180 = Thing 80, direction West, btw Tucholskystr. & Borsigstr.).
Unlike TC073's live ThermiCam feed, the TEU network is **frozen / decommissioned**;
TE180's PKW 5-min stream runs 2023-02-22 .. 2025-04-13 but is dense only in its
**first year**, then decays to near-dead (status `n.o.k.`). We therefore pull the
**first full year of the stream** (the only year with usable coverage):

    2023-02-22T00:00:00Z .. 2024-02-22T00:00:00Z   (UTC)

Design notes (same contract as ../tc073-deepdive/fetch.py):
- IDEMPOTENT: if the output CSV already exists, does nothing (--force to re-fetch).
  Re-discovers the datastream IDs by name (survives ID changes).
- GENTLE on the API (see ../../AGENTS.md): sequential requests only, a polite delay
  between calls, exponential backoff, month-windowed queries, follow @iot.nextLink
  (server caps the page at 100).
- DEDUPE: TEU carries a duplicate-row gotcha (a NaN placeholder + a value row for
  the same interval). We key by interval-start and keep the *finite* value.
- Data is intentionally NOT committed to git (see .gitignore).

Usage:  python3 fetch.py            # fetch if missing
        python3 fetch.py --force    # ignore cache and re-fetch
"""
import json, sys, time, math, urllib.request, urllib.parse, datetime as dt, os, csv

BASE = "https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
SITE = "TE180"
COUNT_DS = "Anzahl PKW 5 Minuten -  Messquerschnitt"        # two spaces after '-'
SPEED_DS = "Geschwindigkeit PKW 5 Minuten -  Messquerschnitt"
# One-year window: the first (and only dense) year of the TE180 PKW stream.
WIN_START = "2023-02-22T00:00:00Z"
WIN_END   = "2024-02-22T00:00:00Z"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "data", "te180_pkw_5min.csv")
META = os.path.join(HERE, "data", "te180_meta.json")

DELAY = 0.35          # seconds between requests (gentle)
TIMEOUT = 90

def get(url, tries=6):
    """GET JSON with exponential backoff on transient errors. Honours DELAY."""
    delay = 2.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-bot/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = json.load(r)
            time.sleep(DELAY)
            return data
        except Exception as e:
            if attempt == tries - 1:
                raise
            sys.stderr.write(f"  retry {attempt+1} after error: {e}\n")
            time.sleep(delay)
            delay = min(delay * 2, 60)   # back off, cap 60s

def q(base, params):
    return base + "?" + urllib.parse.urlencode(params, safe="@$,()' :/")

def resolve():
    """Find the site Thing, its two datastream IDs, and the site location/metadata."""
    d = get(q(f"{BASE}/Things",
              {"$filter": f"name eq '{SITE}'",
               "$expand": ("Locations($select=name,location),"
                           "Datastreams($select=@iot.id,name,phenomenonTime,unitOfMeasurement)")}))
    if not d["value"]:
        raise SystemExit(f"Thing {SITE} not found on {BASE}")
    thing = d["value"][0]
    ids, span = {}, {}
    for ds in thing["Datastreams"]:
        if ds["name"] == COUNT_DS:
            ids["count"] = ds["@iot.id"]; span["count"] = ds.get("phenomenonTime")
        elif ds["name"] == SPEED_DS:
            ids["speed"] = ds["@iot.id"]; span["speed"] = ds.get("phenomenonTime")
    if "count" not in ids or "speed" not in ids:
        raise SystemExit(f"Could not resolve both datastreams for {SITE}: {ids}")
    loc = thing.get("Locations", [{}])[0]
    coords = (loc.get("location") or {}).get("coordinates")
    meta = {"thing_id": thing["@iot.id"], "description": thing.get("description"),
            "properties": thing.get("properties"),
            "location_name": loc.get("name"), "coordinates": coords,
            "stream_span": span}
    return ids, meta

def month_windows(start_iso, end_iso):
    s = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00")).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    end = dt.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    while s < end:
        nxt = (s.replace(day=28) + dt.timedelta(days=7)).replace(day=1)
        yield s, min(nxt, end)
        s = nxt

def _finite(v):
    """Result -> float or None (TEU encodes missing as null or NaN)."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f

def fetch_stream(ds_id, start, end):
    """Return {interval_start_iso: float} for one datastream, month by month.

    Dedupes the TEU NaN-placeholder/value double rows by keeping the finite value.
    """
    out = {}
    for w0, w1 in month_windows(start, end):
        f = (f"phenomenonTime ge {w0:%Y-%m-%dT%H:%M:%SZ} and "
             f"phenomenonTime lt {w1:%Y-%m-%dT%H:%M:%SZ}")
        url = q(f"{BASE}/Datastreams({ds_id})/Observations",
                {"$filter": f, "$select": "phenomenonTime,result",
                 "$orderby": "phenomenonTime asc", "$top": "100"})
        n0 = len(out)
        while url:
            d = get(url)
            for o in d["value"]:
                ts = o["phenomenonTime"].split("/")[0]
                val = _finite(o.get("result"))
                # keep a finite value; never let a NaN placeholder clobber it
                if ts not in out or out[ts] is None:
                    out[ts] = val
            url = d.get("@iot.nextLink")
        sys.stderr.write(f"    {w0:%Y-%m}: total {len(out)} (+{len(out)-n0})\n")
    return out

def main():
    force = "--force" in sys.argv
    if os.path.exists(OUT) and not force:
        with open(OUT) as fh:
            n = sum(1 for _ in fh) - 1
        print(f"[skip] {OUT} already exists ({n} rows). Use --force to re-fetch.")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ids, meta = resolve()
    print(f"[resolve] {SITE}=Thing{meta['thing_id']} count=DS{ids['count']} "
          f"speed=DS{ids['speed']}  coords={meta['coordinates']}")
    print(f"[window]  {WIN_START} .. {WIN_END}")
    print("[fetch] count (Anzahl PKW) ...")
    counts = fetch_stream(ids["count"], WIN_START, WIN_END)
    print("[fetch] speed (Geschwindigkeit PKW) ...")
    speeds = fetch_stream(ids["speed"], WIN_START, WIN_END)

    keys = sorted(set(counts) | set(speeds))
    def fmt(v):
        return "" if v is None else (f"{v:g}")
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp_utc", "count", "speed_kmh"])
        for k in keys:
            w.writerow([k, fmt(counts.get(k)), fmt(speeds.get(k))])
    json.dump({"site": SITE, "datastream_ids": ids,
               "window": [WIN_START, WIN_END], "base": BASE,
               "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "rows": len(keys), "site_meta": meta,
               "count_ds_name": COUNT_DS, "speed_ds_name": SPEED_DS},
              open(META, "w"), indent=2)
    print(f"[done] wrote {len(keys)} rows -> {OUT}")

if __name__ == "__main__":
    main()
