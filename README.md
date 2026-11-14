# RouteMint-Rules

按「你在哪、要访问什么」分流的代理规则。选一个预设 → 扫码 → 填入自己的机场订阅，就能用。

[![build](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml/badge.svg)](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml)

> 每天自动构建发布 · 配置经 mihomo / sing-box 真实加载校验 · 不含任何节点、订阅或密钥

## 先选场景

四张卡片，各配一个默认档位（`ads-light`）。用客户端内置的扫码功能扫二维码
（Shadowrocket：配置 → 右上角 `+` → 扫描二维码），或直接复制下面的地址。

### 🇨🇳 身在中国大陆 · `cn-mainland`

国内直连，境外走代理，AI 单独一组并自动跳过香港/澳门/大陆节点。

<table>
<tr>
<td align="center"><img src="docs/qr/cn-mainland-mihomo.png?v=2" width="150" alt="Clash 扫码导入"><br>Clash / mihomo</td>
<td align="center"><img src="docs/qr/cn-mainland-shadowrocket.png?v=2" width="150" alt="Shadowrocket 扫码导入"><br>Shadowrocket</td>
</tr>
</table>

<https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml>

### 🌍 身在海外 · `overseas`

默认全部直连，只有 AI 与 Netflix / Disney+ / Max / Prime Video 走代理。

<table>
<tr>
<td align="center"><img src="docs/qr/overseas-mihomo.png?v=2" width="150" alt="Clash 扫码导入"><br>Clash / mihomo</td>
<td align="center"><img src="docs/qr/overseas-shadowrocket.png?v=2" width="150" alt="Shadowrocket 扫码导入"><br>Shadowrocket</td>
</tr>
</table>

<https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/mihomo.yaml>

### 🏠 海外华人回国 · `overseas-return`

默认直连，B 站、网易云、爱奇艺、腾讯视频、优酷、QQ 音乐等限区内容走「回国」节点组。

<table>
<tr>
<td align="center"><img src="docs/qr/overseas-return-mihomo.png?v=2" width="150" alt="Clash 扫码导入"><br>Clash / mihomo</td>
<td align="center"><img src="docs/qr/overseas-return-shadowrocket.png?v=2" width="150" alt="Shadowrocket 扫码导入"><br>Shadowrocket</td>
</tr>
</table>

<https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/mihomo.yaml>

### 🪶 大陆极简 · `cn-mainland-lite`

逻辑和 `cn-mainland` 一样，但只留核心分类，规则量约为六成，适合老设备。

<table>
<tr>
<td align="center"><img src="docs/qr/cn-mainland-lite-mihomo.png?v=2" width="150" alt="Clash 扫码导入"><br>Clash / mihomo</td>
<td align="center"><img src="docs/qr/cn-mainland-lite-shadowrocket.png?v=2" width="150" alt="Shadowrocket 扫码导入"><br>Shadowrocket</td>
</tr>
</table>

<https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/mihomo.yaml>

## 其他客户端

以 `cn-mainland` 为例。其他预设把地址里的 `cn-mainland` 换掉即可。

| 客户端 | 扫码 | 地址 |
|---|---|---|
| Surge | <img src="docs/qr/cn-mainland-surge.png?v=2" width="120"> | `.../cn-mainland/ads-light/surge.conf` |
| Loon | <img src="docs/qr/cn-mainland-loon.png?v=2" width="120"> | `.../cn-mainland/ads-light/loon.conf` |
| Quantumult X | 手动导入 | `.../cn-mainland/ads-light/quantumultx.conf`（QX 不支持用 URL 导入整份配置，下载后在 App 里导入） |
| sing-box | <img src="docs/qr/cn-mainland-singbox.png?v=2" width="120"> | `.../cn-mainland/ads-light/singbox.json` |

地址前缀统一是 `https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/`。

二维码会直接以「配置」导入；如果被当成「订阅」，说明扫的是旧码（浏览器/App 缓存了旧图），
请刷新本页，或改用客户端内的扫码入口重新扫一次。

节点怎么填：

- **Clash / mihomo**：改 `proxy-providers.airport.url`；
- **Surge**：改 `Airport = select, policy-path=...` 那一行的 URL；
- **Loon**：改 `[Remote Proxy]` 里 `Airport` 的 URL；
- **Quantumult X**：改 `[server_remote]` 里 `Airport` 那一行；
- **sing-box**：完整配置必须自带出站，文件里用 `127.0.0.1:1080` 的 SOCKS 占位；
  正确用法是把 `route` / `dns` / `rule_set` 合并进你由订阅生成的配置。
- **Shadowrocket**：在 App 里单独添加机场订阅，配置里的 `PROXY` 指当前选中的代理。

## 三档广告

默认 `ads-light`。把地址里的档位换掉即可，不用重新选预设。

| 档位 | 内容 | 链接（以 cn-mainland 为例） |
|---|---|---|
| `ads-off` | 不拦广告 | `.../configs/cn-mainland/ads-off/mihomo.yaml` |
| `ads-light` | 广告 + 常见追踪器（默认） | `.../configs/cn-mainland/ads-light/mihomo.yaml` |
| `ads-strict` | 再加恶意域名 | `.../configs/cn-mainland/ads-strict/mihomo.yaml` |

## 常见问题

**扫码后被当成订阅了？**
Shadowrocket 需要 `shadowrocket://config/add/...` 这种协议才会按配置导入，普通网址会被当成
节点订阅。本页二维码已经是配置协议；如果你之前存过旧码，重新扫一次即可。

**扫码后没有节点？**
本仓库只发规则，不提供节点。请在客户端里添加你自己的机场订阅，配置里只有一处占位符要改。

**AI 为什么要单独一组？**
OpenAI / Anthropic / Gemini 按出口 IP 判断地区，香港、澳门、大陆节点会被拒绝，所以 AI 组会
按节点名先把这些地区排除掉，再在剩下的节点里挑最快的。细节见[规则体系](docs/architecture.md)。

**链接打开是旧规则？**
jsDelivr 的分支缓存最长 12 小时（发布后会自动刷新变更文件）。着急就把地址前缀换成
`https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/`。

**会不会拖慢手机？**
规则集以 mihomo 二进制格式 `.mrs` 分发，配里只有二十来条 `RULE-SET` 引用，不是几万行文本；
规则本身做了后缀压缩与 IP 合并。最大的一类是广告（约 3.7 万条），不需要就切 `ads-off`。
各分类实际条数见[分类表](docs/architecture.md#分类表)。

**想加/删某个域名？**
用 Issue 模板「规则修改请求」，写清域名、期望分类、理由和验证方式。

**支持哪些客户端？**
mihomo / Clash、Shadowrocket、Surge、Loon、Quantumult X、sing-box。节点名过滤只有 mihomo
能完全做到（见[规则体系](docs/architecture.md#客户端能力差异)）。

## 更多

- [规则体系与分类表](docs/architecture.md)
- [质量校验与发布流程](docs/quality.md)
- [开发、数据来源与已知限制](docs/development.md)
- [第三方许可证](THIRD_PARTY_NOTICES.md)
- [变更日志](CHANGELOG.md)
