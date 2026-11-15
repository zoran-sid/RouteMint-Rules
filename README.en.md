# RouteMint-Rules

Routing profiles for mihomo, Shadowrocket, Surge, Loon, Quantumult X and sing-box. Bring your own proxy nodes.

| Profile | Direct | Proxy | Default |
|---|---|---|---|
| `cn-mainland` | Mainland services and local networks | Google, YouTube, AI and overseas services | Proxy |
| `overseas` | Google, YouTube and ordinary traffic | AI and selected streaming services | Direct |
| `overseas-return` | Ordinary traffic | Mainland region-restricted media | Direct |
| `cn-mainland-lite` | Mainland services and local networks | AI and other overseas traffic | Proxy |

See the [Chinese guide](README.md) for full configuration URLs, QR codes for every client, import steps and troubleshooting. Quantumult X QR codes open a download for manual import. sing-box profiles are templates with a local SOCKS placeholder; merge your own outbounds before use. Classic Clash cores do not support the MRS rule providers.

Streaming selectors use fixed manual choices. Select a verified mainland exit in the return group after import; its initial choice is REJECT. DNS follows each service policy in mihomo and sing-box. The default advertising tier is `ads-light`; change the URL path to `ads-off` to diagnose playback problems.

Public templates carry no credentials. Keep personal node sources in a local or privately hosted copy; remote rule sets update separately. Remove Surge's managed profile header from a customized local copy to retain personal changes.
