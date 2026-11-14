# 质量校验与发布

## 必过项（失败即中止发布）

| 校验 | 实现 |
|---|---|
| `sources/` / `presets/` schema | `builder/spec.py`，字段、顺序、必填项、关键字理由 |
| 预算 | `budgets.yaml`，每分类与每预设 × 档位都有上限 |
| 条数突变保护 | 某分类较上一版下降超过 30% 即中止（`reject-malware` 单独豁免） |
| 配置可加载 | `mihomo -t` ×12、`sing-box check` ×12 |
| 路由冒烟 | `tests/expectations.yaml`，按 `dist/` 实际产物匹配 |
| 体积 | 单文件 ≤ 20 MB（jsDelivr 限制） |

## 报告项（不阻断发布）

- **失效域名抽样**：每天轮换解析 40 个手工添加的域名，连续 NXDOMAIN 才标记，写入构建报告。
- **冲突裁决**：谁被谁裁掉、原因、样例。
- **版本差异**：每分类增删条数与样例，写入 `CHANGELOG.md` 与 GitHub Release 说明。

## 发布流程

每天 19:17 UTC（北京时间 03:17）自动跑一次，也可在 Actions 手动触发。分两段：

**build（只读）**

1. 拉取上游（失败沿用上次成功快照）；
2. 归一化、去重、后缀压缩、IP 合并、跨分类冲突裁决；
3. 预算、突变保护、冒烟测试；
4. 生成 6 种客户端的规则与配置；
5. `mihomo -t` + `sing-box check`；
6. 抽样解析手工域名（报告项）。

任何一步失败都不会发布，`release` 分支保持上一版可用。

**publish（需要写权限）**

1. 与 `release` 分支上的 `manifest.json` 逐文件比对 SHA256；
2. 只有 `rules/` 或 `configs/` 真的变了才继续，否则直接跳过，不产生空提交；
3. 以**单一提交**强制推送到 `release` 分支（历史不会膨胀）；
4. 对变更文件逐个调用 `purge.jsdelivr.net` 刷新缓存；
5. 用当天 CHANGELOG 段落创建 GitHub Release；
6. 把 `CHANGELOG.md` 提交回 `main`（带 `[skip ci]`，不会自我触发）。

产物内容不含时间戳，所以「规则没变」时生成的文件逐字节相同，比对才可靠。

## 分发

- **jsDelivr**：`https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/...`
  分支引用缓存最长 12 小时，发布后会自动 purge 变更文件。
- **GitHub Raw**：`https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/...`
  没有缓存，国内访问可能不稳定。

二维码（`docs/qr/`）由 `python -m builder qr` 生成，CI 会校验它们与当前地址一致。
