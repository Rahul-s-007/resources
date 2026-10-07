# Token engineering skills

Companion to [LLM Token Engineering: Prompt Caching, Batch APIs and the Silent Cache Busters](https://rahul.sumbly.tech/blog/llm-token-engineering/).

A main skill plus five focused sub-skills. The main one routes; each sub-skill is small and loads its reference material only when needed.

| Skill | Use it to |
|---|---|
| `token-engineering` | Entry point. Diagnoses the request and routes to a sub-skill |
| `cache-audit` | Find cache busters in prompt-building code |
| `cache-setup` | Add or fix caching for Anthropic, OpenAI or Gemini |
| `prompt-fingerprinting` | Measure stability, find the diverging segment, predict hit rate (includes scripts) |
| `cost-estimate` | Project costs, break-even, long-context thresholds |
| `batch-planner` | Decide and design Batch / Flex workloads |

## Install

```
/plugin marketplace add Rahul-s-007/resources
/plugin install token-engineering@rahul-resources
```

Then ask naturally ("why is my cache hit rate 0?") or invoke directly, e.g. `/token-engineering:cache-audit`.

## Notes

- `cost-estimate` ships no prices: it fetches them from the official provider pricing pages on every run and feeds them to `scripts/estimate.py`. Other skills include limits and defaults dated 2026-10-04; they tell Claude to re-verify before relying on exact values.
- Fingerprint scripts need only Python 3.9+ and the standard library:
  ```bash
  PROMPT_FP_KEY=dev python3 token-engineering/skills/prompt-fingerprinting/scripts/fingerprint.py diff a.json b.json
  ```
