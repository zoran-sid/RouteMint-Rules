# RouteMint-Rules

按「你在哪、要访问什么」分流的代理规则仓库。同一份规则源，生成多套开箱即用的完整配置：
选一个预设、填一行机场订阅，就能用。规则每天自动构建，带条数预算、冲突裁决、变更日志。

## 我在哪 × 我要访问什么 → 选哪个预设

| 你在哪 | 你要访问什么 | 选这个预设 |
|---|---|---|
| 中国大陆 | 国内网站直连，Google / YouTube / AI 走代理 | [`cn-mainland`](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml) |
| 中国大陆 | 同上，但设备老旧、在意内存与耗电 | [`cn-mainland-lite`](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/mihomo.yaml) |
| 海外 | Google 等可直连，只把 AI 与部分流媒体交给代理 | [`overseas`](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/mihomo.yaml) |
| 海外 | 回国看 B 站港澳台、网易云、爱奇艺、腾讯视频等限区内容 | [`overseas-return`](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/mihomo.yaml) |

预设不是「另一份规则」，而是同一份规则源的不同**策略组 + 规则顺序 + 兜底策略**组合。
分类内容完全一致，差别只在谁走代理、谁直连、以及**没命中分类时往哪走**。

## 快速开始

### Clash / mihomo（Clash Verge Rev、Mihomo Party 等）

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml
```

一键导入：

```text
clash://install-config?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fzoran-sid%2FRouteMint-Rules%40release%2Fconfigs%2Fcn-mainland%2Fads-light%2Fmihomo.yaml
```

导入后只改一处：把 `proxy-providers.airport.url` 换成你自己的机场订阅地址。
配置里没有任何节点、订阅或密钥，只有占位符。

> 规则集以 `.mrs`（mihomo 二进制格式）分发，比 YAML 文本省内存、加载更快。
> 客户端不支持 `.mrs` 时，把 `format: mrs` 改成 `format: yaml` 并换用同目录 `.yaml` 链接。

### Shadowrocket

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf
```

在 Shadowrocket「配置 → 添加配置」里粘贴该地址。节点请另行添加机场订阅，
配置里的 `PROXY` 指你当前选中的代理；`update-url` 会让它每天自动拉新版。

**已知限制**：Shadowrocket 的远程配置不支持按节点名正则过滤，所以「AI 组自动排除
香港/澳门/大陆节点」「回国组自动筛选国内节点」只在 mihomo 配置里生效。
Shadowrocket 上需要你手动在对应组里选节点。

### 全部订阅地址

把下面的 `cn-mainland` 换成 `cn-mainland-lite` / `overseas` / `overseas-return`，
把 `ads-light` 换成 `ads-off` / `ads-strict`，就是对应组合的地址。

| 预设 | 广告档位 | mihomo | Shadowrocket |
|---|---|---|---|
| `cn-mainland` | ads-off | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-off/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-off/shadowrocket.conf) |
| | ads-light（默认） | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf) |
| | ads-strict | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-strict/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-strict/shadowrocket.conf) |
| `cn-mainland-lite` | ads-off | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-off/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-off/shadowrocket.conf) |
| | ads-light（默认） | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-light/shadowrocket.conf) |
| | ads-strict | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-strict/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland-lite/ads-strict/shadowrocket.conf) |
| `overseas` | ads-off | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-off/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-off/shadowrocket.conf) |
| | ads-light（默认） | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-light/shadowrocket.conf) |
| | ads-strict | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-strict/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas/ads-strict/shadowrocket.conf) |
| `overseas-return` | ads-off | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-off/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-off/shadowrocket.conf) |
| | ads-light（默认） | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-light/shadowrocket.conf) |
| | ads-strict | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-strict/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/overseas-return/ads-strict/shadowrocket.conf) |

### 备用地址（GitHub Raw）

jsDelivr 的分支引用有缓存（最长 12 小时，且需要主动 purge）。着急时把地址前缀换成：

```text
https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/
```

Raw 不走 CDN，国内访问可能不稳定。

## 三档广告拦截

