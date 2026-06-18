# Cato Networks Linux SDP client — containerized (headless, user/password auth).
#
# Base: Ubuntu 24.04 (the Cato Linux client supports Ubuntu 20 and newer).
#
# IMPORTANT: the Cato Linux client is **amd64-only**, and it does NOT function under ARM
# emulation (on Apple Silicon the image builds, but the client fails to connect at the
# crypto/posture step). RUN THIS ON A NATIVE amd64 LINUX HOST — see DEPLOYMENT.md.
# The platform is pinned to linux/amd64 so the build is always amd64 regardless of build host
# (never a binary-less ARM image where the amd64 .deb silently fails to install).
FROM --platform=linux/amd64 ubuntu:24.04

# --- Supply-chain controls -------------------------------------------------------------------
# The .deb at the public URL is a rolling "latest". For reproducible/pinned builds, pass a
# specific URL and/or a SHA256 at build time:
#   docker build --build-arg CATO_DEB_SHA256=<sha256> ...
# If a SHA256 build-arg is empty, the checksum step is skipped (latest, non-reproducible).
ARG CATO_DEB_URL=https://clientdownload.catonetworks.com/public/clients/cato-client-install.deb
ARG CATO_DEB_SHA256=
ARG CATO_CA_URL=https://clientdownload.catonetworks.com/public/certificates/CatoNetworksTrustedRootCA.pem
ARG CATO_CA_SHA256=

# Runtime deps:
#   wget/ca-certificates/openssl — fetch + install the public Cato root CA
#   iproute2                     — the daemon creates tun0 and rewrites routes (needs `ip`)
#   procps                       — diagnostics (ps) inside the container
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget ca-certificates openssl iproute2 procps && \
    rm -rf /var/lib/apt/lists/*

# Install the PUBLIC Cato root CA into the system trust store (lets the client trust Cato services).
RUN set -eux; \
    mkdir -p /usr/local/share/ca-certificates/Cato; \
    wget --https-only -O /tmp/CatoRootCA.pem "$CATO_CA_URL"; \
    if [ -n "$CATO_CA_SHA256" ]; then echo "${CATO_CA_SHA256}  /tmp/CatoRootCA.pem" | sha256sum -c -; fi; \
    openssl x509 -in /tmp/CatoRootCA.pem -out /usr/local/share/ca-certificates/Cato/CatoNetworksTrustedRootCA.crt; \
    rm -f /tmp/CatoRootCA.pem; \
    update-ca-certificates

# Install the Cato Linux client (.deb). apt resolves any missing dependencies.
# The final `test -x` is a build-time guard: if the client binary isn't present after install
# (e.g. an architecture mismatch silently swallowed by `apt-get install -f`), FAIL the build
# loudly here instead of shipping a broken image that dies at runtime.
RUN set -eux; \
    wget --https-only -O /tmp/cato-client-install.deb "$CATO_DEB_URL"; \
    if [ -n "$CATO_DEB_SHA256" ]; then echo "${CATO_DEB_SHA256}  /tmp/cato-client-install.deb" | sha256sum -c -; fi; \
    apt-get update; \
    (dpkg -i /tmp/cato-client-install.deb || apt-get install -f -y); \
    rm -f /tmp/cato-client-install.deb; \
    rm -rf /var/lib/apt/lists/*; \
    test -x /usr/sbin/cato-clientd || { \
      echo "ERROR: /usr/sbin/cato-clientd not installed — the Cato client is amd64-only. Build for linux/amd64." >&2; \
      exit 1; }

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
