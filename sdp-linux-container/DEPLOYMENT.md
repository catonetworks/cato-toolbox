# Cato SDP Client — Container Deployment Guide

Run the **Cato Networks Linux SDP Client** unattended inside a Docker container.

This is intended for environments that need Cato SDP connectivity but have **no Cato Socket
on-site** — for example cloud workloads, CI/build runners, jump hosts, or any headless Linux
host that should ride the Cato fabric like a roaming user would.

The container runs the standard Cato Linux client in **headless** mode, authenticates with a
**username and password** (no GUI, no browser SSO), builds the Cato tunnel on a `tun0`
interface, and routes the container's traffic through the Cato cloud — the same behavior as the
desktop client.

> **⚠️ Supported platform: native amd64 (x86_64) Linux only.** The Cato Linux client is an
> amd64-only binary and **does not work under ARM emulation** — on an Apple Silicon Mac the
> image builds but the client cannot connect. Run this on a native amd64 Linux host. On a Mac,
> use the native macOS Cato client instead. (See [Prerequisites](#docker-host-side) for detail.)

---

## Prerequisites

### Cato side (Cato Management Application)

You need three values: your **account name**, an **SDP user** (email address), and that user's
**password**.

1. In the CMA, create an SDP **user** (`Access > Users`). It must be a standard
   username/password user — **not** an SSO/OAuth-only user (OAuth users cannot authenticate
   headlessly).
2. **Send the user an activation email.** The administrator *cannot* set the password directly —
   the user opens the activation link and sets their **own** password.
3. The values you'll hand to the container are: the **account name**, the **user's email**, and
   the **password the user set** during activation.

### Docker host side

- A **Linux host** with **Docker Engine** and **Docker Compose v2**.
- **Architecture: amd64 (x86_64) only — ARM is NOT supported.** The Cato Linux client ships
  only as an amd64 binary, and it does **not function under ARM emulation**. On an Apple
  Silicon Mac via Docker Desktop the image will *build* (under emulation) but the client
  **cannot establish the tunnel** — it fails at the crypto/posture step under emulation, and
  no container-level workaround (transport, crypto flags) resolves it. **Run on a native
  amd64 Linux host** — bare metal, a VM, an LXC, or an amd64 cloud instance. The image is
  pinned to `linux/amd64` so the build is always correct on amd64 and never silently produces
  a binary-less ARM image.
  - **On an Apple Silicon Mac:** for endpoint access use the **native macOS Cato client**; for
    a containerized gateway, deploy this on a native amd64 Linux host.
- The **TUN device** present on the host: `/dev/net/tun` (the `tun` kernel module). Verify:
  ```bash
  ls -l /dev/net/tun        # should exist; if not: sudo modprobe tun
  ```
- **Outbound internet** to the Cato cloud (the client uses DTLS over UDP/443; TCP/443 fallback).
- The container is granted these at run time (already set in the provided compose file):
  - Capabilities: `NET_ADMIN`, `NET_RAW`, `SYS_ADMIN`
  - Device: `/dev/net/tun`
  - **Bridge** networking (the default — do **not** use host networking)

---

## Step 1 — Get the artifacts

Clone the toolbox and change into this subdirectory:

```bash
git clone https://github.com/catonetworks/cato-toolbox.git
cd cato-toolbox/sdp-linux-container/docker
```

The set contains these files:

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds the image: Ubuntu base + the Cato Linux client (`.deb`) + Cato's public root CA. |
| `entrypoint.sh` | Container startup: launches the Cato daemon, prepares container networking, connects with your credentials, and supervises the tunnel. |
| `docker-compose.yml` | Run configuration: capabilities, the `tun` device, the file-based password secret, restart policy. |
| `.env.example` | Template for the **non-secret** identifiers (account + user). |
| `secrets/cato_password.example` | Template for the password file (a **file-based secret** — see Step 2). |

> The `Dockerfile` downloads the current Cato Linux client from
> `clientdownload.catonetworks.com`. To pin a specific version for reproducible builds, pass a
> versioned URL via the `CATO_DEB_URL` build argument.

---

## Step 2 — Configure credentials

The password is handled as a **file-based secret** — it is kept out of the container environment
(`docker inspect` / `/proc/1/environ`) and out of git. The non-secret identifiers (account, user)
go in `.env`.

**a. Non-secret identifiers** — copy and edit `.env`:

```bash
cp .env.example .env
```
```ini
CATO_ACCOUNT=your-cato-account
CATO_USER=user@example.com
```

**b. Password** — write it to the secret file (a single line, no surrounding quotes):

```bash
mkdir -p secrets
printf '%s' 'the-password-the-user-set' > secrets/cato_password
chmod 0400 secrets/cato_password
```

Both `.env` and `secrets/cato_password` are git-ignored (only `secrets/cato_password.example`
ships). Compose mounts the secret read-only at `/run/secrets/cato_password`; the entrypoint reads
it via `CATO_PASSWORD_FILE`. See **Known Issues** below for the residual argv consideration.

> **No external secret server required.** This uses Docker's built-in file-based secrets — fully
> portable. The entrypoint reads the password from whatever path `CATO_PASSWORD_FILE` points at,
> so the *same image* also works on Kubernetes (mount a `Secret` volume) or with any other secret
> provider that can present the value as a file. See [Running on Kubernetes](#running-on-kubernetes).

---

## Step 3 — Build and start

```bash
docker compose build
docker compose up -d
```

The container starts the Cato daemon, applies the required container-network preparation, and
connects automatically. There are no further manual steps.

---

## Step 4 — Verify

**Watch it connect:**

```bash
docker compose logs -f
# success line:  Successfully connected to CATO VPN "<pop>" via DTLS mode
```

**Confirm the tunnel is up and holding:**

```bash
docker exec cato-sdp-client cato-sdp status
#   pop name    = "<pop>"
#   tunnel ip   = 10.x.x.x
#   tun device  = tun0
#   duration    = 00:00:NN     <- climbing = the tunnel is stable

docker exec cato-sdp-client ip -br addr | grep tun0
```

**Confirm traffic egresses through Cato** (no extra tools required):

```bash
docker exec cato-sdp-client bash -c 'timeout 6 bash -c "echo > /dev/tcp/8.8.8.8/53" \
  && echo "internet reachable via Cato tunnel" || echo "NOT reachable"'
```

---

## Step 5 — Operate

| Action | Command |
|--------|---------|
| Tail logs | `docker compose logs -f` |
| Restart | `docker compose restart` |
| Stop & disconnect | `docker compose down` |
| Status | `docker exec cato-sdp-client cato-sdp status` |

The container reconnects automatically on failure (Docker restart policy plus the entrypoint's
built-in connect supervision and backoff).

---

## Running on Kubernetes

The same image runs on Kubernetes — the `*_FILE` convention means the only change is *how* the
password file gets mounted. Put the password in a `Secret`, mount it as a volume, and point
`CATO_PASSWORD_FILE` at the mounted file. Kubernetes `Secret` volumes are backed by tmpfs, so the
plaintext never touches node disk.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cato-sdp
type: Opaque
stringData:
  password: the-password-the-user-set      # better: source from an external secrets operator
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cato-sdp
spec:
  replicas: 1
  selector: { matchLabels: { app: cato-sdp } }
  template:
    metadata: { labels: { app: cato-sdp } }
    spec:
      containers:
        - name: cato-sdp
          image: <your-registry>/cato-sdp-client:<tag>   # amd64 image; schedule onto an amd64 node
          env:
            - { name: CATO_ACCOUNT, value: your-cato-account }
            - { name: CATO_USER, value: user@example.com }
            - { name: CATO_PASSWORD_FILE, value: /run/secrets/cato/password }
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              add: [NET_ADMIN, NET_RAW, SYS_ADMIN]      # required for the tunnel (see Prerequisites)
          volumeMounts:
            - { name: cato-password, mountPath: /run/secrets/cato, readOnly: true }
            - { name: tun, mountPath: /dev/net/tun }
      volumes:
        - name: cato-password
          secret:
            secretName: cato-sdp
            items: [{ key: password, path: password }]
            defaultMode: 0400
        - name: tun
          hostPath: { path: /dev/net/tun, type: CharDevice }
```

Notes:
- **Pin to amd64.** Schedule onto an amd64 node (e.g. `nodeSelector: { kubernetes.io/arch: amd64 }`)
  — the client is amd64-only (see [Prerequisites](#docker-host-side)).
- **`SYS_ADMIN` + `/dev/net/tun`** mean this pod will not pass a `restricted` Pod Security Standard;
  run it in a `baseline`/privileged namespace. This is the same capability requirement as the
  Docker deployment, not a Kubernetes-specific escalation.
- **External secrets:** to source the password from an operator (e.g. External Secrets Operator /
  Vault / Infisical), have it materialize the `Secret` above — no change to the image or the
  Deployment's volume wiring.

---

## Known issues / limitations

- **Password on argv (residual exposure).** The Cato client requires the password on its command
  line (`cato-sdp start --password=<password>`) — there is no file/stdin/env input for it. The
  password is delivered to the container as a **file-based secret** (out of the environment, out
  of git — see Step 2), and the `cato-sdp start` call is **transient**: it hands the credential to
  the `cato-clientd` daemon over a control pipe and then exits, so the password is visible to `ps`
  **only during a connect attempt, not while connected** — the persistent daemon carries neither
  the password on its argv nor in its environment. Note that if a connect *fails* (wrong/expired
  password), the entrypoint retries with backoff, so the brief argv window recurs once per attempt
  until it succeeds. The exposure is bounded to the container's own PID namespace (a root-adjacent
  trust boundary). After the first successful connect the daemon caches a session **token** under
  the persisted `/opt/cato` volume — the password itself is not re-stored there.
- **One plaintext file at rest.** With no external secret server (a deliberate portability
  choice), the password necessarily exists as one local plaintext file — `secrets/cato_password`
  (Docker) or the `Secret` (Kubernetes, tmpfs-backed). It is git-ignored and should be `0400`. To
  remove even this, point `CATO_PASSWORD_FILE` at a file materialized at runtime by an external
  secrets operator (External Secrets Operator / Vault / Infisical) — no image change required.
- **`SYS_ADMIN` capability.** The container needs `SYS_ADMIN` so it can convert the
  Docker-managed `/etc/resolv.conf` into a writable file for the client's DNS handling. Note this
  in environments with strict capability policies.
- **Bridge networking only.** Run with the default bridge network. Host networking would let the
  client rewrite the *host's* routing table.
- **Internal name resolution** (corporate/private DNS) depends on your Cato policy permitting
  this user to reach those DNS servers; that is a Cato policy matter, independent of the
  container.
