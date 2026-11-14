# RouteMint-Rules

按「你在哪、要访问什么」分流的代理规则仓库。同一份规则源，生成多套开箱即用的完整配置：
选一个预设、填一行机场订阅，就能用。规则每天自动构建，带预算校验、冲突裁决和变更日志。

> 当前进度：阶段一（MVP）。已交付 `cn-mainland` 预设、mihomo 与 Shadowrocket 两种完整配置、
> 核心分类与每日 CI。其余预设与客户端在后续阶段补齐，见文末 Roadmap。

## 我在哪 × 我要访问什么 → 选哪个预设

| 你在哪 | 你要访问什么 | 选这个预设 | 状态 |
|---|---|---|---|
| 中国大陆 | 国内网站直连，Google/YouTube/AI 走代理 | `cn-mainland` | ✅ 可用 |
| 中国大陆 | 同上，但手机老旧、追求省电省内存 | `cn-mainland-lite` | 阶段二 |
| 海外 | Google 等可直连，只把 AI 与部分流媒体交给代理 | `overseas` | 阶段二 |
| 海外 | 回国看 B 站港澳台、网易云、爱奇艺等限区内容 | `overseas-return` | 阶段二 |

预设不是「另一份规则」，而是同一份规则源的不同**策略组 + 规则顺序**组合。
分类内容完全一致，差别只在谁走代理、谁直连。

## 快速开始

### Clash / mihomo（Clash Verge Rev、Mihomo Party 等）

订阅地址（默认 `ads-light` 档）：

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml
```

一键导入：

```text
clash://install-config?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fzoran-sid%2FRouteMint-Rules%40release%2Fconfigs%2Fcn-mainland%2Fads-light%2Fmihomo.yaml
```

导入后只需要改一处：把 `proxy-providers.airport.url` 换成你自己的机场订阅地址。
配置里不含任何节点、订阅或密钥，只有占位符。

> 本仓库的规则集以 `.mrs`（mihomo 二进制格式）分发，比 YAML 文本省内存、加载更快。
> 如果你的客户端不支持 `.mrs`，改用同目录下的 `.yaml` 或 `.list`。

### Shadowrocket

配置地址（在 Shadowrocket 里「配置 → 添加配置 → 粘贴 URL」）：

```text
https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf
```

节点请在 Shadowrocket 里另行添加机场订阅；配置里的 `PROXY` 指你当前选中的代理。
配置中的 `update-url` 会让 Shadowrocket 每天自动拉取新版。

**已知限制**：Shadowrocket 的远程配置不支持按节点名正则过滤，所以「AI 组自动排除
香港/澳门/大陆节点」只在 mihomo 配置里生效；Shadowrocket 上需要你手动在 AI 组里选节点。
需要自动过滤请用 mihomo 系客户端。

### 三档广告拦截

每个预设都生成三档，互不影响，换链接即换档位：

| 档位 | 包含分类 | mihomo | Shadowrocket |
|---|---|---|---|
| `ads-off` | 不拦广告 | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-off/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-off/shadowrocket.conf) |
| `ads-light`（默认） | 广告 + 常见追踪器 | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-light/shadowrocket.conf) |
| `ads-strict` | 再加恶意域名 | [mihomo](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-strict/mihomo.yaml) | [conf](https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/configs/cn-mainland/ads-strict/shadowrocket.conf) |

### 备用地址（GitHub Raw）

jsDelivr 有缓存延迟（分支引用最长 12 小时，且需要主动 purge），着急时用 Raw：

```text
https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-light/mihomo.yaml
```

Raw 没有缓存，但国内访问可能不稳定。

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
| `cn` | 中国大陆域名 | 6235 | 🎯 全球直连 |
| `cn-ip` | 中国大陆 IP 段 | 9639 | 🎯 全球直连 |
| `private` | 局域网、保留地址、本地主机名 | 23 | DIRECT |
| `proxy` | 其余境外常用服务 | 23448 | 🌍 境外服务 |
| `reject-ads` | 广告域名（含插屏、弹窗、推送广告） | 29335 | REJECT |
| `reject-malware` | 恶意软件分发与钓鱼域名 | 18377 | REJECT |
| `reject-tracker` | 常见追踪器、分析 SDK、归因与热图服务 | 668 | REJECT |
<!-- END CATEGORY TABLE -->

## 规则顺序

所有客户端模板都按同一顺序编排：

```text
private → reject → ai → 流媒体 → cn-region-locked → dev → game
        → telegram → apple/microsoft → proxy → cn → GEOIP/cn-ip → FINAL
