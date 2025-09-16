#!/usr/bin/env sh
set -eu

: "${ZAP_LOG_LEVEL:=INFO}"
: "${ZAP_STARTUP_TIMEOUT:=120}"
READY_URL="http://localhost:8080/JSON/core/view/version"

echo "[entrypoint] Configuring Firefox for headless mode (no X11 display needed)"
# Set Firefox to run in headless mode without X11
export MOZ_HEADLESS=1
export MOZ_DISABLE_CONTENT_SANDBOX=1
export MOZ_DISABLE_GMP_SANDBOX=1
export MOZ_DISABLE_RDD_SANDBOX=1
export MOZ_DISABLE_GPU_SANDBOX=1
export MOZ_DISABLE_SOCKET_PROCESS_SANDBOX=1
export MOZ_DISABLE_UTILITY_SANDBOX=1

# Create Firefox profile directory and configuration
FIREFOX_PROFILE_DIR="/home/zap/.mozilla/firefox/headless"
mkdir -p "$FIREFOX_PROFILE_DIR"

# Create Firefox prefs.js to force headless mode
cat > "$FIREFOX_PROFILE_DIR/prefs.js" << 'EOF'
// Force headless mode
user_pref("browser.dom.window.dump.enabled", true);
user_pref("browser.laterrun.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.page", 0);
user_pref("browser.startup.homepage", "about:blank");
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.tabs.warnOnCloseOtherTabs", false);
user_pref("browser.tabs.warnOnOpen", false);
user_pref("browser.warnOnQuit", false);
user_pref("dom.disable_beforeunload", true);
user_pref("dom.disable_open_during_load", false);
user_pref("dom.max_script_run_time", 0);
user_pref("dom.max_chrome_script_run_time", 0);
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 0);
user_pref("extensions.update.enabled", false);
user_pref("general.warnOnAboutConfig", false);
user_pref("media.navigator.enabled", false);
user_pref("media.peerconnection.enabled", false);
user_pref("network.manage-offline-status", false);
user_pref("offline-apps.allow_by_default", false);
user_pref("security.tls.insecure_fallback_hosts", "");
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.server", "");
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.coverage.enabled", false);
user_pref("toolkit.coverage.opt-out", true);
user_pref("toolkit.coverage.endpoint.base", "");
user_pref("browser.ping-centre.telemetry", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
user_pref("browser.ping-centre.telemetry", false);
user_pref("toolkit.telemetry.hybridContent.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.coverage.enabled", false);
user_pref("toolkit.coverage.opt-out", true);
user_pref("toolkit.coverage.endpoint.base", "");
user_pref("browser.ping-centre.telemetry", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
user_pref("browser.ping-centre.telemetry", false);
user_pref("toolkit.telemetry.hybridContent.enabled", false);
EOF

# Create Firefox profiles.ini
cat > "/home/zap/.mozilla/firefox/profiles.ini" << 'EOF'
[Install4F96D1934A9F5E70]
Default=headless
Locked=1

[Profile0]
Name=headless
IsRelative=1
Path=headless
Default=1
EOF

echo "[entrypoint] Firefox headless configuration created"

# Test Firefox headless mode
echo "[entrypoint] Testing Firefox headless mode..."
if firefox --headless --version >/dev/null 2>&1; then
  echo "[entrypoint] ✅ Firefox headless mode working correctly"
else
  echo "[entrypoint] ⚠️  Firefox headless test failed, but continuing..."
fi

echo "[entrypoint] Cleanup stale locks & broken addons (safe)"
rm -f /home/zap/.ZAP/*.lck /home/zap/.ZAP/*.lock /home/zap/.ZAP/.ZAP.lock 2>/dev/null || true
rm -f /home/zap/.ZAP/plugin/*.zap* 2>/dev/null || true

echo "[entrypoint] Starting ZAP (no API key, bind 0.0.0.0:8080)"
# Set JVM options via JAVA_OPTS environment variable
export JAVA_OPTS="-Djava.awt.headless=true -Dsun.java2d.xrender=false -Dsun.java2d.noddraw=true -Dsun.java2d.opengl=false -Dsun.java2d.pmoffscreen=false -Dsun.java2d.d3d=false -Dsun.java2d.ddoffscreen=false"

# Start ZAP with headless mode and no X11 dependencies
/zap/zap.sh \
  -daemon \
  -host 0.0.0.0 \
  -port 8080 \
  -config api.disablekey=true \
  -config api.addrs.addr.name=.* \
  -config api.addrs.addr.regex=true \
  -config logger.level="${ZAP_LOG_LEVEL}" &

echo "[entrypoint] Waiting for ZAP to be ready (timeout: ${ZAP_STARTUP_TIMEOUT}s)"
end=$(( $(date +%s) + ZAP_STARTUP_TIMEOUT ))
while :; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$READY_URL" || true)
  [ "$code" = "200" ] || [ "$code" = "403" ] && break
  [ "$(date +%s)" -ge "$end" ] && { echo >&2 "[entrypoint] ZAP failed to start within timeout"; exit 1; }
  sleep 2
done
echo "[entrypoint] ZAP is up."

echo "[entrypoint] Starting app: $*"
exec "$@"
