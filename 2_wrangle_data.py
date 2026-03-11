"""
2_wrangle_data.py – Pull Gemini market data into pandas and wrangle it.

Demonstrates:
    • Converting candle arrays → DataFrame
    • Computing rolling indicators (SMA, EMA, Bollinger Bands, RSI)
    • Merging multi-symbol data
    • Exporting to CSV / Excel

Requirements:  pip install pandas openpyxl
"""

import pandas as pd
from datetime import datetime, timezone
from gemini_client import GeminiClient

client = GeminiClient()

# ═══════════════════════════════════════════════════════════════════════
# 1.  CANDLES → DataFrame
# ═══════════════════════════════════════════════════════════════════════

def candles_to_df(symbol: str, time_frame: str = "1hr") -> pd.DataFrame:
    """Fetch candles from Gemini and return a tidy DataFrame."""
    raw = client.candles(symbol, time_frame)
    df = pd.DataFrame(raw, columns=["timestamp_ms", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df = df.sort_values("datetime").reset_index(drop=True)
    df["symbol"] = symbol.upper()
    return df


btc = candles_to_df("BTCUSD", "1h")
eth = candles_to_df("ETHUSD", "1h")

print(f"BTC rows: {len(btc)}  |  ETH rows: {len(eth)}")
print(btc.head())

# ═══════════════════════════════════════════════════════════════════════
# 2.  TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════════════

def add_indicators(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add SMA, EMA, Bollinger Bands, and RSI to a candle DataFrame."""
    df = df.copy()

    # Simple & Exponential Moving Averages
    df[f"sma_{window}"] = df["close"].rolling(window).mean()
    df[f"ema_{window}"] = df["close"].ewm(span=window, adjust=False).mean()

    # Bollinger Bands (2 std dev)
    rolling_std = df["close"].rolling(window).std()
    df["bb_upper"] = df[f"sma_{window}"] + 2 * rolling_std
    df["bb_lower"] = df[f"sma_{window}"] - 2 * rolling_std

    # RSI (14-period by default)
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # Hourly return %
    df["return_pct"] = df["close"].pct_change() * 100

    return df


btc = add_indicators(btc)
eth = add_indicators(eth)

print("\nBTC with indicators (last 5 rows):")
print(btc[["datetime", "close", "sma_20", "ema_20", "rsi_14", "return_pct"]].tail())

# ═══════════════════════════════════════════════════════════════════════
# 3.  MERGE MULTIPLE SYMBOLS
# ═══════════════════════════════════════════════════════════════════════

combined = pd.concat([btc, eth], ignore_index=True)
print(f"\nCombined shape: {combined.shape}")

# Pivot to side-by-side close prices for correlation analysis
pivot = combined.pivot_table(
    index="datetime", columns="symbol", values="close"
)
print("\nBTC / ETH correlation (close prices):")
print(pivot.corr())

# ═══════════════════════════════════════════════════════════════════════
# 4.  PRICEFEED → DataFrame  (snapshot of all pairs)
# ═══════════════════════════════════════════════════════════════════════

feed = client.pricefeed()
pf = pd.DataFrame(feed)
pf["price"] = pd.to_numeric(pf["price"])
pf["percentChange24h"] = pd.to_numeric(pf["percentChange24h"])

# Filter USD pairs, rank by market cap proxy (price)
usd = pf[pf["pair"].str.endswith("USD")].sort_values("price", ascending=False)
print("\nTop 10 USD pairs by price:")
print(usd[["pair", "price", "percentChange24h"]].head(10).to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════
# 5.  EXPORT
# ═══════════════════════════════════════════════════════════════════════

btc.to_csv("btc_candles.csv", index=False)
eth.to_csv("eth_candles.csv", index=False)
usd.to_csv("pricefeed_usd.csv", index=False)

print("\nExported: btc_candles.csv, eth_candles.csv, pricefeed_usd.csv")
