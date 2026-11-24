# v2rayN 桌面端分流规则

使用 Xray 内核。RouteMint 的路由 JSON 保存规则顺序与出口，两个 `.dat` 文件保存域名与 IP 数据。代理规则沿用 v2rayN 中已配置的节点。

## 首次导入

1. 下载下表中的两个文件，保留原文件名，放进 v2rayN 数据目录的 `bin/`。通常可在同一目录看到 `geosite.dat` 和 `geoip.dat`。
2. 打开「路由设置 → 添加规则集」，填写可辨识的备注，例如「RouteMint · 海外 · 轻量去广告」。将场景表中的链接粘贴到「可选地址（URL）」，在导入菜单选择「从订阅 URL 中导入规则」。也可下载 JSON 后选择「从文件中导入规则」。重新导入同一规则集时，选择「否」来替换旧规则。
3. 保存规则集，选中它并「设为活动规则」，然后用 Xray 内核重新连接节点。

| 文件名 | 下载 |
| --- | --- |
| `routemint-geosite.dat` | [域名数据](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/rules/v2rayng/routemint-geosite.dat) |
| `routemint-geoip.dat` | [IP 数据](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/rules/v2rayng/routemint-geoip.dat) |

## 选择场景和广告档

| 场景 | 关闭去广告 | 轻量去广告 | 严格去广告 |
| --- | --- | --- | --- |
| 中国内地 | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-off/v2rayn.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-light/v2rayn.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-strict/v2rayn.json) |
| 海外 | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-off/v2rayn.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-light/v2rayn.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-strict/v2rayn.json) |
| 海外回国 | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-off/v2rayn.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-light/v2rayn.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-strict/v2rayn.json) |
| 中国内地精简版 | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-off/v2rayn.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-light/v2rayn.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-strict/v2rayn.json) |

## 出口与更新

- 域名和 IP 规则按场景预设排序。Steam 商店和社区走代理，Steam 登录、游戏下载和百度网盘走直连。
- 规则里的 `proxy` 默认使用当前节点。AI 和流媒体需要相应地区的出口。海外回国模式下，`cn-region-locked` 默认拒绝。请在 v2rayN 中编辑对应规则，将出站绑定到已有的大陆节点。
- 仓库每天构建规则。要刷新域名和 IP，重新下载两个 `.dat` 覆盖后重连。要更新规则顺序、增加的分类或切换广告档，从 URL 再次导入并替换规则集。替换后需重新设置手动调整过的出站。

导入菜单及规则格式可参考 [v2rayN 的路由规则说明](https://github.com/2dust/v2rayN/wiki/Description-of-custom-routing-rules)。
