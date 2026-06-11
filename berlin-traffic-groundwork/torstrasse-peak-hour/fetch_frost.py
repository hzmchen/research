#!/usr/bin/env python3
"""Fetch the LATEST hourly Messquerschnitt observations for TE180/TE181 from
the legacy TEU SensorThings (FROST) API — the blob archive ends 2024-12, the
FROST server carries observations into 2025 (TE180 to ~2025-04-13, TE181 to
~2025-07-02; the TEU network is frozen, so this is the end of the series).

Pulls 'Anzahl KFZ Stunde - Messquerschnitt', the matching speed stream and
'Anzahl LKW Stunde - Messquerschnitt' from 2024-11-01 on (slightly overlapping
the blob so analyze.py can prefer the QA-gated blob rows), converts UTC
interval stamps to Berlin local date/hour, and writes
data/torstrasse_frost_latest.csv in the same schema as the blob extract.

NOTE: FROST observations carry NO 'qualitaet' field; rows are written with
qualitaet = 1.0 and must be treated as un-QA'd (see README caveats).

Gentle + idempotent: sequential, paged ($top=1000), ~0.4 s between requests;
exits if the output exists (--force to refetch).
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
SINCE = "2024-11-01T00:00:00Z"
THINGS = {"TE180": 80, "TE181": 81}
STREAMS = {  # column -> datastream name (note the double space in the API)
    "q_kfz_mq_hr": "Anzahl KFZ Stunde -  Messquerschnitt",
    "v_kfz_mq_hr": "Geschwindigkeit KFZ Stunde -  Messquerschnitt",
    "q_lkw_mq_hr": "Anzahl LKW Stunde -  Messquerschnitt",
}
HERE = Path(__file__).parent
OUT = HERE / "data" / "torstrasse_frost_latest.csv"
PAUSE = 0.4
BERLIN = ZoneInfo("Europe/Berlin")
FIELDS = ["mq_name", "tag", "stunde", "qualitaet", "q_kfz_mq_hr",
          "v_kfz_mq_hr", "q_pkw_mq_hr", "v_pkw_mq_hr", "q_lkw_mq_hr",
          "v_lkw_mq_hr"]


def get_json(url: str) -> dict:
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            wait = 2 ** attempt * 5
            print(f"  {type(e).__name__}: {e}, backing off {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {url}")


def find_datastream(thing_id: int, name: str) -> int:
    q = urllib.parse.quote(f"name eq '{name}'")
    d = get_json(f"{BASE}/Things({thing_id})/Datastreams?$filter={q}"
                 f"&$select=@iot.id,name")
    if not d["value"]:
        raise RuntimeError(f"no datastream {name!r} on Thing({thing_id})")
    return d["value"][0]["@iot.id"]


def fetch_stream(ds_id: int) -> dict:
    """{UTC interval-start ISO: result} with NaN-placeholder rows dropped."""
    out = {}
    url = (f"{BASE}/Datastreams({ds_id})/Observations?"
           f"$filter=phenomenonTime%20ge%20{SINCE}"
           f"&$orderby=phenomenonTime&$top=1000"
           f"&$select=phenomenonTime,result")
    while url:
        d = get_json(url)
        for o in d["value"]:
            start = o["phenomenonTime"].split("/")[0]
            r = o["result"]
            if r is not None and out.get(start) is None:
                out[start] = r
            out.setdefault(start, r)
        url = d.get("@iot.nextLink")
        time.sleep(PAUSE)
    return out


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        print(f"{OUT} exists - nothing to do (--force to refetch)")
        return
    from datetime import datetime

    rows = {}
    for mq, tid in THINGS.items():
        for col, name in STREAMS.items():
            ds = find_datastream(tid, name)
            obs = fetch_stream(ds)
            print(f"{mq} {col}: datastream {ds}, {len(obs)} hours", flush=True)
            for iso, val in obs.items():
                loc = datetime.fromisoformat(iso.replace("Z", "+00:00")) \
                    .astimezone(BERLIN)
                key = (mq, loc.strftime("%d.%m.%Y"), loc.hour)
                rows.setdefault(key, {})[col] = val
            time.sleep(PAUSE)

    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter=";")
        w.writeheader()
        for (mq, tag, stunde), vals in sorted(rows.items()):
            if vals.get("q_kfz_mq_hr") is None:
                continue                      # placeholder-only hour
            w.writerow({"mq_name": mq, "tag": tag, "stunde": stunde,
                        "qualitaet": 1.0, **vals})
    n = sum(1 for _ in OUT.open()) - 1
    print(f"wrote {OUT} ({n} rows)")


if __name__ == "__main__":
    main()
