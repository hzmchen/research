#!/usr/bin/env python3
"""Analyse TE180 PKW (car) 5-minute count & speed data (one year).

Reads data/te180_pkw_5min.csv (produced by fetch.py), reindexes onto the complete
5-minute grid, and writes:
  - figures/*.png        : time-series, daily/weekday/hour profiles, ECDF, boxplots
  - data/outages.csv     : detected gaps & zero-count runs (for the writeup)
  - data/summary.json    : headline stats + break runs
  - prints the findings summary

Mirrors ../tc073-deepdive/analyze.py so the two single-site studies are directly
comparable. Reproducible & idempotent: pure function of the cached CSV, no network.
"""
import os, json, csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
from matplotlib.colors import Normalize

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "te180_pkw_5min.csv")
FIG  = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True,
                     "grid.alpha": 0.3, "font.size": 9})

WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TITLE = "TE180 Torstraße (West)"

def load():
    df = pd.read_csv(DATA, parse_dates=["timestamp_utc"])
    df = df.set_index("timestamp_utc").sort_index()
    # collapse any residual duplicate timestamps, preferring the row that has data
    df = df.groupby(level=0).first()
    # full 5-min grid (UTC, no DST artefacts) -> exposes MISSING slots vs zero
    full = pd.date_range(df.index.min(), df.index.max(), freq="5min", tz="UTC")
    df = df.reindex(full)
    df.index.name = "ts"
    df["present"] = df["count"].notna()
    # derive Berlin-local fields for interpretable time-of-day / weekday patterns
    local = df.index.tz_convert("Europe/Berlin")
    df["hour"] = local.hour
    df["dow"] = local.dayofweek
    df["date"] = local.date
    df["local"] = local
    return df

# ----------------------------------------------------------------- time series
def fig_overview(df):
    daily = df.groupby("date").agg(count_sum=("count", "sum"),
                                   count_obs=("count", "count"),
                                   speed_mean=("speed_kmh", "mean"))
    daily.index = pd.to_datetime(daily.index)
    daily.loc[daily.count_obs == 0, ["count_sum", "speed_mean"]] = np.nan
    fig, ax = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
    ax[0].plot(daily.index, daily.count_sum, color="#1f77b4")
    ax[0].set_ylabel("PKW / day"); ax[0].set_title(
        f"{TITLE} — daily car volume & mean speed (5-min PKW data, 1 year)")
    ax[1].plot(daily.index, daily.speed_mean, color="#d62728")
    ax[1].set_ylabel("mean speed (km/h)"); ax[1].set_xlabel("date")
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout(); fig.savefig(f"{FIG}/01_overview_daily.png"); plt.close(fig)
    return daily

def fig_week(df):
    # a representative full week (first Mon..Sun >95% present)
    wk = None
    for mon in pd.date_range(df.index.min().normalize(), df.index.max(), freq="W-MON"):
        seg = df.loc[mon:mon + pd.Timedelta(days=7) - pd.Timedelta(minutes=5)]
        if len(seg) > 2000 and seg["present"].mean() > 0.95:
            wk = seg; break
    if wk is None:
        wk = df.loc[df.index.min():df.index.min() + pd.Timedelta(days=7)]
    fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    ax[0].plot(wk.index, wk["count"], lw=0.7, color="#1f77b4")
    ax[0].set_ylabel("PKW / 5 min")
    ax[0].set_title(f"Representative week (raw 5-min) — week of {wk.index.min():%Y-%m-%d}")
    ax[1].plot(wk.index, wk["speed_kmh"], lw=0.7, color="#d62728")
    ax[1].set_ylabel("speed (km/h)"); ax[1].set_xlabel("date")
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%a %d\n%H:%M"))
    fig.tight_layout(); fig.savefig(f"{FIG}/02_week_raw.png"); plt.close(fig)

def fig_tod(df):
    d = df[df.present]
    d = d.assign(weekend=d["dow"] >= 5)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for label, sub in [("weekday", d[~d.weekend]), ("weekend", d[d.weekend])]:
        tod = sub["local"].dt.hour + sub["local"].dt.minute / 60
        g = sub.groupby(tod)
        ax[0].plot(g["count"].mean().index, g["count"].mean().values, label=label)
        ax[1].plot(g["speed_kmh"].mean().index, g["speed_kmh"].mean().values, label=label)
    ax[0].set_title("Mean car count by time of day"); ax[0].set_ylabel("PKW / 5 min")
    ax[1].set_title("Mean speed by time of day"); ax[1].set_ylabel("km/h")
    for a in ax:
        a.set_xlabel("hour of day (Berlin local)"); a.legend()
        a.set_xlim(0, 24); a.set_xticks(range(0, 25, 3))
    fig.tight_layout(); fig.savefig(f"{FIG}/03_time_of_day.png"); plt.close(fig)

