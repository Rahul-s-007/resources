# Cache buster catalog

Every item reduces to: some byte in the prefix changed.

## 1. Timestamps / dates at the top
`datetime.now()` busts every call. `date.today()` busts daily at midnight UTC (shows up as a daily cost spike). Also time-of-day greetings and countdowns.
**Fix:** keep the system prompt constant; append `(Current date: ...)` to the user turn, after the breakpoint.

## 2. Request IDs, trace IDs, nonces, random seeds in prompt text
**Fix:** move to request metadata or headers.

## 3. Non-deterministic JSON serialization
- Python dicts keep insertion order: merges (`{**a, **b}`), DB column order, ORM `to_dict()` changes.
- JS objects order integer-like keys first (`{"b":1,"10":2}` serializes `10` first).
- Python `set` iteration differs across processes (hash randomization). Use `sorted(...)`.
- Separators and escaping: `json.dumps` default `", "` vs JS compact; `indent`; `ensure_ascii`; float formatting.
- Go: map keys sorted, but struct field order follows declaration.

**Fix:** `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`; one shared serializer for every service.

## 4. Tool definitions
Tools render first, so any change invalidates everything.
- Registry iteration order varies: sort tools by name.
- Different tool sets per user/plan: use one superset; enforce permissions in the handler.
- Schemas generated from Pydantic/Zod change on library upgrades (property order, `title`, `$defs`).
- Adding/removing tools mid-conversation or per "mode".
- Interpolated values in descriptions.

## 5. Conditional sections in the system prompt
N flags give 2^N prefixes, each colder. Order by change frequency: universal, per-tenant, per-user, per-request. Breakpoint at each boundary (Anthropic: max 4). Personalization ("helping Priya from Acme") at the top makes the cache per-user.

## 6. Question before document
`[instructions][question][50K doc]` never reuses the doc. Use `[instructions][doc][question]`.

## 7. Rewriting conversation history
- Sliding-window truncation one message per turn changes position 0 every turn. Truncate in big, infrequent chunks or summarize once.
- Re-templating, whitespace normalization, or PII redaction of old turns.
- Injecting then removing reminder messages.
- Re-serializing tool results differently on replay.

## 8. Non-deterministic retrieval
Tie-breaking and ANN variance reorder the same top-k. Sort chunks by (doc id, chunk index) after choosing top-k. Place retrieved context after static instructions.

## 9. Invisible byte differences
Trailing whitespace/newline from templates, `\r\n` vs `\n`, Unicode NFC vs NFD, smart quotes, prompt files changed by a deploy.

## 10. Re-encoded images and files
Resizing, recompressing, or re-encoding yields different bytes. Encode once; store bytes or a file ID.

## 11. "Harmless" parameter changes
- Model is part of the key; cascades split the cache.
- OpenAI: `tools`, `parallel_tool_calls`, `text.format` schema, `reasoning.effort`, `text.verbosity` are in the key.
- Anthropic: changing thinking/effort invalidates the messages cache; changing `tool_choice` keeps tools+system but invalidates messages. Pin per route.

## 12. Misses with a clean prompt
- Prefix below the model's minimum cacheable length (silent: `cache_creation_input_tokens: 0`).
- TTL gap: traffic every 7 min with a 5 min TTL = 0% hits. Use longer TTL or a keep-alive.
- Split traffic: separate Anthropic workspaces (caches are per workspace); OpenAI pre-5.6 keys above ~15 RPM per prefix+key overflow to other machines.
- Breakpoint on the unique tail: pays the write premium, never reads. Put it at the end of the shared part.
- Anthropic 20-block lookback: a turn appending more than 20 blocks can miss the previous entry.
