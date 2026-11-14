# 第三方数据来源与许可证

本仓库的代码、脚本与 `sources/` 下自维护的规则采用 MIT 许可证。
构建产物另外包含下列上游的数据（或其派生集合），其版权归原作者所有，
分发时请同时遵守对应许可证。

| 上游 ID | 项目 | 许可证 | 主页 |
|---|---|---|---|
| `v2fly-dlc` | v2fly domain-list-community | MIT | [https://github.com/v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) |
| `china-operator-ip` | gaoyifan/china-operator-ip | MIT | [https://github.com/gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip) |
| `shadowwhisperer` | ShadowWhisperer/BlockLists | Unlicense | [https://github.com/ShadowWhisperer/BlockLists](https://github.com/ShadowWhisperer/BlockLists) |
| `cname-trackers` | AdGuard CNAME disguised ads list | MIT | [https://github.com/AdguardTeam/cname-trackers](https://github.com/AdguardTeam/cname-trackers) |
| `urlhaus` | malware-filter/urlhaus-filter（GitLab） | MIT / CC0-1.0 | [https://gitlab.com/malware-filter/urlhaus-filter](https://gitlab.com/malware-filter/urlhaus-filter) |

## 逐项说明

### v2fly domain-list-community

- 许可证：MIT
- 许可证原文：https://github.com/v2fly/domain-list-community/blob/master/LICENSE
- 项目主页：https://github.com/v2fly/domain-list-community

### gaoyifan/china-operator-ip

- 许可证：MIT
- 许可证原文：https://github.com/gaoyifan/china-operator-ip/blob/ip-lists/LICENSE
- 项目主页：https://github.com/gaoyifan/china-operator-ip

### ShadowWhisperer/BlockLists

- 许可证：Unlicense
- 许可证原文：https://github.com/ShadowWhisperer/BlockLists/blob/master/LICENSE
- 项目主页：https://github.com/ShadowWhisperer/BlockLists

### AdGuard CNAME disguised ads list

- 许可证：MIT
- 许可证原文：https://github.com/AdguardTeam/cname-trackers/blob/master/LICENSE
- 项目主页：https://github.com/AdguardTeam/cname-trackers

### malware-filter/urlhaus-filter（GitLab）

- 许可证：MIT / CC0-1.0
- 许可证原文：https://gitlab.com/malware-filter/urlhaus-filter/-/blob/main/LICENSE-CC0.md
- 项目主页：https://gitlab.com/malware-filter/urlhaus-filter

## 为什么没有 AdGuard DNS filter / EasyList

AdGuard SDNS Filter 与 EasyList 分别是 GPL-3.0 与 GPL-3.0-or-later / CC-BY-SA-3.0。
把它们的数据随 MIT 产物一起分发会产生许可证冲突，因此本仓库改用许可证兼容的来源：
ShadowWhisperer/BlockLists（Unlicense）与 urlhaus-filter（CC0 数据部分）。
如果你在本地构建时想自行接入 GPL 上游，请自行评估合规性，本仓库不代为分发。

仓库地址：https://github.com/zoran-sid/RouteMint-Rules