| 档位 | 包含分类 | 说明 |
|---|---|---|
| `ads-off` | 无 | 完全不拦广告，适合依赖广告的 App 或排障 |
| `ads-light`（默认） | `reject-ads` + `reject-tracker` | 广告域名 + 高频追踪器 |
| `ads-strict` | 再加 `reject-malware` | 恶意软件与钓鱼域名（urlhaus，每天轮换） |

三档只是分类开关，规则内容完全一样；换 URL 即换档位，不需要重新导入订阅。

## 分类说明

条数由构建自动写入，每次发布同步更新。

<!-- BEGIN CATEGORY TABLE -->
| 分类 | 内容 | 条数 | 推荐策略 |
|---|---|---|---|
| `ai` | AI 服务汇总（六个子分类的并集） | 227 | 🤖 AI 服务 |
| `ai-anthropic` | Anthropic / Claude | 19 | 🤖 AI 服务 |
| `ai-copilot` | GitHub Copilot / Microsoft Copilot | 9 | 🤖 AI 服务 |
| `ai-gemini` | Google Gemini / AI Studio / DeepMind | 7 | 🤖 AI 服务 |
| `ai-openai` | OpenAI / ChatGPT / Sora | 22 | 🤖 AI 服务 |
| `ai-others` | 其他 AI 服务（对话、绘图、语音、模型托管） | 165 | 🤖 AI 服务 |
| `ai-perplexity` | Perplexity | 5 | 🤖 AI 服务 |
| `apple` | Apple 服务 | 1583 | 🎯 全球直连 |
| `cn` | 中国大陆域名 | 6235 | 🎯 全球直连 |
| `cn-ip` | 中国大陆 IP 段 | 6211 | 🎯 全球直连 |
| `cn-ip6` | 中国大陆 IPv6 段 | 3428 | 🎯 全球直连 |
| `cn-region-locked` | 中国大陆限区内容（海外需回国节点） | 24 | 🏠 回国 |
| `dev` | 开发者服务（代码托管、包管理、模型托管） | 87 | 🌍 境外服务 |
| `disney` | Disney+ / Hulu / ESPN（Disney 体系） | 218 | 🎬 Disney+ |
| `game-download` | 游戏下载 CDN（体积大、可直连） | 15 | 🎯 全球直连 |
| `game-platform` | 游戏商店、社区与联机服务 | 258 | 🌍 境外服务 |
| `google` | Google 服务（搜索、地图、Gmail 等） | 663 | 🌍 境外服务 |
| `max` | Max / HBO Max | 64 | 🎬 Max |
| `microsoft` | Microsoft 服务 | 556 | 🎯 全球直连 |
| `netflix` | Netflix | 24 | 🎬 Netflix |
| `primevideo` | Prime Video | 25 | 🎬 Prime Video |
| `private` | 局域网、保留地址、本地主机名 | 23 | DIRECT |
| `proxy` | 其余境外常用服务 | 18588 | 🌍 境外服务 |
| `reject-ads` | 广告域名（含插屏、弹窗、推送广告） | 29335 | REJECT |
| `reject-malware` | 恶意软件分发与钓鱼域名 | 18377 | REJECT |
| `reject-tracker` | 常见追踪器、分析 SDK、归因与热图服务 | 668 | REJECT |
| `spotify` | Spotify | 23 | 🎵 Spotify |
| `streaming-others` | 其他流媒体与音视频平台 | 1587 | 📺 其他流媒体 |
| `telegram` | Telegram（域名 + 官方 IP 段） | 31 | 🌍 境外服务 |
| `tiktok` | TikTok（不含抖音） | 40 | 🎬 TikTok |
| `youtube` | YouTube 及视频 CDN | 177 | 📺 YouTube |
<!-- END CATEGORY TABLE -->

## 规则顺序

所有客户端模板都按同一顺序编排：

```text
private → reject → ai → 流媒体 → cn-region-locked → dev → game
        → telegram → apple/microsoft/google → proxy → cn → cn-ip → cn-ip6 → FINAL
```

