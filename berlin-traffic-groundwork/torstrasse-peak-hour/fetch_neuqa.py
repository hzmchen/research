#!/usr/bin/env python3
"""Fetch the NEUE Qualitaetssicherung hourly lane data for the four western
Torstrasse detectors from the blob archive. Neue-QS exists only for
2023-01 .. 2025-06, as monthly .tgz bundles of one CSV per detector
(naming: detektoren_YYYY_MM.tgz in 2023/2024, detektor_YYYY_MM.tgz in 2025).

Handles the documented NaN-placeholder duplicate rows (one all-NaN + one
value row per valid hour) by keeping the non-NaN row.

Output: data/torstrasse_neuqa_hr.csv with columns
  det;tag;stunde;qkfz;qpkw;qlkw;vkfz;datapoints_rel;hist_cor

Gentle + resumable, same pattern as the other fetchers.
"""

import csv
import io
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://mdhopendata.blob.core.windows.net/verkehrsdetektion"
DETS = ("TEU00180_Det0", "TEU00180_Det1", "TEU00181_Det0", "TEU00181_Det1")
MONTHS = ([(2023, m) for m in range(1, 13)] + [(2024, m) for m in range(1, 13)]
          + [(2025, m) for m in range(1, 7)])
HERE = Path(__file__).parent
RAW = HERE / "data" / "raw_months_neuqa"
OUT = HERE / "data" / "torstrasse_neuqa_hr.csv"
PAUSE = 0.8
FIELDS = ["det", "tag", "stunde", "qkfz", "qpkw", "qlkw", "vkfz",
          "datapoints_rel", "hist_cor"]


def fetch_month(year: int, month: int) -> list:
    rows = []
    for stem in ("detektoren", "detektor"):
        url = (f"{BASE}/{year}/neue_qualitaetssicherung/Fahrstreifendetektoren/"
               f"{stem}_{year}_{month:02d}.tgz")
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                blob = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
    else:
        return rows
    tf = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
    members = {m.name.split("/")[-1].removesuffix(".csv"): m
               for m in tf.getmembers() if m.name.endswith(".csv")}
    for det in DETS:
        m = members.get(det)
        if m is None:
            continue
        text = tf.extractfile(m).read().decode("utf-8", errors="replace")
        best = {}
        rdr = csv.DictReader(io.StringIO(text), delimiter=";")
        # header variants: 'Datum (Ortszeit)'/'Stunde des Tages (Ortszeit)'
        # (2023/24) vs plain 'Datum'/'Stunde' (some 2025 months)
        dcol = next(c for c in rdr.fieldnames if c.startswith("Datum"))
        hcol = next(c for c in rdr.fieldnames if c.startswith("Stunde"))
        for r in rdr:
            key = (r[dcol], r[hcol])
            if key not in best or (best[key]["qkfz"] in ("NaN", "", None)
                                   and r["qkfz"] not in ("NaN", "")):
                best[key] = r
        for (tag, stunde), r in sorted(best.items()):
            if r["qkfz"] in ("NaN", ""):
                continue
            # quality field: 2023/24 schema has 'Vollständigkeit' (0-100),
            # the 2025 schema 'Datapoints_Rel' (0-1) -> normalise to 0-1
            if "Datapoints_Rel" in r:
                rel = r["Datapoints_Rel"]
            else:
                v = r.get("Vollständigkeit", "")
                try:
                    rel = f"{float(v) / 100:.4f}"
                except ValueError:
                    rel = ""
            rows.append([det, tag, stunde, r["qkfz"], r["qpkw"], r["qlkw"],
                         r["vkfz"], rel, r.get("hist_cor", "")])
    return rows


def main() -> None:
    force = "--force" in sys.argv
    if OUT.exists() and not force:
        print(f"{OUT} exists - nothing to do (--force to rebuild)")
        return
    RAW.mkdir(parents=True, exist_ok=True)
    for year, month in MONTHS:
        cache = RAW / f"{year}_{month:02d}.csv"
        if cache.exists() and not force:
            continue
        print(f"fetch neue-QS {year}-{month:02d} ...", flush=True)
        rows = fetch_month(year, month)
        with cache.open("w", newline="") as fh:
            csv.writer(fh, delimiter=";").writerows(rows)
        print(f"  {len(rows)} rows", flush=True)
        time.sleep(PAUSE)
    with OUT.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(FIELDS)
        for f in sorted(RAW.glob("*.csv")):
            body = f.read_text().strip()
            if body:
                fh.write(body + "\n")
    print(f"wrote {OUT} ({sum(1 for _ in OUT.open()) - 1} rows)")


if __name__ == "__main__":
    main()
