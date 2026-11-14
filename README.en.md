# RouteMint-Rules

Scene-based routing rules for mihomo / Clash, Shadowrocket, Surge, Loon, Quantumult X and
sing-box. Pick a preset, scan the code, paste your own airport subscription.

[![build](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml/badge.svg)](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml)

> Rebuilt daily · every mihomo and sing-box config is load-tested · no nodes, no keys

## Pick a preset

| Preset | Who it is for | Import |
|---|---|---|
| `cn-mainland` | mainland China: CN direct, foreign proxied, AI on its own group | <img src="docs/qr/cn-mainland-mihomo.png" width="120"> |
| `overseas` | abroad: direct by default; only AI, TikTok and some streaming proxied | <img src="docs/qr/overseas-mihomo.png" width="120"> |
| `overseas-return` | abroad, needs CN region-locked content via a return node | <img src="docs/qr/overseas-return-mihomo.png" width="120"> |
| `cn-mainland-lite` | mainland China, minimal rule count for old devices | <img src="docs/qr/cn-mainland-lite-mihomo.png" width="120"> |

Config URL prefix: `https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/`
(`<preset>/<ads-off|ads-light|ads-strict>/<client>`).

## Clients

| Client | File | Node setup |
|---|---|---|
| Clash / mihomo | `mihomo.conf` | edit `proxy-providers.airport.url` |
| Shadowrocket | `shadowrocket.conf` | add your subscription in the app |
| Surge | `surge.conf` | edit the `policy-path=` URL |
| Loon | `loon.conf` | edit `[Remote Proxy] Airport` |
| Quantumult X | `quantumultx.conf` | edit `[server_remote] Airport` |
| sing-box | `singbox.conf` | merge `route` / `dns` / `rule_set` into your own outbounds |

Only mihomo can filter nodes by name (the AI group excludes HK / MO / CN nodes); see
[docs/architecture.md](docs/architecture.md) for the per-client capability table.

## Docs

- [Rule order, categories, DNS](docs/architecture.md)
- [Quality gates and publishing](docs/quality.md)
- [Development, data sources, limitations](docs/development.md)
- [Third-party licences](THIRD_PARTY_NOTICES.md)