```

顺序即路由契约，原因：

1. **private 最前**：局域网和保留地址永远不该进代理，放最后会被别的规则抢先命中。
2. **reject 紧随其后**：广告域名经常同时出现在境外列表里，先拦掉才不会被后面的代理规则「救回来」。
3. **具体先于笼统**：AI、流媒体、dev、game 都是具体服务，必须排在 `proxy`（其余境外服务）之前。
4. **proxy 在 cn 之前、cn 在 cn-ip 之前**：这是配置里的书写顺序；跨分类冲突另有显式优先级裁决
   （见 `presets/_defaults.yaml`），国内域名会在裁决阶段从 `proxy` 里被删掉，不会被代理抢先命中。
5. **cn-ip 带 `no-resolve`**：命中 IP 段时不再触发 DNS 解析，避免为直连流量做无谓查询。
6. **FINAL 兜底**：没匹配上的流量交给「漏网之鱼」，默认跟随节点选择而不是直连，避免漏代理。

## 为什么 AI 组要排除香港、大陆、澳门节点

OpenAI、Anthropic、Google Gemini 都按**出口 IP 归属地**判断可用性：香港、澳门、中国大陆
的出口会被拒绝或触发风控，俄罗斯、伊朗等地区同样不可用。机场节点名通常带地区标记，
所以 AI 组用两条正则做了两层过滤：

- `filter`：只保留美国、日本、新加坡、台湾、韩国、英国、德国等可用地区的节点；
- `exclude_filter`：再排除香港/澳门/大陆/俄罗斯等地区，防止节点名同时命中两边。

`🤖 AI 服务` 是一个 `select` 组，成员是 `♻️ AI 自动选择`（url-test，带上述过滤）和 `DIRECT`，
你仍然可以手动改选。这样默认走延迟最低的合规节点，也不会在你手动切换后失效。

## DNS 防泄漏

配置做了三件事：

1. **fake-ip**：客户端拿到的是假 IP，真实域名延迟到代理端解析，减少本地 DNS 暴露面。
2. **nameserver-policy + `rule-set:`**：AI、流媒体、境外服务等分类的域名，强制使用境外 DoH
   （`https://1.1.1.1/dns-query`）并指定经 `🚀 节点选择` 发出；只有 `cn`、`private` 走国内 DoH。
3. **proxy-server-nameserver**：机场节点域名用国内 DNS 解析，避免「为了连代理而先泄漏查询」。

结果是：境外域名的解析不会落到国内 DNS 上，国内域名也不会被绕到境外解析。

## 高级用法：只引用单个规则集

规则集可以单独使用，不依赖完整配置。以 AI 为例：

| 格式 | 地址 | 适用 |
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

说明两点：

- `sources/` 用 YAML 而不是纯文本，是为了让「为什么删掉这条」「这个分类适用于哪些地区」
  跟规则放在一起，review 时能看到理由。
- `dist/` 与源码分离，`main` 分支只放源码，产物以单次提交推到 `release` 分支，仓库历史不会膨胀。

## 本地构建与测试

需要 Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync --frozen
uv run python -m builder check          # 只校验 YAML，不联网
uv run python -m builder build          # 构建到 dist/
uv run pytest                           # 冒烟测试 + 单测
```

想校验生成的 mihomo 配置，需要本地有 mihomo 二进制：

```bash
uv run python -m builder build --mihomo-bin /path/to/mihomo --validate
```

上游数据会缓存在 `.cache/upstreams/`，单个上游失败时沿用上一次成功的快照并在报告里标注，
不会产出空文件。`--offline` 完全使用快照。

## 提交规则修改

请用 Issue 模板「规则修改请求」，写清四件事：

1. **域名**：要加/要删的完整域名；
2. **期望分类**：例如 `ai-openai`、`cn`、`dev`；
3. **理由**：为什么属于这个分类（服务官网、官方文档、实际抓包）；
4. **验证方式**：你如何确认（截图、`dig` 结果、页面出处）。

关键字规则（`DOMAIN-KEYWORD`）默认不接受：它会误伤普通站点。确有必要时，必须在
`sources/` 里写明理由，并控制在每分类 3 条以内。

## 数据来源

见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。一句话版本：
v2fly domain-list-community（MIT）、china-operator-ip（MIT）、ShadowWhisperer BlockLists（Unlicense）、
urlhaus-filter（CC0 数据）。AdGuard 与 EasyList 因 GPL/CC-BY-SA 与本仓库 MIT 不兼容，未接入。

## 已知限制与 Roadmap

- [x] 阶段一：核心分类、mihomo + Shadowrocket、`cn-mainland`、每日 CI
- [ ] 阶段二：补齐流媒体/开发者/游戏/大厂/回国分类，新增 `overseas`、`overseas-return`、`cn-mainland-lite`
- [ ] 阶段三：Surge / Loon / Quantumult X / sing-box 的规则与配置输出
- [ ] 阶段四：失效域名抽检、CHANGELOG 自动提交、GitHub Release、README 表格自动更新

其他限制：

- Shadowrocket 不支持节点名正则过滤，AI 组需手动选节点（见上文）。
- `ads-light` 的广告列表约 2.9 万条，是当前体积最大的分类；`cn-mainland-lite` 会进一步裁剪。
- 失效域名检测只覆盖手工添加的规则，且有抽样上限（阶段四实现）。
