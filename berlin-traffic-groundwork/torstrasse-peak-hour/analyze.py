#!/usr/bin/env python3
"""Compute and illustrate every relevant definition of the 'peak hour'
(Spitzenstunde) metric for the Torstrasse cross-section TE180 (West) +
TE181 (Ost), 2015-2024 hourly Kfz data.

Definitions computed (see README for the regulatory mapping):
  D1  absolute peak hour of the year                       (q1)
  D2  30th-highest hour of the year   (HBS 2001 MSV)       (q30)
  D3  50th-highest hour of the year   (HBS 2015 MSV / qB)  (q50)
  D4  standardised weekday peak hour  (mean Mo-Fr non-holiday diurnal max)
  D5  median / distribution of daily peak hours
  D6  short-count proxy               (peak hour within 15-19h on Tue/Thu)
  D7  shortcut from daily volume      (10% / 11.5% of DTV)
  D8  RLS-19 hourly mean M_t          (0.055 x DTV; the non-peak trap)
  D9  heavier-direction peak hour     (RASt 06 fig. 77 basis)

Pure function of data/torstrasse_mq_hr.csv + data/dtv_editions.csv
(no network). Regenerates figures/01-08 and data/summary.json.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.easter import easter

HERE = Path(__file__).parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)

QUALITY_MIN = 0.75        # the archive's own validity convention
COVERAGE_GOOD = 0.90      # year usable for n-th-hour statistics
SCRUB_MAX = 1300          # Kfz/h per direction; clean-period envelope max ~1,230
CONTAMINATED_MAX = 0.005  # >0.5 % scrubbed directional hours -> year unusable
REF_YEAR = 2019           # last pre-COVID year, both directions ~98 %

BANDS = [(0, 400), (400, 1000), (800, 1800), (1600, 2600), (2600, 3400)]
BAND_LABELS = ["< 400", "400-1,000", "800-1,800", "1,600-2,600", "> 2,600"]

# The BMW Berlin-Marathon runs ALONG Torstrasse (Reinhardtstr. -> Torstr. ->
# Karl-Marx-Allee, ~km 7). On race Sundays the street is closed and the
# infrared detectors count RUNNERS (counts at 3-10 km/h "speeds", or with
# absurd 69-84 km/h misreads, after a near-zero closure hour) -> the whole
# day is invalid as vehicle data. 2020 was cancelled (COVID).
MARATHON_SUNDAYS = pd.to_datetime([
    "2015-09-27", "2016-09-25", "2017-09-24", "2018-09-16", "2019-09-29",
    "2021-09-26", "2022-09-25", "2023-09-24", "2024-09-29", "2025-09-21",
])


def berlin_holidays(year: int) -> set:
    e = easter(year)
    days = {
        pd.Timestamp(year, 1, 1), pd.Timestamp(year, 5, 1),
        pd.Timestamp(year, 10, 3), pd.Timestamp(year, 12, 25),
        pd.Timestamp(year, 12, 26),
        pd.Timestamp(e) - pd.Timedelta(days=2),   # Good Friday
        pd.Timestamp(e) + pd.Timedelta(days=1),   # Easter Monday
        pd.Timestamp(e) + pd.Timedelta(days=39),  # Ascension
        pd.Timestamp(e) + pd.Timedelta(days=50),  # Whit Monday
    }
    if year >= 2019:
        days.add(pd.Timestamp(year, 3, 8))        # Frauentag (Berlin)
    if year == 2017:
        days.add(pd.Timestamp(2017, 10, 31))      # Reformation 500 (one-off)
    if year == 2020:
        days.add(pd.Timestamp(2020, 5, 8))        # 75 J. Kriegsende (one-off)
    return days


def load() -> pd.DataFrame:
    df = pd.read_csv(HERE / "data" / "torstrasse_mq_hr.csv", sep=";")
    df["date"] = pd.to_datetime(df["tag"], format="%d.%m.%Y")
    key = ["mq_name", "date", "stunde"]
    # keys the QA'd archive has SEEN (incl. hours its QA rejected) — the
    # un-QA'd FROST tail must not resurrect QA-rejected hours
    seen = set(map(tuple, df[key].itertuples(index=False)))
    df = df[(df["qualitaet"] >= QUALITY_MIN) & df["q_kfz_mq_hr"].notna()]
    # collapse rare duplicate (mq,date,hour) rows, keep the better-quality one
    df = (df.sort_values("qualitaet")
            .drop_duplicates(key, keep="last"))
    # append the un-QA'd FROST tail (2024-11 ..; see fetch_frost.py) only for
    # (mq, date, hour) slots the blob archive never covered
    frost_csv = HERE / "data" / "torstrasse_frost_latest.csv"
    if frost_csv.exists():
        fr = pd.read_csv(frost_csv, sep=";")
        fr["date"] = pd.to_datetime(fr["tag"], format="%d.%m.%Y")
        fr = fr[fr["q_kfz_mq_hr"].notna()]
        fr = fr[~fr[key].apply(tuple, axis=1).isin(seen)]
        df = pd.concat([df, fr], ignore_index=True)
    kfz = df.pivot(index=["date", "stunde"], columns="mq_name",
                   values="q_kfz_mq_hr")
    lkw = df.pivot(index=["date", "stunde"], columns="mq_name",
                   values="q_lkw_mq_hr")
    wide = kfz.rename(columns={"TE180": "west", "TE181": "ost"}).reset_index()
    wide["lkw_cross"] = (lkw["TE180"] + lkw["TE181"]).values
    wide["year"] = wide["date"].dt.year
    # plausibility scrub: directional hours above the clean-period envelope
    # (max ~1,230 Kfz/h over 2018-2021) are sensor artefacts -> missing.
    # 2015-2017 TE181 additionally has an inflated BULK (median 15h-hour 2016:
    # 903 vs ~640 in clean years), which no scrub can repair -> those years are
    # flagged contaminated via the scrub share and excluded from year metrics.
    wide["cross_raw"] = wide["west"] + wide["ost"]      # pre-scrub, for fig 03
    scrub = {}
    marathon = wide["date"].isin(MARATHON_SUNDAYS)
    for c in ("west", "ost"):
        # artefact scrub (counted): spikes above the clean-period envelope,
        # and exact zeros — an hourly zero is physically impossible here
        # (2018-2020 floor: 3-5 Kfz/h, never 0) and marks a dead lane head
        # reporting zeros; see frost-qa.md "Do zeros mean 'no cars'?"
        bad = (wide[c] > SCRUB_MAX) | (wide[c] == 0)
        scrub[c] = wide.loc[bad].groupby("year")[c].size().to_dict()
        wide.loc[bad | marathon, c] = np.nan  # marathon Sundays: runners, not Kfz
    wide["cross"] = wide["west"] + wide["ost"]          # NaN unless both valid
    wide["dow"] = wide["date"].dt.dayofweek
    hols = set().union(*(berlin_holidays(y) for y in range(2015, 2025)))
    wide["workday"] = (wide["dow"] < 5) & ~wide["date"].isin(hols)
    wide.attrs["scrub"] = scrub
    return wide


def hours_in_year(y: int) -> int:
    return 8784 if y % 4 == 0 else 8760


def nth_hour(s: pd.Series, n: int) -> float:
    s = s.dropna().sort_values(ascending=False)
    return float(s.iloc[n - 1]) if len(s) >= n else np.nan


def year_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y, g in wide.groupby("year"):
        cross = g["cross"]
        cov = cross.notna().sum() / hours_in_year(y)
        # daily totals from complete days only
        day = g.dropna(subset=["cross"]).groupby("date").agg(
            q=("cross", "sum"), n=("cross", "size"), wd=("workday", "first"))
        full = day[day["n"] == 24]
        dtv = full["q"].mean() if len(full) >= 30 else np.nan
        dtvw = full.loc[full["wd"], "q"].mean() if full["wd"].sum() >= 20 else np.nan
        # standardised weekday peak: mean workday diurnal profile -> max
        prof = (g[g["workday"]].groupby("stunde")["cross"].mean())
        wk_peak, wk_peak_h = ((prof.max(), int(prof.idxmax()))
                              if prof.notna().sum() == 24 else (np.nan, -1))
        # daily peak distribution (complete days)
        dmax = (g.dropna(subset=["cross"]).groupby("date")
                  .agg(m=("cross", "max"), n=("cross", "size")))
        dmax = dmax[dmax["n"] == 24]["m"]
        # short-count proxy: Tue/Thu workdays, max hour within 15-19h
        sc = g[(g["workday"]) & (g["dow"].isin([1, 3]))
               & (g["stunde"].between(15, 18))]
        sc_days = sc.groupby("date").agg(m=("cross", "max"), n=("cross", "size"))
        sc_peak = sc_days[sc_days["n"] == 4]["m"].mean()
        # heavier-direction standardised peak
        dir_peaks = {}
        for c in ("west", "ost"):
            p = g[g["workday"]].groupby("stunde")[c].mean()
            dir_peaks[c] = (p.max(), int(p.idxmax())) if p.notna().sum() == 24 \
                else (np.nan, -1)
        heavier = max(dir_peaks["west"][0], dir_peaks["ost"][0])
        # Lkw share in the top-50 cross-section hours
        top = g.dropna(subset=["cross"]).nlargest(50, "cross")
        lkw_share = (top["lkw_cross"].sum() / top["cross"].sum()
                     if len(top) == 50 else np.nan)
        n30 = max(1, round(30 * cov))   # coverage-proportional rank
        n50 = max(1, round(50 * cov))
        scrub = wide.attrs["scrub"]
        n_scrub = int(scrub["west"].get(y, 0) + scrub["ost"].get(y, 0))
        n_dir = int(g["west"].notna().sum() + g["ost"].notna().sum()) + n_scrub
        contaminated = n_scrub / max(n_dir, 1) > CONTAMINATED_MAX
        rows.append(dict(
            year=y, coverage=cov, scrubbed=n_scrub, contaminated=contaminated,
            usable=(cov >= COVERAGE_GOOD) and not contaminated,
            dtv=dtv, dtvw=dtvw,
            q1=nth_hour(cross, 1), q30=nth_hour(cross, 30),
            q50=nth_hour(cross, 50),
            q30_adj=nth_hour(cross, n30), q50_adj=nth_hour(cross, n50),
            wk_peak=wk_peak, wk_peak_h=wk_peak_h,
            daily_peak_med=dmax.median() if len(dmax) else np.nan,
            sc_peak=sc_peak,
            west_peak=dir_peaks["west"][0], west_peak_h=dir_peaks["west"][1],
            ost_peak=dir_peaks["ost"][0], ost_peak_h=dir_peaks["ost"][1],
            heavier_dir_peak=heavier, lkw_share_top50=lkw_share,
        ))
    return pd.DataFrame(rows).set_index("year")


def dtv_editions() -> pd.DataFrame:
    ed = pd.read_csv(HERE / "data" / "dtv_editions.csv")
    ed = ed[ed["edition"].astype(str) != "1993"]  # classed range, handled separately
    ed["value"] = pd.to_numeric(ed["value"])
    # DTVw editions -> DTV via the Senate factor 0.91
    ed["dtv_equiv"] = np.where(ed["kind"].str.startswith("DTVw"),
                               ed["value"] * 0.91, ed["value"])
    g = ed.groupby(["edition", "kind"])["dtv_equiv"].agg(["min", "max", "mean"])
    return g.reset_index()


# ---------------------------------------------------------------- figures

def shade_bands(ax, xmax=1.0):
    colors = ["#f0f0f0", "#dcebf7", "#c6dbef", "#9ecae1", "#6baed6"]
    for (lo, hi), c in zip(BANDS, colors):
        ax.axhspan(lo, hi, color=c, alpha=0.35, zorder=0)
    for edge in (400, 800, 1000, 1600, 1800, 2600):
        ax.axhline(edge, color="grey", lw=0.4, alpha=0.5, zorder=0)


def fig01_coverage(wide):
    fig, ax = plt.subplots(figsize=(11, 3.2))
    m = wide.set_index("date").groupby([pd.Grouper(freq="ME")]).agg(
        west=("west", lambda s: s.notna().mean()),
        ost=("ost", lambda s: s.notna().mean()),
        cross=("cross", lambda s: s.notna().mean()))
    # months have differing slot counts in the data (gaps) -> recompute vs grid
    grid = wide.groupby(wide["date"].dt.to_period("M")).size()
    full = grid.index.days_in_month * 24
    img = []
    for col in ("west", "ost", "cross"):
        per = wide.groupby(wide["date"].dt.to_period("M"))[col].apply(
            lambda s: s.notna().sum())
        img.append((per / full).reindex(grid.index).values)
    im = ax.imshow(np.array(img), aspect="auto", cmap="RdYlGn",
                   vmin=0, vmax=1, interpolation="nearest")
    ax.set_yticks([0, 1, 2], ["TE180 West", "TE181 Ost", "cross-section"])
    ticks = [i for i, p in enumerate(grid.index) if p.month == 1]
    ax.set_xticks(ticks, [str(p.year) for p in grid.index[ticks]])
    fig.colorbar(im, ax=ax, label="valid-hour share")
    ax.set_title("Monthly valid-hour coverage (qualitaet ≥ 0.75) — the cross-"
                 "section needs BOTH directions")
    fig.tight_layout()
    fig.savefig(FIG / "01_coverage.png", dpi=150)
    plt.close(fig)


def fig02_diurnal(wide):
    g = wide[(wide["year"] == REF_YEAR) & wide["workday"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    for col, c, lab in [("west", "#1f77b4", "TE180 West"),
                        ("ost", "#d62728", "TE181 Ost"),
                        ("cross", "k", "cross-section (West+Ost)")]:
        prof = g.groupby("stunde")[col].mean()
        ax.plot(prof.index, prof.values, color=c, lw=2.2 if col == "cross" else 1.6,
                label=lab)
        pk_h, pk = int(prof.idxmax()), prof.max()
        ax.annotate(f"{pk:,.0f} Kfz/h @ {pk_h:02d}h", (pk_h, pk),
                    xytext=(pk_h + 0.4, pk + 60), color=c, fontsize=9)
        ax.scatter([pk_h], [pk], color=c, zorder=5, s=25)
    shade_bands(ax)
    ax.set_ylim(0, 2700)
    ax.set_xlabel("hour of day (local)")
    ax.set_ylabel("mean Kfz/h")
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title(f"Standardised workday diurnal profile {REF_YEAR} (Mo-Fr, "
                 "non-holiday)\npeak hour per direction vs cross-section; "
                 "background: RASt 06 bands")
    fig.tight_layout()
    fig.savefig(FIG / "02_diurnal_peak.png", dpi=150)
    plt.close(fig)


def fig03_duration_curves(wide, ym):
    fig, (ax, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4.8),
                                       gridspec_kw={"width_ratios": [3, 2, 2]})
    cmap = plt.get_cmap("viridis")
    years = [2018, 2019, 2020, 2023]
    for i, y in enumerate(years):
        s = wide.loc[wide["year"] == y, "cross"].dropna().sort_values(
            ascending=False).reset_index(drop=True)
        if s.empty:
            continue
        c = cmap(i / (len(years) - 1))
        ls = "--" if not ym.loc[y, "usable"] else "-"
        ax.plot(np.arange(1, len(s) + 1), s, color=c, ls=ls, lw=1.4,
                label=f"{y} (cov {ym.loc[y, 'coverage']:.0%})")
        ax2.plot(np.arange(1, min(201, len(s) + 1)), s.iloc[:200], color=c,
                 ls=ls, lw=1.4)
    for a in (ax, ax2, ax3):
        a.axvline(30, color="crimson", lw=0.9)
        a.axvline(50, color="navy", lw=0.9)
    ax.text(31, 100, "n=30 (HBS 2001)", rotation=90, fontsize=8, color="crimson")
    ax.text(52, 100, "n=50 (HBS 2015 MSV/qB)", rotation=90, fontsize=8,
            color="navy")
    ax.set_xscale("log")
    ax.set_xlabel("hour rank n (log)")
    ax.set_ylabel("Kfz/h, cross-section")
    ax.set_title("Annual duration curves (Dauerlinien)")
    ax2.set_xlabel("hour rank n (top 200, linear)")
    ax2.set_title("zoom: the design-hour region")
    ax.legend(fontsize=8)
    # the cautionary panel: 2016 with the contaminated TE181 left in
    s_raw = wide.loc[wide["year"] == 2016, "cross_raw"].dropna().sort_values(
        ascending=False).reset_index(drop=True)
    s_cln = wide.loc[wide["year"] == 2016, "cross"].dropna().sort_values(
        ascending=False).reset_index(drop=True)
    ax3.plot(np.arange(1, min(201, len(s_raw) + 1)), s_raw.iloc[:200],
             color="crimson", lw=1.3, label="2016 raw (TE181 artefacts)")
    ax3.plot(np.arange(1, min(201, len(s_cln) + 1)), s_cln.iloc[:200],
             color="grey", lw=1.3,
             label="2016 after scrub (bulk still inflated)")
    ax3.set_xlabel("hour rank n (top 200)")
    ax3.set_title("why 2015-2017 are excluded")
    ax3.legend(fontsize=7, loc="upper right")
    fig.suptitle("Torstrasse TE180+TE181 — ranked hourly Kfz volumes; the "
                 "n-th-highest hour IS the formal design value, and it is "
                 "extremely sensitive to tail artefacts", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "03_duration_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig04_definitions_by_year(ym):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ymp = ym[~ym["contaminated"]]
    x = ymp.index.values
    series = [("q1", "absolute max hour (q1)", "#999999", "o"),
              ("q30", "30th hour (HBS 2001)", "crimson", "s"),
              ("q50", "50th hour (HBS 2015 MSV/qB)", "navy", "D"),
              ("wk_peak", "standardised workday peak (D4)", "#2ca02c", "^"),
              ("daily_peak_med", "median daily peak (D5)", "#ff7f0e", "v"),
              ("sc_peak", "short-count 15-19h proxy (D6)", "#8c564b", "x")]
    for col, lab, c, m in series:
        ax.plot(x, ymp[col], color=c, marker=m, ms=5, lw=1.2, label=lab)
    for xi, b in zip(x, ymp["coverage"] < COVERAGE_GOOD):
        if b:
            ax.axvspan(xi - 0.4, xi + 0.4, color="grey", alpha=0.12, zorder=0)
    for y in ym.index[ym["contaminated"]]:
        ax.axvspan(y - 0.4, y + 0.4, color="crimson", alpha=0.06, zorder=0)
        ax.text(y, 2600, "TE181\ncontam.", ha="center", va="top", fontsize=7,
                color="crimson")
    shade_bands(ax)
    ax.set_ylim(0, 2700)
    ax.set_xticks(ym.index.values)
    ax.set_ylabel("Kfz/h, cross-section")
    ax.legend(fontsize=8, loc="lower left", ncols=2)
    ax.set_title("All peak-hour definitions by year\nred columns: excluded "
                 "(TE181 contaminated) · grey: coverage < 90 %, biased low · "
                 "background: RASt 06 bands")
    fig.tight_layout()
    fig.savefig(FIG / "04_definitions_by_year.png", dpi=150)
    plt.close(fig)


def fig05_peak_share(ym):
    fig, ax = plt.subplots(figsize=(9, 5))
    good = ym[ym["usable"]]
    for col, lab, c in [("q30", "q30 / DTV", "crimson"),
                        ("q50", "q50 / DTV", "navy"),
                        ("wk_peak", "workday peak / DTVw", "#2ca02c")]:
        base = good["dtv"] if col != "wk_peak" else good["dtvw"]
        ax.plot(good.index, good[col] / base * 100, "o-", color=c, label=lab)
    ax.axhline(10, color="k", lw=1, ls="--")
    ax.text(good.index[0], 10.15, "10 % rule of thumb (DTV ≈ 10 × MSV)",
            fontsize=8)
    ax.axhline(11.5, color="k", lw=1, ls=":")
    ax.text(good.index[0], 11.65, "11.5 % (HBS day-curve share cited in "
            "Gutachten)", fontsize=8)
    ax.axhline(5.5, color="purple", lw=1, ls="-.")
    ax.text(good.index[0], 4.8, "RLS-19 M_t = 5.5 % of DTV — an AVERAGE "
            "hour, not a peak (the trap)", fontsize=8, color="purple")
    ax.set_ylabel("peak-hour share of daily volume [%]")
    ax.set_ylim(0, 13)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_title("How big is the peak hour relative to the day? "
                 "(detector-derived, years with ≥90 % coverage)")
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "05_peak_share_of_dtv.png", dpi=150)
    plt.close(fig)


def fig06_thirty_years(ym, ed):
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    # official editions: DTV-equivalent (DTVw x 0.91), min-max across links
    pos = {"1998": 1998, "2005": 2005, "2009": 2009, "2014": 2014,
           "2019": 2019, "2023": 2023}
    for _, r in ed.iterrows():
        x = pos[str(r["edition"])]
        x = x + (0.35 if r["kind"].startswith("DTVw") else 0)
        for frac, c in ((0.10, "k"), (0.115, "grey")):
            lo, hi = r["min"] * frac, r["max"] * frac
            pad = max(0, (60 - (hi - lo)) / 2)   # keep zero-range bars visible
            ax.plot([x, x], [lo - pad, hi + pad], color=c, lw=3,
                    alpha=0.85 if c == "k" else 0.5,
                    solid_capstyle="butt")
    # 1993 classed range 20,001-30,000 DTV
    ax.plot([1993, 1993], [20001 * 0.10, 30000 * 0.10], color="k", lw=3,
            alpha=0.85)
    ax.plot([1993, 1993], [20001 * 0.115, 30000 * 0.115], color="grey", lw=3,
            alpha=0.5)
    ax.annotate("1993 edition is a class\n(20-30 k DTV) → wide band",
                (1993, 3000), fontsize=8, ha="left")
    good = ym[ym["usable"]]
    ax.plot(good.index, good["q50"], "D-", color="navy", ms=5,
            label="measured 50th hour (MSV/qB)")
    ax.plot(good.index, good["wk_peak"], "^-", color="#2ca02c", ms=5,
            label="measured standardised workday peak")
    ok23 = ym.loc[2023]
    ax.plot([2023], [ok23["q50"]], "D", color="navy", mfc="none",
            label="2023 measured (coverage ~60 %, biased low)")
    ax.plot([], [], color="k", lw=3, label="shortcut: 10 % of official DTV")
    ax.plot([], [], color="grey", lw=3, alpha=0.6,
            label="shortcut: 11.5 % of official DTV")
    ax.set_xlabel("year / map edition")
    ax.set_ylabel("Kfz/h, cross-section")
    ax.set_title("30 years of the SHORTCUT definition (peak ≈ 10-11.5 % of "
                 "official DTV, Torstrasse links at the detectors)\nvs the "
                 "measured design hours 2015-2020 — DTVw editions converted "
                 "to DTV with the Senate factor 0.91")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_ylim(0, 3400)
    shade_bands(ax)
    fig.tight_layout()
    fig.savefig(FIG / "06_thirty_year_shortcut.png", dpi=150)
    plt.close(fig)


def fig07_top50_anatomy(wide):
    g = wide[wide["year"] == REF_YEAR].dropna(subset=["cross"])
    top = g.nlargest(50, "cross")
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax.hist([top.loc[top["dow"] < 5, "stunde"],
             top.loc[top["dow"] >= 5, "stunde"]],
            bins=np.arange(0, 25) - 0.5, stacked=True,
            color=["#444444", "#bbbbbb"], label=["Mo-Fr", "Sa-So"])
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("hour of day")
    ax.set_ylabel("count of top-50 hours")
    ax.legend(fontsize=9)
    ax.set_title(f"WHEN the {REF_YEAR} top-50 hours occur")
    share = top["west"] / top["cross"]
    ax2.scatter(top["cross"], share * 100, c=top["stunde"], cmap="coolwarm",
                s=30)
    ax2.axhline(50, color="k", lw=0.8)
    ax2.set_xlabel("cross-section volume [Kfz/h]")
    ax2.set_ylabel("West share of cross-section [%]")
    sc = ax2.collections[0]
    fig.colorbar(sc, ax=ax2, label="hour of day")
    ax2.set_title("Directional split inside the top-50 hours")
    fig.suptitle("Anatomy of the design hours — afternoon-dominated, "
                 "direction-balanced (no single 'heavier direction' rules "
                 "them)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "07_top50_anatomy.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig08_placement(ym, ed):
    fig, ax = plt.subplots(figsize=(10, 4.6))
    y = ym.loc[REF_YEAR]
    vals = [
        ("q1 absolute max", y["q1"]),
        ("q30 (HBS 2001)", y["q30"]),
        ("q50 (HBS 2015 MSV/qB)", y["q50"]),
        ("standardised workday peak", y["wk_peak"]),
        ("median daily peak", y["daily_peak_med"]),
        ("short-count 15-19h proxy", y["sc_peak"]),
        ("shortcut 10 % x DTVw2019 x 0.91", 0.10 * 20100 * 0.91),
        ("shortcut 11.5 % x DTVw2019 x 0.91", 0.115 * 20100 * 0.91),
        ("RLS-19 M_t (5.5 % x DTV) — NOT a peak", 0.055 * 18260),
        ("heavier-direction workday peak (fig. 77)", y["heavier_dir_peak"]),
    ]
    # staggered band chart so the deliberate overlaps are visible
    for i, ((lo, hi), lab) in enumerate(zip(BANDS, BAND_LABELS)):
        row = -1.0 if i % 2 == 0 else -1.7
        ax.barh(row, hi - lo, left=lo, height=0.55,
                color=["#f0f0f0", "#dcebf7", "#c6dbef", "#9ecae1", "#6baed6"][i],
                edgecolor="grey", lw=0.5)
        ax.text((lo + hi) / 2, row, lab, ha="center", va="center", fontsize=8)
    ax.axvline(750, color="brown", lw=0.8, ls=":")
    ax.text(750, len(vals) - 0.4, "750 Kfz/h — RASt 06 fig. 77 indicative\n"
            "limit for crossing facilities", fontsize=7.5, color="brown",
            ha="center", va="bottom")
    for i, (lab, v) in enumerate(vals):
        ax.plot([v, v], [-0.7, len(vals) - 1 - i + 0.3], color="grey", lw=0.5,
                zorder=1)
        ax.scatter([v], [len(vals) - 1 - i], s=40, zorder=3,
                   color="purple" if "RLS" in lab else
                   ("#2ca02c" if "shortcut" in lab else "navy"))
        ax.text(v + 25, len(vals) - 1 - i, f"{lab}: {v:,.0f}", fontsize=8.5,
                va="center")
    ax.set_xlim(0, 3000)
    ax.set_ylim(-2.1, len(vals) + 1.2)
    ax.set_yticks([])
    ax.set_xlabel(f"Kfz/h — cross-section, {REF_YEAR}")
    ax.set_title("Where Torstrasse lands in the five RASt 06 volume bands, "
                 "definition by definition (reference year 2019)")
    fig.tight_layout()
    fig.savefig(FIG / "08_rast_band_placement.png", dpi=150)
    plt.close(fig)


def main() -> None:
    wide = load()
    ym = year_metrics(wide)
    ed = dtv_editions()

    fig01_coverage(wide)
    fig02_diurnal(wide)
    fig03_duration_curves(wide, ym)
    fig04_definitions_by_year(ym)
    fig05_peak_share(ym)
    fig06_thirty_years(ym, ed)
    fig07_top50_anatomy(wide)
    fig08_placement(ym, ed)

    out = {"year_metrics": json.loads(ym.to_json(orient="index")),
           "dtv_editions": json.loads(ed.to_json(orient="records"))}
    (HERE / "data" / "summary.json").write_text(json.dumps(out, indent=1))

    pd.set_option("display.width", 200)
    print(ym.round(1).to_string())
    print()
    print(ed.round(0).to_string())


if __name__ == "__main__":
    main()
