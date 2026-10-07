# Where to get prices, and what to extract

## Official pricing pages (fetch these every run)

| Provider | Page | Also check |
|---|---|---|
| Anthropic | https://platform.claude.com/docs/en/about-claude/pricing | batch and caching sections on the same page |
| OpenAI | https://developers.openai.com/api/docs/pricing | batch and flex tables, long-context notes |
| Google | https://ai.google.dev/gemini-api/docs/pricing | context caching storage price, batch and flex columns |

If these URLs have moved, search for the provider's current "API pricing" page (WebSearch) and prefer the provider's own domain. Do not use third-party price aggregators as the source.

## Fetch fallbacks, in order

1. WebFetch the page with a prompt asking for the exact table rows for the requested models, per 1M tokens, including cache read/write/storage, batch, flex and long-context columns.
2. If the content is empty or truncated, try the page's Markdown/raw form (append `.md` or fetch the docs source) or fetch the specific section anchor.
3. Browser tool (built-in browser or Chrome) to read the rendered page.
4. Ask the user to paste the table. Never fall back to remembered prices.

## Fields to extract per model (USD per 1M tokens)

| Field | Meaning |
|---|---|
| `input` | standard input |
| `output` | standard output |
| `cache_read` | cached input read |
| `cache_write_5m`, `cache_write_1h` | cache write per TTL tier (Anthropic style); `null` if no write fee |
| `cache_write` | single write price if the provider has one (OpenAI 5.6+ style), else `null` |
| `cache_storage_per_hour` | storage per 1M tokens per hour (Gemini explicit), else `null` |
| `batch_discount` | fraction off for batch, e.g. 0.5 |
| `batch_cache_stacks` | `true` if the page says batch and cache discounts combine, `false` if cached tokens are billed as non-batch, `null` if unclear |
| `long_context` | `{threshold, input_mult, cached_mult, output_mult}` or `null` if none |

## Price object schema

```json
{
  "provider": "anthropic",
  "model": "<model id as on the page>",
  "source": "<url>",
  "as_of": "<YYYY-MM-DD fetch date>",
  "input": 0, "output": 0,
  "cache_read": 0,
  "cache_write_5m": null, "cache_write_1h": null, "cache_write": null,
  "cache_storage_per_hour": null,
  "batch_discount": 0.5,
  "batch_cache_stacks": null,
  "long_context": null,
  "notes": "promotions, scheduled changes, anything uncertain"
}
```

Zeros above are placeholders for the schema only; fill every value from the fetched page.

## Workload object

```json
{
  "requests": 0,
  "stable_tokens": 0,
  "volatile_tokens": 0,
  "output_tokens": 0,
  "hit_rate": 0.0,
  "ttl": "5m",
  "batch_share": 0.0,
  "period_hours": 1
}
```

`requests` is the total for the period; `period_hours` is used for storage cost (Gemini explicit caching).
