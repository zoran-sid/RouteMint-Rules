# HomeProxy / PassWall 分流导入

导入包将同一场景预设转换为客户端原生 UCI 分流。节点地址、密码和订阅继续保存在路由器上。HomeProxy 使用 `routing_node` / `routing_rule` / `ruleset` / `dns_rule`；PassWall 使用 `nodes` 中的 sing-box `_shunt` 节点和 `shunt_rules`。

## 版本与依赖

- sing-box 1.14+：本仓库的 SRS 使用版本 5。脚本逐个下载并反编译远程 SRS，版本不兼容时在应用前停止。
- HomeProxy：支持上述自定义 UCI 类型、`generate_client.uc` 的版本。脚本基于你提供的参考包改进，会先用实际设备生成器创建隔离配置并运行 `sing-box check`。生成器布局或核心格式不兼容时先修复设备版本，导入会停止并保留活动配置。
- PassWall：支持 `rule-set:remote:` 的 sing-box 分流后端。Xray 不能使用这份远程 SRS 计划；请选择 sing-box 分流节点。
- 命令：`uci`、`ucode`、`curl`、`sing-box`、`sha256sum`。ucode 需能加载 fs 和 uci 模块；常见包名为 `ucode-mod-fs`、`ucode-mod-uci`，以当前固件包管理器为准。

原生结构参考 [HomeProxy 生成器](https://github.com/immortalwrt/homeproxy/blob/master/root/etc/homeproxy/scripts/generate_client.uc) 与 [PassWall 分流规则](https://github.com/Openwrt-Passwall/openwrt-passwall/blob/main/luci-app-passwall/luasrc/model/cbi/passwall/client/shunt_rules.lua)。

## 下载与检查

从首页选择客户端、场景和广告档的导入包，解压到 `/tmp`。包内包含 `install.sh`、`configure.uc`、`profile.json`。默认运行或传入 `--check-only` 均只做隔离检查：

```sh
sh /tmp/routemint-homeproxy/install.sh --check-only
# 检查通过后导入 UCI
sh /tmp/routemint-homeproxy/install.sh --apply
```

PassWall 将路径中的 `homeproxy` 改为 `passwall`。脚本先检查当前 UCI 没有待保存修改，再复制配置到临时目录。HomeProxy 检查真实生成器输出；PassWall 检查原生分流计划、节点引用与远程规则。两者都不会替你切换代理管理器或重启服务。

HomeProxy 模块路径已内置为 `ucode -L /etc/homeproxy/scripts -S`，包括生成预览的调用，无需额外 `sed` 修改。

## 节点绑定

默认沿用当前主节点；HomeProxy 也可沿用当前自定义默认出站。节点无法推断时，用已有的 UCI 节点 ID 指定：

```sh
export RM_PROXY_NODE='已有节点ID'
# 可选：为 AI 或回国媒体单独指定已有节点
export RM_AI_NODE='已有AI节点ID'
export RM_CN_RETURN_NODE='已有大陆节点ID'
sh /tmp/routemint-homeproxy/install.sh --check-only
sh /tmp/routemint-homeproxy/install.sh --apply
```

PassWall 同样使用这些变量。节点 ID 不是节点名称；可用 `uci show homeproxy` 或 `uci show passwall` 检查相应 `node` / `nodes` 段。全程在路由器上操作，节点凭据不会上传到本仓库。

回国媒体默认拒绝，设置 `RM_CN_RETURN_NODE` 后才使用该大陆出口。回国场景 AI 默认直连，设置 `RM_AI_NODE` 可为它指定代理。其他服务组可按计划中的组 ID 设置 `RM_<大写组ID>_NODE`，例如 `RM_NETFLIX_NODE`。

源站下载失败时，HomeProxy 会尝试已有的本地 SOCKS 监听。其他端口或 PassWall 可显式指定：

```sh
export RM_SOCKS='127.0.0.1:本地SOCKS端口'
```

## 应用与回退

`--apply` 会在 `/root/routemint-客户端-backup-时间戳/` 保存原 UCI，再原子替换客户端配置。检查失败、节点 ID 无效或准备期间配置被其他操作修改时停止导入。

- HomeProxy：导入停用旧的自定义规则、DNS 与路由节点，建立 RouteMint 规则并选择自定义模式。在 LuCI 启用客户端并保存应用。若设备使用 `proxy-switch` / `proxy-guard`，通过已有管理器切换到 HomeProxy，不要同时启动多个透明代理。
- PassWall：保留其他分流组，建立独立 RouteMint 规则组和分流节点。在 LuCI 把 TCP、UDP 选择为该 RouteMint 节点，保存应用。

回退时，将脚本输出的备份文件恢复到 `/etc/config/homeproxy` 或 `/etc/config/passwall`，再通过原管理器应用该客户端配置。

## 自动更新与 DNS

HomeProxy 的远程规则更新间隔为 `1d`；PassWall 使用 sing-box 远程规则集的默认更新周期。规则列表始终来自固定的源站 URL。规则顺序、分类或组发生变化时，重新下载导入包并检查、导入一次；无需重新添加节点。

HomeProxy 为直连国内服务、Steam 登录与下载、百度网盘使用 WAN DNS，服务代理 DNS 通过对应出站。PassWall 由其原生的直连/远程 DNS 设置处理；请在 LuCI 选择当地直连 DNS，并确保代理流量使用远程 DNS。包不会覆盖 PassWall 全局 DNS，以便保留设备现有设置。

## Steam 与百度网盘验证

Steam 仅将 `store.steampowered.com`、`steamcommunity.com` 及其子域代理。登录、CM 连接管理、API 和下载域名直连。新规则启用后完全退出 Steam 再登录，结合连接日志与 `ip_country` 检查；已经建立的连接不会因规则更新自动重建。对纯 IP 登录连接，构建器从 Valve 官方 GetCMList 目录提取公网服务器 IP，生成精确 IP 直连规则；不会放开整个 ASN 或端口范围。新服务器地址在目录更新并完成每日构建后加入。

`ip_country` 关联 Steam 登录/账户信息中的 IP 国家字段，可参考 [Steamworks GetIPCountry](https://partner.steamgames.com/doc/api/ISteamUtils#GetIPCountry) 与其[协议定义](https://github.com/SteamTracking/Protobufs/blob/master/steam/steammessages_clientserver_login.proto)；它不等同于账户商店国家。

百度网盘覆盖网盘接口、百度 PCS、百度云对象存储和 CDN 主域。海外场景另含国内域名与 IPv4/IPv6 直连，避免已知国内服务落入可切换的兜底组。自定义的全局代理、路由器第二层透明代理仍会影响最终出口，应使用本场景的规则模式。
