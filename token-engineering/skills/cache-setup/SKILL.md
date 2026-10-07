---
name: cache-setup
description: Implement or fix prompt caching for a specific provider. Covers Anthropic cache_control breakpoints and TTL, OpenAI implicit caching, prompt_cache_key and prompt_cache_retention, and Gemini implicit vs explicit cachedContents. Use when adding caching to an LLM integration, choosing breakpoint placement or TTL, or when caching is on but cached token counts stay at zero.
---

# Cache setup

Provider-specific syntax lives in [references/providers.md](references/providers.md). Read only the section for the provider in use.

## Procedure

1. **Identify provider + model.** Defaults differ: Anthropic is opt-in; OpenAI and Gemini 2.5+ cache implicitly.
2. **Check the minimum prefix** for that model. Below it, caching silently does nothing.
3. **Order the request** stable-to-volatile: tools, static system, per-tenant, per-user, per-request. See `token-engineering:cache-audit` if the prompt builder needs cleanup first.
4. **Place breakpoints** (explicit modes) after the last segment shared by the traffic you want to hit. Never on the per-request tail.
5. **Choose TTL** from traffic gaps: 5 min pays off after one read, 1 h after two (Anthropic). If requests arrive less often than the TTL, pick the longer TTL. Batches sharing context should use 1 h.
6. **Add observability in the same change:** log the provider's cache usage fields on every call and the input token count. Without this nobody will notice a regression.
7. **Verify:** send the same request twice within the TTL; the second must report cached/read tokens roughly equal to the prefix size.

## Decision guide

- Need predictability and control: use explicit caching (Anthropic breakpoints, OpenAI 5.6+ breakpoints, Gemini `cachedContents`).
- Want zero code and accept variance: rely on implicit (OpenAI, Gemini).
- Gemini explicit storage is billed per token-hour: do not set a long TTL on a cache nobody reads.
- OpenAI pre-5.6 high traffic: shard `prompt_cache_key` deterministically to stay near 15 RPM per key.

Current prices (write premiums, read rates) come from `token-engineering:cost-estimate`, which fetches them live.