def fig_weekday(df):
    d = df[df.present]
    cnt = d.groupby("dow")["count"].mean().reindex(range(7))
    spd = d.groupby("dow")["speed_kmh"].mean().reindex(range(7))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].bar(WD, cnt.values, color="#1f77b4")
    ax[0].set_title("Mean car count by weekday"); ax[0].set_ylabel("PKW / 5 min")
    ax[1].bar(WD, spd.values, color="#d62728")
    ax[1].set_title("Mean speed by weekday"); ax[1].set_ylabel("km/h")
    fig.tight_layout(); fig.savefig(f"{FIG}/04_weekday.png"); plt.close(fig)

def fig_heatmap(df):
    d = df[df.present]
    piv = d.pivot_table(index="dow", columns="hour", values="count", aggfunc="mean")
    piv = piv.reindex(range(7))
    fig, ax = plt.subplots(figsize=(12, 3.8))
    im = ax.imshow(piv.values, aspect="auto", cmap="magma", origin="upper")
    ax.set_yticks(range(7)); ax.set_yticklabels(WD); ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("hour of day (Berlin local)"); ax.set_title("Mean car count — weekday × hour")
    fig.colorbar(im, ax=ax, label="PKW / 5 min"); ax.grid(False)
    fig.tight_layout(); fig.savefig(f"{FIG}/05_heatmap_hour_weekday.png"); plt.close(fig)

# ---------------------------------------- day pattern decomposed (month/week/dow)
# Each figure shows the mean car-count time-of-day profile (Berlin local, 5-min
# resolution), with one line per group and a *progressive* (sequential) colour
# scheme so the chronological order of the groups is read straight off the colour.
# Weekday (Mon-Fri) and weekend (Sat-Sun) are drawn in separate panels.
def _day_fields(df):
    d = df[df.present].copy()
    ln = d["local"].dt.tz_localize(None)            # naive Berlin wall-clock
    d["tod"] = ln.dt.hour + ln.dt.minute / 60       # 0..24 at 5-min steps
    d["month"] = ln.dt.to_period("M").astype(str)   # "2023-02" .. "2024-01"
    d["week_start"] = ln.dt.to_period("W-MON").dt.start_time  # Monday of each week
    d["weekend"] = d["dow"] >= 5
    return d

def _profile_line(ax, sub, color, label=None, lw=1.2):
    if sub.empty:
        return
    prof = sub.groupby("tod")["count"].mean()
    ax.plot(prof.index, prof.values, color=color, lw=lw, label=label)

def _style_tod(ax, title):
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3))
    ax.set_xlabel("hour of day (Berlin local)"); ax.set_ylabel("PKW / 5 min")
    ax.set_title(title)

def fig_day_pattern_by_month(d):
    months = sorted(d["month"].unique())
    cmap = plt.get_cmap("viridis")
    cols = {m: cmap(i / max(1, len(months) - 1)) for i, m in enumerate(months)}
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for a, (lab, wknd) in zip(ax, [("weekday (Mon–Fri)", False), ("weekend (Sat–Sun)", True)]):
        sub = d[d.weekend == wknd]
        for m in months:
            _profile_line(a, sub[sub.month == m], cols[m], label=m)
        _style_tod(a, f"{TITLE} — day pattern by month, {lab}")
        a.legend(title="month", fontsize=6.5, ncol=2)
    fig.tight_layout(); fig.savefig(f"{FIG}/11_day_pattern_by_month.png"); plt.close(fig)

def fig_day_pattern_by_week(d):
    weeks = sorted(d["week_start"].unique())
    cmap = plt.get_cmap("viridis")
    nums = mdates.date2num(pd.to_datetime(list(weeks)))
    norm = Normalize(nums.min(), nums.max())
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for a, (lab, wknd) in zip(ax, [("weekday (Mon–Fri)", False), ("weekend (Sat–Sun)", True)]):
        sub = d[d.weekend == wknd]
        for w in weeks:
            _profile_line(a, sub[sub.week_start == w],
                          cmap(norm(mdates.date2num(pd.Timestamp(w)))), lw=0.9)
        _style_tod(a, f"{TITLE} — day pattern by week, {lab}")
    # one shared colorbar maps line colour -> week (chronology, incl. year wrap)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
    cb.set_label("week (start date)")
    cb.ax.yaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.savefig(f"{FIG}/12_day_pattern_by_week.png", bbox_inches="tight"); plt.close(fig)

