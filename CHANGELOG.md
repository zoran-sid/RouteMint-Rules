# 变更日志

由每日构建自动生成。只记录规则层面的变化，格式变化不计。

## 2026-11-15

- **cn-region-locked**：24 → 30（+6）
  - 新增：DOMAIN,ykimg.alicdn.com, DOMAIN-SUFFIX,71edge.com, DOMAIN-SUFFIX,acgvideo.com, DOMAIN-SUFFIX,qiyipic.com, DOMAIN-SUFFIX,qy.net, DOMAIN-SUFFIX,tudou.com
- **google**：619 → 627（+8）
  - 新增：DOMAIN-SUFFIX,go-lang.com, DOMAIN-SUFFIX,go-lang.net, DOMAIN-SUFFIX,go-lang.org, DOMAIN-SUFFIX,go.dev, DOMAIN-SUFFIX,godoc.org, DOMAIN-SUFFIX,golang.com, DOMAIN-SUFFIX,golang.net, DOMAIN-SUFFIX,golang.org
- **netflix**：24 → 28（+4）
  - 新增：DOMAIN-KEYWORD,apiproxy-device-prod-nlb-, DOMAIN-KEYWORD,apiproxy-website-nlb-prod-, DOMAIN-KEYWORD,dualstack.apiproxy-, DOMAIN-KEYWORD,dualstack.ichnaea-web-

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 39983 | 77765 | 96164 |
| overseas | 1423 | 39205 | 57604 |
| overseas-return | 16137 | 53919 | 72318 |
| cn-mainland-lite | 12670 | 50452 | 68851 |

## 2026-11-14

- **cn-ip**：6211 → 6219（+8）
  - 新增：IP-CIDR,1.0.1.0/24, IP-CIDR,1.0.2.0/23, IP-CIDR,1.0.32.0/19, IP-CIDR,1.0.8.0/21, IP-CIDR,1.1.0.0/24, IP-CIDR,1.1.16.0/20, IP-CIDR,1.1.2.0/23, IP-CIDR,1.1.32.0/19 …
  - 删除：IP-CIDR,1.0.1.0/24,no-resolve, IP-CIDR,1.0.2.0/23,no-resolve, IP-CIDR,1.0.32.0/19,no-resolve, IP-CIDR,1.0.8.0/21,no-resolve, IP-CIDR,1.1.0.0/24,no-resolve, IP-CIDR,1.1.16.0/20,no-resolve, IP-CIDR,1.1.2.0/23,no-resolve, IP-CIDR,1.1.32.0/19,no-resolve …
- **cn-ip6**：3428 → 3437（+9）
  - 新增：IP-CIDR6,2001:250::/30, IP-CIDR6,2001:254::/33, IP-CIDR6,2001:255::/32, IP-CIDR6,2001:4510:1480::/41, IP-CIDR6,2001:4510:400::/40, IP-CIDR6,2001:4511:1480::/41, IP-CIDR6,2001:7fa:5::/48, IP-CIDR6,2001:c68::/32 …
  - 删除：IP-CIDR6,2001:250::/30,no-resolve, IP-CIDR6,2001:254::/33,no-resolve, IP-CIDR6,2001:255::/32,no-resolve, IP-CIDR6,2001:4510:1480::/41,no-resolve, IP-CIDR6,2001:4510:400::/40,no-resolve, IP-CIDR6,2001:4511:1480::/41,no-resolve, IP-CIDR6,2001:7fa:5::/48,no-resolve, IP-CIDR6,2001:c68::/32,no-resolve …
- **reject-ads**：37113 → 37114（+1）
  - 新增：DOMAIN-SUFFIX,mangamad.com
- **reject-malware**：18377 → 18399（+22）
  - 新增：DOMAIN-SUFFIX,100.70.23.103, DOMAIN-SUFFIX,103.43.128.123, DOMAIN-SUFFIX,105.184.185.76, DOMAIN-SUFFIX,105.184.222.233, DOMAIN-SUFFIX,105.225.189.149, DOMAIN-SUFFIX,110.85.98.184, DOMAIN-SUFFIX,112.192.143.98, DOMAIN-SUFFIX,112.232.224.88 …
  - 删除：DOMAIN-SUFFIX,101.109.201.128, DOMAIN-SUFFIX,109.69.79.44, DOMAIN-SUFFIX,110.36.25.33, DOMAIN-SUFFIX,110.36.80.162, DOMAIN-SUFFIX,110.36.86.83, DOMAIN-SUFFIX,110.39.227.44, DOMAIN-SUFFIX,112.228.4.224, DOMAIN-SUFFIX,112.239.122.112 …

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 39971 | 77753 | 96152 |
| overseas | 615 | 38397 | 56796 |
| overseas-return | 16131 | 53913 | 72312 |
| cn-mainland-lite | 12670 | 50452 | 68851 |
