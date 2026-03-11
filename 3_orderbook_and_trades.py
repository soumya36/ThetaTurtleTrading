"""
3_orderbook_and_trades.py – Analyse the Gemini order book and recent trades.

Demonstrates:
    • Fetching and visualising the order book depth
    • Computing bid-ask spread, mid-price, book imbalance
    • Pulling recent trade history and aggregating it

No API key required.
"""

import pandas as pd
from datetime import datetime, timezone
from gemini_client import GeminiClient

client = GeminiClient()
SYMBOL = "BTCUSD"

# ═══════════════════════════════════════════════════════════════════════
# 1.  ORDER BOOK SNAPSHOT
# ═══════════════════════════════════════════════════════════════════════

book = client.order_book(SYMBOL, limit_bids=20, limit_asks=20)

bids = pd.DataFrame(book["bids"]).astype({"price": float, "amount": float})
asks = pd.DataFrame(book["asks"]).astype({"price": float, "amount": float})

best_bid = bids["price"].iloc[0]
best_ask = asks["price"].iloc[0]
spread = best_ask - best_bid
mid = (best_bid + best_ask) / 2
spread_bps = (spread / mid) * 10_000

print("=" * 55)
print(f"ORDER BOOK – {SYMBOL}")
print("=" * 55)
print(f"  Best bid:     ${best_bid:>12,.2f}")
print(f"  Best ask:     ${best_ask:>12,.2f}")
print(f"  Spread:       ${spread:>12,.2f}  ({spread_bps:.1f} bps)")
print(f"  Mid-price:    ${mid:>12,.2f}")

# cumulative depth
bids["cum_amount"] = bids["amount"].cumsum()
asks["cum_amount"] = asks["amount"].cumsum()

bid_depth = bids["amount"].sum()
ask_depth = asks["amount"].sum()
imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)

print(f"\n  Bid depth (top 20):  {bid_depth:>10.4f} BTC")
print(f"  Ask depth (top 20):  {ask_depth:>10.4f} BTC")
print(f"  Book imbalance:      {imbalance:>+10.4f}  (>0 = buy pressure)")

print("\n  Top 5 Bids:")
print(bids[["price", "amount", "cum_amount"]].head().to_string(index=False))
print("\n  Top 5 Asks:")
print(asks[["price", "amount", "cum_amount"]].head().to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════
# 2.  RECENT TRADES
# ═══════════════════════════════════════════════════════════════════════

raw_trades = client.trades(SYMBOL, limit_trades=500)
trades = pd.DataFrame(raw_trades)
trades["price"] = trades["price"].astype(float)
trades["amount"] = trades["amount"].astype(float)
trades["notional"] = trades["price"] * trades["amount"]
trades["datetime"] = pd.to_datetime(trades["timestampms"], unit="ms", utc=True)

print("\n" + "=" * 55)
print(f"RECENT TRADES – {SYMBOL}  (last {len(trades)})")
print("=" * 55)

# Summary stats
buys = trades[trades["type"] == "buy"]
sells = trades[trades["type"] == "sell"]

print(f"  Period:        {trades['datetime'].min()} → {trades['datetime'].max()}")
print(f"  Buy trades:    {len(buys):>6}   Vol: {buys['amount'].sum():>12.4f} BTC  (${buys['notional'].sum():>14,.2f})")
print(f"  Sell trades:   {len(sells):>6}   Vol: {sells['amount'].sum():>12.4f} BTC  (${sells['notional'].sum():>14,.2f})")
print(f"  VWAP:          ${(trades['notional'].sum() / trades['amount'].sum()):>12,.2f}")
print(f"  Price range:   ${trades['price'].min():>12,.2f} – ${trades['price'].max():>12,.2f}")

# ═══════════════════════════════════════════════════════════════════════
# 3.  AGGREGATE BY MINUTE
# ═══════════════════════════════════════════════════════════════════════

trades.set_index("datetime", inplace=True)
minute_bars = trades.resample("1min").agg(
    open=("price", "first"),
    high=("price", "max"),
    low=("price", "min"),
    close=("price", "last"),
    volume=("amount", "sum"),
    trade_count=("tid", "count"),
    buy_volume=("amount", lambda x: trades.loc[x.index, "amount"][trades.loc[x.index, "type"] == "buy"].sum()),
).dropna()

print("\nMinute bars (last 5):")
print(minute_bars.tail().to_string())

# ═══════════════════════════════════════════════════════════════════════
# 4.  EXPORT
# ═══════════════════════════════════════════════════════════════════════

trades.to_csv("recent_trades.csv")
minute_bars.to_csv("minute_bars.csv")
print("\nExported: recent_trades.csv, minute_bars.csv")