def fig_day_pattern_by_dow(d):
    cmap = plt.get_cmap("viridis")
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for a, (lab, days) in zip(ax, [("weekday (Mon–Fri)", range(0, 5)),
                                    ("weekend (Sat–Sun)", range(5, 7))]):
        days = list(days)
        for i, dow in enumerate(days):
            _profile_line(a, d[d.dow == dow], cmap(i / max(1, len(days) - 1)),
                          label=WD[dow])
        _style_tod(a, f"{TITLE} — day pattern by day of week, {lab}")
        a.legend(title="day", fontsize=7)
    fig.tight_layout(); fig.savefig(f"{FIG}/13_day_pattern_by_dow.png"); plt.close(fig)

# ------------------------------------------------------------------ statistics
def fig_distributions(df):
    d = df[df.present]
    c = d["count"].dropna().values
    s = d["speed_kmh"].dropna().values
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].hist(c, bins=60, color="#1f77b4"); ax[0, 0].set_title("Car count histogram (5-min)")
    ax[0, 0].set_xlabel("PKW / 5 min"); ax[0, 0].set_ylabel("freq")
    ax[0, 1].hist(s, bins=60, color="#d62728"); ax[0, 1].set_title("Speed histogram (5-min)")
    ax[0, 1].set_xlabel("km/h")
    for arr, a, lab in [(c, ax[1, 0], "PKW / 5 min"), (s, ax[1, 1], "km/h")]:
        xs = np.sort(arr); ys = np.arange(1, len(xs) + 1) / len(xs)
        a.plot(xs, ys, color="#333"); a.set_title(f"ECDF — {lab}")
        a.set_xlabel(lab); a.set_ylabel("F(x)"); a.set_ylim(0, 1)
    fig.tight_layout(); fig.savefig(f"{FIG}/06_distributions.png"); plt.close(fig)

def fig_boxplots(df):
    d = df[df.present]
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    data_c = [d[d.hour == h]["count"].dropna().values for h in range(24)]
    data_s = [d[d.hour == h]["speed_kmh"].dropna().values for h in range(24)]
    ax[0].boxplot(data_c, positions=range(24), widths=0.6, showfliers=True,
                  flierprops=dict(marker=".", markersize=2, alpha=0.3))
    ax[0].set_ylabel("PKW / 5 min")
    ax[0].set_title("Car count distribution by hour (box = IQR, points = outliers)")
    ax[1].boxplot(data_s, positions=range(24), widths=0.6, showfliers=True,
                  flierprops=dict(marker=".", markersize=2, alpha=0.3))
    ax[1].set_ylabel("speed (km/h)"); ax[1].set_xlabel("hour of day (Berlin local)")
    ax[1].set_title("Speed distribution by hour")
    fig.tight_layout(); fig.savefig(f"{FIG}/07_boxplots_by_hour.png"); plt.close(fig)

def fig_fundamental(df):
    d = df[df.present].dropna(subset=["count", "speed_kmh"])
    fig, ax = plt.subplots(figsize=(7, 5.5))
    sc = ax.scatter(d["count"], d["speed_kmh"], s=4, alpha=0.15,
                    c=(d["hour"].values), cmap="twilight")
    ax.set_xlabel("PKW / 5 min (flow)"); ax.set_ylabel("speed (km/h)")
    ax.set_title("Speed vs flow (fundamental-diagram view), coloured by hour")
    # colorbar from an opaque proxy (same cmap/norm) so the scatter's alpha
    # doesn't wash out the swatch and make the hour scale unreadable
    sm = cm.ScalarMappable(norm=sc.norm, cmap=sc.cmap); sm.set_array([])
    fig.colorbar(sm, ax=ax, label="hour")
    fig.tight_layout(); fig.savefig(f"{FIG}/08_speed_vs_flow.png"); plt.close(fig)

# ----------------------------------------------------- breaks / outages / zeros
def runs(mask):
    """Yield (start_ts, end_ts, length) for contiguous True runs in a boolean Series."""
    vals = mask.values.astype(int)
    idx = mask.index
    d = np.diff(np.concatenate([[0], vals, [0]]))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    for a, b in zip(starts, ends):
        yield idx[a], idx[b - 1], b - a

