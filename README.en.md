# RouteMint-Rules

Scene-based routing rules for mihomo / Clash, Shadowrocket, Sing-box, Surge, Loon and
Quantumult X. One rule source, several ready-to-use presets: pick one, paste your airport
subscription, done.

> Status: stage 1 (MVP). Only `cn-mainland` plus mihomo and Shadowrocket configs are
> shipped so far; the other presets and clients follow.

## Which preset?

| Where you are | What you need | Preset | Status |
|---|---|---|---|
| Mainland China | CN sites direct, everything foreign + AI via proxy | `cn-mainland` | available |
| Mainland China | same, but minimal rules for low-end phones | `cn-mainland-lite` | stage 2 |
| Overseas | direct by default, only AI / geo-locked streaming proxied | `overseas` | stage 2 |
| Overseas | access CN-only content (Bilibili region lock, NetEase Music, ...) | `overseas-return` | stage 2 |

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
never contains node addresses, subscription links or secrets — only placeholders.

Shadowrocket: add the following URL as a configuration (Settings → Config → Add):

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf
```

Ad tiers: replace `ads-light` with `ads-off` or `ads-strict` in the URL. Rule sets are
also published individually under `rules/<category>/` as `.mrs`, `.yaml` and `.list`.

## Design notes

- **Rule order is the routing contract**: private → reject → ai → streaming →
  cn-region-locked → dev → game → telegram → apple/microsoft → proxy → cn → cn-ip → FINAL.
- **AI group excludes HK / MO / CN nodes** by regex, because OpenAI, Anthropic and Gemini
  reject those exit IPs. Two filters (`filter` + `exclude-filter`) so a node name cannot
  slip through both.
- **DNS leak protection**: fake-ip mode, `nameserver-policy` with `rule-set:` keys, and
  foreign DoH forced through the proxy group. Only `cn` / `private` resolve domestically.
- **Lean output**: `.mrs` binary rule sets, suffix compaction, IP collapsing, per-category
  budgets, and a 30% drop guard against broken upstreams.

## Develop

```bash
uv sync --frozen
uv run python -m builder check
uv run python -m builder build --mihomo-bin /path/to/mihomo --validate
uv run pytest
```

Licensing of upstream data: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
