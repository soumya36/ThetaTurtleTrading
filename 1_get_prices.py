"""
1_get_prices.py – Fetch live crypto prices from Gemini.

Demonstrates:
    • pricefeed   (all pairs at once)
    • ticker_v2   (detailed single-symbol ticker)
    • candles     (OHLCV history)

No API key required – these are all public endpoints.
"""

from gemini_client import GeminiClient

client = GeminiClient()

# ─── 1. Price-feed snapshot ────────────────────────────────────────────
print("=" * 60)
print("TOP 10 PAIRS BY 24h PRICE CHANGE (absolute)")
print("=" * 60)

feed = client.pricefeed()

# filter to USD pairs and sort by absolute 24h change
usd_pairs = [p for p in feed if p["pair"].endswith("USD")]
usd_pairs.sort(key=lambda p: abs(float(p["percentChange24h"])), reverse=True)

print(f"{'Pair':<16} {'Price':>12} {'24h %':>10}")
print("-" * 40)
for p in usd_pairs[:10]:
    print(f"{p['pair']:<16} {float(p['price']):>12,.2f} {float(p['percentChange24h']):>9.2f}%")

# ─── 2. Detailed ticker for a single symbol ───────────────────────────
print("\n" + "=" * 60)
symbol = "BTCUSD"
print(f"TICKER V2 – {symbol}")
print("=" * 60)

t = client.ticker_v2(symbol)
print(f"  Open:   ${float(t['open']):>12,.2f}")
print(f"  High:   ${float(t['high']):>12,.2f}")
print(f"  Low:    ${float(t['low']):>12,.2f}")
print(f"  Close:  ${float(t['close']):>12,.2f}")
print(f"  Bid:    ${float(t['bid']):>12,.2f}")
print(f"  Ask:    ${float(t['ask']):>12,.2f}")
print(f"  Hourly prices (last 6h): {t['changes'][:6]}")

# ─── 3. Recent candles ────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"LAST 5 HOURLY CANDLES – {symbol}")
print("=" * 60)

candles = client.candles(symbol, "1hr")   # newest first
print(f"{'Timestamp':<28} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Vol':>12}")
print("-" * 84)

from datetime import datetime, timezone

for c in candles[:5]:
    ts = datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    o, h, lo, cl, vol = c[1], c[2], c[3], c[4], c[5]
    print(f"{ts:<28} {o:>10,.2f} {h:>10,.2f} {lo:>10,.2f} {cl:>10,.2f} {vol:>12,.4f}")