def analyze_breaks(df):
    miss = ~df["present"]
    zero = df["present"] & (df["count"] == 0)
    rep = {}
    rep["window_utc"] = [df.index.min().isoformat(), df.index.max().isoformat()]
    rep["total_slots"] = int(len(df))
    rep["present"] = int(df["present"].sum())
    rep["missing"] = int(miss.sum())
    rep["fill_pct"] = round(100 * df["present"].mean(), 2)
    rep["zero_count_slots"] = int(zero.sum())
    d = df[df.present]
    rep["count_stats"] = {k: round(float(v), 2) for k, v in
        dict(median=d["count"].median(), mean=d["count"].mean(),
             p95=d["count"].quantile(.95), max=d["count"].max()).items()}
    rep["speed_stats"] = {k: round(float(v), 2) for k, v in
        dict(median=d["speed_kmh"].median(), mean=d["speed_kmh"].mean(),
             p05=d["speed_kmh"].quantile(.05), p95=d["speed_kmh"].quantile(.95)).items()}
    # significant runs: missing >= 6 slots (>=30 min) ; zero runs >= 6 slots
    out_rows = []
    for kind, mask in [("missing", miss), ("zero", zero)]:
        for a, b, n in runs(mask):
            if n >= 6:
                out_rows.append(dict(kind=kind, start=a.isoformat(), end=b.isoformat(),
                                     slots=int(n), minutes=int(n * 5)))
    out_rows.sort(key=lambda r: r["start"])
    with open(os.path.join(HERE, "data", "outages.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["kind", "start", "end", "slots", "minutes"])
        w.writeheader(); w.writerows(out_rows)
    rep["significant_runs(>=30min)"] = len(out_rows)
    rep["longest_runs"] = sorted(out_rows, key=lambda r: -r["slots"])[:15]
    # artefact check: speed present while count==0 ?
    sp_when_zero = df[(df["count"] == 0) & df["speed_kmh"].notna() & (df["speed_kmh"] > 0)]
    rep["speed>0_while_count0"] = int(len(sp_when_zero))
    return rep, out_rows

def fig_daily_coverage(df, out_rows):
    cov = df.groupby("date")["present"].mean() * 100
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.bar(list(cov.index), cov.values, color="#2ca02c", width=1.0)
    ax.set_ylabel("% of 5-min slots present"); ax.set_ylim(0, 105)
    ax.set_title("Daily data coverage (gaps = sensor outage / break)")
    ax.axhline(100, color="grey", lw=0.6, ls="--")
    fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(f"{FIG}/09_daily_coverage.png"); plt.close(fig)

def fig_annotated(df, out_rows):
    """Daily volume with the longest data gaps marked automatically."""
    daily = df.groupby("date").agg(csum=("count", "sum"), n=("count", "count"))
    daily.index = pd.to_datetime(daily.index)
    daily.loc[daily.n < 100, "csum"] = np.nan
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot(daily.index, daily.csum, color="#1f77b4", label="PKW / day")
    top = sorted([r for r in out_rows if r["kind"] == "missing"],
                 key=lambda r: -r["slots"])[:5]
    for r in top:
        s = pd.Timestamp(r["start"]); e = pd.Timestamp(r["end"])
        ax.axvspan(s, e, color="#d62728", alpha=0.18, zorder=0)
        ax.annotate(f"{r['minutes']//60} h gap", xy=(s, ax.get_ylim()[1]*0.92),
                    fontsize=7, ha="left", color="#a00", rotation=90, va="top")
    ax.set_ylabel("PKW / day")
    ax.set_title(f"{TITLE} daily car volume — longest outages shaded")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y")); ax.legend(loc="upper right")
    fig.tight_layout(); fig.savefig(f"{FIG}/10_annotated.png"); plt.close(fig)

def main():
    df = load()
    fig_overview(df)
    fig_week(df); fig_tod(df); fig_weekday(df); fig_heatmap(df)
    dd = _day_fields(df)
    fig_day_pattern_by_month(dd); fig_day_pattern_by_week(dd); fig_day_pattern_by_dow(dd)
    fig_distributions(df); fig_boxplots(df); fig_fundamental(df)
    rep, out_rows = analyze_breaks(df)
    fig_daily_coverage(df, out_rows)
    fig_annotated(df, out_rows)
    print(json.dumps(rep, indent=2, default=str))
    json.dump(rep, open(os.path.join(HERE, "data", "summary.json"), "w"),
              indent=2, default=str)

if __name__ == "__main__":
    main()
