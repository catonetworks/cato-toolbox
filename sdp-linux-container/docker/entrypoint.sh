#!/usr/bin/env bash
#
# entrypoint.sh — launch the Cato SDP client inside a container (user/password auth).
#
# Auth model (confirmed empirically + with Cato support docs):
#   * There is NO certificate-only authentication. A device certificate is ZTNA device-posture
#     (a "device check"), layered ON TOP of user auth — it never replaces it.
#   * Headless / no-GUI devices cannot use the OAuth SSO device-flow (Cato returns
#     "USER_NOT_ALLOWED — Only 'TVs and Limited Input devices' can use OAuth 2.0"), so OAuth
#     accounts cannot be used unattended. The unattended path is manual user/password:
#       cato-sdp start --user <email> --account <account> --password=<pw>
#     The user must be a password-activated (non-OAuth) account.
#
# Process model (from the native install):
#   * cato-clientd  — daemon, runs as root (needs NET_ADMIN + /dev/net/tun), builds the tunnel.
#   * cato-sdp      — CLI; runs as root here (opens the daemon pipes directly). CATO_CLI_USER can
#     drop it to a non-root user, but that user must be in the cato-client group.
#   A bare `cato-sdp start` with no running daemon is a no-op, so we start the daemon first,
#   wait for its control pipe, THEN issue start.
#
# Container-network preparation (see prepare_container_network) — REQUIRED for the tunnel to hold:
#   * /etc/resolv.conf is a Docker bind-mount; the client backs up DNS by renaming it, which
#     fails on a mountpoint. We convert it to a regular file first (needs CAP_SYS_ADMIN).
#   * the client installs 'default dev tun0' at metric 0 and refuses if a metric-0 default
#     already exists (Docker's bridge default); we re-add the bridge default at metric 100
#     (needs NET_ADMIN).
#
set -euo pipefail

log() { echo "[entrypoint] $*"; }

: "${CATO_ACCOUNT:?CATO_ACCOUNT is not set — copy docker/.env.example to docker/.env and set your Cato account name (see DEPLOYMENT.md Step 2)}"
: "${CATO_USER:?CATO_USER is not set — set it in docker/.env (e.g. user@example.com)}"

# Resolve the password. PREFER a file (a Docker/Kubernetes secret mounted at a path) over a plain
# env var, so the secret never enters the container environment (docker inspect / /proc/1/environ).
# This is the standard *_FILE convention (postgres/mysql images use it) and is substrate-agnostic —
# the SAME image works on:
#   * Docker Compose — secrets: mounts the file at /run/secrets/cato_password; set
#                      CATO_PASSWORD_FILE=/run/secrets/cato_password
#   * Kubernetes     — mount a Secret volume, point CATO_PASSWORD_FILE at the mounted file
#                      (Secret volumes are tmpfs — the plaintext never touches node disk)
#   * any host       — bind-mount a 0400 file and point CATO_PASSWORD_FILE at it
# CATO_PASSWORD (plain env) still works as a fallback for quick local tests, but it sits in the
# environment and is discouraged for anything but throwaway use.
if [[ -n "${CATO_PASSWORD_FILE:-}" ]]; then
  [[ -r "$CATO_PASSWORD_FILE" ]] || { log "ERROR: CATO_PASSWORD_FILE=$CATO_PASSWORD_FILE is not readable." >&2; exit 1; }
  if [[ -n "${CATO_PASSWORD:-}" ]]; then
    log "WARNING: both CATO_PASSWORD_FILE and CATO_PASSWORD are set; using the file." >&2
  fi
  # $(< file) strips trailing newlines (editors/`echo` add them); the password must not rely on one.
  CATO_PASSWORD="$(< "$CATO_PASSWORD_FILE")"
  [[ -n "$CATO_PASSWORD" ]] || { log "ERROR: CATO_PASSWORD_FILE=$CATO_PASSWORD_FILE is empty." >&2; exit 1; }
