# Cato SDP Linux Client — Container

Run the **Cato Networks Linux SDP Client** headless (unattended) inside a Docker container, so any
Linux host can join the Cato fabric the way a roaming user would — no Cato Socket required on-site.

This is useful for environments that need Cato SDP connectivity but have **no Socket**: cloud
workloads, CI/build runners, jump hosts, NAS appliances, or any headless Linux host. The container
authenticates with a **username and password** (no GUI, no browser SSO), builds the Cato tunnel on
a `tun0` interface, and routes the container's traffic through the Cato cloud.

> **⚠️ Supported platform: native amd64 (x86_64) Linux only.** The Cato Linux client is an
> amd64-only binary and does **not** work under ARM emulation. Run on a native amd64 Linux host.

## Highlights

- **Headless / unattended** — daemon + CLI orchestrated by a single entrypoint with connect
  supervision and bounded reconnect backoff.
- **File-based secret** — the password is read from a mounted file via `CATO_PASSWORD_FILE`
  (Docker secret or Kubernetes Secret), kept out of the container environment and out of git. No
  external secret server required; pluggable with one later (ESO / Vault / etc.).
- **Docker *and* Kubernetes** — the same image runs on both; full K8s wiring is documented.
- **Gateway pattern** — optionally route other LAN hosts out through the tunnel
  (`ip_forward` + `MASQUERADE` on `tun0`).

## Quick start

```bash
cd docker
cp .env.example .env                                   # CATO_ACCOUNT + CATO_USER (non-secret)
printf '%s' 'the-user-password' > secrets/cato_password && chmod 0400 secrets/cato_password
docker compose build && docker compose up -d
docker compose logs -f                                 # watch it connect
```

**Full guide — prerequisites, auth model, Kubernetes deployment, verification, and known
issues — is in [DEPLOYMENT.md](DEPLOYMENT.md).**

## Auth note

The headless path requires a **password-activated** Cato SDP user (created in the CMA, then
activated by the user via the activation email — OAuth/SSO-only users cannot authenticate
headlessly). A device certificate is ZTNA device-posture layered on top of user auth, never a
replacement for it.

## Layout

| Path | Purpose |
|------|---------|
| `DEPLOYMENT.md` | Full deployment guide (Docker + Kubernetes). |
| `docker/Dockerfile` | Builds the image: Ubuntu + the Cato Linux client + Cato's public root CA. |
| `docker/entrypoint.sh` | Daemon launch, container-network prep, connect supervision. |
| `docker/docker-compose.yml` | Run config: capabilities, the `tun` device, file-based secret. |
| `docker/.env.example` | Template for the non-secret identifiers (account + user). |
| `docker/secrets/cato_password.example` | Template for the password file. |