顺序即路由契约，原因：

1. **private 最前**：局域网和保留地址永远不该进代理。
2. **reject 紧随其后**：广告域名经常同时出现在境外列表里，先拦掉才不会被后面的代理规则「救回来」。
3. **具体先于笼统**：AI、流媒体、开发者、游戏都是具体服务，必须排在 `proxy`（其余境外服务）之前。
4. **cn-region-locked 在 cn 之前**：回国限区域名同时也属于 `cn`，先被回国组拿走，才能保证海外用户的 B 站、网易云走回国节点。
5. **cn-ip 带 `no-resolve`**：命中 IP 段时不再触发 DNS 解析。
6. **FINAL 兜底**：没匹配上的流量交给「漏网之鱼」，而它的默认走向**因预设而异**（见下）。

### 兜底策略：大陆优先代理，海外优先直连

| 预设 | 漏网之鱼成员顺序 | 含义 |
|---|---|---|
| `cn-mainland` / `cn-mainland-lite` | 节点选择 → 直连 | 判断不了的域名优先走代理，避免该代理的站点被直连漏掉 |
| `overseas` / `overseas-return` | 直连 → 节点选择 | 判断不了的域名优先直连；发现某个站点代理更快，手动切一下即可 |

跨分类冲突另有显式优先级（`presets/_defaults.yaml`）：具体分类 > 笼统分类，`cn` > `proxy`，
`reject` > 一切（`private` 除外）。裁决结果会写进构建报告的「冲突裁决」表。

## 为什么 AI 组要排除香港、大陆、澳门节点

OpenAI、Anthropic、Google Gemini 都按**出口 IP 归属地**判断可用性：香港、澳门、中国大陆
的出口会被拒绝或触发风控，俄罗斯、伊朗等地区同样不可用。机场节点名通常带地区标记，
所以 AI 组做了两层过滤：

- `filter`：只保留美国、日本、新加坡、台湾、韩国、英国、德国等可用地区；
- `exclude_filter`：再排除香港/澳门/大陆/俄罗斯，防止节点名同时命中两边。

`🤖 AI 服务` 是 `select` 组，成员是 `♻️ AI 自动选择`（url-test，带上述过滤）和 `直连`，
默认走延迟最低的合规节点，也可以随时手动改选。

`overseas-return` 里 AI 组的成员顺序是「直连 → AI 自动选择」：海外网络通常能直连 AI，
真遇到不可用时一键切到代理节点即可。

## DNS 防泄漏

1. **fake-ip**：客户端拿到假 IP，真实域名延迟到代理端解析，减少本地 DNS 暴露面。
2. **nameserver-policy + `rule-set:`**：AI、流媒体、境外服务等分类强制用境外 DoH
   （`https://1.1.1.1/dns-query`）并指定经 `🚀 节点选择` 发出；只有 `cn`、`private` 走国内 DoH。
3. **proxy-server-nameserver**：机场节点域名用国内 DNS 解析，避免「为了连代理先泄漏查询」。

结果：境外域名的解析不会落到国内 DNS 上，国内域名也不会被绕到境外解析。

## 精简版做了什么减法

`cn-mainland-lite` 的思路是「能靠 FINAL 兜住的分类型就不下发」：

- 不拆流媒体、开发者、游戏、大厂分类，全部交给「漏网之鱼」（节点选择）；
- 跳过 `proxy` 分类（两万多条）和 `cn-ip6`（三千多条），因为默认配置关闭 IPv6；
- 只保留 `private`、三档广告、`ai`（汇总）、`cn`、`cn-ip` 五个分类。

规则条数约为标准版的六成；再把档位换成 `ads-off`，总量会降到一万出头。
AI 单独留一组，是因为它需要按节点名排除地区，FINAL 做不到这件事。

## 高级用法：只引用单个规则集

规则集可以单独使用，不依赖完整配置。以 AI 汇总为例：

