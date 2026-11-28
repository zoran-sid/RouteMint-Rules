// Native UCI adapter. Modifies only RM_STAGE; the installer applies it atomically.
import { cursor } from 'uci';
import { readfile, writefile } from 'fs';
const stage = getenv('RM_STAGE');
const plan = json(readfile(getenv('RM_PLAN')));
const app = getenv('RM_APP');
if (plan.schema !== 1 || plan.client !== app || !length(plan.rules)) die('Invalid routing plan');
const hp = app === 'homeproxy';
if (!hp && app !== 'passwall') die('Unsupported application');
const ctx = cursor(stage + '/config', stage + '/delta');
ctx.load(app) || die('Cannot load staged configuration');
function get(s, o) { return ctx.get(app, s, o); }
function set(s, o, v) { ctx.set(app, s, o, v) || die('Cannot set ' + s + '.' + o); }
function list(v) { return type(v) === 'array' ? v : (v ? [v] : []); }
function node(v) {
    if (get(v) !== (hp ? 'node' : 'nodes')) die('Unknown node ID: ' + v);
    if (!hp && match(get(v, 'protocol') || '', /^_/)) die('Select a real PassWall node, not another virtual shunt/balancer');
    return v;
}
let main = getenv('RM_PROXY_NODE');
let defaults = [];
if (main) defaults = [node(main)];
else if (hp) {
    let old = get('routing', 'default_outbound');
    let chosen = get('config', 'routing_mode') === 'custom' && get(old) === 'routing_node' ? old : 'config';
    let selected = get(chosen, chosen === 'config' ? 'main_node' : 'node');
    defaults = selected === 'urltest' ? list(get(chosen, chosen === 'config' ? 'main_urltest_nodes' : 'urltest_nodes')) : list(selected);
} else {
    ctx.foreach(app, 'global', (s) => { if (!main) main = s.tcp_node; });
    if (get(main, 'protocol') === '_shunt') main = get(main, 'default_node');
    defaults = list(main);
}
if (!length(defaults)) die('Set RM_PROXY_NODE to an existing node ID');
for (let n in defaults) node(n);
let targets = {};
for (let id, group in plan.groups) {
    const override = getenv('RM_' + uc(id) + '_NODE');
    if (override) targets[id] = [node(override)];
    else if (group.default === 'direct' || group.default === 'reject') targets[id] = group.default;
    else targets[id] = defaults;
}
// Delete only our own previous sections. Preserve node subscriptions and credentials.
let remove = [];
ctx.foreach(app, null, (s) => {
    if (s.routemint === '1') push(remove, s['.name']);
    else if (hp && index(['routing_node', 'routing_rule', 'ruleset', 'dns_server', 'dns_rule'], s['.type']) >= 0)
        set(s['.name'], 'enabled', '0');
});
for (let s in remove) ctx.delete(app, s);
function section(id, kind, label) {
    if (get(id)) die('Reserved section exists: ' + id);
    ctx.set(app, id, kind) || die('Cannot create section');
    set(id, 'routemint', '1');
    set(id, hp ? 'label' : 'remarks', label);
    if (hp) set(id, 'enabled', '1');
}
function policy(p) {
    if (p !== 'direct' && p !== 'reject') {
        if (!(p in targets)) die('Unknown policy: ' + p);
        if (type(targets[p]) === 'string') p = targets[p];
        else return hp ? 'rm_' + p : targets[p][0];
    }
    return hp ? (p === 'direct' ? 'direct-out' : 'block-out') : (p === 'direct' ? '_direct' : '_blackhole');
}
if (hp) {
    for (let id, values in targets) {
        if (type(values) !== 'array') continue;
        const name = 'rm_' + id;
        section(name, 'routing_node', plan.groups[id].label);
        set(name, 'node', 'urltest');
        set(name, 'urltest_nodes', values);
        set(name, 'urltest_url', 'https://www.gstatic.com/generate_204');
        set(name, 'urltest_interval', '300');
        set(name, 'domain_resolver', 'default-dns');
        const dns = 'rm_dns_' + id;
        section(dns, 'dns_server', 'RouteMint DNS ' + id);
        const domestic = id === 'cn_return';
        set(dns, 'type', 'https');
        set(dns, 'server', domestic ? '223.5.5.5' : '1.1.1.1');
        set(dns, 'server_port', '443');
        set(dns, 'path', '/dns-query');
        set(dns, 'tls_sni', domestic ? 'dns.alidns.com' : 'cloudflare-dns.com');
        set(dns, 'outbound', name);
    }
} else {
    section('rm_shunt', 'nodes', 'RouteMint ' + plan.preset + ' / ' + plan.ads);
    set('rm_shunt', 'type', 'sing-box');
    set('rm_shunt', 'protocol', '_shunt');
    set('rm_shunt', 'shunt_group', 'RouteMint');
    set('rm_shunt', 'default_node', policy(plan.default));
}
let urls = [];
for (let index, rule in plan.rules) {
    if (!match(rule.category, /^[a-z0-9-]+$/) || !match(rule.url, /^https:\/\/raw\.githubusercontent\.com\//)) die('Invalid rule URL');
    push(urls, rule.url);
    const key = replace(rule.category, /-/g, '_');
    const id = 'rm_route_' + key;
    const outbound = policy(rule.policy);
    if (hp) {
        const rs = 'rm_set_' + key;
        section(rs, 'ruleset', 'RouteMint ' + rule.category);
        set(rs, 'type', 'remote');
        set(rs, 'format', 'binary');
        set(rs, 'url', rule.url);
        set(rs, 'outbound', plan.preset === 'overseas' || plan.preset === 'overseas-return' ? 'direct-out' : 'rm_proxy');
        set(rs, 'update_interval', '1d');
        section(id, 'routing_rule', 'RouteMint ' + rule.category);
        set(id, 'rule_set', [rs]);
        set(id, 'action', outbound === 'block-out' ? 'reject' : 'route');
        if (outbound !== 'block-out') set(id, 'outbound', outbound);
        if (!rule.domains) continue;
        const dns = 'rm_query_' + key;
        section(dns, 'dns_rule', 'RouteMint DNS ' + rule.category);
        set(dns, 'rule_set', [rs]);
        set(dns, 'action', outbound === 'block-out' ? 'reject' : 'route');
        if (outbound !== 'block-out')
            set(dns, 'server', rule.dns === 'local' || outbound === 'direct-out' ? 'default-dns' : 'rm_dns_' + rule.policy);
    } else {
        section(id, 'shunt_rules', 'RouteMint ' + rule.category);
        set(id, 'group', 'RouteMint');
        set(id, rule.domains ? 'domain_list' : 'ip_list', 'rule-set:remote:' + rule.url);
        set('rm_shunt', id, outbound);
    }
}
if (hp) {
    if (!get('routing')) ctx.set(app, 'routing', 'homeproxy');
    if (!get('dns')) ctx.set(app, 'dns', 'homeproxy');
    set('config', 'routing_mode', 'custom');
    set('routing', 'default_outbound', policy(plan.default));
    set('routing', 'default_outbound_dns', 'default-dns');
    set('routing', 'bypass_cn_traffic', '0');
    ctx.delete(app, 'routing', 'domain_strategy');
    set('dns', 'default_server', policy(plan.default) === 'direct-out' ? 'default-dns' : 'rm_dns_' + plan.default);
    const generator = readfile('/etc/homeproxy/scripts/generate_client.uc');
    if (!generator) die('HomeProxy generator is missing');
    const cursor_line = 'const uci = cursor();';
    const output_line = "writefile(RUN_DIR + '/sing-box-c.json',";
    if (length(split(generator, cursor_line)) !== 2 || length(split(generator, output_line)) !== 2)
        die('HomeProxy generator layout changed; preview is required');
    let preview = join("const uci = cursor(getenv('RM_STAGE') + '/config', getenv('RM_STAGE') + '/delta');", split(generator, cursor_line));
    preview = join("writefile(getenv('RM_STAGE') + '/preview.json',", split(preview, output_line));
    writefile(stage + '/generate-preview.uc', preview);
}
ctx.commit(app) || die('Cannot commit staged configuration');
writefile(stage + '/urls', join('\n', urls) + '\n');
print('Prepared ', app, ' / ', plan.preset, ' / ', plan.ads, '\n');
