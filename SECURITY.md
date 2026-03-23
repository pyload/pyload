<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/main/media/logo.png" alt="pyLoad" height="100" />
</p>

## Security Policy

### Supported Versions

pyLoad Next releases will receive security vulnerabilities patches.
Old versions of pyLoad, working on Python 2, will receive plugin updates only.

### Reporting a Vulnerability

Please report any security vulnerabilities by sending an email to security@pyload.net.

You will receive a response from us within a short time.
If the issue is confirmed, we will release a patch as soon as possible depending on complexity.

### Deployment Guidance

- Use a reverse proxy with TLS if pyLoad is reachable from outside the local machine or LAN.
- Restrict access to the pyLoad upstream service so only the reverse proxy or trusted hosts can reach it.
- Do not treat reverse-proxied requests as equivalent to direct localhost access unless trusted forwarding headers are enforced end-to-end.
- Avoid exposing Click'N'Load and other localhost-oriented convenience features on public deployments.
- Change the default credentials immediately on first start.

### Reverse Proxy Notes

If pyLoad is deployed behind a reverse proxy on the same host, localhost-only routes and features should still be considered sensitive. A local proxy that forwards untrusted traffic can weaken assumptions based on the apparent source address. Prefer explicit network isolation and conservative proxy configuration over convenience features.

<br />

---

###### © 2008-2026 pyLoad team
