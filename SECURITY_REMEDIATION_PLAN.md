# Security Remediation Plan

Date: 2026-03-14
Repository: `pyload`

## Goal

Reduce externally reachable risk in the web/API surface first, then address plugin-supply and operational hardening concerns.

## Priority 0 - Completed In This Pass

### Web/UI access control
- `src/pyload/webui/app/blueprints/cnl_blueprint.py`
  - Removed trust in `HTTP_HOST` for localhost checks
  - Restricted Click'N'Load access to loopback socket peers only

- `src/pyload/webui/app/blueprints/app_blueprint.py`
  - Restricted `autologin` to loopback requests only

- `src/pyload/webui/app/helpers.py`
  - Added reusable loopback request detection helper

### Session and CSRF hardening
- `src/pyload/webui/app/__init__.py`
  - Removed header-driven `SESSION_COOKIE_SECURE` mutation

- `src/pyload/webui/app/blueprints/json_blueprint.py`
  - Converted state-changing endpoints from GET to POST

- `src/pyload/webui/app/themes/modern/templates/js/dashboard.js`
- `src/pyload/webui/app/themes/modern/templates/js/packages.js`
- `src/pyload/webui/app/themes/pyplex/templates/js/dashboard.js`
- `src/pyload/webui/app/themes/pyplex/templates/js/packages.js`
  - Updated frontend callers to use POST so existing CSRF protections apply

### API and addon surface
- `src/pyload/core/api/__init__.py`
  - Restricted `service_call()` to admin-only access
  - Added destination validation to `parse_urls(url=...)` to reduce SSRF risk

- `src/pyload/plugins/addons/UpdateManager.py`
  - Added identifier validation and path-containment checks before plugin deletion

## Priority 1 - Next Recommended Changes

### Remove hardcoded keys and tokens
- `src/pyload/plugins/downloaders/GoogledriveCom.py`
- `src/pyload/plugins/decrypters/GooGl.py`
- `src/pyload/plugins/downloaders/StreamCz.py`
- `src/pyload/plugins/accounts/FastixRu.py`
  - Confirm whether embedded keys are public/demo keys or actual credentials
  - Move sensitive values to config or plugin metadata where possible
  - Rotate any secrets that should not be public

### Review login CSRF posture
- `src/pyload/webui/app/blueprints/app_blueprint.py`
  - Evaluate whether `/login` still needs `@csrf_exempt`
  - If not required, remove the exemption and verify browser/API compatibility

### Add security tests
- `tests/`
  - Add tests for loopback-only Click'N'Load access
  - Add tests that POST is required for mutating JSON routes
  - Add tests that `parse_urls(url=...)` rejects private and loopback destinations
  - Add tests that non-admin users cannot call `service_call`

## Priority 2 - Architectural Hardening

### Dangerous addon capabilities
- `src/pyload/plugins/addons/ExternalScripts.py`
- `src/pyload/core/managers/addon_manager.py`
  - Review whether dangerous exposed addon methods should require explicit admin-only gates even internally
  - Consider allowlisting safe RPC methods instead of exposing addon internals broadly

### Plugin trust model
- `src/pyload/core/managers/plugin_manager.py`
- `src/pyload/plugins/addons/UpdateManager.py`
  - Review how remote plugin updates are authenticated and verified
  - Consider signature verification or stronger provenance controls for updated plugin code

### Reverse proxy guidance
- `README.md`
- `SECURITY.md`
  - Document safe deployment behind reverse proxies
  - Clarify how `webui.use_ssl`, secure cookies, and trusted headers should be configured
  - Explicitly warn that loopback-only features must not rely on a same-host reverse proxy unless forwarding headers are trusted and enforced

### SSRF enforcement at transport layer
- `src/pyload/core/network/request_factory.py`
- `src/pyload/core/network/http/http_request.py`
  - Move destination filtering closer to the actual connection layer
  - Re-validate redirect targets and final resolved IPs, not only the initial hostname lookup
  - Decide how proxy-based requests should be handled for security-sensitive fetches

## Suggested Validation Commands

```bash
python3 -m compileall src
python3 -m pytest tests
```

If the full test suite is not available locally, prioritize targeted web/API regression tests around the patched code paths.