fi
: "${CATO_PASSWORD:?No password — create docker/secrets/cato_password (the compose secret mounts it at CATO_PASSWORD_FILE), or set CATO_PASSWORD directly. Use a password-activated, non-OAuth account.}"
# Keep the password a shell-local variable only — never let child processes inherit it via the
# environment (it is handed to cato-sdp on argv, not through the environment).
export -n CATO_PASSWORD 2>/dev/null || true

CATO_EXTRA_ARGS="${CATO_EXTRA_ARGS:-}"      # e.g. "--route 10.0.0.0/8" split-tunnel
CLI_USER="${CATO_CLI_USER:-}"               # empty = run CLI as root (default). Set a username to
                                            # drop privileges, but that user must be in the
                                            # cato-client group to reach the daemon pipes.
PIPE_WAIT_S="${CATO_PIPE_WAIT_S:-30}"
RETRY_MAX="${CATO_RETRY_MAX:-0}"            # connect attempts; 0 = retry forever (with backoff)
BACKOFF_CAP_S="${CATO_BACKOFF_CAP_S:-60}"

DAEMON=/usr/sbin/cato-clientd
PIPE_IN=/var/run/cato-sdp.i
DAEMON_PID=""
_cleaning=0

# Run the CLI. Default is root (opens the daemon pipes directly); CATO_CLI_USER drops privilege.
# NOTE: never pass --password through `log`.
sdp() {
  if [[ -n "$CLI_USER" && "$CLI_USER" != "root" ]]; then
    runuser -u "$CLI_USER" -- cato-sdp "$@"
  else
    cato-sdp "$@"
  fi
}

# Two Docker-specific network fixes the client needs before it can BUILD and HOLD the tunnel
# (both confirmed from the daemon log / connect errors — neither is auth/posture related):
prepare_container_network() {
  # FIX 1 (DNS): Docker bind-mounts /etc/resolv.conf as a mountpoint. The client backs up DNS by
  # RENAMING resolv.conf, which fails on a mountpoint ("Failed to DNS" -> the client self-aborts
  # the tunnel after ~8s). Convert it to a regular file so the rename works. Needs CAP_SYS_ADMIN.
  if mount 2>/dev/null | grep -q ' /etc/resolv.conf '; then
    if cp /etc/resolv.conf /run/resolv.conf.real && umount /etc/resolv.conf 2>/dev/null; then
      if cp /run/resolv.conf.real /etc/resolv.conf; then
        log "resolv.conf converted (bind-mount -> regular file) for DNS rewrite."
      else
        log "ERROR: failed to restore /etc/resolv.conf after umount — DNS would be broken." >&2
        exit 1
      fi
      rm -f /run/resolv.conf.real
    else
      log "WARNING: could not umount /etc/resolv.conf — add --cap-add=SYS_ADMIN or DNS setup fails." >&2
    fi
  fi
  # FIX 2 (route): the client installs 'default dev tun0' at metric 0 and REFUSES if a metric-0
  # default already exists (Docker's bridge default). Re-add the bridge default at metric 100 so
  # the client's tunnel default wins. Needs NET_ADMIN. Parse 'via'/'dev' by name (a gateway-less
  # or absent default route is skipped safely), and ADD-before-delete so we never strand the netns.
  local route_line gw="" dev="" tok prev=""
  route_line="$(ip route show default 2>/dev/null | head -1)"
  if [[ "$route_line" == default\ * ]]; then
    for tok in $route_line; do
      [[ "$prev" == "via" ]] && gw="$tok"
      [[ "$prev" == "dev" ]] && dev="$tok"
      prev="$tok"
    done
    if [[ -n "$gw" && -n "$dev" ]]; then
      # add the metric-100 default first (connectivity never drops), THEN remove the metric-0 one.
      if ip route replace default via "$gw" dev "$dev" metric 100 2>/dev/null; then
        ip route del default metric 0 2>/dev/null || true
        log "bumped bridge default route to metric 100 (clears metric-0 for tun0)."
      else
        log "WARNING: could not add metric-100 default; routes untouched (tun0 install may fail)." >&2
      fi
    fi
  fi
}

