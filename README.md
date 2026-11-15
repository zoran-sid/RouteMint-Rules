# RouteMint-Rules

按使用地区和访问目标选择分流配置，提供 **mihomo、Shadowrocket、Surge、Loon、Quantumult X、sing-box** 六种格式。

[![build](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml/badge.svg)](https://github.com/zoran-sid/RouteMint-Rules/actions/workflows/build.yml)

先选择场景，再选择客户端。下方地址用于**分流配置订阅**，节点由你现有的服务提供。
Shadowrocket 可直接在「配置」中添加地址；其余客户端按[导入说明](#导入与更新)绑定自己的节点。

使用步骤：**选择下方场景 → 找到自己的客户端 → 复制配置地址或扫描二维码 → 按导入说明绑定节点并启用。**
规则每天自动更新，后续继续使用同一地址。

## 选择场景

| 场景 | 使用位置 | 直连 | 代理 | 未匹配流量 |
|---|---|---|---|---|
| `cn-mainland` | 中国内地 | 国内服务、局域网、游戏与网盘下载 | Google、YouTube、AI 和其他境外服务 | 代理（白名单模式） |
| `overseas` | 海外，部分服务受地区限制 | Google、YouTube、国内服务及普通网站 | AI、Netflix、Disney+、HBO/Max、Prime Video、TikTok、游戏商店 | 直连 |
| `overseas-return` | 海外，访问国内限区内容 | 普通网站、Google、YouTube | 国内限区影音（回国组）、游戏商店（普通代理组） | 直连 |

回国模式将已列出的限区媒体交给回国节点，游戏商店交给普通代理节点；微信、邮箱、购物等继续直连。需要全量国内服务回国时，可在自己的配置中把 `cn` / `cn-ip` / `cn-ip6` 改为回国组。

## 订阅地址与二维码

以下均为默认 `ads-light` 档。点击「订阅配置」可获取完整地址；点击「二维码」可打开大图。
二维码与同一行地址对应同一份配置。Quantumult X 扫码打开下载地址，再手动导入；其他二维码使用客户端配置导入协议，是否能唤起取决于 App 和系统。

### 中国内地：国内直连，境外代理

国内域名与中国大陆 IP 直连，其他请求交给代理。AI 与流媒体保留独立策略组。

| 客户端 | 配置地址 | 二维码 |
|---|---|---|
| mihomo / Clash Meta 内核 | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.conf) | [二维码](docs/qr/cn-mainland-mihomo.png) |
| Shadowrocket | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/RouteMint-CN-Whitelist-ads-light.conf) | [二维码](docs/qr/cn-mainland-shadowrocket.png) |
| Surge | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/surge.conf) | [二维码](docs/qr/cn-mainland-surge.png) |
| Loon | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/loon.conf) | [二维码](docs/qr/cn-mainland-loon.png) |
| Quantumult X | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/quantumultx.conf) | [二维码](docs/qr/cn-mainland-quantumultx.png) |
| sing-box | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/singbox.conf) | [二维码](docs/qr/cn-mainland-singbox.png) |

<table>
<tr>
<td align="center"><img src="docs/qr/cn-mainland-mihomo.png?v=4" width="140" alt="cn-mainland mihomo / Clash Meta 内核 配置二维码"><br>mihomo / Clash Meta 内核</td>
<td align="center"><img src="docs/qr/cn-mainland-shadowrocket.png?v=5" width="140" alt="cn-mainland Shadowrocket 配置二维码"><br>Shadowrocket</td>
<td align="center"><img src="docs/qr/cn-mainland-surge.png?v=4" width="140" alt="cn-mainland Surge 配置二维码"><br>Surge</td>
<td align="center"><img src="docs/qr/cn-mainland-loon.png?v=4" width="140" alt="cn-mainland Loon 配置二维码"><br>Loon</td>
<td align="center"><img src="docs/qr/cn-mainland-quantumultx.png?v=4" width="140" alt="cn-mainland Quantumult X 配置二维码"><br>Quantumult X</td>
<td align="center"><img src="docs/qr/cn-mainland-singbox.png?v=4" width="140" alt="cn-mainland sing-box 配置二维码"><br>sing-box</td>
</tr>
</table>

### 海外：Google / YouTube 直连，AI 与流媒体代理

AI 优先于 Google 大类匹配。Netflix、Disney+、HBO/Max、Prime Video 分别选出口；在 mihomo、Surge、Loon、sing-box 中可继承固定的流媒体出口；Shadowrocket 和 Quantumult X 按下方说明绑定节点。

