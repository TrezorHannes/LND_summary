#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.projections")

import argparse
import csv
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

# -----------------------------
# Argument Parsing
# -----------------------------
parser = argparse.ArgumentParser(
    description="Generate LND daily forwarding CSV, charts, and year-in-review summary"
)
parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
parser.add_argument("--output-dir", default="lnd_stats", help="Directory to save CSV and charts")
args = parser.parse_args()

start_date = datetime.strptime(args.start, "%Y-%m-%d")
end_date = datetime.strptime(args.end, "%Y-%m-%d")
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

csv_file = output_dir / "daily_forwarding.csv"
charts_dir = output_dir  # Same directory for charts

# -----------------------------
# Step 1: Generate CSV
# -----------------------------
def generate_csv(start_date, end_date, output_file):
    header = [
        "date", "tx_count", "total_forwarded_sat", "fees_earned_sat",
        "avg_ppm", "p50_sat", "p95_sat", "max_forward_sat", "max_fee_sat"
    ]

    total_days = (end_date - start_date).days + 1
    current_date = start_date

    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for _ in tqdm(
            range(total_days),
            desc="Processing data",
            unit="days",
            ncols=80,  # progress bar width
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} days processed [{elapsed} elapsed]"
        ):
            date_str = current_date.strftime("%Y-%m-%d")

            start_ts = int(current_date.timestamp())
            end_ts = int((current_date + timedelta(days=1)).timestamp())

            result = subprocess.run(
                ["lncli", "fwdinghistory", str(start_ts), str(end_ts), "--max_events=50000"],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                tqdm.write(f"ERROR on {date_str}: {result.stderr}")
                current_date += timedelta(days=1)
                continue

            data = json.loads(result.stdout)
            events = data.get("forwarding_events", [])

            if not events:
                writer.writerow({
                    "date": date_str,
                    "tx_count": 0,
                    "total_forwarded_sat": 0,
                    "fees_earned_sat": 0,
                    "avg_ppm": 0,
                    "p50_sat": 0,
                    "p95_sat": 0,
                    "max_forward_sat": 0,
                    "max_fee_sat": 0
                })
                current_date += timedelta(days=1)
                continue

            amt_out_list = [int(e["amt_out_msat"]) // 1000 for e in events]
            fee_list = [int(e["fee_msat"]) // 1000 for e in events]
            ppm_list = [f / a * 1_000_000 if a > 0 else 0 for a, f in zip(amt_out_list, fee_list)]

            writer.writerow({
                "date": date_str,
                "tx_count": len(events),
                "total_forwarded_sat": sum(amt_out_list),
                "fees_earned_sat": sum(fee_list),
                "avg_ppm": int(np.mean(ppm_list)),
                "p50_sat": int(np.percentile(amt_out_list, 50)),
                "p95_sat": int(np.percentile(amt_out_list, 95)),
                "max_forward_sat": max(amt_out_list),
                "max_fee_sat": max(fee_list)
            })

            current_date += timedelta(days=1)

    print(f"\nCSV generated: {output_file.resolve()}")
    return pd.read_csv(output_file, parse_dates=["date"])

# -----------------------------
# Step 2: Generate Charts
# -----------------------------
def generate_charts(df, output_dir):
    df = df.sort_values("date")
    df["total_forwarded_btc"] = df["total_forwarded_sat"] / 1e8
    df["forwarded_5d_avg"] = df["total_forwarded_btc"].rolling(5, min_periods=1).mean()
    df["avg_ppm"] = (df["fees_earned_sat"] / df["total_forwarded_sat"] * 1_000_000).fillna(0)

    # Chart 1: Forwarded BTC
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df["date"], df["total_forwarded_btc"], color="blue", label="Daily Forwarded BTC")
    ax.plot(df["date"], df["forwarded_5d_avg"], color="red", linestyle="--", label="5-Day MA")
    ax.set_xlabel("Date")
    ax.set_ylabel("Forwarded BTC")
    ax.set_title("Daily Forwarded BTC", pad=20)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout(pad=2.0)
    chart1_path = output_dir / "daily_forwarded_btc.png"
    plt.savefig(chart1_path, bbox_inches="tight")
    plt.close()

    # Chart 2: Fees + avg PPM
    df["fees_btc"] = df["fees_earned_sat"] / 1e8
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.bar(df["date"], df["fees_earned_sat"], color="orange", alpha=0.7, label="Fees Earned (sats)")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Fees Earned (sats)")

    ax2 = ax1.twinx()
    ax2.plot(df["date"], df["avg_ppm"], color="purple", linestyle="--", label="Average PPM")
    ax2.set_ylabel("Average PPM")

    ax1.set_title("Daily Fees Earned & Average PPM", pad=20)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    fig.autofmt_xdate()
    fig.tight_layout(pad=2.0)
    chart2_path = output_dir / "daily_fees_sats.png"
    plt.savefig(chart2_path, bbox_inches="tight")
    plt.close()

    print("Charts saved:")
    print(f" - {chart1_path.resolve()}")
    print(f" - {chart2_path.resolve()}")

# -----------------------------
# Step 3: Year-in-Review Summary
# -----------------------------
def generate_summary(df):
    df = df.sort_values("date")
    df["total_forwarded_btc"] = df["total_forwarded_sat"] / 1e8
    df["fees_btc"] = df["fees_earned_sat"] / 1e8
    df["max_forward_btc"] = df["max_forward_sat"] / 1e8
    df["max_fee_btc"] = df["max_fee_sat"] / 1e8

    df['month'] = df['date'].dt.strftime('%m-%Y')
    monthly = df.groupby('month').agg(
        total_forwarded_btc=('total_forwarded_btc', 'sum'),
        total_fees_btc=('fees_btc', 'sum')
    ).reset_index()
    monthly['avg_ppm'] = (monthly['total_fees_btc'] / monthly['total_forwarded_btc'] * 1_000_000).astype(int)

    total_forwarded = monthly['total_forwarded_btc'].sum()
    total_fees = monthly['total_fees_btc'].sum()
    avg_forwarded_per_month = monthly['total_forwarded_btc'].mean()
    avg_ppm_overall = int(total_fees / total_forwarded * 1_000_000) if total_forwarded > 0 else 0

    max_forwarded_day = df.loc[df['total_forwarded_btc'].idxmax()]
    max_fees_day = df.loc[df['fees_btc'].idxmax()]
    max_ppm_day = df.loc[(df['fees_btc'] / df['total_forwarded_btc']).idxmax()]
    largest_single_forward = df.loc[df['max_forward_btc'].idxmax()]
    largest_single_fee = df.loc[df['max_fee_btc'].idxmax()]

    print("\n===== Year-in-Review Summary =====")
    print(f"Highest forwarding day: {max_forwarded_day['date'].date()} → {max_forwarded_day['total_forwarded_btc']:.4f} BTC")
    print(f"Highest fees day: {max_fees_day['date'].date()} → {max_fees_day['fees_btc']:.4f} BTC")
    print(f"Highest avg PPM day: {max_ppm_day['date'].date()} → {(max_ppm_day['fees_btc']/max_ppm_day['total_forwarded_btc']*1_000_000):.1f} ppm")
    print(f"Largest single forward: {largest_single_forward['max_forward_btc']:.4f} BTC on {largest_single_forward['date'].date()}")
    print(f"Largest single fee: {largest_single_fee['max_fee_btc']:.4f} BTC on {largest_single_fee['date'].date()}\n")

    # Monthly table as string
    monthly_str = monthly.to_string(index=False, float_format="%.6f")
    print("Monthly Totals (with overall totals/averages):")
    print(monthly_str)

    # Divider line same width as table
    table_width = len(monthly_str.splitlines()[0])
    print("-" * table_width)

    # Calculate column widths based on printed table, not just names
    col_widths = []
    for col in monthly.columns:
        max_width = max(len(f"{v:.6f}" if isinstance(v, float) else str(v)) for v in monthly[col])
        col_widths.append(max(max_width, len(col)))  # make sure at least as wide as header

    # TOTAL row with proper right alignment
    total_line = (
        f"{'TOTAL':<{col_widths[0]}}  "
        f"{total_forwarded:>{col_widths[1]}.6f}  "
        f"{total_fees:>{col_widths[2]}.6f}  "
        f"{avg_ppm_overall:>{col_widths[3]}}"
    )
    print(total_line)

    print("\nOverall Totals & Averages:")
    print(f" - Total BTC forwarded: {total_forwarded:.6f}")
    print(f" - Average BTC forwarded per month: {avg_forwarded_per_month:.6f}")
    print(f" - Overall average PPM: {avg_ppm_overall}")

# -----------------------------
# Run All Steps
# -----------------------------
df = generate_csv(start_date, end_date, csv_file)
generate_charts(df, output_dir)
generate_summary(df)
