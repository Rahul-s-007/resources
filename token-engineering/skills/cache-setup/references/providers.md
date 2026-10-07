# Provider caching reference

Snapshot from the provider docs as of 2026-10-04. Verify before relying on exact values.

| | Anthropic | OpenAI | Gemini |
|---|---|---|---|
| Default | Off; opt in with `cache_control` | On, implicit | On, implicit (2.5+) |
| Explicit | `cache_control` breakpoints (max 4) or one top-level `cache_control` | GPT-5.6+: `prompt_cache_options` + `prompt_cache_breakpoint` (max 4 writes/request) | `cachedContents` named cache |
| TTL | 5 min (default) or 1 h, refreshed on hit | 5.6+: `ttl: "30m"`; older: ~5-10 min idle up to 1 h, or `prompt_cache_retention: "24h"` | Explicit: default 1 h, adjustable. Implicit: unspecified |
| Min prefix | 512 to 4,096 tokens by model | 1,024 | Implicit 2,048 (2.5) / 4,096 (3.x) |

## Anthropic

- Render order: tools, system, messages. A breakpoint on the last system block caches tools + system.
- Minimums: Opus 5 512; Sonnet 5 / Opus 4.8 1,024; Opus 4.7 2,048; Opus 4.6 and Haiku 4.5 4,096. Too short = silently not cached.
- Caches are isolated per workspace.

```python
system=[{
    "type": "text",
    "text": LARGE_STABLE_INSTRUCTIONS,
    "cache_control": {"type": "ephemeral"},   # add "ttl": "1h" for 1 hour
}],
messages=[{"role": "user", "content": user_question}],  # volatile part after the breakpoint
# usage: cache_creation_input_tokens, cache_read_input_tokens, input_tokens
```

Multi-turn: use the top-level automatic `cache_control` so the breakpoint advances, or move a message-level breakpoint to the last block each turn. Mind the 20-block lookback.

## OpenAI

- Cache key covers: `model`, `tools`, `parallel_tool_calls`, `text.format` schema, `reasoning.effort`, `text.verbosity`.
- Routing uses a hash of the first prompt tokens plus `prompt_cache_key`. Pre-5.6: ~15 RPM per prefix+key before overflow; shard deterministically (`f"app:{hash(tenant) % 8}"`). 5.6+: routing is automatic; the key mainly isolates tenants.
- Key by what shares a prefix, never by request ID.

```python
resp = client.responses.create(
    model="gpt-5.5",
    instructions=STABLE_INSTRUCTIONS,
    input=user_message,
    prompt_cache_key=f"kb-assistant:{shard}",
    prompt_cache_retention="24h",     # supported on several models
)
# usage.input_tokens_details.cached_tokens (and cache_write_tokens on newer models)
```

## Gemini

- Implicit: put large common content first; send similar-prefix requests close together. No savings guarantee.
- Explicit: three cost parts (cached reads, storage per token-hour, normal uncached tokens).

```python
cache = client.caches.create(
    model="gemini-2.5-pro",
    config=types.CreateCachedContentConfig(
        system_instruction="...", contents=[big_doc], ttl="3600s"),
)
resp = client.models.generate_content(
    model="gemini-2.5-pro", contents=question,
    config=types.GenerateContentConfig(cached_content=cache.name))
```

## Sources
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://ai.google.dev/gemini-api/docs/generate-content/caching
