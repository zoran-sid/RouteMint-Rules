# 开发与数据来源

## 仓库结构

```text
upstreams.yaml          # 上游声明：URL、解析器、许可证、失败策略
sources/                # 每个分类一个 YAML：include / add / remove / meta
presets/                # 场景预设：策略组 + 规则顺序的唯一定义
  _defaults.yaml        #   全局冲突裁决优先级
templates/              # 各客户端 Jinja2 模板
budgets.yaml            # 条数预算与突变保护阈值
builder/                # 构建代码：fetch / parse / optimize / emit / render / report / publish
tests/                  # pytest 与冒烟用例 expectations.yaml
.github/workflows/      # build.yml、pr-check.yml
docs/                   # 文档与二维码
dist/                   # 构建产物（CI 发布到 release 分支，不入 main）
```

`sources/` 用 YAML 而不是纯文本，是为了让「为什么加/删这条」「适用于哪些地区」跟规则放在一起；
`dist/` 与源码分离，`main` 只放源码，产物以单次提交推到 `release` 分支。
所有对外配置统一用 `.conf` 后缀（mihomo 是 YAML 内容、sing-box 是 JSON 内容），
避免不同客户端对扩展名的识别差异。

## 本地构建

需要 Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync --frozen
uv run python -m builder check                  # 只校验 YAML，不联网
uv run python -m builder build                  # 构建到 dist/
uv run python -m builder build --check-domains  # 额外抽样检测失效域名（报告项）
uv run pytest                                   # 单测 + 产物冒烟
```

带完整校验（需要本地 mihomo / sing-box 二进制）：

```bash
uv run python -m builder build \
  --mihomo-bin /path/to/mihomo \
  --singbox-bin /path/to/sing-box \
  --validate
```

其他子命令：

```bash
python -m builder qr --out docs/qr   # 重新生成 README 的二维码
# 二维码内容变了要给 README 里的图片地址加 ?v=N，否则 GitHub 图片代理会继续发旧图
python -m builder publish --help     # 发布辅助（CI 用）
```

上游数据缓存在 `.cache/upstreams/`，单个上游失败时沿用上一次成功的快照并在报告里标注，
不会产出空文件。`--offline` 完全使用快照。

## 提交规则修改

用 Issue 模板「规则修改请求」，写清四件事：

1. **域名**：要加/要删的完整域名；
2. **期望分类**：例如 `ai-openai`、`cn`、`dev`；
3. **理由**：为什么属于这个分类（官网、官方文档、抓包）；
4. **验证方式**：截图、`dig` 结果、页面出处。

关键字规则（`DOMAIN-KEYWORD`）默认不接受：它会误伤普通站点。确有必要时必须在 `sources/`
里写明理由，且每分类不超过 3 条。

## 数据来源

见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。一句话：v2fly domain-list-community（MIT）、
china-operator-ip（MIT）、ShadowWhisperer BlockLists（Unlicense）、AdGuard cname-trackers（MIT）、
urlhaus-filter（MIT / CC0 数据）。

### 为什么广告源不用 AdGuard / EasyList

实测同行现状（2026-11）：

| 仓库 | 声明许可证 | 广告列表来源 | 规模 |
|---|---|---|---|
| blackmatrix7/ios_rule_script | GPL-2.0 | 未标注，实为 AdGuard / EasyList 派生 | 291,159 |
| Loyalsoldier/clash-rules | GPL-3.0 | `category-ads-all`（EasyList + AdGuard + Peter Lowe） | 200,345 |
| ACL4SSR/ACL4SSR | CC-BY-SA-4.0 | `BanEasyList.list` 直接写明来源 easylist.txt | 40,977 |
| 本仓库 | MIT | ShadowWhisperer + v2fly + AdGuard cname-trackers | 37,113 |

主流仓库确实把 GPL / CC-BY-SA 来源的列表直接再分发了（有的干脆不放 LICENSE），但这与
「仓库声明 MIT」冲突。本仓库只用可再分发的来源，代价是少覆盖一些长尾与内嵌广告。

要更高覆盖率可以自行接入 AdGuard SDNS（约 19 万条），但那时产物整体应按 GPL-3.0 分发，
`THIRD_PARTY_NOTICES.md` 的口径也要跟着改。

## Roadmap

- [x] 阶段一：核心分类、mihomo + Shadowrocket、`cn-mainland`、每日 CI
- [x] 阶段二：流媒体/开发者/游戏/大厂/回国分类，`overseas`、`overseas-return`、`cn-mainland-lite`
- [x] 阶段三：Surge / Loon / Quantumult X / sing-box 的规则与配置输出
- [x] 阶段四：失效域名抽检、CHANGELOG 自动提交、GitHub Release、release 分支发布

## 已知限制

- Shadowrocket / Quantumult X / sing-box 不支持按节点名过滤，AI 与回国组需手动选节点。
- v2fly 里约 160 条 `regexp:` 规则没有导出（构建报告按分类计数），主要是一些 CDN 边缘域名。
- `reject-malware` 每日波动大，单独关闭了 30% 突变保护。
- `cn-region-locked` 是手工维护的媒体域名清单，不含银行类 App。
- 广告分类约 3.7 万条，是全仓库最大的单类；不需要就用 `ads-off` 档位。
