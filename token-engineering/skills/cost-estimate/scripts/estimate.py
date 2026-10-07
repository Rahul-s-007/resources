#!/usr/bin/env python3
"""LLM cost calculator. Contains no prices: pass them in via --prices.

Usage:
    python3 estimate.py --prices prices.json --workload workload.json

prices.json: one price object or a list of them (schema: references/sources.md).
Costs are USD for the whole workload period.

Model: of `requests`, a fraction `hit_rate` read the stable prefix from cache; the
rest write it (at the write price, or plain input price if there is no write fee).
Volatile input and output are never cached. `batch_share` of requests get the batch
discount. Where batch_cache_stacks is false, cached reads in batch are billed at
the non-batch rate. All estimates are approximations; confirm on a real invoice.
"""
import argparse
import json

M = 1_000_000


def _write_price(p, ttl):
    w = p.get("cache_write_1h" if ttl == "1h" else "cache_write_5m")
    if w is None:
        w = p.get("cache_write")
    return p["input"] if w is None else w


def _tier(p, prompt_tokens):
    lc = p.get("long_context")
    if lc and prompt_tokens > lc["threshold"]:
        return lc["input_mult"], lc.get("cached_mult", lc["input_mult"]), lc["output_mult"], True
    return 1.0, 1.0, 1.0, False


def cost(p, w, caching, batch_share):
    n = w["requests"]
    stable, vol, out = w["stable_tokens"], w["volatile_tokens"], w["output_tokens"]
    im, cm, om, over = _tier(p, stable + vol)
    inp, outp = p["input"] * im, p["output"] * om
    read = p["cache_read"] * cm
    write = _write_price(p, w.get("ttl", "5m")) * im
    h = w["hit_rate"] if caching else 0.0

    def per_request(batch):
        d = 1 - p.get("batch_discount", 0.5) if batch else 1.0
        stable_cost = h * read * (1.0 if (batch and p.get("batch_cache_stacks") is False) else d)
        stable_cost += (1 - h) * (write if caching else inp) * d
        return (stable * stable_cost + vol * inp * d + out * outp * d) / M

    total = n * ((1 - batch_share) * per_request(False) + batch_share * per_request(True))
    if caching and p.get("cache_storage_per_hour"):
        total += p["cache_storage_per_hour"] * stable / M * w.get("period_hours", 1)
    return total, over


def breakeven_reads(p, ttl):
    """Reads needed after one write for caching to beat no caching."""
    write, read, inp = _write_price(p, ttl), p["cache_read"], p["input"]
    if write <= inp:
        return 0
    if read >= inp:
        return None
    return (write - inp) / (inp - read)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--workload", required=True)
    a = ap.parse_args()
    prices = json.load(open(a.prices))
    prices = prices if isinstance(prices, list) else [prices]
    w = json.load(open(a.workload))
    bs = w.get("batch_share", 0.0)

    print(f'workload: {w["requests"]:,} requests, {w["stable_tokens"]:,} stable + '
          f'{w["volatile_tokens"]:,} volatile in, {w["output_tokens"]:,} out, '
          f'hit_rate={w["hit_rate"]:.0%}, ttl={w.get("ttl", "5m")}, batch_share={bs:.0%}\n')
    print(f'{"model":<28}{"no cache":>12}{"cached":>12}{"cached+batch":>14}{"saved":>8}  notes')
    for p in prices:
        base, over = cost(p, w, False, 0.0)
        cached, _ = cost(p, w, True, 0.0)
        both, _ = cost(p, w, True, bs)
        notes = []
        if over:
            notes.append("long-context tier")
        be = breakeven_reads(p, w.get("ttl", "5m"))
        if be:
            notes.append(f"break-even {be:.1f} read(s)")
        if p.get("batch_cache_stacks") is None and bs:
            notes.append("batch+cache stacking unverified")
        notes.append(f'{p.get("as_of", "?")}')
        saved = 1 - both / base if base else 0
        print(f'{p["model"]:<28}{base:>12,.2f}{cached:>12,.2f}{both:>14,.2f}{saved:>8.0%}  {"; ".join(notes)}')


if __name__ == "__main__":
    main()
