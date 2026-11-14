# 规则体系

这份文档解释「规则为什么这样组织」。日常使用不需要读它，改规则或排查路由时再看。

## 分类表

条数由构建自动写入。

<!-- BEGIN CATEGORY TABLE -->
| 分类 | 内容 | 条数 | 推荐策略 |
|---|---|---|---|
| `ai` | AI 服务汇总（六个子分类的并集） | 225 | 🤖 AI 服务 |
| `ai-anthropic` | Anthropic / Claude | 19 | 🤖 AI 服务 |
| `ai-copilot` | GitHub Copilot / Microsoft Copilot | 9 | 🤖 AI 服务 |
| `ai-gemini` | Google Gemini / AI Studio / DeepMind | 7 | 🤖 AI 服务 |
| `ai-openai` | OpenAI / ChatGPT / Sora | 20 | 🤖 AI 服务 |
| `ai-others` | 其他 AI 服务（对话、绘图、语音、模型托管） | 165 | 🤖 AI 服务 |
| `ai-perplexity` | Perplexity | 5 | 🤖 AI 服务 |
| `apple` | Apple 服务 | 1583 | 🎯 全球直连 |
| `cn` | 中国大陆域名 | 6203 | 🎯 全球直连 |
| `cn-ip` | 中国大陆 IP 段 | 6211 | 🎯 全球直连 |
| `cn-ip6` | 中国大陆 IPv6 段 | 3428 | 🎯 全球直连 |
| `cn-region-locked` | 中国大陆限区内容（海外需回国节点） | 24 | 🏠 回国 |
| `dev` | 开发者服务（代码托管、包管理、模型托管） | 87 | 🌍 境外服务 |
| `disney` | Disney+ / Hulu / ESPN（Disney 体系） | 218 | 🎬 Disney+ |
| `game-download` | 游戏下载 CDN（体积大、可直连） | 15 | 🎯 全球直连 |
| `game-platform` | 游戏商店、社区与联机服务 | 258 | 🌍 境外服务 |
| `google` | Google 服务（搜索、地图、Gmail 等） | 619 | 🌍 境外服务 |
| `max` | Max / HBO Max | 64 | 🎬 Max |
| `microsoft` | Microsoft 服务 | 554 | 🎯 全球直连 |
| `netflix` | Netflix | 24 | 🎬 Netflix |
| `primevideo` | Prime Video | 25 | 🎬 Prime Video |
| `private` | 局域网、保留地址、本地主机名 | 23 | DIRECT |
| `proxy` | 其余境外常用服务 | 18563 | 🌍 境外服务 |
| `reject-ads` | 广告域名（含插屏、弹窗、推送广告） | 37113 | REJECT |
| `reject-malware` | 恶意软件分发与钓鱼域名 | 18377 | REJECT |
| `reject-tracker` | 常见追踪器、分析 SDK、归因与热图服务 | 668 | REJECT |
| `spotify` | Spotify | 23 | 🎵 Spotify |
| `streaming-others` | 其他流媒体与音视频平台 | 1587 | 📺 其他流媒体 |
| `telegram` | Telegram（域名 + 官方 IP 段） | 31 | 🌍 境外服务 |
| `tiktok` | TikTok（不含抖音） | 36 | 🎬 TikTok |
| `youtube` | YouTube 及视频 CDN | 177 | 📺 YouTube |
<!-- END CATEGORY TABLE -->

## 规则顺序

所有客户端模板都按同一顺序编排：

```text
private → reject → ai → 流媒体 → cn-region-locked → dev → game
        → telegram → apple/microsoft/google → proxy → cn → cn-ip → cn-ip6 → FINAL
```

顺序即路由契约：

1. **private 最前**：局域网与保留地址永远不进代理。
2. **reject 紧随其后**：广告域名常同时出现在境外列表里，先拦掉才不会被后面的代理规则「救回来」。
3. **具体先于笼统**：AI、流媒体、开发者、游戏都排在 `proxy`（其余境外服务）之前。
4. **cn-region-locked 在 cn 之前**：回国限区域名也属于 `cn`，先被回国组拿走，海外用户的 B 站、网易云才会走回国节点。
5. **cn-ip / cn-ip6 带 `no-resolve`**：命中 IP 段时不再触发 DNS 解析。
6. **FINAL 兜底**：没匹配上的流量交给「漏网之鱼」，默认走向因预设而异。

