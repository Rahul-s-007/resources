# Resources

Companion material for posts on [rahul.sumbly.tech](https://rahul.sumbly.tech). One folder per post, named after the post slug. Each folder is self-contained and holds whatever that post needs (skills, code, data, notebooks).

| Post | Folder | What's inside |
|---|---|---|
| [LLM Token Engineering](https://rahul.sumbly.tech/blog/llm-token-engineering/) | [`token-engineering/`](token-engineering) | Claude Code plugin: 6 skills for cutting LLM costs, plus fingerprinting scripts |

## Install the plugins in Claude Code

```
/plugin marketplace add Rahul-s-007/resources
/plugin install token-engineering@rahul-resources
```

Or copy a single skill folder (for example `token-engineering/skills/cache-audit`) into `~/.claude/skills/` or your project's `.claude/skills/`.

## Layout

```
.claude-plugin/marketplace.json   lists the installable plugins
<post-slug>/
  README.md
  .claude-plugin/plugin.json      only if the folder ships a plugin
  skills/ code/ data/ ...         whatever the post needs
```

To add a post: create `<post-slug>/`, add its README, and add a row above. If it ships a plugin, also add it to `.claude-plugin/marketplace.json`.
