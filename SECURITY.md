<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/main/media/logo.png" alt="pyLoad" height="100" />
</p>

## Security Policy

### Supported Versions

pyLoad Next releases will receive security vulnerabilities patches.
Old versions of pyLoad, working on Python 2 is End-of-Life.

### Reporting a Vulnerability

Please report any security vulnerabilities by sending an email to security@pyload.net.

You will receive a response from us within a short time.
If the issue is confirmed, we will release a patch as soon as possible depending on complexity.

### User Permissions & Scope

pyLoad provides a role and permission-based access control system.

Please note the following regarding user permissions:
- **`SETTINGS` Permission**: The explicit purpose and design of the `SETTINGS` permission is to grant users full ability to modify core and plugin configurations (such as download directories, external scripts, proxies, network options, etc.). Therefore, any report or issue demonstrating that a user with the `SETTINGS` permission can modify settings, or execute functionality governed by those settings, is **by design and is not considered a security vulnerability**.
- Normal or untrusted users must **never** be granted the `SETTINGS` permission. It should strictly be reserved for trusted administrators.

<br />

---

###### © 2008-2026 pyLoad team
