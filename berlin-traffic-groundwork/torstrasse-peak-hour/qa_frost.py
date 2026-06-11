#!/usr/bin/env python3
"""QA of the TEU FROST (SensorThings) data for TE180/TE181 — single lanes and
cross-section (Messquerschnitt), hourly and 5-min. Pure function of the caches
written by fetch_frost_qa.py (+ the QA'd blob extract for cross-checking).

Produces figures/qa1..qa4 and data/qa_summary.json, and prints the stats the
verdict tables in frost-qa.md are built from.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
QA = HERE / "data" / "qa"
FIG = HERE / "figures"

THINGS = ("TE180", "TE181")
LEVELS = ("mq", "hf1", "hf2")
WINDOW_LABELS = {2022: "2022-06 (early FROST)", 2023: "2023-03 (healthy)",
                 2024: "2024-02 (TE180 dying)", 2025: "2025-03 (single-lane)"}


def load_stream(thing, level, var, agg) -> pd.Series:
    f = QA / f"{thing}_{level}_{var}_{agg}.csv"
    if not f.exists():
        return pd.Series(dtype=float)
    df = pd.read_csv(f, sep=";")
    if df.empty:
        return pd.Series(dtype=float)
    t = (pd.to_datetime(df["t_utc"], utc=True)
           .dt.tz_convert("Europe/Berlin").dt.tz_localize(None))
    s = pd.Series(pd.to_numeric(df["result"], errors="coerce").values, index=t)
    return s[~s.index.duplicated(keep="first")].sort_index()


def monthly(s: pd.Series, how: str) -> pd.Series:
    """Monthly stat over daytime hours (08-18 local)."""
    d = s[(s.index.hour >= 8) & (s.index.hour <= 18)]
    g = d.groupby(d.index.to_period("M"))
    return g.median() if how == "median" else g.apply(lambda x: x.notna().mean())


def month_coverage(s: pd.Series, agg="hr") -> pd.Series:
    """Valid share vs the full month grid."""
    if s.empty:
        return pd.Series(dtype=float)
    per = s.dropna().groupby(s.dropna().index.to_period("M")).size()
    full = per.index.days_in_month * (24 if agg == "hr" else 288)
    return per / full


def main() -> None:
    hr_q = {(t, l): load_stream(t, l, "q", "hr") for t in THINGS for l in LEVELS}
    hr_v = {(t, "mq"): load_stream(t, "mq", "v", "hr") for t in THINGS}
    hr_v[("TE181", "hf1")] = load_stream("TE181", "hf1", "v", "hr")
    hr_v[("TE181", "hf2")] = load_stream("TE181", "hf2", "v", "hr")
    m5_q = {(t, l): load_stream(t, l, "q", "5min") for t in THINGS for l in LEVELS}
    m5_v = {(t, "mq"): load_stream(t, "mq", "v", "5min") for t in THINGS}

    out = {}

    # ---- inventory --------------------------------------------------------
    print("== inventory (hourly count streams)")
    inv = {}
    for (t, l), s in hr_q.items():
        v = s.dropna()
        inv[f"{t}_{l}"] = dict(
            first=str(v.index.min())[:16] if len(v) else None,
            last=str(v.index.max())[:16] if len(v) else None,
            valid_hours=int(len(v)))
        print(f"  {t} {l:3s}: {inv[f'{t}_{l}']}")
    out["inventory_hr"] = inv

    # ---- fig qa1: monthly coverage heatmaps, hourly + 5-min ----------------
    months = pd.period_range("2022-01", "2025-07", freq="M")
    rows, labels = [], []
    for t in THINGS:
        for l in LEVELS:
            rows.append(month_coverage(hr_q[(t, l)]).reindex(months).values)
            labels.append(f"{t} {l.upper()}")
    panels = [("hourly KFZ count streams (full pull)", rows, labels)]
    cnt_f = QA / "counts_5min_monthly.csv"
    if cnt_f.exists():
        cnt = pd.read_csv(cnt_f, sep=";")
        cnt["month"] = pd.PeriodIndex(cnt["month"], freq="M")
        cnt["days"] = cnt["month"].dt.days_in_month
        cnt["share"] = cnt["n_valid"] / (cnt["days"] * 288)
        rows5, labels5 = [], []
        for t in THINGS:
            for l in LEVELS:
                sub = cnt[(cnt["thing"] == t) & (cnt["level"] == l)] \
                    .set_index("month")["share"].reindex(months)
                rows5.append(sub.values)
                labels5.append(f"{t} {l.upper()}")
        panels.append(("5-min KFZ count streams ($count scan, full history)",
                       rows5, labels5))
        out["coverage_5min_monthly"] = {
            f"{r.thing}_{r.level}_{r.month}": round(float(r.share), 3)
            for r in cnt.itertuples()}
    fig, axes = plt.subplots(len(panels), 1, figsize=(12, 3.4 * len(panels)))
    axes = np.atleast_1d(axes)
    for ax, (title, rws, labs) in zip(axes, panels):
        im = ax.imshow(np.array(rws, dtype=float), aspect="auto",
                       cmap="RdYlGn", vmin=0, vmax=1, interpolation="nearest")
        ax.set_yticks(range(len(labs)), labs, fontsize=8)
        ticks = [i for i, p in enumerate(months) if p.month in (1, 7)]
        ax.set_xticks(ticks, [str(months[i])[:7] for i in ticks], fontsize=8)
        fig.colorbar(im, ax=ax, label="valid share")
        ax.set_title(f"FROST {title} — no QA gate; presence ≠ validity!",
                     fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "qa1_coverage.png", dpi=150)
    plt.close(fig)

    # ---- healthy envelope from the QA'd blob (2018-2020) ------------------
    blob = pd.read_csv(HERE / "data" / "torstrasse_mq_hr.csv", sep=";")
    blob["date"] = pd.to_datetime(blob["tag"], format="%d.%m.%Y")
    blob = blob[(blob["qualitaet"] >= 0.75) & blob["q_kfz_mq_hr"].notna()]
    ref = blob[blob["date"].dt.year.isin([2018, 2019, 2020])]
    ref = ref[(ref["stunde"] >= 8) & (ref["stunde"] <= 18)]
    envelope = ref.groupby(["mq_name", ref["date"].dt.month])["q_kfz_mq_hr"] \
                  .median()

    # ---- fig qa2: health timeline ------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, t in zip(axes, THINGS):
        for l, c in zip(LEVELS, ("k", "#1f77b4", "#d62728")):
            med = monthly(hr_q[(t, l)], "median").reindex(months)
            ax.plot(months.to_timestamp(), med.values, color=c, lw=1.6,
                    label=f"{l.upper()} count median (08-18h)")
        env = envelope.loc[t].reindex([p.month for p in months])
        ax.plot(months.to_timestamp(), env.values, color="green", ls=":",
                lw=1.5, label="healthy envelope (blob 2018-20, QA'd)")
        vmed = monthly(hr_v[(t, "mq")], "median").reindex(months)
        ax2 = ax.twinx()
        ax2.plot(months.to_timestamp(), vmed.values, color="purple", lw=1,
                 alpha=0.6)
        ax2.set_ylabel("MQ speed median [km/h]", color="purple", fontsize=8)
        ax2.set_ylim(0, 60)
        ax2.axhline(20, color="purple", lw=0.5, ls="--", alpha=0.5)
        ax.set_title(f"{t} — monthly daytime medians, FROST hourly")
        ax.set_ylabel("Kfz/h")
        ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "qa2_health_timeline.png", dpi=150)
    plt.close(fig)

    # ---- lane backing of the MQ rollup -------------------------------------
    print("\n== lane backing of MQ hourly values")
    backing = {}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, t in zip(axes, THINGS):
        df = pd.DataFrame({l: hr_q[(t, l)] for l in LEVELS}).dropna(
            subset=["mq"])
        both = df["hf1"].notna() & df["hf2"].notna()
        one = df["hf1"].notna() ^ df["hf2"].notna()
        none = ~(df["hf1"].notna() | df["hf2"].notna())
        sum_ok = (df.loc[both, "mq"]
                  - df.loc[both, "hf1"] - df.loc[both, "hf2"]).abs() <= 2
        single = df.loc[one, ["hf1", "hf2"]].sum(axis=1, min_count=1)
        single_ok = (df.loc[one, "mq"] - single).abs() <= 2
        backing[t] = dict(
            mq_hours=int(len(df)), both=int(both.sum()), one=int(one.sum()),
            none=int(none.sum()),
            sum_match_when_both=round(float(sum_ok.mean()), 4) if both.any() else None,
            mq_equals_single_lane=round(float(single_ok.mean()), 4) if one.any() else None)
        print(f"  {t}: {backing[t]}")
        share = pd.DataFrame({"2 lanes": both, "1 lane": one, "0 lanes": none})
        share = share.groupby(df.index.to_period("M")).mean().reindex(months)
        ax.stackplot(months.to_timestamp(), share["2 lanes"].fillna(0),
                     share["1 lane"].fillna(0), share["0 lanes"].fillna(0),
                     colors=["#2ca02c", "#ff7f0e", "#d62728"],
                     labels=["both lanes", "ONE lane only", "no lane stream"])
        ax.set_title(f"{t}: what backs an 'MQ' hour?")
        ax.set_ylim(0, 1)
        ax.legend(fontsize=8, loc="lower left")
    fig.suptitle("The Messquerschnitt rollup silently degrades to whatever "
                 "lanes still report", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "qa3_lane_backing.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    out["lane_backing"] = backing

    # ---- cross-check vs the QA'd blob archive ------------------------------
    print("\n== FROST hourly vs QA'd blob archive (matched hours)")
    xc = {}
    for t in THINGS:
        b = blob[blob["mq_name"] == t]
        bi = pd.Series(b["q_kfz_mq_hr"].values,
                       index=b["date"] + pd.to_timedelta(b["stunde"], unit="h"))
        f = hr_q[(t, "mq")].dropna()
        f = f[f.index < pd.Timestamp("2025-01-01")]
        common = f.index.intersection(bi.index)
        diff = (f.loc[common] - bi.loc[common])
        extra = f.index.difference(bi.index)
        xc[t] = dict(matched=int(len(common)),
                     agree_pm2=round(float((diff.abs() <= 2).mean()), 4),
                     frost_only_hours=int(len(extra)),
                     frost_only_daytime_median=float(
                         f.loc[extra][(f.loc[extra].index.hour >= 8)
                                      & (f.loc[extra].index.hour <= 18)]
                         .median()) if len(extra) else None)
        print(f"  {t}: {xc[t]}")
    out["blob_crosscheck"] = xc

    # ---- 5-min windows ------------------------------------------------------
    print("\n== 5-min windows: coverage / spikes / hourly-consistency")
    w5 = {}
    fig, ax = plt.subplots(figsize=(7.5, 6))
    colors = {2022: "#1f77b4", 2023: "#2ca02c", 2024: "#ff7f0e",
              2025: "#d62728"}
    for t in THINGS:
        for l in LEVELS:
            s = m5_q[(t, l)]
            if s.dropna().empty:
                continue
            for y, g in s.groupby(s.index.year):
                v = g.dropna()
                cov = len(v) / (7 * 288)
                spikes = int((v > (220 if l == "mq" else 110)).sum())
                hsum = v.resample("1h").agg(["sum", "count"])
                hsum = hsum[hsum["count"] == 12]["sum"]
                hr = hr_q[(t, l)].reindex(hsum.index)
                ok = (hsum - hr).abs() <= 2
                w5[f"{t}_{l}_{y}"] = dict(
                    coverage=round(cov, 3), spikes_gt_thresh=spikes,
                    full_hours=int(len(hsum)),
                    hourly_match_pm2=round(float(ok.mean()), 4)
                    if len(hsum) and hr.notna().any() else None)
                print(f"  {t} {l:3s} {y}: {w5[f'{t}_{l}_{y}']}")
                if l == "mq" and len(hsum):
                    ax.scatter(hsum.values, hr.values, s=8,
                               color=colors[y], alpha=0.5,
                               label=f"{t} {WINDOW_LABELS[y]}"
                               if f"{t}{y}" not in getattr(ax, "_seen", set())
                               else None)
                    seen = getattr(ax, "_seen", set())
                    seen.add(f"{t}{y}")
                    ax._seen = seen
    lim = 2000
    ax.plot([0, lim], [0, lim], color="grey", lw=0.7)
    ax.set_xlabel("sum of 12 × 5-min counts [Kfz/h]")
    ax.set_ylabel("hourly rollup value [Kfz/h]")
    ax.set_title("MQ: hourly rollup vs 5-min sum (sampled weeks)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "qa4_5min_consistency.png", dpi=150)
    plt.close(fig)
    out["windows_5min"] = w5

    (HERE / "data" / "qa_summary.json").write_text(json.dumps(out, indent=1))
    print("\nwrote data/qa_summary.json + figures/qa1-qa4")


if __name__ == "__main__":
    main()
