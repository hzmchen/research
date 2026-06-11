#!/usr/bin/env python3
"""Fetch hourly Messquerschnitt (cross-section) data for the two western
Torstrasse TEU detectors (TE180 West, TE181 Ost) from the Berlin
Verkehrsdetektion open-data blob archive (alte Qualitaetssicherung,
2015-01 .. 2024-12).

Gentle + resumable (see ../../AGENTS.md "Be a good citizen"):
  - strictly sequential, one monthly bundle at a time, with a pause between
    requests and exponential backoff on errors;
  - each month's filtered rows are cached in data/raw_months/, so an
    interrupted run never refetches finished months;
  - if the final CSV already exists the script exits immediately
    (use --force to rebuild).

Output: data/torstrasse_mq_hr.csv with columns
  mq_name;tag;stunde;qualitaet;q_kfz_mq_hr;v_kfz_mq_hr;q_pkw_mq_hr;
  v_pkw_mq_hr;q_lkw_mq_hr;v_lkw_mq_hr

Licence of the data: dl-de/by-2.0, attribution
"Digitale Plattform Stadtverkehr Berlin / Verkehrsdetektion Berlin".
"""

import gzip
import io
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://mdhopendata.blob.core.windows.net/verkehrsdetektion"
MQS = ("TE180", "TE181")
YEARS = range(2015, 2025)
HERE = Path(__file__).parent
RAW = HERE / "data" / "raw_months"
OUT = HERE / "data" / "torstrasse_mq_hr.csv"
HEADER = ("mq_name;tag;stunde;qualitaet;q_kfz_mq_hr;v_kfz_mq_hr;"
          "q_pkw_mq_hr;v_pkw_mq_hr;q_lkw_mq_hr;v_lkw_mq_hr")
PAUSE = 0.8  # seconds between requests


def fetch_month(year: int, month: int) -> str:
    """Download one monthly bundle and return the TE180/TE181 rows."""
    url = (f"{BASE}/{year}/alte_qualitaetssicherung/Messquerschnitte/"
           f"mq_hr_{year}_{month:02d}.csv.gz")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                blob = resp.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""          # month not published
            wait = 2 ** attempt * 5
            print(f"  HTTP {e.code}, backing off {wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:  # noqa: BLE001 - network grab-bag
            wait = 2 ** attempt * 5
            print(f"  {type(e).__name__}: {e}, backing off {wait}s", flush=True)
            time.sleep(wait)
    else:
        raise RuntimeError(f"giving up on {url}")

    text = gzip.decompress(blob).decode("utf-8", errors="replace")
    keep = []
    for line in io.StringIO(text):
        if line.startswith(MQS):
            keep.append(line.rstrip("\n"))
    return "\n".join(keep)


def main() -> None:
    force = "--force" in sys.argv
    if OUT.exists() and not force:
        print(f"{OUT} exists - nothing to do (--force to rebuild)")
        return
    RAW.mkdir(parents=True, exist_ok=True)

    for year in YEARS:
        for month in range(1, 13):
            cache = RAW / f"{year}_{month:02d}.csv"
            if cache.exists() and not force:
                continue
            print(f"fetch {year}-{month:02d} ...", flush=True)
            rows = fetch_month(year, month)
            cache.write_text(rows + ("\n" if rows else ""))
            print(f"  {len(rows.splitlines())} rows", flush=True)
            time.sleep(PAUSE)

    parts = [HEADER]
    for f in sorted(RAW.glob("*.csv")):
        body = f.read_text().strip()
        if body:
            parts.append(body)
    OUT.write_text("\n".join(parts) + "\n")
    n = sum(1 for _ in OUT.open()) - 1
    print(f"wrote {OUT} ({n} rows)")


if __name__ == "__main__":
    main()
