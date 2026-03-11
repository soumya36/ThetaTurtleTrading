"""
4_tick_sizes.py – Fetch minimum tick sizes and order details for Gemini instruments.

Displays: tick_size, quote_increment, min_order_size, status, product_type
for all available symbols, with filtering and sorting options.

No API key required.
"""

import pandas as pd
from gemini_client import GeminiClient

client = GeminiClient()

# ─── 1. Fetch all symbols ─────────────────────────────────────────────
symbols = client.list_symbols()
print(f"Fetching details for {len(symbols)} symbols...\n")

# ─── 2. Pull details for each symbol ──────────────────────────────────
records = []
errors = []

for sym in symbols:
    try:
        d = client.symbol_details(sym)
        records.append({
            "symbol":          d.get("symbol", sym.upper()),
            "base_currency":   d.get("base_currency"),
            "quote_currency":  d.get("quote_currency"),
            "tick_size":       d.get("tick_size"),
            "quote_increment": d.get("quote_increment"),
            "min_order_size":  d.get("min_order_size"),
            "status":          d.get("status"),
            "product_type":    d.get("product_type"),
            "contract_type":   d.get("contract_type"),
        })
    except Exception as e:
        errors.append((sym, str(e)))

df = pd.DataFrame(records)

# convert numeric columns
for col in ["tick_size", "quote_increment", "min_order_size"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ─── 3. Summary table ─────────────────────────────────────────────────
print("=" * 90)
print("ALL INSTRUMENTS – TICK SIZES & MINIMUMS")
print("=" * 90)

display_cols = ["symbol", "base_currency", "tick_size", "quote_increment",
                "min_order_size", "status", "product_type"]

print(df[display_cols].to_string(index=False))

# ─── 4. Grouped summaries ─────────────────────────────────────────────
print("\n" + "=" * 90)
print("TICK SIZE SUMMARY BY BASE CURRENCY")
print("=" * 90)

summary = (
    df.groupby("base_currency")
    .agg(
        tick_size=("tick_size", "first"),
        quote_increment=("quote_increment", "first"),
        min_order_size=("min_order_size", "first"),
        num_pairs=("symbol", "count"),
    )
    .sort_values("tick_size")
    .reset_index()
)
print(summary.to_string(index=False))

# ─── 5. Spot vs Perpetual breakdown ───────────────────────────────────
print("\n" + "=" * 90)
print("SPOT vs PERPETUAL SWAP")
print("=" * 90)

for ptype, group in df.groupby("product_type"):
    print(f"\n  {ptype.upper()} ({len(group)} instruments)")
    print(f"  {'Symbol':<20} {'Tick Size':>12} {'Quote Inc':>12} {'Min Order':>12} {'Status':>10}")
    print("  " + "-" * 68)
    for _, r in group.iterrows():
        print(f"  {r['symbol']:<20} {r['tick_size']:>12.0e} {r['quote_increment']:>12.4f} "
              f"{r['min_order_size']:>12.6f} {r['status']:>10}")

# ─── 6. Export ─────────────────────────────────────────────────────────
df.to_csv("instrument_details.csv", index=False)
print(f"\nExported: instrument_details.csv  ({len(df)} rows)")

if errors:
    print(f"\n⚠ Failed to fetch {len(errors)} symbols: {errors}")
