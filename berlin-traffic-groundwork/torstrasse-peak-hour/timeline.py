#!/usr/bin/env python3
"""Full-sample hourly timeline illustration: the four lane detectors, the two
directional Messquerschnitte and the derived cross-section, 2015 -> 2025,
with data provenance (blob alte-QS vs FROST SensorThings) and a mechanical
monthly quality classification.

Inputs (all cached by the fetchers):
  data/torstrasse_mq_hr.csv    blob MQ hourly, 2015-2024, qualitaet-gated
  data/torstrasse_det_hr.csv   blob lane hourly, 2015-2024 (fetch_lanes.py)
  data/qa/TE18*_q_hr.csv       FROST hourly counts, 2022-2025 (fetch_frost_qa.py)

Output: figures/09_timeline_full_sample.png + a printed per-series summary.

Merge rule (same as the main pipeline): the QA-gated blob value wins; FROST
fills only hours the blob never covered. Provenance is tracked per hour.

Quality classes per (series, month), mechanical:
  none      coverage < 5 %
  sparse    coverage < 50 %
  degraded  zeros > 2 % of valid hours, spikes > 0.5 % (lane > 800 /
            MQ > 1,300 / cross > 2,600 Kfz/h), or daytime median < 70 % of
            the series' own 2018-2020 same-calendar-month envelope
  clean     everything else
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
FIG = HERE / "figures"
QUALITY_MIN = 0.75
DET_MAP = {100101010030479: ("TE180", "hf1"), 100101010030580: ("TE180", "hf2"),
           100101010030681: ("TE181", "hf1"), 100101010030782: ("TE181", "hf2")}
SPIKE = {"hf1": 1200, "hf2": 1200, "mq": 1300, "cross": 2600}
# lane threshold 1,200: clean-era lane maxima are ~1,050-1,150 (HF2, blob
# 2018-20) while the artefact regime starts ~1,300; 800 would flag the busy
# lane's legitimate rush-hour p99 (~850)
COL_BLOB, COL_FROST = "#1f4e79", "#e07b39"
QCOL = {"clean": "#d9ead3", "degraded": "#ffe9a8", "sparse": "#e8e8e8",
        "none": "white"}


def blob_series() -> dict:
    out = {}
    mq = pd.read_csv(HERE / "data" / "torstrasse_mq_hr.csv", sep=";")
    mq["t"] = (pd.to_datetime(mq["tag"], format="%d.%m.%Y")
               + pd.to_timedelta(mq["stunde"], unit="h"))
    mq = mq[(mq["qualitaet"] >= QUALITY_MIN) & mq["q_kfz_mq_hr"].notna()]
    mq = mq.sort_values("qualitaet").drop_duplicates(["mq_name", "t"],
                                                     keep="last")
    for name, g in mq.groupby("mq_name"):
        out[(name, "mq")] = pd.Series(g["q_kfz_mq_hr"].values,
                                      index=g["t"]).sort_index()
    det = pd.read_csv(HERE / "data" / "torstrasse_det_hr.csv", sep=";")
    det["t"] = (pd.to_datetime(det["tag"], format="%d.%m.%Y")
                + pd.to_timedelta(det["stunde"], unit="h"))
    det = det[(det["qualitaet"] >= QUALITY_MIN) & det["q_kfz_det_hr"].notna()]
    det = det.sort_values("qualitaet").drop_duplicates(["detid_15", "t"],
                                                       keep="last")
    for did, g in det.groupby("detid_15"):
        key = DET_MAP.get(int(did))
        if key:
            out[key] = pd.Series(g["q_kfz_det_hr"].values,
                                 index=g["t"]).sort_index()
    return out


def frost_series() -> dict:
    out = {}
    for t in ("TE180", "TE181"):
        for l in ("mq", "hf1", "hf2"):
            f = HERE / "data" / "qa" / f"{t}_{l}_q_hr.csv"
            if not f.exists():
                continue
            df = pd.read_csv(f, sep=";")
            ts = (pd.to_datetime(df["t_utc"], utc=True)
                  .dt.tz_convert("Europe/Berlin").dt.tz_localize(None))
            s = pd.Series(pd.to_numeric(df["result"], errors="coerce").values,
                          index=ts).dropna()
            out[(t, l)] = s[~s.index.duplicated()].sort_index()
    return out


def merge(blob: pd.Series, frost: pd.Series):
    """Blob wins; FROST fills only blob-uncovered hours. Returns (values,
    provenance) with provenance 0 = blob, 1 = FROST."""
    fr = frost[~frost.index.isin(blob.index)] if len(blob) else frost
    vals = pd.concat([blob, fr]).sort_index()
    prov = pd.concat([pd.Series(0, index=blob.index),
                      pd.Series(1, index=fr.index)]).sort_index()
    return vals, prov


def weekly_daytime(s: pd.Series, how="median") -> pd.Series:
    d = s[(s.index.hour >= 8) & (s.index.hour <= 18) & (s.index.dayofweek < 5)]
    return getattr(d.resample("W-MON"), how)()


def month_quality(vals: pd.Series, level: str, envelope: pd.Series) -> pd.Series:
    grid_hours = vals.index.to_period("M")
    per = vals.groupby(grid_hours)
    months = pd.period_range("2015-01", "2025-07", freq="M")
    cov = (per.size() / (months.days_in_month * 24).to_numpy()[
        months.searchsorted(per.size().index)]).reindex(months)
    zero = per.apply(lambda x: (x == 0).mean()).reindex(months)
    spike = per.apply(lambda x: (x > SPIKE[level]).mean()).reindex(months)
    day = vals[(vals.index.hour >= 8) & (vals.index.hour <= 18)]
    med = day.groupby(day.index.to_period("M")).median().reindex(months)
    env = envelope.reindex([m.month for m in months])
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = (med.values / env.values if envelope.notna().any()
                 else np.ones(len(months)))
        ratio = np.where(np.isfinite(ratio), ratio, np.nan)
    cls = []
    for c, z, sp, r in zip(cov.fillna(0), zero.fillna(0), spike.fillna(0),
                           ratio):
        if c < 0.05:
            cls.append("none")
        elif c < 0.50:
            cls.append("sparse")
        elif z > 0.02 or sp > 0.005 or (not np.isnan(r) and r < 0.70):
            cls.append("degraded")
        else:
            cls.append("clean")
    return pd.Series(cls, index=months)


def main() -> None:
    blob, frost = blob_series(), frost_series()
    panels = [("TE180", "hf1", "TE180 West — HF1 (right lane)"),
              ("TE180", "hf2", "TE180 West — HF2 (2nd lane)"),
              ("TE180", "mq", "TE180 West — Messquerschnitt (2 lanes)"),
              ("TE181", "hf1", "TE181 Ost — HF1 (right lane)"),
              ("TE181", "hf2", "TE181 Ost — HF2 (2nd lane)"),
              ("TE181", "mq", "TE181 Ost — Messquerschnitt (2 lanes)"),
              (None, "cross", "Cross-section West+Ost (RASt reference; "
                              "hours where BOTH MQs are valid)")]

    merged = {}
    for t in ("TE180", "TE181"):
        for l in ("mq", "hf1", "hf2"):
            b = blob.get((t, l), pd.Series(dtype=float))
            f = frost.get((t, l), pd.Series(dtype=float))
            merged[(t, l)] = merge(b, f)
    # derived cross-section
    w, pw = merged[("TE180", "mq")]
    o, po = merged[("TE181", "mq")]
    cross = (w + o).dropna()
    pcross = ((pw.reindex(cross.index).fillna(1)
               + po.reindex(cross.index).fillna(1)) > 0).astype(int)
    merged[(None, "cross")] = (cross, pcross)

    fig, axes = plt.subplots(len(panels), 1, figsize=(14, 14.5), sharex=True)
    print(f"{'series':44s} {'hours':>7s} {'blob':>7s} {'frost':>6s} "
          f"{'first':>10s} {'last':>10s}  clean/degr/sparse months")
    for ax, (t, l, title) in zip(axes, panels):
        vals, prov = merged[(t, l)]
        env_src = vals[(prov == 0).values] if len(vals) else vals
        env_day = env_src[(env_src.index.year >= 2018)
                          & (env_src.index.year <= 2020)
                          & (env_src.index.hour >= 8)
                          & (env_src.index.hour <= 18)]
        envelope = env_day.groupby(env_day.index.month).median()
        q = month_quality(vals, l, envelope)
        for m, c in q.items():
            if c != "none":
                ax.axvspan(m.to_timestamp(), (m + 1).to_timestamp(),
                           color=QCOL[c], lw=0, zorder=0)
        wk = weekly_daytime(vals)
        wk_prov = weekly_daytime(prov, how="mean")
        frost_dom = wk_prov >= 0.5
        ax.plot(wk.index, wk.where(~frost_dom), color=COL_BLOB, lw=1.1,
                zorder=3)
        ax.plot(wk.index, wk.where(frost_dom), color=COL_FROST, lw=1.1,
                zorder=3)
        if envelope.notna().any():
            months_x = pd.date_range("2015-01-01", "2025-08-01", freq="MS")
            ax.plot(months_x, envelope.reindex(months_x.month).values,
                    color="green", ls=":", lw=0.8, zorder=2)
        ax.set_ylabel("Kfz/h", fontsize=8)
        ax.set_ylim(0, max(200, np.nanpercentile(wk.values, 99.5) * 1.25)
                    if wk.notna().any() else 200)
        ax.set_title(title, fontsize=9.5, loc="left")
        ax.tick_params(labelsize=8)
        n_b, n_f = int((prov == 0).sum()), int((prov == 1).sum())
        qc = q.value_counts()
        print(f"{title[:44]:44s} {len(vals):7d} {n_b:7d} {n_f:6d} "
              f"{str(vals.index.min())[:10]:>10s} {str(vals.index.max())[:10]:>10s}  "
              f"{qc.get('clean', 0)}/{qc.get('degraded', 0)}/{qc.get('sparse', 0)}")

    handles = [
        plt.Line2D([], [], color=COL_BLOB, lw=2,
                   label="blob archive (alte QS, quality-gated)"),
        plt.Line2D([], [], color=COL_FROST, lw=2,
                   label="FROST SensorThings (un-QA'd)"),
        plt.Line2D([], [], color="green", ls=":", lw=1.5,
                   label="2018-20 envelope (same-month median)"),
        Patch(color=QCOL["clean"], label="month: clean"),
        Patch(color=QCOL["degraded"],
              label="month: suspect (zeros / spikes / < 70 % of envelope — "
                    "sensor trouble OR real decline)"),
        Patch(color=QCOL["sparse"], label="month: sparse (< 50 % coverage)"),
        Patch(facecolor="white", edgecolor="grey",
              label="month: no data (< 5 %)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8.5,
               frameon=False)
    fig.suptitle("Torstrasse West+Ost, hourly Kfz — lanes, Messquerschnitte, "
                 "cross-section: full sample 2015 → 2025\n"
                 "line = weekly workday-daytime median (Mo-Fr 8-18 h) · "
                 "line colour = data source · background = mechanical monthly "
                 "quality class", y=0.995, fontsize=12)
    fig.tight_layout(rect=[0, 0.035, 1, 0.97])
    fig.savefig(FIG / "09_timeline_full_sample.png", dpi=150)
    print("wrote figures/09_timeline_full_sample.png")


if __name__ == "__main__":
    main()
