---
name: prompt-fingerprinting
description: Measure prompt stability without logging prompts. Hash each prompt segment and a running prefix hash, find which segment breaks the cache between requests, choose breakpoint positions from stability profiles, and replay logged traffic to predict cache hit rate for 5 min, 30 min and 1 h TTLs. Use when instrumenting an LLM app, debugging cache misses with evidence, or estimating savings before enabling caching.
---

# Prompt fingerprinting

Per request, record for each ordered segment (config, each tool, each system block, each message):

- **segment hash**: that segment alone, says *what* changed.
- **prefix hash**: running chain over all segments so far, mirrors the provider cache. Two requests share a cacheable prefix up to N exactly when prefix hashes at N match.

Scripts (Python 3.9+, stdlib only) are in `scripts/`. Run them rather than rewriting the logic.

## Workflow

1. **Instrument.** Import `fingerprint()` from `scripts/fingerprint.py` and call it on the exact payload right before each API call. Log with timestamp, route, tenant id and the provider's cache usage numbers. Set `PROMPT_FP_KEY` (secret); keyed hashes are safe to store.
2. **Compare two payloads** during debugging:
   ```bash
   PROMPT_FP_KEY=dev python3 scripts/fingerprint.py diff a.json b.json
   ```
   Prints the first diverging segment label.
3. **Profile stability** over a day of logs: count distinct segment hashes per label (and per tenant). 1 per day = cache it; one per tenant = breakpoint here for tenant-shared traffic; one per user or request = move it after the breakpoints. A segment that "should be static" with thousands of hashes is a bug.
4. **First-divergence histogram** across consecutive requests in a conversation. Healthy routes almost never diverge. `system[0]` always diverging = timestamp/ID in system prompt. `msg[0]` after N turns = per-turn truncation. `tool:*` in different order = unsorted tools.
5. **Simulate hit rate** from a JSONL log (`{"ts": <seconds>, "fingerprint": [...]}` per line):
   ```bash
   python3 scripts/simulate.py log.jsonl --min-chars 16384
   ```
   If 5 min and 1 h rates are close, the 1 h write premium is wasted. The result is an upper bound (ignores routing, overflow, eviction).
6. **Reconcile with provider counters:**
   - fingerprints say hit and provider hits: healthy.
   - fingerprints diverge early: your prompt; fix that segment.
   - fingerprints match but provider misses: TTL expiry, minimum length, split workspaces, OpenAI key overflow.

## Rules that matter

- **Do not canonicalize inside the fingerprint.** Hash the bytes actually sent, or you hide the key-order bugs you are hunting. Only strip `cache_control`, which moves by design.
- **Use HMAC, not plain SHA-256**, so short segments like `{"plan":"pro"}` cannot be recovered by guessing.
- Put every cache-key setting in the `config` segment (OpenAI `text.format`, `reasoning.effort`; Anthropic `thinking`, `tool_choice`).
- Additional checks: snapshot test that builds the prompt in two separate processes and asserts identical bytes (catches set-order bugs); alert on per-route hit rate.