| 格式 | 路径 | 适用 |
|---|---|---|
| mihomo `.mrs` | `rules/ai/ai.mrs` | mihomo（推荐，二进制、省内存） |
| mihomo `.yaml` | `rules/ai/ai.yaml` | mihomo（domain behavior） |
| 通用 `.list` | `rules/ai/ai.list` | Surge / Shadowrocket / Loon |

完整前缀：`https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/`。

自己组合时的最小示例（mihomo）：

```yaml
rule-providers:
  ai:
    type: http
    behavior: domain
    format: mrs
    url: "https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/rules/ai/ai.mrs"
    path: ./rules/ai.mrs
    interval: 86400

rules:
  - RULE-SET,ai,🤖 AI 服务
  - GEOIP,CN,DIRECT
  - MATCH,🐟 漏网之鱼
```

## 仓库结构

```text
upstreams.yaml          # 上游声明：URL、解析器、许可证、失败策略
sources/                # 每个分类一个 YAML：include / add / remove / meta
presets/                # 场景预设：策略组 + 规则顺序的唯一定义
  _defaults.yaml        #   全局冲突裁决优先级
templates/              # 各客户端 Jinja2 模板
budgets.yaml            # 条数预算与突变保护阈值
builder/                # Python 构建：fetch / parse / optimize / emit / render / report
tests/                  # pytest 与冒烟用例 expectations.yaml
.github/workflows/      # build.yml、pr-check.yml
dist/                   # 构建产物（CI 发布到 release 分支，不入 main）
```

两点说明：

- `sources/` 用 YAML 而不是纯文本，是为了让「为什么加/删这条」「适用于哪些地区」跟规则放在一起；
- `dist/` 与源码分离，`main` 只放源码，产物以单次提交推到 `release` 分支，仓库历史不会膨胀。

## 本地构建与测试

需要 Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync --frozen
uv run python -m builder check          # 只校验 YAML，不联网
uv run python -m builder build          # 构建到 dist/
uv run pytest                           # 单测 + 产物冒烟测试
```

校验生成的 mihomo 配置（需要本地 mihomo 二进制）：

```bash
uv run python -m builder build --mihomo-bin /path/to/mihomo --validate
```

上游数据缓存在 `.cache/upstreams/`，单个上游失败时沿用上一次成功的快照并在报告里标注，
不会产出空文件。`--offline` 完全使用快照。

## 提交规则修改

用 Issue 模板「规则修改请求」，写清四件事：

1. **域名**：要加/要删的完整域名；
2. **期望分类**：例如 `ai-openai`、`cn`、`dev`；
3. **理由**：为什么属于这个分类（官网、官方文档、抓包）；
4. **验证方式**：截图、`dig` 结果、页面出处。

关键字规则（`DOMAIN-KEYWORD`）默认不接受：它会误伤普通站点。确有必要时必须在
`sources/` 里写明理由，且每分类不超过 3 条。

## 数据来源

见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。一句话：
v2fly domain-list-community（MIT）、china-operator-ip（MIT）、ShadowWhisperer BlockLists（Unlicense）、
urlhaus-filter（CC0 数据）。AdGuard 与 EasyList 因 GPL / CC-BY-SA 与本仓库 MIT 不兼容，未接入。

## Roadmap 与已知限制

- [x] 阶段一：核心分类、mihomo + Shadowrocket、`cn-mainland`、每日 CI
- [x] 阶段二：流媒体/开发者/游戏/大厂/回国分类，`overseas`、`overseas-return`、`cn-mainland-lite`
- [ ] 阶段三：Surge / Loon / Quantumult X / sing-box 的规则与配置输出
- [ ] 阶段四：失效域名抽检、CHANGELOG 自动提交、GitHub Release、README 表格自动更新

已知限制：

- Shadowrocket 不支持节点名正则过滤，AI / 回国组需手动选节点。
- v2fly 里有约 160 条 `regexp:` 规则没有导出（构建报告里按分类计数），主要是一些 CDN 边缘域名。
- `reject-malware` 的条数每天波动较大，已单独关闭 30% 突变保护。
- `cn-region-locked` 是手工维护的媒体域名清单，不含银行类 App（其域名难以稳定枚举）。
