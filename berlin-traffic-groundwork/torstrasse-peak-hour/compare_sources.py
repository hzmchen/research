#!/usr/bin/env python3
"""Side-by-side comparison of the three data sources for the Torstrasse
detectors — alte Qualitaetssicherung (blob), neue Qualitaetssicherung (blob)
and FROST SensorThings — at hourly granularity, including each source's own
missingness / quality / validity semantics.

  fig 10  pairwise value-agreement scatters (direction level, valid hours)
  fig 11  hourly dot-density panels, year x direction, all sources overlaid
  fig 12  overlap + quality carpet (per direction): for every (day, hour),
          four bands - alte validity, neue validity, FROST plausibility,
          and cross-source agreement
  fig 13  day / week / month pattern profiles per source (common era 2023)

Validity semantics used:
  alte QS   row exists -> measured; qualitaet >= 0.75 -> valid (the archive's
            own gate); below -> flagged
  neue QS   row with non-NaN qkfz -> measured; Datapoints_Rel >= 0.75 ->
            valid; below -> flagged (NaN-placeholder rows dropped at fetch)
  FROST     observation exists -> measured; flagged if implausible
            (q == 0 or q > 1,300 MQ / 1,200 lane - no native QA field)

Pure function of the cached CSVs (no network).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
FIG = HERE / "figures"
TOL_ABS, TOL_REL = 10, 0.05      # agreement tolerance
YEARS = [2022, 2023, 2024, 2025]
DET_NAMES = {"TEU00180_Det0": ("TE180", "hf1"), "TEU00180_Det1": ("TE180", "hf2"),
             "TEU00181_Det0": ("TE181", "hf1"), "TEU00181_Det1": ("TE181", "hf2")}
DIR_LABEL = {"TE180": "TE180 West", "TE181": "TE181 Ost"}
SRC_COLOR = {"alte": "#1f4e79", "neue": "#1b7837", "frost": "#e07b39"}


def load_alte_mq():
    df = pd.read_csv(HERE / "data" / "torstrasse_mq_hr.csv", sep=";")
    df["t"] = (pd.to_datetime(df["tag"], format="%d.%m.%Y")
               + pd.to_timedelta(df["stunde"], unit="h"))
    df = df.dropna(subset=["q_kfz_mq_hr"]).sort_values("qualitaet") \
           .drop_duplicates(["mq_name", "t"], keep="last")
    out = {}
    for name, g in df.groupby("mq_name"):
        out[name] = pd.DataFrame(
            {"q": g["q_kfz_mq_hr"].values,
             "ok": (g["qualitaet"] >= 0.75).values},
            index=g["t"]).sort_index()
    return out


def load_neue_mq():
    df = pd.read_csv(HERE / "data" / "torstrasse_neuqa_hr.csv", sep=";")
    df["t"] = (pd.to_datetime(df["tag"], format="%Y-%m-%d")
               + pd.to_timedelta(df["stunde"], unit="h"))
    df["thing"] = df["det"].map({k: v[0] for k, v in DET_NAMES.items()})
    df["rel"] = pd.to_numeric(df["datapoints_rel"], errors="coerce")
    df["qkfz"] = pd.to_numeric(df["qkfz"], errors="coerce")
    out = {}
    for thing, g in df.groupby("thing"):
        lanes = g.pivot_table(index="t", columns="det", values="qkfz")
        rel = g.pivot_table(index="t", columns="det", values="rel")
        if lanes.shape[1] < 2:
            continue
        q = lanes.sum(axis=1, min_count=2)          # MQ needs both lanes
        ok = rel.min(axis=1) >= 0.75
        out[thing] = pd.DataFrame({"q": q, "ok": ok.values if hasattr(ok, "values") else ok}).dropna(subset=["q"])
    return out


def load_frost_mq():
    out = {}
    for thing in ("TE180", "TE181"):
        f = HERE / "data" / "qa" / f"{thing}_mq_q_hr.csv"
        df = pd.read_csv(f, sep=";")
        ts = (pd.to_datetime(df["t_utc"], utc=True)
              .dt.tz_convert("Europe/Berlin").dt.tz_localize(None))
        q = pd.to_numeric(df["result"], errors="coerce")
        d = pd.DataFrame({"q": q.values}, index=ts).dropna()
        d = d[~d.index.duplicated()].sort_index()
        d["ok"] = (d["q"] > 0) & (d["q"] <= 1300)
        out[thing] = d
    return out


def fig10_scatter(alte, neue, frost):
    pairs = [("alte", "neue"), ("alte", "frost"), ("neue", "frost")]
    src = {"alte": alte, "neue": neue, "frost": frost}
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.5), sharex=True, sharey=True)
    stats = {}
    for i, thing in enumerate(("TE180", "TE181")):
        for j, (a, b) in enumerate(pairs):
            ax = axes[i, j]
            A = src[a].get(thing); B = src[b].get(thing)
            if A is None or B is None:
                ax.set_axis_off(); continue
            Av = A[A["ok"].fillna(False).astype(bool)]
            Bv = B[B["ok"].fillna(False).astype(bool)]
            common = Av.index.intersection(Bv.index)
            x, y = Av.loc[common, "q"], Bv.loc[common, "q"]
            ax.scatter(x, y, s=2, alpha=0.05, color="#30506e", rasterized=True)
            ax.plot([0, 1500], [0, 1500], color="crimson", lw=0.8)
            d = (y - x)
            agree = (d.abs() <= np.maximum(TOL_ABS, TOL_REL * x)).mean() \
                if len(common) else np.nan
            stats[f"{thing} {a}-vs-{b}"] = dict(
                n=int(len(common)), agree=round(float(agree), 3),
                med_diff=float(d.median()) if len(common) else None)
            ax.set_title(f"{DIR_LABEL[thing]}: {a} vs {b}\n"
                         f"n={len(common):,}, within tol: {agree:.0%}, "
                         f"median diff {d.median():+.0f}", fontsize=9)
            if i == 1:
                ax.set_xlabel(f"{a} [Kfz/h]", fontsize=8)
            ax.set_ylabel(f"{b} [Kfz/h]", fontsize=8)
            ax.set_xlim(0, 1500); ax.set_ylim(0, 1500)
    fig.suptitle("Pairwise source agreement — directional MQ, hourly, "
                 "valid hours only (tolerance: max(10 Kfz, 5 %))", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "10_source_scatter.png", dpi=150)
    plt.close(fig)
    return stats


def fig11_dots(alte, neue, frost):
    fig, axes = plt.subplots(len(YEARS), 2, figsize=(14, 11), sharex=True,
                             sharey="col")
    for j, thing in enumerate(("TE180", "TE181")):
        for i, year in enumerate(YEARS):
            ax = axes[i, j]
            for name, src in (("alte", alte), ("neue", neue),
                              ("frost", frost)):
                d = src.get(thing)
                if d is None:
                    continue
                g = d[(d.index.year == year)]
                if g.empty:
                    continue
                doy = g.index.dayofyear + g.index.hour / 24
                ax.scatter(doy, g["q"], s=1.2, alpha=0.06,
                           color=SRC_COLOR[name], rasterized=True)
                bad = g[~g["ok"].fillna(False).astype(bool)]
                ax.scatter(bad.index.dayofyear + bad.index.hour / 24,
                           bad["q"], s=1.2, alpha=0.25, color="red",
                           rasterized=True)
            ax.set_ylim(0, 1100)
            ax.text(0.005, 0.92, str(year), transform=ax.transAxes,
                    fontsize=10, weight="bold")
            if i == 0:
                ax.set_title(f"{DIR_LABEL[thing]} — MQ, every hour as a dot",
                             fontsize=10)
            if i == len(YEARS) - 1:
                ax.set_xlabel("day of year")
            if j == 0:
                ax.set_ylabel("Kfz/h", fontsize=8)
    handles = [Line2D([], [], marker="o", ls="", color=SRC_COLOR[s],
                      label={"alte": "alte QS (blob)", "neue": "neue QS (blob)",
                             "frost": "FROST"}[s]) for s in SRC_COLOR]
    handles.append(Line2D([], [], marker="o", ls="", color="red",
                          label="flagged by that source's validity rule"))
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=9,
               frameon=False)
    fig.suptitle("All sources, all hours, side by side — high-transparency "
                 "dots; systematic offsets show as colour separation",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    fig.savefig(FIG / "11_source_dots.png", dpi=140)
    plt.close(fig)


def fig12_carpet(alte, neue, frost):
    BANDS = ["alte", "neue", "frost", "agree"]
    COLORS = {
        ("alte", "missing"): (1, 1, 1), ("alte", "flag"): (0.66, 0.8, 0.94),
        ("alte", "valid"): (0.12, 0.31, 0.55),
        ("neue", "missing"): (1, 1, 1), ("neue", "flag"): (0.72, 0.89, 0.72),
        ("neue", "valid"): (0.11, 0.46, 0.21),
        ("frost", "missing"): (1, 1, 1), ("frost", "flag"): (0.82, 0.12, 0.12),
        ("frost", "valid"): (0.94, 0.62, 0.27),
        ("agree", "none"): (1, 1, 1), ("agree", "single"): (0.86, 0.86, 0.86),
        ("agree", "agree"): (0.22, 0.62, 0.26),
        ("agree", "disagree"): (0.85, 0.15, 0.15),
    }
    GAP, BH = 6, 24
    for thing in ("TE180", "TE181"):
        blocks = []
        for year in YEARS:
            ndays = 366 if year % 4 == 0 else 365
            img = np.ones((BH * 4 + GAP, 366, 3))
            grid = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00",
                                 freq="1h")
            frames = {"alte": alte.get(thing), "neue": neue.get(thing),
                      "frost": frost.get(thing)}
            vals, oks = {}, {}
            for k, d in frames.items():
                if d is None:
                    d = pd.DataFrame(columns=["q", "ok"])
                vals[k] = d["q"].reindex(grid)
                oks[k] = d["ok"].reindex(grid)
            for b, k in enumerate(("alte", "neue", "frost")):
                v, ok = vals[k], oks[k]
                state = np.where(v.isna(), 0, np.where(ok.fillna(False), 2, 1))
                lut = np.array([COLORS[(k, "missing")], COLORS[(k, "flag")],
                                COLORS[(k, "valid")]])
                rgb = lut[state].reshape(ndays, 24, 3).transpose(1, 0, 2)
                img[b * BH:(b + 1) * BH, :ndays] = rgb
            # agreement band: among VALID values only
            V = pd.DataFrame({k: vals[k].where(oks[k].fillna(False))
                              for k in ("alte", "neue", "frost")})
            n = V.notna().sum(axis=1).values
            mx, mn, base = (V.max(axis=1).values, V.min(axis=1).values,
                            V.mean(axis=1).values)
            agree = (mx - mn) <= np.maximum(TOL_ABS, TOL_REL * base)
            state = np.where(n == 0, 0, np.where(n == 1, 1,
                             np.where(agree, 2, 3)))
            lut = np.array([COLORS[("agree", "none")],
                            COLORS[("agree", "single")],
                            COLORS[("agree", "agree")],
                            COLORS[("agree", "disagree")]])
            rgb = lut[state].reshape(ndays, 24, 3).transpose(1, 0, 2)
            img[3 * BH:4 * BH, :ndays] = rgb
            blocks.append((year, img))

        H = sum(b.shape[0] for _, b in blocks)
        fig, ax = plt.subplots(figsize=(15, H / 38))
        canvas = np.ones((H, 366, 3))
        y0 = 0
        for year, img in blocks:
            canvas[y0:y0 + img.shape[0]] = img
            for b, lab in enumerate(BANDS):
                ax.text(-4, y0 + b * BH + BH / 2, lab, ha="right",
                        va="center", fontsize=7)
            ax.text(-22, y0 + 2 * BH, str(year), ha="right", va="center",
                    fontsize=11, weight="bold", rotation=90)
            y0 += img.shape[0]
        ax.imshow(canvas, aspect="auto", interpolation="nearest")
        ax.set_xlim(-30, 366)
        ax.set_xlabel("day of year (within each band: hour 0 top → 23 bottom)")
        ax.set_yticks([])
        ax.set_title(f"{DIR_LABEL[thing]} — hourly missingness / validity per "
                     "source + cross-source agreement, 2022-2025")
        handles = [
            Patch(color=COLORS[("alte", "valid")], label="alte: valid (q ≥ 0.75)"),
            Patch(color=COLORS[("alte", "flag")], label="alte: flagged"),
            Patch(color=COLORS[("neue", "valid")], label="neue: valid (Rel ≥ 0.75)"),
            Patch(color=COLORS[("neue", "flag")], label="neue: flagged"),
            Patch(color=COLORS[("frost", "valid")], label="FROST: plausible"),
            Patch(color=COLORS[("frost", "flag")], label="FROST: implausible (0 / spike)"),
            Patch(color=COLORS[("agree", "agree")], label="≥2 valid sources agree"),
            Patch(color=COLORS[("agree", "disagree")], label="≥2 valid sources DISAGREE"),
            Patch(color=COLORS[("agree", "single")], label="only one valid source"),
            Patch(facecolor="white", edgecolor="grey", label="missing"),
        ]
        ax.legend(handles=handles, loc="upper center",
                  bbox_to_anchor=(0.5, -0.06), ncol=5, fontsize=7.5,
                  frameon=False)
        fig.tight_layout()
        fig.savefig(FIG / f"12_overlap_carpet_{thing.lower()}.png", dpi=150,
                    bbox_inches="tight")
        plt.close(fig)


def fig13_patterns(alte, neue, frost):
    era = slice("2023-01-01", "2023-12-31")
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    specs = [("hour of day", lambda ix: ix.hour, range(24)),
             ("day of week", lambda ix: ix.dayofweek, range(7)),
             ("month (2023)", lambda ix: ix.month, range(1, 13))]
    for j, thing in enumerate(("TE180", "TE181")):
        for i, (lab, keyf, dom) in enumerate(specs):
            ax = axes[i, j]
            for name, src in (("alte", alte), ("neue", neue),
                              ("frost", frost)):
                d = src.get(thing)
                if d is None:
                    continue
                g = d.loc[era]
                g = g[g["ok"].fillna(False).astype(bool)]
                if g.empty:
                    continue
                prof = g["q"].groupby(keyf(g.index)).mean().reindex(dom)
                ax.plot(prof.index, prof.values, color=SRC_COLOR[name],
                        lw=1.6, label=name)
            ax.set_xlabel(lab, fontsize=8)
            ax.set_ylabel("mean Kfz/h", fontsize=8)
            if i == 0:
                ax.set_title(f"{DIR_LABEL[thing]} — common era 2023 "
                             "(valid hours per source)", fontsize=10)
            if i == 0 and j == 0:
                ax.legend(fontsize=8)
            if lab == "day of week":
                ax.set_xticks(range(7),
                              ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"])
    fig.suptitle("Do the sources agree on the PATTERNS even where levels "
                 "differ? — diurnal / weekly / seasonal profiles", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "13_source_patterns.png", dpi=150)
    plt.close(fig)


def validity_table(alte, neue, frost):
    print("\n== validity over the common era 2023-01 .. 2024-12 "
          "(share of grid hours)")
    grid = pd.date_range("2023-01-01", "2024-12-31 23:00", freq="1h")
    out = {}
    for name, src in (("alte", alte), ("neue", neue), ("frost", frost)):
        for thing in ("TE180", "TE181"):
            d = src.get(thing)
            if d is None:
                continue
            v = d.reindex(grid)
            missing = v["q"].isna().mean()
            valid = (v["ok"].fillna(False) & v["q"].notna()).mean()
            flagged = 1 - missing - valid
            out[f"{name} {thing}"] = (valid, flagged, missing)
            print(f"  {name:5s} {thing}: valid {valid:6.1%}  "
                  f"flagged {flagged:6.1%}  missing {missing:6.1%}")
    return out


def main():
    alte, neue, frost = load_alte_mq(), load_neue_mq(), load_frost_mq()
    stats = fig10_scatter(alte, neue, frost)
    print("== pairwise agreement (valid hours, direction level)")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    fig11_dots(alte, neue, frost)
    fig12_carpet(alte, neue, frost)
    fig13_patterns(alte, neue, frost)
    validity_table(alte, neue, frost)
    print("wrote figures/10-13")


if __name__ == "__main__":
    main()
