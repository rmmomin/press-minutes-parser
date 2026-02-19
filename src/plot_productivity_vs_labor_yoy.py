#!/usr/bin/env python3
"""
Download labor productivity from FRED, compute year-over-year percent change,
and plot it against quarterly total FOMC productivity mentions
(minutes + press conference).
"""

import csv
import os
from datetime import date, datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, YearLocator
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
WORD_COUNTS_FILE = BASE_DIR / "data" / "word_counts.csv"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_PLOT = OUTPUT_DIR / "productivity_mentions_vs_labor_productivity_yoy_quarterly.png"
OUTPUT_DATA = BASE_DIR / "data" / "productivity_mentions_vs_labor_productivity_yoy_quarterly.csv"
DOTENV_FILE = BASE_DIR / ".env"

FRED_SERIES_ID = "OPHNFB"
FRED_SERIES_NAME = "Labor Productivity (Output Per Hour, Nonfarm Business)"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def load_dotenv_file(dotenv_path):
    """Load KEY=VALUE pairs from a .env file."""
    env_vars = {}
    if not dotenv_path.exists():
        return env_vars

    with open(dotenv_path, "r") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip().strip('"').strip("'")

    return env_vars


def get_fred_api_key():
    """Get FRED API key from environment or local .env file."""
    api_key = os.getenv("FRED_API_KEY")
    if api_key:
        return api_key

    return load_dotenv_file(DOTENV_FILE).get("FRED_API_KEY")


def quarter_from_date(dt):
    """Return quarter tuple (year, quarter_number) for a date."""
    return (dt.year, (dt.month - 1) // 3 + 1)


def quarter_label(year, quarter):
    """Format quarter label like 2026-Q1."""
    return f"{year}-Q{quarter}"


def quarter_end_date(year, quarter):
    """Return quarter-end date for a given year/quarter tuple."""
    month_day = {
        1: (3, 31),
        2: (6, 30),
        3: (9, 30),
        4: (12, 31),
    }
    month, day = month_day[quarter]
    return date(year, month, day)


def load_productivity_mentions_by_quarter(csv_path):
    """Load and aggregate total productivity mentions by quarter."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing {csv_path}. Run the pipeline first to create word counts."
        )

    totals = {}
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("word") != "productivity":
                continue

            meeting_date = datetime.strptime(row["meeting_date"], "%Y-%m-%d").date()
            quarter_key = quarter_from_date(meeting_date)
            totals[quarter_key] = totals.get(quarter_key, 0) + int(row["count"])

    return totals


def fetch_fred_series(api_key, series_id):
    """Fetch FRED series observations."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    response = requests.get(FRED_URL, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    observations = payload.get("observations", [])

    series = []
    for obs in observations:
        value_str = obs.get("value", ".")
        try:
            value = float(value_str)
        except (TypeError, ValueError):
            continue

        date_str = obs.get("date")
        if not date_str:
            continue
        obs_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        series.append((obs_date, value))

    series.sort(key=lambda x: x[0])
    return series


def compute_yoy_percent_change(series):
    """Compute y/y percent change using a 4-observation lag (quarterly data)."""
    yoy_series = []
    for idx, (obs_date, value) in enumerate(series):
        if idx < 4:
            continue

        prior_value = series[idx - 4][1]
        if prior_value == 0:
            continue

        yoy = ((value / prior_value) - 1.0) * 100.0
        yoy_series.append((obs_date, yoy))

    return yoy_series


def build_yoy_by_quarter(yoy_series):
    """Map quarterly y/y values to quarter keys."""
    yoy_by_quarter = {}
    for obs_date, yoy in yoy_series:
        quarter_key = quarter_from_date(obs_date)
        yoy_by_quarter[quarter_key] = yoy
    return yoy_by_quarter


def combine_quarterly_series(mentions_by_quarter, yoy_by_quarter):
    """Combine mentions with y/y values, keeping all mention quarters."""
    combined = []

    for quarter_key in sorted(mentions_by_quarter):
        year, quarter = quarter_key
        combined.append({
            "quarter": quarter_label(year, quarter),
            "quarter_end_date": quarter_end_date(year, quarter),
            "productivity_mentions_total": mentions_by_quarter[quarter_key],
            "labor_productivity_yoy_pct": yoy_by_quarter.get(quarter_key),
        })

    return combined


def write_combined_data(output_path, combined_data):
    """Write combined quarterly data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "quarter",
            "quarter_end_date",
            "productivity_mentions_total",
            "labor_productivity_yoy_pct",
        ])
        for row in combined_data:
            yoy = row["labor_productivity_yoy_pct"]
            writer.writerow([
                row["quarter"],
                row["quarter_end_date"].isoformat(),
                row["productivity_mentions_total"],
                "" if yoy is None else f"{yoy:.4f}",
            ])


def plot_series(output_path, combined_data):
    """Create dual-axis quarterly plot for mentions and labor productivity y/y."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dates = [row["quarter_end_date"] for row in combined_data]
    mentions = [row["productivity_mentions_total"] for row in combined_data]
    yoy_values = [
        row["labor_productivity_yoy_pct"]
        if row["labor_productivity_yoy_pct"] is not None
        else float("nan")
        for row in combined_data
    ]

    fig, ax1 = plt.subplots(figsize=(16, 8))

    ax1.bar(
        dates,
        mentions,
        width=65,
        color="#4e79a7",
        alpha=0.7,
        label="Quarterly FOMC Productivity Mentions",
    )
    ax1.set_ylabel("Total Productivity Mentions", color="#4e79a7")
    ax1.tick_params(axis="y", labelcolor="#4e79a7")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    ax2.plot(
        dates,
        yoy_values,
        color="#e15759",
        linewidth=2.5,
        marker="o",
        markersize=4,
        label="Labor Productivity y/y % (OPHNFB)",
    )
    ax2.set_ylabel("Labor Productivity y/y %", color="#e15759")
    ax2.tick_params(axis="y", labelcolor="#e15759")

    ax1.xaxis.set_major_locator(YearLocator(base=1))
    ax1.xaxis.set_major_formatter(DateFormatter("%Y"))
    fig.autofmt_xdate()

    plt.title("Quarterly FOMC Productivity Mentions vs U.S. Labor Productivity Growth")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    """Run download, transformation, and plotting workflow."""
    api_key = get_fred_api_key()
    if not api_key:
        raise RuntimeError("FRED_API_KEY not found in environment or .env file.")

    print("Loading quarterly FOMC productivity mentions...")
    mentions_by_quarter = load_productivity_mentions_by_quarter(WORD_COUNTS_FILE)

    print(f"Fetching {FRED_SERIES_NAME} ({FRED_SERIES_ID}) from FRED...")
    fred_series = fetch_fred_series(api_key, FRED_SERIES_ID)
    yoy_series = compute_yoy_percent_change(fred_series)
    yoy_by_quarter = build_yoy_by_quarter(yoy_series)

    print("Combining quarterly mentions with quarterly y/y productivity growth...")
    combined_data = combine_quarterly_series(mentions_by_quarter, yoy_by_quarter)

    if not combined_data:
        raise RuntimeError("No overlapping quarterly data between mentions and FRED series.")

    write_combined_data(OUTPUT_DATA, combined_data)
    plot_series(OUTPUT_PLOT, combined_data)

    print("Done.")
    print(f"Combined quarterly data: {OUTPUT_DATA}")
    print(f"Quarterly plot: {OUTPUT_PLOT}")
    print(f"Quarters plotted: {len(combined_data)}")


if __name__ == "__main__":
    main()
