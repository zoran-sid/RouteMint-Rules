# 变更日志

由每日构建自动生成。只记录规则层面的变化，格式变化不计。

## 2026-11-21

- **cn-ip**：6223 → 6219（-4）
  - 新增：IP-CIDR,1.0.1.0/24, IP-CIDR,1.0.2.0/23, IP-CIDR,1.0.32.0/19, IP-CIDR,1.0.8.0/21, IP-CIDR,1.1.0.0/24, IP-CIDR,1.1.16.0/20, IP-CIDR,1.1.2.0/23, IP-CIDR,1.1.32.0/19 …
  - 删除：IP-CIDR,1.0.1.0/24,no-resolve, IP-CIDR,1.0.2.0/23,no-resolve, IP-CIDR,1.0.32.0/19,no-resolve, IP-CIDR,1.0.8.0/21,no-resolve, IP-CIDR,1.1.0.0/24,no-resolve, IP-CIDR,1.1.16.0/20,no-resolve, IP-CIDR,1.1.2.0/23,no-resolve, IP-CIDR,1.1.32.0/19,no-resolve …
- **proxy**：18325 → 18331（+6）
  - 新增：DOMAIN-SUFFIX,51papaya.com, DOMAIN-SUFFIX,fanza.jp, DOMAIN-SUFFIX,hkt, DOMAIN-SUFFIX,pccw, DOMAIN-SUFFIX,replit.com, DOMAIN-SUFFIX,tortoisegit.org
- **reject-malware**：18918 → 18942（+24）
  - 新增：DOMAIN-SUFFIX,101.29.21.174, DOMAIN-SUFFIX,105.154.96.249, DOMAIN-SUFFIX,105.224.249.164, DOMAIN-SUFFIX,110.188.42.181, DOMAIN-SUFFIX,110.39.41.202, DOMAIN-SUFFIX,112.248.80.87, DOMAIN-SUFFIX,112.248.97.125, DOMAIN-SUFFIX,115.203.74.234 …
  - 删除：DOMAIN-SUFFIX,101.109.237.184, DOMAIN-SUFFIX,101.29.22.214, DOMAIN-SUFFIX,103.151.43.183, DOMAIN-SUFFIX,103.90.207.13, DOMAIN-SUFFIX,106.15.6.205, DOMAIN-SUFFIX,112.237.148.180, DOMAIN-SUFFIX,112.248.106.88, DOMAIN-SUFFIX,113.229.190.135 …
- **streaming-others**：1587 → 1605（+18）
  - 新增：DOMAIN-SUFFIX,bravotv.com, DOMAIN-SUFFIX,cnbccouncils.com, DOMAIN-SUFFIX,focusfeatures.com, DOMAIN-SUFFIX,hayu.com, DOMAIN-SUFFIX,illumination.com, DOMAIN-SUFFIX,nbcumv.com, DOMAIN-SUFFIX,nbcunicareers.com, DOMAIN-SUFFIX,nbcuniversalprivacy.com …
  - 删除：DOMAIN-SUFFIX,msnbc.com

| 预设 | ads-off | ads-light | ads-strict |
|---|---|---|---|
| cn-mainland | 40117 | 78507 | 97449 |
| overseas | 18033 | 56423 | 75365 |
| overseas-return | 16888 | 55278 | 74220 |
| cn-mainland-lite | 13414 | 51804 | 70746 |
