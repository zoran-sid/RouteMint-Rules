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
| `cn-ip` | 中国大陆 IP 段 | 6219 | 🎯 全球直连 |
| `cn-ip6` | 中国大陆 IPv6 段 | 3439 | 🎯 全球直连 |
| `cn-region-locked` | 中国大陆限区内容（海外需回国节点） | 30 | 🏠 回国 |
| `dev` | 开发者服务（代码托管、包管理、模型托管） | 87 | 🌍 境外服务 |
| `disney` | Disney+ / Hulu / ESPN（Disney 体系） | 218 | 🎬 Disney+ |
| `game-download` | 游戏下载 CDN（体积大、可直连） | 15 | 🎯 全球直连 |
| `game-platform` | 游戏商店、社区与联机服务 | 258 | 🌍 境外服务 |
| `google` | Google 服务（搜索、地图、Gmail 等） | 627 | 🌍 境外服务 |
| `max` | Max / HBO Max | 64 | 🎬 Max |
| `microsoft` | Microsoft 服务 | 554 | 🎯 全球直连 |
| `netflix` | Netflix | 28 | 🎬 Netflix |
| `primevideo` | Prime Video | 25 | 🎬 Prime Video |
| `private` | 局域网、保留地址、本地主机名 | 23 | DIRECT |
| `proxy` | 其余境外常用服务 | 18563 | 🌍 境外服务 |
| `reject-ads` | 广告域名（含插屏、弹窗、推送广告） | 37114 | REJECT |
| `reject-malware` | 恶意软件分发与钓鱼域名 | 18442 | REJECT |
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

## AI 节点选择

AI 组按节点名排除模板列出的常见受限出口，自动选择组在剩余候选中测试延迟。节点名只能提供筛选线索；实际出口、账号条件与服务支持地区共同影响可用性。

`🤖 AI 服务` 默认选「♻️ AI 自动选择」，也保留手动选择入口。`overseas-return` 中 AI 默认直连，可手动切换代理。选节点后应分别验证 ChatGPT、Claude 等目标服务；延迟测试不验证服务访问权限。

如果候选为空，mihomo 可能回落到 DIRECT。请检查组内实际候选和客户端日志，选择经验证的可用节点。节点名无地区标记或中转地与落地地不同，也可能使名称筛选失效。

## DNS 与服务出口

mihomo 的 `nameserver-policy` 为每个服务使用对应策略组。例如 Netflix 的查询经「🎬 Netflix」，AI 经「🤖 AI 服务」，国内限区媒体经「🏠 回国」。手动把服务改为直连时，该服务 DNS 也经直连。局域网主机名使用系统 DNS。

sing-box 为每个实际使用的策略生成独立 DNS 服务器并用 `detour` 指定同一出站；国内媒体使用大陆 DoH，境外服务使用境外 DoH。默认 DNS 与节点域名解析按场景选择：大陆使用国内 DoH，海外使用系统 DNS。HTTPS DNS 的服务器地址与 `/dns-query` 路径分开填写。

fake-ip 和嗅探有助于保留域名信息。DNS 是否全部被客户端接管还取决于系统、浏览器 DoH 与 TUN/VPN 设置。Surge、Loon、Shadowrocket、Quantumult X 模板在海外默认使用系统 DNS，服务连接按域名规则分流。

## 海外流媒体与回国出口

`overseas` 明确列出 Google、YouTube 直连；AI 分类先于 Google 匹配。Netflix、Disney+、HBO/Max、Prime Video 分别有手动选择组，默认继承「🌍 流媒体」的固定节点，避免播放会话随延迟测试自动换区。

Netflix 上游含动态 AWS API 主机的正则，本仓库用四个附理由的基础设施关键字补齐。关键字匹配范围比上游正则宽，应以日志核查；不代理整个共享 AWS/CDN 主域。

`overseas-return` 的回国组默认 `REJECT`，导入后选择实际落地中国大陆的节点。候选名筛选不包含 `CN2`，因为线路名称不能确认出口国家；组内不再提供普通境外节点组作为默认成员。回国媒体 CDN 与 API 先于普通 `cn` 规则匹配，其他国内服务保持直连。

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
| Quantumult X | 手动选择 | 本模板按订阅资源展开候选节点，导入后固定目标节点 |
| sing-box | ❌ | 策略组没有按名字过滤的参数 |

Surge / Loon / Quantumult X 没有可脚本化的校验器，仓库只做结构断言（段落、结尾 FINAL、
URL 白名单、无凭据）；mihomo 与 sing-box 的配置每次构建都会真实加载校验。
