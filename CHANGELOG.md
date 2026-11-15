# 变更日志

由每日构建自动生成。只记录规则层面的变化，格式变化不计。

## 2026-11-15

- **baidu-pan**：10 → 20（+10）
  - 新增：DOMAIN-SUFFIX,baidu-cdn.cn, DOMAIN-SUFFIX,baidu-cdn.com, DOMAIN-SUFFIX,baidu-cdn.net, DOMAIN-SUFFIX,baidubce.com, DOMAIN-SUFFIX,baidubcr.com, DOMAIN-SUFFIX,bce-cdn.cn, DOMAIN-SUFFIX,bce-cdn.com, DOMAIN-SUFFIX,bce-cdn.net …
- **cn**：6199 → 6192（-7）
  - 删除：DOMAIN-SUFFIX,baidu-cdn.com, DOMAIN-SUFFIX,baidu-cdn.net, DOMAIN-SUFFIX,baidubce.com, DOMAIN-SUFFIX,baidubcr.com, DOMAIN-SUFFIX,bce-cdn.com, DOMAIN-SUFFIX,bce-cdn.net, DOMAIN-SUFFIX,bcebos.com
- **cn-ip6**：3437 → 3439（+2）
  - 新增：IP-CIDR6,2001:250::/30, IP-CIDR6,2001:254::/33, IP-CIDR6,2001:255::/32, IP-CIDR6,2001:4510:1480::/41, IP-CIDR6,2001:4510:400::/40, IP-CIDR6,2001:4511:1480::/41, IP-CIDR6,2001:7fa:5::/48, IP-CIDR6,2001:c68::/32 …
  - 删除：IP-CIDR6,2001:250::/30,no-resolve, IP-CIDR6,2001:254::/33,no-resolve, IP-CIDR6,2001:255::/32,no-resolve, IP-CIDR6,2001:4510:1480::/41,no-resolve, IP-CIDR6,2001:4510:400::/40,no-resolve, IP-CIDR6,2001:4511:1480::/41,no-resolve, IP-CIDR6,2001:7fa:5::/48,no-resolve, IP-CIDR6,2001:c68::/32,no-resolve …
- **game-platform**：534 → 484（-50）
  - 新增：DOMAIN-SUFFIX,store.steampowered.com
  - 删除：DOMAIN,a4e8s8k3.map2.ssl.hwcdn.net, DOMAIN,f3b7q2p3.ssl.hwcdn.net, DOMAIN,steambroadcast.akamaized.net, DOMAIN,steamcloudsweden.blob.core.windows.net, DOMAIN,steamcommunity-a.akamaihd.net, DOMAIN,steamcommunity-a.akamaihd.net.edgesuite.net, DOMAIN,steammobile.akamaized.net, DOMAIN,steamstore-a.akamaihd.net …
- **proxy**：18322 → 18324（+2）
  - 新增：DOMAIN-SUFFIX,debot.ai, DOMAIN-SUFFIX,remna.dev
- **reject-malware**：18399 → 18449（+50）
  - 新增：DOMAIN-SUFFIX,1.162.102.55, DOMAIN-SUFFIX,101.108.252.236, DOMAIN-SUFFIX,104.249.10.240, DOMAIN-SUFFIX,105.154.234.74, DOMAIN-SUFFIX,105.157.124.212, DOMAIN-SUFFIX,105.184.100.241, DOMAIN-SUFFIX,105.184.136.237, DOMAIN-SUFFIX,105.184.174.68 …
  - 删除：DOMAIN-SUFFIX,101.108.253.192, DOMAIN-SUFFIX,102.23.89.5, DOMAIN-SUFFIX,103.181.102.189, DOMAIN-SUFFIX,103.43.128.123, DOMAIN-SUFFIX,104.239.66.70, DOMAIN-SUFFIX,105.184.121.27, DOMAIN-SUFFIX,105.186.118.24, DOMAIN-SUFFIX,105.186.202.62 …
- **steam-direct**：0 → 122（+122）
  - 新增：DOMAIN,a4e8s8k3.map2.ssl.hwcdn.net, DOMAIN,f3b7q2p3.ssl.hwcdn.net, DOMAIN,steambroadcast.akamaized.net, DOMAIN,steamcloudsweden.blob.core.windows.net, DOMAIN,steamcommunity-a.akamaihd.net, DOMAIN,steamcommunity-a.akamaihd.net.edgesuite.net, DOMAIN,steammobile.akamaized.net, DOMAIN,steamstore-a.akamaihd.net …

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 40184 | 77966 | 96415 |
| overseas | 17995 | 55777 | 74226 |
| overseas-return | 16850 | 54632 | 73081 |
| cn-mainland-lite | 13381 | 51163 | 69612 |
