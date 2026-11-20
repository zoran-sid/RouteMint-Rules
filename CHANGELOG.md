# 变更日志

由每日构建自动生成。只记录规则层面的变化，格式变化不计。

## 2026-11-20

- **cn-ip**：6221 → 6227（+6）
  - 新增：IP-CIDR,1.0.1.0/24, IP-CIDR,1.0.2.0/23, IP-CIDR,1.0.32.0/19, IP-CIDR,1.0.8.0/21, IP-CIDR,1.1.0.0/24, IP-CIDR,1.1.16.0/20, IP-CIDR,1.1.2.0/23, IP-CIDR,1.1.32.0/19 …
  - 删除：IP-CIDR,1.0.1.0/24,no-resolve, IP-CIDR,1.0.2.0/23,no-resolve, IP-CIDR,1.0.32.0/19,no-resolve, IP-CIDR,1.0.8.0/21,no-resolve, IP-CIDR,1.1.0.0/24,no-resolve, IP-CIDR,1.1.16.0/20,no-resolve, IP-CIDR,1.1.2.0/23,no-resolve, IP-CIDR,1.1.32.0/19,no-resolve …
- **cn-ip6**：3444 → 3446（+2）
  - 新增：IP-CIDR6,2001:250::/30, IP-CIDR6,2001:254::/33, IP-CIDR6,2001:255::/32, IP-CIDR6,2001:4510:1480::/41, IP-CIDR6,2001:4510:400::/40, IP-CIDR6,2001:4511:1480::/41, IP-CIDR6,2001:7fa:5::/48, IP-CIDR6,2001:c68::/32 …
  - 删除：IP-CIDR6,2001:250::/30,no-resolve, IP-CIDR6,2001:254::/33,no-resolve, IP-CIDR6,2001:255::/32,no-resolve, IP-CIDR6,2001:4510:1480::/41,no-resolve, IP-CIDR6,2001:4510:400::/40,no-resolve, IP-CIDR6,2001:4511:1480::/41,no-resolve, IP-CIDR6,2001:7fa:5::/48,no-resolve, IP-CIDR6,2001:c68::/32,no-resolve …
- **reject-malware**：18609 → 18823（+214）
  - 新增：DOMAIN-SUFFIX,101.108.5.206, DOMAIN-SUFFIX,101.108.76.71, DOMAIN-SUFFIX,103.145.31.238, DOMAIN-SUFFIX,103.159.152.118, DOMAIN-SUFFIX,103.173.173.98, DOMAIN-SUFFIX,103.182.59.110, DOMAIN-SUFFIX,103.187.151.107, DOMAIN-SUFFIX,103.209.184.118 …
  - 删除：DOMAIN-SUFFIX,1.92.101.221, DOMAIN-SUFFIX,102.216.69.112, DOMAIN-SUFFIX,105.158.197.238, DOMAIN-SUFFIX,105.184.63.144, DOMAIN-SUFFIX,105.186.163.117, DOMAIN-SUFFIX,105.225.189.234, DOMAIN-SUFFIX,108.69.135.26, DOMAIN-SUFFIX,109.245.220.229 …

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 40229 | 78619 | 97442 |
| overseas | 18039 | 56429 | 75252 |
| overseas-return | 16894 | 55284 | 74107 |
| cn-mainland-lite | 13418 | 51808 | 70631 |

## 2026-11-19

- **cn**：6200 → 6220（+20）
  - 新增：DOMAIN-SUFFIX,172.com, DOMAIN-SUFFIX,1qianbao.com, DOMAIN-SUFFIX,1y.com, DOMAIN-SUFFIX,1ycdn.com, DOMAIN-SUFFIX,4008000000.com, DOMAIN-SUFFIX,ajkimg.com, DOMAIN-SUFFIX,baishan.com, DOMAIN-SUFFIX,baishancloud.com …
