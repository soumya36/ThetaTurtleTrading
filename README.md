# Gemini Market Data Scripts

## Files

| File | Description |
|---|---|
| `gemini_client.py` | Reusable API wrapper — all public + authenticated endpoints |
| `1_get_prices.py` | Fetch live prices, ticker data, and candles |
| `2_wrangle_data.py` | Candles → pandas, technical indicators (SMA/EMA/RSI/Bollinger), multi-symbol merge, CSV export |
| `3_orderbook_and_trades.py` | Order book depth analysis, trade history, VWAP, minute-bar aggregation |
| `4_tick_sizes.py` | Tick sizes, quote increments, and min order sizes for all instruments |

## Setup

```bash
pip install requests pandas openpyxl
```

All scripts import `gemini_client.py`, so keep them in the same directory.

## Usage

```bash
# Live prices & candles
python 1_get_prices.py

# Data wrangling & indicators
python 2_wrangle_data.py

# Order book & trade analysis
python 3_orderbook_and_trades.py

# Tick sizes & instrument details
python 4_tick_sizes.py
```

**No API key is needed** — all endpoints used are public market data.

Your API key + secret are only needed if you want to call the `fx_rate()` method
or the private order/fund-management endpoints (not covered in these scripts).

## Customisation

- Change `SYMBOL` in any script to analyse a different pair (e.g. `ETHUSD`, `SOLUSD`).
- Change `time_frame` in `candles()` to `1m`, `5m`, `15m`, `30m`, `1hr`, `6hr`, or `1day`.
- Adjust indicator windows in `add_indicators()`.
