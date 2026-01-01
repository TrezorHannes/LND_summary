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

```bash
pip install -r requirements.txt