## 兜底策略：大陆优先代理，海外优先直连

| 预设 | 漏网之鱼成员顺序 | 含义 |
|---|---|---|
| `cn-mainland` / `cn-mainland-lite` | 节点选择 → 直连 | 判断不了的域名优先走代理 |
| `overseas` / `overseas-return` | 直连 → 节点选择 | 判断不了的域名优先直连，觉得慢手动切 |

跨分类冲突另有显式优先级（`presets/_defaults.yaml`）：具体分类 > 笼统分类，`cn` > `proxy`，
`reject` > 一切（`private` 除外）。裁决结果写进构建报告的「冲突裁决」表。

还有一条容易被忽略的规则：**共享分类的删除必须对所有预设安全**。只有当所有引用分类 A 的
预设都同时引用获胜分类 B 时，才允许把规则从 A 里删掉。否则会出现「cn-mainland 没有回国组，
导致 bilibili 被从 cn 删掉、掉进 FINAL 走代理」这类事故。

## 为什么 AI 组要排除香港、大陆、澳门节点

OpenAI、Anthropic、Gemini 都按出口 IP 归属地判断可用性：香港、澳门、中国大陆的出口会被拒绝
或触发风控，俄罗斯、伊朗等地区同样不可用。所以 AI 组只做**排除**，不做**白名单**：

- `exclude_filter` 排除香港/澳门/大陆/俄罗斯、伊朗、朝鲜等地区的节点名，能识别 `HK01`、
  `🇭🇰`、`香港 02`、`CN2 上海`、`回国 01` 这些常见写法，同时不会误伤 `Russia` 里的 `us`；
- 不再要求节点名必须包含「美国/US/日本」等字样。

这条改动是踩坑换来的：早先还加了一层 `filter` 白名单，结果机场把节点命名成 `US01`、`JP02`
时正则 `\bus\b` 匹配不到，AI 组变成空组；而 mihomo 对空组的处理是**静默回落 DIRECT**，
表现就是「AI 没走代理」。现在去掉白名单，并在组里保留 `🚀 节点选择` 作为手动兜底。

`🤖 AI 服务` 是 `select` 组，默认成员是 `♻️ AI 自动选择`（url-test，带上述排除），
可以随时手动改选。

代价：没有地区标记、实际落地却在受限地区的节点仍可能被选中。如果全部节点都是港/澳/大陆，
AI 组依然会为空——这时需要手动选节点，或者换一个带可用地区节点的机场。

`overseas-return` 里 AI 组成员顺序是「直连 → AI 自动选择」：海外网络通常能直连 AI，
真遇到不可用时一键切到代理节点。

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

AI 单独留一组，是因为它需要按节点名排除地区，FINAL 做不到这件事。

## 客户端能力差异

同样是「AI 组排除香港/澳门/大陆节点」，各客户端能做到的程度不同：

| 客户端 | 按节点名过滤 | 说明 |
|---|---|---|
| mihomo | ✅ `filter` + `exclude-filter` | 唯一能做到「正向包含 + 反向排除」双保险 |
| Surge | ⚠️ `policy-regex-filter` | 只能正向筛选；节点名写成「HK-US」这种混合名时可能漏过 |
| Loon | ⚠️ `[Remote Filter]` NameRegex | 同上 |
| Shadowrocket | ❌ | 远程配置没有节点名过滤，需手动选节点 |
| Quantumult X | ❌ | 策略组只能按订阅资源/服务器标签划分 |
| sing-box | ❌ | 策略组没有按名字过滤的参数 |

Surge / Loon / Quantumult X 没有可脚本化的校验器，仓库只做结构断言（段落、结尾 FINAL、
URL 白名单、无凭据）；mihomo 与 sing-box 的配置每次构建都会真实加载校验。
