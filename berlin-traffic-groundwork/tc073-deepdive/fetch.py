#!/usr/bin/env python3
"""Idempotent, gentle fetch of TC073 PKW (car) 5-minute cross-section data.

Pulls count (Anzahl) and speed (Geschwindigkeit) for the PKW class at the
Messquerschnitt level from the Berlin VIZ/DPS ThermiCam FROST (OGC SensorThings)
server, merges them onto the 5-minute interval-start timestamp, and writes a tidy
CSV to data/tc073_pkw_5min.csv.

Design notes:
- IDEMPOTENT: if the output CSV already exists and looks complete, does nothing.
  Re-running re-discovers the datastream IDs by name (so it survives ID changes).
- GENTLE on the API (see ../AGENTS.md): sequential requests only, a polite delay
  between calls, exponential backoff on 5xx/timeouts, month-windowed queries so the
  server never has to sort the whole stream at once (the page size is capped at 100
  server-side, so we follow @iot.nextLink).
- Data is intentionally NOT committed to git (see .gitignore).

Usage:  python3 fetch.py            # fetch if missing
        python3 fetch.py --force    # ignore cache and re-fetch
"""
import json, sys, time, urllib.request, urllib.parse, datetime as dt, os, csv

BASE = "https://api.viz.berlin.de/FROST-Server-ThermiCam/v1.1"
SITE = "TC073"
COUNT_DS = "Anzahl PKW 5 Minuten -  Messquerschnitt"        # two spaces after '-'
SPEED_DS = "Geschwindigkeit PKW 5 Minuten -  Messquerschnitt"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "data", "tc073_pkw_5min.csv")
META = os.path.join(HERE, "data", "tc073_meta.json")

DELAY = 0.35          # seconds between requests (gentle)
TIMEOUT = 90

def get(url, tries=6):
    """GET JSON with exponential backoff on transient errors. Honours DELAY."""
    delay = 2.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
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
    """Find the site + its two datastream IDs and the observed time span."""
    f = (f"Thing/name eq '{SITE}' and (name eq '{COUNT_DS}' or name eq '{SPEED_DS}')")
    d = get(q(f"{BASE}/Datastreams",
              {"$filter": f, "$select": "@iot.id,name,phenomenonTime"}))
    ids, span = {}, None
    for r in d["value"]:
        kind = "count" if r["name"].startswith("Anzahl") else "speed"
        ids[kind] = r["@iot.id"]
        span = r.get("phenomenonTime") or span
    if "count" not in ids or "speed" not in ids:
        raise SystemExit(f"Could not resolve both datastreams for {SITE}: {ids}")
    start, end = span.split("/")
    return ids, start, end

def month_windows(start_iso, end_iso):
    s = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00")).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    end = dt.datetime.fromisoformat(end_iso.replace("Z", "+00:00")) + dt.timedelta(days=1)
    while s < end:
        nxt = (s.replace(day=28) + dt.timedelta(days=7)).replace(day=1)
        yield s, min(nxt, end)
        s = nxt

def fetch_stream(ds_id, start, end):
    """Return {interval_start_iso: result} for one datastream, month by month."""
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
                out[o["phenomenonTime"].split("/")[0]] = o["result"]
            url = d.get("@iot.nextLink")
        sys.stderr.write(f"    {w0:%Y-%m}: +{len(out)-n0} (total {len(out)})\n")
    return out

def main():
    force = "--force" in sys.argv
    if os.path.exists(OUT) and not force:
        with open(OUT) as fh:
            n = sum(1 for _ in fh) - 1
        print(f"[skip] {OUT} already exists ({n} rows). Use --force to re-fetch.")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ids, start, end = resolve()
    print(f"[resolve] {SITE} count=DS{ids['count']} speed=DS{ids['speed']} "
          f"span {start} .. {end}")
    print("[fetch] count (Anzahl PKW) ...")
    counts = fetch_stream(ids["count"], start, end)
    print("[fetch] speed (Geschwindigkeit PKW) ...")
    speeds = fetch_stream(ids["speed"], start, end)

    keys = sorted(set(counts) | set(speeds))
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp_utc", "count", "speed_kmh"])
        for k in keys:
            w.writerow([k, counts.get(k, ""), speeds.get(k, "")])
    json.dump({"site": SITE, "datastream_ids": ids, "span": [start, end],
               "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "rows": len(keys), "base": BASE,
               "count_ds_name": COUNT_DS, "speed_ds_name": SPEED_DS},
              open(META, "w"), indent=2)
    print(f"[done] wrote {len(keys)} rows -> {OUT}")

if __name__ == "__main__":
    main()