- **cn-ip**：6222 → 6221（-1）
  - 新增：IP-CIDR,1.0.1.0/24, IP-CIDR,1.0.2.0/23, IP-CIDR,1.0.32.0/19, IP-CIDR,1.0.8.0/21, IP-CIDR,1.1.0.0/24, IP-CIDR,1.1.16.0/20, IP-CIDR,1.1.2.0/23, IP-CIDR,1.1.32.0/19 …
  - 删除：IP-CIDR,1.0.1.0/24,no-resolve, IP-CIDR,1.0.2.0/23,no-resolve, IP-CIDR,1.0.32.0/19,no-resolve, IP-CIDR,1.0.8.0/21,no-resolve, IP-CIDR,1.1.0.0/24,no-resolve, IP-CIDR,1.1.16.0/20,no-resolve, IP-CIDR,1.1.2.0/23,no-resolve, IP-CIDR,1.1.32.0/19,no-resolve …
- **cn-ip6**：3441 → 3444（+3）
  - 新增：IP-CIDR6,2001:250::/30, IP-CIDR6,2001:254::/33, IP-CIDR6,2001:255::/32, IP-CIDR6,2001:4510:1480::/41, IP-CIDR6,2001:4510:400::/40, IP-CIDR6,2001:4511:1480::/41, IP-CIDR6,2001:7fa:5::/48, IP-CIDR6,2001:c68::/32 …
  - 删除：IP-CIDR6,2001:250::/30,no-resolve, IP-CIDR6,2001:254::/33,no-resolve, IP-CIDR6,2001:255::/32,no-resolve, IP-CIDR6,2001:4510:1480::/41,no-resolve, IP-CIDR6,2001:4510:400::/40,no-resolve, IP-CIDR6,2001:4511:1480::/41,no-resolve, IP-CIDR6,2001:7fa:5::/48,no-resolve, IP-CIDR6,2001:c68::/32,no-resolve …
- **reject-ads**：37661 → 37722（+61）
  - 新增：DOMAIN-SUFFIX,aa.beeg.porn, DOMAIN-SUFFIX,ad1n.net, DOMAIN-SUFFIX,adipolo.live, DOMAIN-SUFFIX,ads-bidstrade.io, DOMAIN-SUFFIX,airyorchid.com, DOMAIN-SUFFIX,aj1070.online, DOMAIN-SUFFIX,aj2294.online, DOMAIN-SUFFIX,aj2295.online …
  - 删除：DOMAIN-SUFFIX,ns150.aj1070.online, DOMAIN-SUFFIX,ns186.aj1070.online, DOMAIN-SUFFIX,ribsiuds.qpon, DOMAIN-SUFFIX,s.dslrph.com, DOMAIN-SUFFIX,s.dttxqa.com, DOMAIN-SUFFIX,s.dtxelz.com, DOMAIN-SUFFIX,s.dtyvtj.com
- **reject-malware**：18580 → 18609（+29）
  - 新增：DOMAIN-SUFFIX,103.245.204.42, DOMAIN-SUFFIX,103.78.81.106, DOMAIN-SUFFIX,104.168.70.178, DOMAIN-SUFFIX,104.251.180.214, DOMAIN-SUFFIX,105.224.59.0, DOMAIN-SUFFIX,105.224.75.116, DOMAIN-SUFFIX,105.226.64.72, DOMAIN-SUFFIX,109.165.41.47 …
  - 删除：DOMAIN-SUFFIX,101.108.7.49, DOMAIN-SUFFIX,107.174.251.112, DOMAIN-SUFFIX,107.175.88.87, DOMAIN-SUFFIX,109.108.84.121, DOMAIN-SUFFIX,109.166.211.222, DOMAIN-SUFFIX,109.69.79.44, DOMAIN-SUFFIX,110.186.229.108, DOMAIN-SUFFIX,112.232.226.68 …

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 40221 | 78611 | 97220 |
| overseas | 18031 | 56421 | 75030 |
| overseas-return | 16886 | 55276 | 73885 |
| cn-mainland-lite | 13412 | 51802 | 70411 |

## 2026-11-18

无规则变化。

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 40199 | 78528 | 97108 |
| overseas | 18009 | 56338 | 74918 |
| overseas-return | 16864 | 55193 | 73773 |
| cn-mainland-lite | 13393 | 51722 | 70302 |