| 客户端 | 配置地址 | 二维码 |
|---|---|---|
| mihomo / Clash Meta 内核 | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/mihomo.conf) | [二维码](docs/qr/overseas-mihomo.png) |
| Shadowrocket | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/RouteMint-Overseas-AI-Media-ads-light.conf) | [二维码](docs/qr/overseas-shadowrocket.png) |
| Surge | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/surge.conf) | [二维码](docs/qr/overseas-surge.png) |
| Loon | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/loon.conf) | [二维码](docs/qr/overseas-loon.png) |
| Quantumult X | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/quantumultx.conf) | [二维码](docs/qr/overseas-quantumultx.png) |
| sing-box | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/singbox.conf) | [二维码](docs/qr/overseas-singbox.png) |

<table>
<tr>
<td align="center"><img src="docs/qr/overseas-mihomo.png?v=4" width="140" alt="overseas mihomo / Clash Meta 内核 配置二维码"><br>mihomo / Clash Meta 内核</td>
<td align="center"><img src="docs/qr/overseas-shadowrocket.png?v=5" width="140" alt="overseas Shadowrocket 配置二维码"><br>Shadowrocket</td>
<td align="center"><img src="docs/qr/overseas-surge.png?v=4" width="140" alt="overseas Surge 配置二维码"><br>Surge</td>
<td align="center"><img src="docs/qr/overseas-loon.png?v=4" width="140" alt="overseas Loon 配置二维码"><br>Loon</td>
<td align="center"><img src="docs/qr/overseas-quantumultx.png?v=4" width="140" alt="overseas Quantumult X 配置二维码"><br>Quantumult X</td>
<td align="center"><img src="docs/qr/overseas-singbox.png?v=4" width="140" alt="overseas sing-box 配置二维码"><br>sing-box</td>
</tr>
</table>

### 海外回国：国内限区媒体走大陆出口

导入后在「🏠 回国」中选择实际落地中国大陆的节点。未选择前默认拒绝该组流量，避免误走普通境外节点。

| 客户端 | 配置地址 | 二维码 |
|---|---|---|
| mihomo / Clash Meta 内核 | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/mihomo.conf) | [二维码](docs/qr/overseas-return-mihomo.png) |
| Shadowrocket | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/RouteMint-Return-CN-ads-light.conf) | [二维码](docs/qr/overseas-return-shadowrocket.png) |
| Surge | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/surge.conf) | [二维码](docs/qr/overseas-return-surge.png) |
| Loon | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/loon.conf) | [二维码](docs/qr/overseas-return-loon.png) |
| Quantumult X | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/quantumultx.conf) | [二维码](docs/qr/overseas-return-quantumultx.png) |
| sing-box | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/singbox.conf) | [二维码](docs/qr/overseas-return-singbox.png) |

<table>
<tr>
<td align="center"><img src="docs/qr/overseas-return-mihomo.png?v=4" width="140" alt="overseas-return mihomo / Clash Meta 内核 配置二维码"><br>mihomo / Clash Meta 内核</td>
<td align="center"><img src="docs/qr/overseas-return-shadowrocket.png?v=5" width="140" alt="overseas-return Shadowrocket 配置二维码"><br>Shadowrocket</td>
<td align="center"><img src="docs/qr/overseas-return-surge.png?v=4" width="140" alt="overseas-return Surge 配置二维码"><br>Surge</td>
<td align="center"><img src="docs/qr/overseas-return-loon.png?v=4" width="140" alt="overseas-return Loon 配置二维码"><br>Loon</td>
<td align="center"><img src="docs/qr/overseas-return-quantumultx.png?v=4" width="140" alt="overseas-return Quantumult X 配置二维码"><br>Quantumult X</td>
<td align="center"><img src="docs/qr/overseas-return-singbox.png?v=4" width="140" alt="overseas-return sing-box 配置二维码"><br>sing-box</td>
</tr>
</table>

### 中国内地精简版

`cn-mainland-lite` 保留局域网、广告、AI、游戏平台下载、百度网盘、国内域名和国内 IP 分类，境外流量由默认代理兜底。适合需要较少分类的设备。

