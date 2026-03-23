# Security Audit Report

Date: 2026-03-14
Repository: `pyload`
Scope: repository-level code review, local static analysis, dependency audit, and manual web/API attack-surface review

## Executive Summary

This audit found one high-severity issue and several medium-severity issues in the web/API layer and addon RPC surface. The most serious issue was a Click'N'Load localhost restriction bypass caused by trusting the `Host` header. Additional risks included CSRF-prone state-changing GET endpoints, authenticated SSRF in URL parsing, and overbroad access to addon RPC methods.

High-confidence vulnerabilities with low regression risk were patched in this pass. Some architectural or product-level risks remain and should be addressed in follow-up work.

## Methodology

- Manual review of authentication, authorization, session handling, web routes, and addon/plugin execution paths
- Local static analysis with `bandit`
- Python dependency audit with `pip-audit`
- Secret-pattern scan with repository-wide regex search

## Tool Results

- `bandit`: 140 raw findings; most were informational or generic warnings, with a smaller subset manually confirmed as relevant
- `pip-audit`: no known vulnerabilities found in resolved third-party dependencies; local package `pyload-ng` could not be audited via PyPI
- Secret scan: no obvious first-party production secrets; several hardcoded third-party API keys exist in plugin code

## Findings Summary

- High: 1
- Medium: 5
- Low/Info: 3

## Detailed Findings

### FIND-001
- Severity: High
- Title: Click'N'Load localhost restriction bypass via `Host` header
- Location: `src/pyload/webui/app/blueprints/cnl_blueprint.py:23`
- Description: `local_check()` accepted requests if `HTTP_HOST` matched loopback values, but `Host` is client-controlled and not a trust boundary.
- Impact: Remote clients could likely access Click'N'Load endpoints despite the intended localhost-only restriction.
- Status: Partially mitigated in this pass by trusting only the socket peer address and rejecting common forwarding headers. Residual risk remains if pyLoad is placed behind a same-host reverse proxy that does not set forwarding headers.

### FIND-002
- Severity: Medium
- Title: Session cookie security controlled by untrusted forwarded header
- Location: `src/pyload/webui/app/__init__.py:71`
- Description: `SESSION_COOKIE_SECURE` was mutated on every request based on `X-Forwarded-Proto`.
- Impact: Direct exposure or unsanitized proxy headers could weaken cookie transport security.
- Status: Fixed in this pass by removing dynamic header-driven mutation and keeping the explicit app configuration.

### FIND-003
- Severity: Medium
- Title: State-changing JSON endpoints exposed as GET
- Location: `src/pyload/webui/app/blueprints/json_blueprint.py:72`, `src/pyload/webui/app/blueprints/json_blueprint.py:87`, `src/pyload/webui/app/blueprints/json_blueprint.py:101`, `src/pyload/webui/app/blueprints/json_blueprint.py:153`
- Description: Several endpoints mutated state with GET requests.
- Impact: Increased CSRF exposure for authenticated browser users.
- Status: Fixed in this pass by requiring `POST` and updating frontend callers accordingly.

### FIND-004
- Severity: Medium
- Title: Authenticated SSRF in `parse_urls`
- Location: `src/pyload/core/api/__init__.py:540`
- Description: `parse_urls(url=...)` fetched arbitrary remote content without validating destination address ranges.
- Impact: Users with `ADD` permission could probe or trigger requests to internal services.
- Status: Partially mitigated in this pass by allowing only `http`/`https`, disabling redirects for this fetch path, and blocking loopback, private, link-local, multicast, reserved, and unspecified destinations after DNS resolution. Residual TOCTOU/DNS-rebinding risk remains because final network resolution still occurs in the HTTP layer.

### FIND-005
- Severity: Medium
- Title: Overbroad addon RPC access for non-admin users
- Location: `src/pyload/core/api/__init__.py:1497`
- Description: `service_call()` was available to users with `STATUS`, which is too broad for invoking exposed addon methods.
- Impact: Combined with exposed addons such as `ExternalScripts`, low-privilege users could reach dangerous code paths.
- Status: Fixed in this pass by making `service_call()` admin-only.

### FIND-006
- Severity: Medium
- Title: Path traversal risk in plugin removal
- Location: `src/pyload/plugins/addons/UpdateManager.py:395`
- Description: `remove_plugins()` built file paths from attacker-controlled identifiers without validating names or enforcing base-path constraints.
- Impact: Arbitrary `.py`/`.pyc` deletion under attacker-controlled paths was plausible.
- Status: Fixed in this pass by validating identifiers and enforcing real-path containment checks.

### FIND-007
- Severity: Low
- Title: `autologin` can become a deployment footgun
- Location: `src/pyload/webui/app/blueprints/app_blueprint.py:71`
- Description: Auto-login for a single-user setup was not restricted to local access.
- Impact: Remote exposure could turn this convenience option into effective auth bypass.
- Status: Fixed in this pass by limiting autologin to loopback requests.

### FIND-008
- Severity: Low
- Title: Hardcoded third-party API keys in plugin code
- Location: `src/pyload/plugins/downloaders/GoogledriveCom.py:43`, `src/pyload/plugins/downloaders/StreamCz.py:11`, `src/pyload/plugins/accounts/FastixRu.py:26`
- Description: Several plugins embed API credentials or API-like tokens in source.
- Impact: Key leakage, poor rotation hygiene, and uncertainty about intended public/private use.
- Status: Not fixed in this pass; requires per-plugin review.

### FIND-009
- Severity: Info
- Title: Dynamic plugin loading executes Python source from plugin files
- Location: `src/pyload/core/managers/plugin_manager.py:26`
- Description: User/plugin code is executed with `exec()` as part of the plugin architecture.
- Impact: This is inherent to the plugin model; it is not a vulnerability by itself, but it raises the impact of any path or update-chain compromise.
- Status: Accepted architectural risk; harden surrounding trust boundaries.

## Positive Notes

- Password hashing uses PBKDF2-SHA256 with salt in `src/pyload/core/database/user_database.py:9`
- API routes enforce expected HTTP methods in `src/pyload/webui/app/blueprints/api_blueprint.py:32`
- Tar extraction has explicit traversal protection in `src/pyload/plugins/extractors/UnTar.py:8`

## Patched Files

- `src/pyload/webui/app/helpers.py`
- `src/pyload/webui/app/blueprints/cnl_blueprint.py`
- `src/pyload/webui/app/blueprints/app_blueprint.py`
- `src/pyload/webui/app/__init__.py`
- `src/pyload/webui/app/blueprints/json_blueprint.py`
- `src/pyload/core/api/__init__.py`
- `src/pyload/plugins/addons/UpdateManager.py`
- `src/pyload/webui/app/themes/modern/templates/js/dashboard.js`
- `src/pyload/webui/app/themes/modern/templates/js/packages.js`
- `src/pyload/webui/app/themes/pyplex/templates/js/dashboard.js`
- `src/pyload/webui/app/themes/pyplex/templates/js/packages.js`

## Remaining Recommendations

- Review and rotate or remove hardcoded third-party API keys from plugin code
- Consider restricting or sandboxing dangerous addon capabilities such as external script execution
- Review login CSRF posture and decide whether `/login` should remain CSRF-exempt
- Document that loopback-only protections should not be exposed behind a same-host reverse proxy unless the proxy adds trusted forwarding headers and pyLoad explicitly handles them
- Consider moving SSRF destination enforcement into the HTTP request layer so redirects, proxies, and final resolved addresses are checked at connect time
- Add security regression tests for loopback-only routes, CSRF-sensitive routes, and SSRF blocking
