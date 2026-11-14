# RouteMint-Rules

Scene-based routing rules for mihomo / Clash, Shadowrocket, Sing-box, Surge, Loon and
Quantumult X. One rule source, four ready-to-use presets: pick one, paste your airport
subscription, done.

## Which preset?

| Where you are | What you need | Preset |
|---|---|---|
| Mainland China | CN sites direct; foreign services, AI and streaming proxied | `cn-mainland` |
| Mainland China | same logic, minimal rule count for old devices | `cn-mainland-lite` |
| Overseas | direct by default; only AI and some streaming proxied | `overseas` |
| Overseas | access CN-only content (Bilibili region lock, NetEase Music, ...) | `overseas-return` |

Presets share the same categories; they differ only in policy groups, rule order and the
FINAL fallback:

| Preset | FINAL order | Meaning |
|---|---|---|
| `cn-mainland`, `cn-mainland-lite` | proxy → direct | unknown domains go through the proxy |
| `overseas`, `overseas-return` | direct → proxy | unknown domains stay direct |

## Quick start

mihomo (Clash Verge Rev, Mihomo Party, ...):

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml
```

One-click:

```text
clash://install-config?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fzoran-sid%2FRouteMint-Rules%40release%2Fconfigs%2Fcn-mainland%2Fads-light%2Fmihomo.yaml
```

Then replace `proxy-providers.airport.url` with your own subscription. The repository
contains no node addresses, subscriptions or secrets — only placeholders.

Shadowrocket — add this URL as a configuration:

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf
```

Swap `cn-mainland` for any preset and `ads-light` for `ads-off` / `ads-strict` to pick
another combination. Rule sets are also published individually under `rules/<category>/`
as `.mrs`, `.yaml` and `.list`.

## Design notes

- **Rule order is the routing contract**: private → reject → ai → streaming →
  cn-region-locked → dev → game → telegram → apple/microsoft/google → proxy → cn →
  cn-ip → FINAL.
- **AI group excludes HK / MO / CN nodes** by regex, because OpenAI, Anthropic and Gemini
  reject those exit IPs. Two filters (`filter` + `exclude-filter`) so a node name cannot
  slip through both.
- **DNS leak protection**: fake-ip mode, `nameserver-policy` with `rule-set:` keys, and
  foreign DoH forced through the proxy group. Only `cn` / `private` resolve domestically.
- **Lean output**: `.mrs` binary rule sets, suffix compaction (a `.cn` suffix removes
  thousands of entries), IP collapsing, per-category budgets, and a 30% drop guard.
- **`cn-mainland-lite`** skips categories whose policy equals FINAL, plus `proxy` and
  `cn-ip6`: roughly 60% of the standard preset, ~12k rules with `ads-off`.

## Develop

```bash
uv sync --frozen
uv run python -m builder check
uv run python -m builder build --mihomo-bin /path/to/mihomo --validate
uv run pytest
```

Licensing of upstream data: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
