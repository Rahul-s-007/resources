---
name: batch-planner
description: Decide whether an LLM workload fits Batch API or Flex tier pricing (about 50% off) and design it correctly for Anthropic, OpenAI or Gemini. Covers custom_id joins, out-of-order results, partial expiry and resubmission, async validation, batch plus caching, and flex timeouts and fallbacks. Use when someone has bulk, offline, nightly, eval or backfill LLM work, or wants to cut cost on non-interactive calls.
---

# Batch planner

Batch is half price because the provider can run it in idle capacity within a 24 h window. You are selling flexibility.

## 1. Fit check

Good: offline evals, classification/extraction over stored data, embeddings and synthetic data, nightly reports, moderation backfills, LLM-as-judge.
Bad: anything a user waits on; agent loops where step N+1 needs step N; deadlines shorter than the expiry window; jobs so small the file handling costs more than the 50%.
Middle ground: **Flex** (OpenAI, Google) is a normal synchronous call with `service_tier: "flex"` at roughly batch prices, but sheddable. Good for background agents tolerating minutes of delay.

## 2. Limits to design around

| | Anthropic | OpenAI | Google |
|---|---|---|---|
| Size | 100,000 requests or 256 MB | 50,000 requests or 200 MB | 20 MB inline / 2 GB file |
| Window | most within 1 h; expires 24 h | 24 h | target 24 h; expires 48 h |
| Results kept | 29 days | n/a | 6 weeks |

Snapshot from 2026-10-04; verify against the docs.

## 3. Design checklist

1. **Meaningful `custom_id`** (`ticket-48213`, not `req-7`). Results arrive out of order at all three providers; always join on it.
2. **Validate synchronously first.** Anthropic validates `params` during processing, so a typo in request 40,000 surfaces hours later. Send one request through the normal API first.
3. **Plan for partial results.** Expired requests come back as `expired` (Anthropic, not billed) or `batch_expired` (OpenAI). Collect finished ones, resubmit the rest.
4. **Chunk to the limits** and make submission idempotent (key by custom_id, skip ones already done).
5. **Caching inside a batch is best-effort** (concurrent, any order). Use the 1 h TTL for shared context on Anthropic. Discounts multiply on Anthropic; for OpenAI and Gemini confirm the cached-batch rate for the chosen model, ideally with a small batch and the invoice.
6. **Flex:** raise client timeouts (OpenAI about 15 min, Google 10+), handle 429/503 with retry and backoff, and fall back to the standard tier when latency matters.
7. **Poll sensibly** (minutes, not seconds) and persist batch ids so a crashed worker can resume.

## Output

Give the user: fit verdict, chosen mode (batch vs flex), request/chunk layout, the `custom_id` scheme, failure/resubmit flow, and a cost comparison via `token-engineering:cost-estimate`.
