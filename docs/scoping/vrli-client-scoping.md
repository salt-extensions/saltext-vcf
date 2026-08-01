---
orphan: true
---

# vRLI (VCF Operations for Logs 9.0.2.0) client scoping

**Status: implemented.** See PR #TBD on `salt-extensions/saltext-vcf`
(branch `impl-vrli-client`).

vRLI 9.0.2.0 is the rebrand of vRealize Log Insight. Its REST API
lives on **TCP 9543** (the ``:443`` vhost is the web UI — it returns
403 "Page not found" on ``/api/*``). Auth is a session token acquired
with ``POST /api/v2/sessions`` (``{provider,username,password}``) and
sent as ``Authorization: Bearer <sessionId>``; the token TTL is 1800 s
which matches the 912-Controls session inactivity requirement.

## 912-Controls coverage

| Requirement            | Transport   | Endpoint / file                                                     |
| ---------------------- | ----------- | ------------------------------------------------------------------- |
| Cert install           | REST        | `POST /api/v2/certificate` (body `{"certificate": "<PEM cert+key>"}`) |
| Inactive timeout 1800s | **SSH**     | `/usr/lib/loginsight/application/etc/3rd_config/web.xml` (`<session-timeout>` in *minutes*) |
| IPv4 DNS config        | **SSH**     | `/etc/systemd/network/10-eth0.network` (`DNS=` lines)               |
| AD integration         | REST        | `POST /api/v2/ad` (fields: `enableAD`, `domain`, `username`, `password`, `connType`) |

## Endpoints discovered (live probe)

Verified against a real 9.0.2.0.25575214 appliance at `25.0.3.124:9543`
during scoping. `X-LI-Build: 25575214` on all API responses.

- `POST /api/v2/sessions` — auth
- `GET  /api/v2/version` — `{releaseName, version}`
- `GET  /api/v2/certificate` — list installed appliance cert
- `POST /api/v2/certificate` — install (restarts API listener)
- `GET  /api/v2/ad` — current AD config
- `POST /api/v2/ad` — set AD config
- `GET  /api/v2/cluster/nodes` — read-only DNS view (`dnsServers`, space-separated)
- `GET  /api/v2/auth-providers` — enumerate providers (`Local`, `ActiveDirectory`, `vIDM`)
- `GET  /api/v2/users`, `/api/v2/roles`, `/api/v2/alerts` — existing surfaces

## No-surface endpoints (probed, honestly missing)

Every candidate below returned 404 on 9.0.2.0.25575214:

- Session timeout: `/api/v2/settings/*`, `/api/v2/timeouts`, `/api/v2/session-timeout`, `/api/v2/security/session-timeout`
- DNS write: `/api/v2/settings/dns`, `/api/v2/network/*`, `/api/v2/dns`, `/api/v2/system/dns`, `/api/v2/cluster/dns`, `/api/v2/cluster/nodes/<id>/dns`

Both controls are edited via root SSH per the file paths in the table
above. The read-side of DNS is available via REST
(``/api/v2/cluster/nodes[].dnsServers``); we prefer the on-appliance
read for idempotency verification because the REST view lags a
`systemd-resolved` restart by several seconds.

## Certificate DELETE

Not supported by the API: `DELETE /api/v2/certificate` returns 404
"Handler not found". Rotation happens by POST-in-place; the client
mirrors this — no `delete_()` function is exposed.
