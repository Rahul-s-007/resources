---
name: token-engineering
description: Entry point for reducing LLM API spend. Use when the user mentions LLM costs, token bills, prompt caching, cache hit rate, batch API, flex tier, long-context pricing, or asks to "optimize" or "audit" prompts for Anthropic, OpenAI or Gemini. Diagnoses what they need and routes to the right sub-skill.
---

# Token engineering

Most LLM bills are high because the same tokens are paid for repeatedly, not because of the model choice. Two levers: **prompt caching** (cached input costs about 10% of normal) and **batch/flex** (about 50% off for work that can wait).

Core rule behind almost everything: caches match an **exact, byte-identical prefix** (attention is causal). **Stable content first, volatile content last.**

## Route the request

Pick the sub-skill that matches, invoke it, and do not re-derive its content here.

| The user wants to... | Use |
|---|---|
| Find why cache hit rate is low, or review code that builds prompts | `token-engineering:cache-audit` |
| Turn caching on / fix breakpoints, TTL, `prompt_cache_key` for a provider | `token-engineering:cache-setup` |
| Measure stability and predict hit rate from real traffic | `token-engineering:prompt-fingerprinting` |
| Estimate or compare costs, check long-context thresholds | `token-engineering:cost-estimate` |
| Decide if a workload fits batch or flex, and design it | `token-engineering:batch-planner` |

If the request is broad ("cut my LLM bill"), run in this order, stopping when the user has enough:

1. `cost-estimate` on current usage, to find where money goes (input vs output, which route).
2. `cache-audit` on the code that builds the largest repeated prefixes.
3. `cache-setup` for routes with no caching or wrong breakpoints.
4. `batch-planner` for anything nobody is waiting on.
5. `prompt-fingerprinting` to verify the gains and catch regressions.

## Ground rules

- Prices change often and are never hardcoded: `cost-estimate` fetches them live from the provider pricing pages. Limits and defaults in other references are dated snapshots; confirm against the provider docs and say which date a number is from.
- Ask which provider and model before advising: minimum cacheable length, TTLs and defaults differ per provider and per model.
- Never ask for or log raw prompts or API keys. Fingerprints use keyed hashes for this reason.
- Prefer measurement over guessing: the provider's usage fields (`cache_read_input_tokens`, `cached_tokens`, `usage_metadata`) are ground truth.

Full write-up: https://rahul.sumbly.tech/blog/llm-token-engineering/
