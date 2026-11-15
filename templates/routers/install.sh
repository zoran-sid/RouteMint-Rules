#!/bin/sh
# Import routing into a staged copy; credentials stay in the existing UCI file.
set -eu
umask 077
APP='@CLIENT@'
HERE="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
MODE="${1:---check-only}"
case "$MODE" in --check-only|--apply) ;; *) echo 'Usage: install.sh [--check-only|--apply]' >&2; exit 1 ;; esac
for cmd in uci ucode curl sing-box sha256sum; do
    command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 1; }
done
[ -f "/etc/config/$APP" ] || { echo "Install $APP and add a node first" >&2; exit 1; }
[ -z "$(uci -q changes "$APP")" ] || { echo "Save or revert pending $APP edits first" >&2; exit 1; }
LOCK="/var/lock/routemint-$APP.lock"
mkdir "$LOCK" 2>/dev/null || { echo 'Another import is running' >&2; exit 1; }
STAGE=""
cleanup() {
    rc=$?
    trap - EXIT INT TERM
    case "$STAGE" in /tmp/routemint-*) rm -rf "$STAGE" ;; esac
    rmdir "$LOCK" 2>/dev/null || true
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
STAGE="$(mktemp -d /tmp/routemint-XXXXXX)"
mkdir -p "$STAGE/config" "$STAGE/delta"
cp "/etc/config/$APP" "$STAGE/config/$APP"
ORIGINAL="$(sha256sum "/etc/config/$APP" | awk '{print $1}')"
export RM_STAGE="$STAGE" RM_PLAN="$HERE/profile.json" RM_APP="$APP"
# HomeProxy's homeproxy.uc module needs this path, including preview generation.
ucode -L /etc/homeproxy/scripts -S "$HERE/configure.uc"
while IFS= read -r url; do
    if ! curl -fsSL --connect-timeout 10 --max-time 30 "$url" -o "$STAGE/rules.srs"; then
        SOCKS="${RM_SOCKS:-}"
        if [ -z "$SOCKS" ] && [ "$APP" = homeproxy ]; then
            PORT="$(uci -q get homeproxy.infra.mixed_port 2>/dev/null || true)"
            case "$PORT" in ''|*[!0-9]*) PORT=5330 ;; esac
            SOCKS="127.0.0.1:$PORT"
        fi
        [ -n "$SOCKS" ] || { echo 'Set RM_SOCKS for rule downloads through the existing proxy' >&2; exit 1; }
        curl -fsSL --socks5-hostname "$SOCKS" --connect-timeout 10 --max-time 90 "$url" -o "$STAGE/rules.srs"
    fi
    sing-box rule-set decompile --output "$STAGE/rules.json" "$STAGE/rules.srs" >/dev/null
done < "$STAGE/urls"
if [ "$APP" = homeproxy ]; then
    [ -f "$STAGE/generate-preview.uc" ] || { echo 'HomeProxy generator preview unavailable' >&2; exit 1; }
    ucode -L /etc/homeproxy/scripts -S "$STAGE/generate-preview.uc"
    sing-box check -c "$STAGE/preview.json"
fi
[ "$MODE" = --apply ] || { echo 'Checks passed; live configuration is unchanged. Use --apply to import.'; exit 0; }
[ "$(sha256sum "/etc/config/$APP" | awk '{print $1}')" = "$ORIGINAL" ] || {
    echo "$APP changed during preparation; aborted" >&2; exit 1;
}
BACKUP="/root/routemint-$APP-backup-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$BACKUP"
cp -p "/etc/config/$APP" "$BACKUP/$APP"
cp "$STAGE/config/$APP" "/etc/config/$APP.routemint-new"
chmod 600 "/etc/config/$APP.routemint-new"
mv -f "/etc/config/$APP.routemint-new" "/etc/config/$APP"
echo "Imported. Backup: $BACKUP/$APP"
if [ "$APP" = homeproxy ]; then
    echo 'HomeProxy: custom routing is configured. Enable the client if needed, then Save & Apply in LuCI.'
else
    echo 'PassWall: select the RouteMint sing-box shunt node for TCP and UDP, then Save & Apply in LuCI.'
fi
# Do not switch proxy managers or restart services on a router with proxy-guard.