| 客户端 | 配置地址 | 二维码 |
|---|---|---|
| mihomo / Clash Meta 内核 | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/mihomo.conf) | [二维码](docs/qr/cn-mainland-lite-mihomo.png) |
| Shadowrocket | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/RouteMint-CN-Lite-ads-light.conf) | [二维码](docs/qr/cn-mainland-lite-shadowrocket.png) |
| Surge | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/surge.conf) | [二维码](docs/qr/cn-mainland-lite-surge.png) |
| Loon | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/loon.conf) | [二维码](docs/qr/cn-mainland-lite-loon.png) |
| Quantumult X | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/quantumultx.conf) | [二维码](docs/qr/cn-mainland-lite-quantumultx.png) |
| sing-box | [订阅配置](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/singbox.conf) | [二维码](docs/qr/cn-mainland-lite-singbox.png) |

## 导入与更新

| 客户端 | 配置格式 | 节点与导入方式 |
|---|---|---|
| mihomo / Clash Meta 内核 | YAML，发布为 `mihomo.conf` | 下载配置，将 `proxy-providers.airport.url` 改为自己的 Clash/mihomo 节点源，再作为个人配置导入。经典 Clash 内核不支持本仓库的 MRS 规则。 |
| Shadowrocket | `RouteMint-场景-广告档.conf` | 在「配置 → 添加配置」粘贴地址，或扫描对应二维码，下载后启用。节点订阅在 App 中另行添加；`PROXY` 使用当前所选节点。AI、流媒体、回国需要相应地区出口。 |
| Surge | `surge.conf` | 下载配置，将 `Airport` 的 `policy-path` 改为自己的 Surge 节点源；通过配置导入或对应二维码导入个人配置。 |
| Loon | `loon.conf` | 下载配置，将 `[Remote Proxy]` 的 `Airport` 改为自己的 Loon 节点源，再导入个人配置。 |
| Quantumult X | `quantumultx.conf` | 下载后将 `[server_remote]` 地址改为自己的 QX 节点源，再手动导入。二维码用于下载文件；`[filter_remote]` 引用 QX 专用分流格式。 |
| sing-box | JSON，发布为 `singbox.conf` | 配置面向仓库 CI 固定的 sing-box 版本，包含本地 SOCKS 占位出站 `127.0.0.1:1080`。将节点出站替换或合并到该模板，保留策略标签引用，再导入客户端。 |

**规则更新与个人节点配置分开维护。** 远程规则由客户端更新，仓库每天构建并发布到 `release` 分支。
修改过节点源的个人配置应保存为本地配置或自己托管：Surge 请移除首行 `#!MANAGED-CONFIG`，避免更新整份公共模板时覆盖个人节点源；公共模板有策略变更时手动合并。
Shadowrocket 的节点保存在 App 中，可继续订阅公共配置更新。

mihomo / sing-box 的 DNS 按服务策略选择出口；其他客户端使用原生域名规则，海外默认系统 DNS。节点名筛选用于缩小候选范围，出口地区和服务可用性应实际验证。`CN2` 是线路标记，不能据此认定为回国节点。
Shadowrocket 的 `PROXY` 共用当前所选节点；需要同时使用多个地区出口时，请在 App 的代理分组中绑定具体节点。
Quantumult X 的候选组按订阅资源展开，导入后手动固定 AI、流媒体、回国节点；回国模式的 AI 组默认直连。

### 小火箭配置名称与更新修复

小火箭按文件名区分配置。默认轻量广告档分别显示为：

| 场景 | 文件名（App 通常隐藏 `.conf`） |
|---|---|
| 中国内地白名单 | `RouteMint-CN-Whitelist-ads-light` |
| 海外 AI 与流媒体 | `RouteMint-Overseas-AI-Media-ads-light` |
| 海外回国 | `RouteMint-Return-CN-ads-light` |
| 内地精简版 | `RouteMint-CN-Lite-ads-light` |

旧配置点更新出现 `not found` 时，请从上表的配置地址或新二维码重新下载一次并启用。旧版 `update-url` 误带了 `interval=86400`，手机可能把它当成网址的一部分。新配置的更新地址只含完整 URL，更新周期在 Shadowrocket 设置中选择。已有节点订阅继续保存在 App 中；原 `shadowrocket.conf` 地址保留兼容。

## 游戏平台下载与百度网盘

四种场景都将已收录的游戏平台下载 CDN 与百度网盘显式设为直连。下载分类同步上游的专用列表，涵盖 Steam、暴雪/Battle.net、Epic、EA、Ubisoft、GOG、Riot、Rockstar、Bethesda、Xbox 等，并保留 PlayStation、Nintendo 的下载域名。游戏平台商店、社区和平台服务在四种场景都走代理；下载与更新 CDN 规则先匹配，保持直连。

