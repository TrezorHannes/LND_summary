# LND Summary

This Python script generates a CSV of LND forwarding data, outputs two basic charts, and prints a year-in-review summary.

## Features

- Generates daily forwarding statistics CSV from `lncli fwdinghistory`.
- Creates two charts:
  - Daily Forwarded BTC (with 5-day moving average)
  - Daily Fees (in sats) + Average PPM
- Prints a year/month summary in the terminal.
- Progress bar shows processing status.

## Requirements

- Python 3.7+
- LND node accessible with `lncli` command
- Python packages:
  - numpy
  - pandas
  - matplotlib
  - tqdm

Install dependencies:

```
pip install -r requirements.txt
```

## Example useage

```
python3 lnd_summary.py --start 2025-01-01 --end 2025-12-31 --output-dir stats_2025
```
## Example output

```
===== Year-in-Review Summary =====
Highest forwarding day: 2025-03-14 → 8.9123 BTC
Highest fees day: 2025-09-22 → 0.0198 BTC
Highest avg PPM day: 2025-07-05 → 3890.5 ppm
Largest single forward: 0.3786 BTC on 2025-03-14
Largest single fee: 0.0023 BTC on 2025-09-22

Monthly Totals (with overall totals/averages):
  month  total_forwarded_btc  total_fees_btc  avg_ppm
01-2025             4.123456        0.001567      412
02-2025             7.654321        0.002345      306
03-2025            12.987654        0.003876      298
04-2025            10.234567        0.004321      422
05-2025            18.543210        0.032100     1729
06-2025            75.876543        0.198765     2615
07-2025            42.135792        0.065432     1552
08-2025            38.987654        0.030210      775
09-2025            36.543210        0.016543      452
10-2025            58.321098        0.038765      665
11-2025           162.432109        0.221098     1362
12-2025           110.987654        0.098765      891
-----------------------------------------------------
TOTAL             577.687327        0.911505     1230

Overall Totals & Averages:
 - Total BTC forwarded: 577.687327
 - Average BTC forwarded per month: 48.140611
 - Overall average PPM: 1230
```

## Charts

<img width="600" height="248" alt="daily_forwarded_btc" src="https://github.com/user-attachments/assets/737bc959-d847-4c77-8406-f5452d3a9f8a" />
<img width="600" height="248" alt="daily_fees_sats" src="https://github.com/user-attachments/assets/20fb3c2a-f8c7-4858-961b-929fff8da121" />

