---
name: cache-audit
description: Audit code that builds LLM prompts for silent prompt-cache busters such as timestamps or IDs in the system prompt, unsorted JSON, unstable tool order, per-user content before shared content, history truncation, non-deterministic RAG order, and cache-key parameter changes. Use when cache hit rate is low, cached tokens read as 0, or when reviewing prompt-building code for Anthropic, OpenAI or Gemini.
---

# Cache audit

A cache hit needs an identical prefix. Find every place a byte before the shared content can change between requests.

## Procedure

1. **Locate prompt construction.** Search for where `system`, `instructions`, `tools`, `messages`, `contents` are assembled. Identify the provider and model (minimum cacheable length and defaults depend on them).
2. **Write down the render order** as the provider sees it (Anthropic: tools, system, messages). Mark each segment as: constant, per-tenant, per-user, or per-request.
3. **Check against the catalog** in [references/cache-busters.md](references/cache-busters.md). Each entry has a grep-able signature and a fix.
4. **Check ordering.** Anything per-request that sits before something constant is a bug. Fix by moving it after the last shared segment.
5. **Check non-prompt causes** (TTL gaps, below minimum length, split workspaces, breakpoint on the unique tail). These are not code bugs but explain misses with a clean prompt.
6. **Report** findings ranked by impact (size of the prefix they invalidate x request volume), each with file:line, why it busts the cache, and the exact fix.

## Quick grep signatures

```bash
grep -rnE "datetime\.(now|utcnow)|date\.today|time\.time\(|new Date\(|Date\.now" <prompt-code>
grep -rnE "uuid|request_id|trace_id|nonce|random" <prompt-code>
grep -rnE "json\.dumps\(" <prompt-code>          # missing sort_keys / separators?
grep -rnE "JSON\.stringify\(" <prompt-code>      # integer-like keys reorder
grep -rnE "for .* in .*set\(|list\(set" <prompt-code>
```

## Verify, don't assume

Before declaring a prompt "fine", confirm with the response usage fields that the cache actually hits on the second identical request. For deeper evidence use `token-engineering:prompt-fingerprinting`.

## Output format

For each finding: **severity**, **location**, **what changes between requests**, **fix**. End with the single highest-value change.