# Idempotent teardown — runs on ANY exit (EXIT trap), so we never leak a live tunnel daemon.
cleanup() {
  [[ "$_cleaning" == 1 ]] && return
  _cleaning=1
  log "disconnecting Cato client..."
  sdp stop 2>/dev/null || true
  if [[ -n "$DAEMON_PID" ]] && kill -0 "$DAEMON_PID" 2>/dev/null; then
    kill "$DAEMON_PID" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$DAEMON_PID" 2>/dev/null || break; sleep 0.25; done
    kill -9 "$DAEMON_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

# Preflight: tunnel device must be passed through (cap_add NET_ADMIN + devices /dev/net/tun).
if [[ ! -c /dev/net/tun ]]; then
  log "ERROR: /dev/net/tun missing. Run with: --cap-add=NET_ADMIN --device=/dev/net/tun" >&2
  exit 1
fi

# Remove any stale FIFO so the guard below only passes once THIS daemon recreates it.
rm -f "$PIPE_IN" 2>/dev/null || true

log "starting cato-clientd daemon (as root)..."
"$DAEMON" systemd &
DAEMON_PID=$!

log "waiting up to ${PIPE_WAIT_S}s for daemon control pipe ($PIPE_IN)..."
pipe_ready=0
for _ in $(seq 1 $(( PIPE_WAIT_S * 2 )) ); do
  if [[ -p "$PIPE_IN" ]]; then pipe_ready=1; break; fi
  if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
    log "ERROR: cato-clientd exited before opening its control pipe." >&2
    exit 1
  fi
  sleep 0.5
done
if [[ "$pipe_ready" != 1 ]]; then
  log "ERROR: daemon control pipe never appeared after ${PIPE_WAIT_S}s." >&2
  exit 1
fi

# Apply the Docker network fixes before connecting (DNS rename + tun0 default-route conflict).
prepare_container_network

# Connect with bounded exponential backoff so a wrong password cannot become a login storm
# (we keep the daemon up and just re-issue `start`). The password is NEVER logged.
attempt=0
backoff=2
while true; do
  attempt=$(( attempt + 1 ))
  log "connect attempt ${attempt} (user=$CATO_USER account=$CATO_ACCOUNT, password hidden)..."
  # `if` disables set -e for this command; word-split of EXTRA_ARGS is intentional.
  # shellcheck disable=SC2086
  if sdp start \
        --user "$CATO_USER" \
        --account "$CATO_ACCOUNT" \
        --password="$CATO_PASSWORD" \
        $CATO_EXTRA_ARGS; then
    sleep 5
    # When connected (tunnel mode) `status` prints a pop/tunnel block ("pop name", "tun device");
    # when down it prints "Cato client is disconnected". Match the connected-only markers.
    if sdp status 2>/dev/null | grep -qiE "pop name|tun device"; then
      log "connection established."
      break
    fi
  fi
  if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
    log "ERROR: cato-clientd died during connect." >&2
    exit 1
  fi
  if [[ "$RETRY_MAX" != 0 && "$attempt" -ge "$RETRY_MAX" ]]; then
    log "ERROR: not connected after ${attempt} attempts; giving up." >&2
    exit 1
  fi
  log "not connected yet; retrying in ${backoff}s..."
  sleep "$backoff"
  backoff=$(( backoff * 2 ))
  [[ "$backoff" -gt "$BACKOFF_CAP_S" ]] && backoff="$BACKOFF_CAP_S"
done

sdp status || true

# Supervise the daemon: keep the container's foreground bound to it. `|| true` so a signalled
# daemon exit (143/130) doesn't trip set -e before the EXIT trap runs deterministically.
log "supervising cato-clientd (PID $DAEMON_PID)."
wait "$DAEMON_PID" || true
log "cato-clientd exited."
