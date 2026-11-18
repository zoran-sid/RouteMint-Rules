# v2rayNG 分流规则

RouteMint 为 v2rayNG 提供四个场景、三个广告档。路由 JSON 保存规则顺序与出口，两个 `.dat` 资源保存实际域名和 IP 数据。继续使用 App 中已配置的节点。

## 首次导入

1. 打开 v2rayNG 的「资源文件」，分别添加以下两个 URL。备注必须填完整文件名，因为 v2rayNG 使用备注保存资源文件。
2. 点击右上角「下载资源文件」，确认两个文件下载成功。
3. 从下表选择路由 JSON，用浏览器打开并复制完整正文（含开头和结尾的方括号）。在「路由设置」右上角选择「从剪贴板导入规则集」。如有原先的自定义规则，可先导出备份。锁定的规则在导入后仍位于最前面。
4. 域名策略可使用默认 `AsIs`，按原始域名或 IP 匹配。导入成功后重新连接节点。

| 资源文件名 | 地址 |
|---|---|
| `routemint-geosite.dat` | [域名资源](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/rules/v2rayng/routemint-geosite.dat) |
| `routemint-geoip.dat` | [IP 资源](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/rules/v2rayng/routemint-geoip.dat) |

| 场景 | 关闭广告拦截 | 轻量拦截（推荐） | 加拦恶意域名 |
|---|---|---|---|
| `cn-mainland` | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-off/v2rayng.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-light/v2rayng.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland/ads-strict/v2rayng.json) |
| `overseas` | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-off/v2rayng.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-light/v2rayng.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas/ads-strict/v2rayng.json) |
| `overseas-return` | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-off/v2rayng.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-light/v2rayng.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/overseas-return/ads-strict/v2rayng.json) |
| `cn-mainland-lite` | [ads-off](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-off/v2rayng.json) | [ads-light](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-light/v2rayng.json) | [ads-strict](https://raw.githubusercontent.com/zoran-sid/RouteMint-Rules/release/configs/cn-mainland-lite/ads-strict/v2rayng.json) |

仓库首页的二维码打开对应 JSON 下载地址。扫码后复制 JSON，在路由设置里导入。

## 出口与更新

- 默认映射使用 v2rayNG 内置的 `proxy`、`direct`、`block`。代理项使用当前节点。AI、流媒体等分类分别保留为可编辑的路由条目。
- 回国场景的「`cn-region-locked`」初始出口为 `block`。确认节点落地中国大陆后，可将该条目的 `outboundTag` 改为大陆节点备注（与节点显示名称完全一致），或选中大陆节点后把该条目设为 `proxy`。未匹配请求仍直连。
- 域名和 IP 数据随仓库每日构建。点击「资源文件 → 下载资源文件」刷新数据，再重新连接。切换场景、广告档或更新规则顺序时重新导入 JSON，保留节点配置。改过出口的条目可先导出，导入新 JSON 后按需恢复。