mihomo / sing-box 对下载与网盘域名使用当前网络的本地 DNS；其他客户端使用所在地区的默认 DNS。这样下载连接使用本地出口，CDN 调度也尽量贴近当前位置。Steam 请将「设置 → 下载 → 下载地区」选为当前或邻近地区；具体服务器由游戏平台调度。[Steam 官方说明](https://help.steampowered.com/en/faqs/view/21F5-8D5D-0141-7A5E)

## 自动更新

仓库每天在北京时间／香港时间 **03:17** 自动触发构建，也会在规则、模板或订阅入口更新到 `main` 后触发；GitHub Actions 排队时实际开始时间会顺延。

流程为：拉取上游规则 → 构建六种客户端配置 → 运行路由、配置与二维码检查 → 发布到 `release`。检查失败时保留上一版发布内容。

客户端继续使用本页的固定地址。完成首次节点绑定并启用远程规则更新后，规则内容按客户端更新周期自动刷新，无需重新寻找地址或扫描二维码。个人配置中的策略组、DNS 设置等模板变更按上方「导入与更新」说明合并。

可通过页首的构建状态徽章查看最新结果。刚发布时 CDN 可能仍有缓存，实时核对方法见[地址、缓存与反馈](#地址缓存与反馈)。

## 广告策略

默认 `ads-light`：拦截广告与常见追踪域名，保持现有的分流方式。配置不启用 HTTPS 解密、证书安装或脚本注入。

| 档位 | 内容 | 使用方法 |
|---|---|---|
| `ads-off` | 关闭广告和追踪器拦截 | 把配置地址中的 `/ads-light/` 改为 `/ads-off/` |
| `ads-light` | 广告、常见追踪器 | 默认档位 |
| `ads-strict` | 广告、追踪器，再加恶意域名 | 把地址中的 `/ads-light/` 改为 `/ads-strict/` |

小火箭切换广告档时，地址中的目录与文件名后缀需一起修改，例如 `/ads-off/RouteMint-Overseas-AI-Media-ads-off.conf`。

播放或登录异常时，先用 `ads-off` 复测，再根据连接日志添加具体例外。域名分流无法完整移除 YouTube 等平台与正文共用域名的视频广告。

## Netflix / HBO 播放排查

1. 固定一个可用于目标服务的节点，检查登录、API、图片和播放 CDN 是否进入同一服务策略组。测速通过只说明网络可达。
2. mihomo / sing-box 的服务 DNS 使用同一策略组；更换节点后重连客户端、清空 DNS 缓存并重启视频 App。
3. 查看连接日志，确认 IPv6、QUIC/UDP 与 DNS 流量由客户端接管。代理不支持 UDP 时检查客户端的拒绝或回退设置；系统代理没有覆盖的 App 需使用客户端的 TUN/VPN 模式。
4. 切换 `ads-off` 复测，区分广告误拦与出口问题。
5. 用 `fast.com` 的客户端 IP/国家检查 Netflix 出口，再根据结果更换节点。规则覆盖和出口 IP 是否被识别为代理是两个排查项。Netflix 官方也要求检查 VPN、出口 IP 与 DNS；含广告套餐及直播不支持 VPN。[Netflix 官方排查说明](https://help.netflix.com/en/node/277)

Netflix 包含主站、视频/图片 CDN、DNS 检测域名，并用有理由记录的关键字补齐动态 AWS API 主机；这些关键字会匹配包含同一片段的主机名，应结合日志核查。共享的 `amazonaws.com`、`cloudfront.net`、`alicdn.com` 不整体划入单一媒体策略。HBO/Max 同步上游 `hbo` 分类的专用 CDN。

## 地址、缓存与反馈

jsDelivr 的分支地址可能存在缓存。要检查刚发布的版本，可把
`https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/` 换成
`https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/`。

反馈路由问题时请提供场景、客户端版本、域名、命中策略、期望出口与脱敏日志，便于复现。

## 维护文档

- [规则体系与分类表](docs/architecture.md)
- [质量校验与发布流程](docs/quality.md)
- [开发、数据来源与已知限制](docs/development.md)
- [第三方许可证](THIRD_PARTY_NOTICES.md)
- [变更日志](CHANGELOG.md)

参考 [Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever) 的按场景选规则、配置地址与二维码并列的使用方式；规则来源和许可证见本仓库第三方声明。
