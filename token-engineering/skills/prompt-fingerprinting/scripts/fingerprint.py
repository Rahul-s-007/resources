#!/usr/bin/env python3
"""Keyed-hash fingerprints of an LLM request, segment by segment.

Library:
    from fingerprint import fingerprint, first_divergence
CLI:
    PROMPT_FP_KEY=secret python3 fingerprint.py show payload.json
    PROMPT_FP_KEY=secret python3 fingerprint.py diff a.json b.json

Handles Anthropic (system/messages), OpenAI Responses (instructions/input)
and Gemini (system_instruction/contents) request shapes.
"""
import hashlib
import hmac
import json
import os
import sys

CONFIG_KEYS = (
    "model", "thinking", "output_config", "tool_choice",          # Anthropic
    "parallel_tool_calls", "text", "reasoning", "prompt_cache_key",  # OpenAI
    "generation_config", "tool_config",                           # Gemini
)


def _key() -> bytes:
    key = os.environ.get("PROMPT_FP_KEY")
    if not key:
        sys.exit("Set PROMPT_FP_KEY (any secret string) before fingerprinting.")
    return key.encode()


def _h(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()[:16]


def _strip_markers(obj):
    # cache_control moves forward every turn by design; it is not a cache buster.
    if isinstance(obj, dict):
        return {k: _strip_markers(v) for k, v in obj.items() if k != "cache_control"}
    if isinstance(obj, list):
        return [_strip_markers(v) for v in obj]
    return obj


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def segments_for(payload: dict) -> list:
    """Ordered (label, value) pairs in provider render order."""
    segs = [("config", {k: payload[k] for k in CONFIG_KEYS if k in payload})]
    for i, t in enumerate(_as_list(payload.get("tools"))):
        name = t.get("name") if isinstance(t, dict) else None
        segs.append((f"tool:{name or i}", t))
    for field in ("system", "instructions", "system_instruction"):
        for i, b in enumerate(_as_list(payload.get(field))):
            segs.append((f"{field}[{i}]", b))
    for field in ("messages", "input", "contents"):
        for i, m in enumerate(_as_list(payload.get(field))):
            role = m.get("role", "") if isinstance(m, dict) else ""
            segs.append((f"{field}[{i}]:{role}" if role else f"{field}[{i}]", m))
    return segs


def fingerprint(payload: dict, key: bytes = None) -> list:
    key = key or _key()
    chain, out = "", []
    for label, value in segments_for(payload):
        value = _strip_markers(value)
        # Hash what goes over the wire: plain json.dumps, no sorting.
        raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        seg = _h(raw.encode("utf-8"), key)
        chain = _h((chain + seg).encode(), key)
        out.append({"label": label, "seg": seg, "prefix": chain, "chars": len(raw)})
    return out


def first_divergence(prev: list, curr: list):
    """Label of the first segment where the prefixes differ, or None if curr extends prev."""
    for a, b in zip(prev, curr):
        if a["prefix"] != b["prefix"]:
            return b["label"]
    return None


def _load(path):
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "show":
        for s in fingerprint(_load(sys.argv[2])):
            print(f'{s["label"]:<28} seg={s["seg"]} prefix={s["prefix"]} chars={s["chars"]}')
    elif len(sys.argv) == 4 and sys.argv[1] == "diff":
        a, b = fingerprint(_load(sys.argv[2])), fingerprint(_load(sys.argv[3]))
        d = first_divergence(a, b)
        print("identical prefix" if d is None and len(a) == len(b) else
              "second extends first" if d is None else f"first divergence at: {d}")
    else:
        sys.exit(__doc__)
