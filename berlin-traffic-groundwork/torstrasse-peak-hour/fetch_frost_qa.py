#!/usr/bin/env python3
"""Fetch the raw material for the FROST-data QA (see frost-qa.md):

  HOURLY, full FROST history (2022-01 .. end of stream):
    - Anzahl KFZ Stunde:        Messquerschnitt + both lanes, TE180 & TE181
    - Geschwindigkeit KFZ Stunde: Messquerschnitt (both Things) + TE181 lanes
  5-MINUTE, four sampled one-week windows (one per network regime):
    - Anzahl KFZ 5 Minuten:     Messquerschnitt + both lanes, TE180 & TE181
    - Geschwindigkeit KFZ 5 Minuten: Messquerschnitt, both Things

Windows (Mon..Mon, local): 2022-06-06, 2023-03-06, 2024-02-05, 2025-03-03.

Each stream is cached as data/qa/<thing>_<level>_<var>_<agg>.csv with columns
t_utc;result (interval start, raw result incl. duplicates-resolved). Gentle:
strictly sequential, ~0.45 s between page requests, exponential backoff;
finished streams are never refetched (delete a file or --force to redo).
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.viz.berlin.de/FROST-Server-TEU/v1.1"
HERE = Path(__file__).parent
QA = HERE / "data" / "qa"
PAUSE = 0.45

THINGS = {"TE180": 80, "TE181": 81}
LEVELS = {  # level tag -> datastream name suffix (double space in the API)
    "mq":  "Messquerschnitt",
    "hf1": "Hauptfahrbahn rechte Spur",
    "hf2": "Hauptfahrbahn, 2. Spur von rechts",
}
AGGS = {"hr": "Stunde", "5min": "5 Minuten"}
WINDOWS = [  # local Mon..Mon, queried as UTC with a 2 h guard
    ("2022-06-05T21:00:00Z", "2022-06-13T01:00:00Z"),
    ("2023-03-05T21:00:00Z", "2023-03-13T01:00:00Z"),
    ("2024-02-04T21:00:00Z", "2024-02-12T01:00:00Z"),
    ("2025-03-02T21:00:00Z", "2025-03-10T01:00:00Z"),
]

# (thing, level, var, agg) jobs
JOBS = []
for th in THINGS:
    for lv in LEVELS:
        JOBS.append((th, lv, "q", "hr"))            # counts, hourly, full
        JOBS.append((th, lv, "q", "5min"))          # counts, 5-min, windows
    JOBS.append((th, "mq", "v", "hr"))              # MQ speed, hourly, full
    JOBS.append((th, "mq", "v", "5min"))            # MQ speed, 5-min, windows
JOBS += [("TE181", "hf1", "v", "hr"), ("TE181", "hf2", "v", "hr")]


def get_json(url: str) -> dict:
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            wait = 2 ** attempt * 5
            print(f"  {type(e).__name__}: {e} -> backoff {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {url}")


def ds_name(level: str, var: str, agg: str) -> str:
    kind = "Anzahl" if var == "q" else "Geschwindigkeit"
    return f"{kind} KFZ {AGGS[agg]} -  {LEVELS[level]}"


def find_datastream(thing_id: int, name: str):
    q = urllib.parse.quote(f"name eq '{name}'")
    d = get_json(f"{BASE}/Things({thing_id})/Datastreams?$filter={q}"
                 f"&$select=@iot.id,name")
    return d["value"][0]["@iot.id"] if d["value"] else None


def pull(ds_id: int, t_from: str, t_to: str | None) -> dict:
    """{interval-start ISO: result}, value rows beating NaN placeholders."""
    out = {}
    flt = f"phenomenonTime ge {t_from}"
    if t_to:
        flt += f" and phenomenonTime lt {t_to}"
    url = (f"{BASE}/Datastreams({ds_id})/Observations?"
           f"$filter={urllib.parse.quote(flt)}"
           f"&$orderby=phenomenonTime&$top=1000&$select=phenomenonTime,result")
    while url:
        d = get_json(url)
        for o in d["value"]:
            start = o["phenomenonTime"].split("/")[0]
            if o["result"] is not None and out.get(start) is None:
                out[start] = o["result"]
            out.setdefault(start, o["result"])
        url = d.get("@iot.nextLink")
        time.sleep(PAUSE)
    return out


def count_scan() -> None:
    """Exhaustive monthly VALID-observation counts for the 5-min count
    streams via $count=true — full-history coverage without bulk download
    (one tiny request per stream-month; 'result ge 0' drops null
    placeholders)."""
    out = QA / "counts_5min_monthly.csv"
    if out.exists() and "--force" not in sys.argv:
        print(f"skip {out.name} (cached)")
        return
    months = [f"{y}-{m:02d}-01T00:00:00Z"
              for y in range(2022, 2026) for m in range(1, 13)][:43 + 1]
    rows = []
    for thing in THINGS:
        for level in LEVELS:
            ds = find_datastream(THINGS[thing], ds_name(level, "q", "5min"))
            if ds is None:
                continue
            for a, b in zip(months[:-1], months[1:]):
                flt = urllib.parse.quote(
                    f"phenomenonTime ge {a} and phenomenonTime lt {b}"
                    f" and result ge 0")
                d = get_json(f"{BASE}/Datastreams({ds})/Observations?"
                             f"$filter={flt}&$count=true&$top=1"
                             f"&$select=@iot.id")
                rows.append((thing, level, a[:7], d.get("@iot.count", 0)))
                time.sleep(PAUSE)
            print(f"counted {thing} {level} 5min "
                  f"({sum(r[3] for r in rows if r[0] == thing and r[1] == level)}"
                  f" valid slots total)", flush=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["thing", "level", "month", "n_valid"])
        w.writerows(rows)
    print(f"wrote {out.name}")


def main() -> None:
    force = "--force" in sys.argv
    QA.mkdir(parents=True, exist_ok=True)
    for thing, level, var, agg in JOBS:
        out = QA / f"{thing}_{level}_{var}_{agg}.csv"
        if out.exists() and not force:
            print(f"skip {out.name} (cached)")
            continue
        name = ds_name(level, var, agg)
        ds = find_datastream(THINGS[thing], name)
        if ds is None:
            print(f"!! no datastream {name!r} on {thing} - writing empty file")
            out.write_text("t_utc;result\n")
            continue
        obs = {}
        if agg == "hr":
            obs = pull(ds, "2021-12-31T00:00:00Z", None)
        else:
            for a, b in WINDOWS:
                obs.update(pull(ds, a, b))
        with out.open("w", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["t_utc", "result"])
            for t in sorted(obs):
                w.writerow([t, "" if obs[t] is None else obs[t]])
        print(f"{out.name}: ds {ds}, {sum(v is not None for v in obs.values())}"
              f" valid / {len(obs)} slots", flush=True)
    count_scan()


if __name__ == "__main__":
    main()
