#!/usr/bin/env python3
"""Replay fingerprinted traffic and estimate prompt-cache hit rate per TTL.

Input: JSONL, one request per line: {"ts": <epoch seconds>, "fingerprint": [<segments from fingerprint.py>]}
Usage: python3 simulate.py log.jsonl [--min-chars 16384]

Optimistic upper bound: assumes one machine, an entry at every segment
boundary, no eviction. min-chars ~= 4 x the model's minimum cacheable tokens.
"""
import argparse
import json


def simulate(requests: list, ttl_s: float, min_chars: int) -> float:
    last_seen = {}
    cached = total = 0
    for req in sorted(requests, key=lambda r: r["ts"]):
        size = hit = 0
        for seg in req["fingerprint"]:
            size += seg["chars"]
            t = last_seen.get(seg["prefix"])
            if t is not None and req["ts"] - t <= ttl_s and size >= min_chars:
                hit = size
            last_seen[seg["prefix"]] = req["ts"]
        cached += hit
        total += size
    return cached / total if total else 0.0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--min-chars", type=int, default=4096)
    args = ap.parse_args()
    with open(args.log) as f:
        log = [json.loads(line) for line in f if line.strip()]
    for name, ttl in [("5 min", 300), ("30 min", 1800), ("1 hour", 3600)]:
        print(f"{name:>7}: {simulate(log, ttl, args.min_chars):.0%}")
