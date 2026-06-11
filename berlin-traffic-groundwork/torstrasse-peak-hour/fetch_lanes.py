#!/usr/bin/env python3
"""Fetch hourly LANE-level (Fahrstreifendetektor) data for the four western
Torstrasse lane detectors from the blob archive (alte Qualitaetssicherung,
det_val_hr_YYYY_MM.csv.gz, 2015-2024) — the lane-level counterpart of
fetch.py, for the full-sample timeline illustration.

Lane detector IDs (Stammdaten_Verkehrsdetektion_2022_07_20.xlsx):
  TE180 (West, MQ 100201010015336): HF1 100101010030479, HF2 100101010030580
  TE181 (Ost,  MQ 100201010015437): HF1 100101010030681, HF2 100101010030782

Gentle + resumable, same pattern as fetch.py. Output:
data/torstrasse_det_hr.csv (schema: detid_15;tag;stunde;qualitaet;
q_kfz_det_hr;v_kfz_det_hr;q_pkw_det_hr;v_pkw_det_hr;q_lkw_det_hr;v_lkw_det_hr)
"""

import gzip
import io
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://mdhopendata.blob.core.windows.net/verkehrsdetektion"
DET_IDS = ("100101010030479", "100101010030580",
           "100101010030681", "100101010030782")
YEARS = range(2015, 2025)
HERE = Path(__file__).parent
RAW = HERE / "data" / "raw_months_det"
OUT = HERE / "data" / "torstrasse_det_hr.csv"
HEADER = ("detid_15;tag;stunde;qualitaet;q_kfz_det_hr;v_kfz_det_hr;"
          "q_pkw_det_hr;v_pkw_det_hr;q_lkw_det_hr;v_lkw_det_hr")
PAUSE = 0.8


def fetch_month(year: int, month: int) -> str:
    url = (f"{BASE}/{year}/alte_qualitaetssicherung/Fahrstreifendetektoren/"
           f"det_val_hr_{year}_{month:02d}.csv.gz")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=180) as resp:
                blob = resp.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            time.sleep(2 ** attempt * 5)
        except Exception:  # noqa: BLE001
            time.sleep(2 ** attempt * 5)
    else:
        raise RuntimeError(f"giving up on {url}")
    text = gzip.decompress(blob).decode("utf-8", errors="replace")
    keep = [ln.rstrip("\n") for ln in io.StringIO(text)
            if ln.startswith(DET_IDS)]
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
            print(f"fetch det {year}-{month:02d} ...", flush=True)
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
    print(f"wrote {OUT} ({sum(1 for _ in OUT.open()) - 1} rows)")


if __name__ == "__main__":
    main()
