# Security Review Reference

Expert-level security patterns and anti-patterns for code review across languages and frameworks.

## Web Security

### CORS Misconfiguration

Wildcard origins (`Access-Control-Allow-Origin: *`) combined with `Access-Control-Allow-Credentials: true` creates a critical vulnerability—browsers reject this combination, but middleware bugs may bypass it. Reflecting the request's `Origin` header without validation is equally dangerous: every domain becomes trusted.

Verify allowed origins against actual trusted domains. Use explicit allowlists, not pattern matching on subdomains unless absolutely necessary. For multi-tenant applications, validate against database records, not string contains checks.

### Rate Limiting

Token bucket allows bursts up to capacity, then enforces steady rate. Sliding window provides smoother enforcement but higher memory overhead. Choose based on use case: token bucket for API gateways, sliding window for authentication endpoints.

Implement multiple dimensions: per-user (authenticated), per-IP (anonymous), per-endpoint (critical operations). Layer them—passing one doesn't bypass others.

Beware header spoofing: `X-Forwarded-For` and `X-Real-IP` are attacker-controlled unless your load balancer strips and rewrites them. Use the rightmost trusted IP or configure your proxy to add its own header.

### Token Management

Access tokens should be short-lived: 15 minutes to 1 hour. Longer lifetimes increase exposure window when compromised. Refresh tokens must rotate on each use—stateless refresh tokens with long TTLs create irrevocable sessions.

Cookies require three flags: `Secure` (HTTPS-only), `HttpOnly` (no JavaScript access), `SameSite=Strict` or `Lax` (CSRF protection). `SameSite=None` should trigger scrutiny—it's rarely necessary and disables CSRF protection.

### TLS Configuration

Enforce TLS 1.2 minimum, prefer 1.3. Disable legacy cipher suites: no RC4, no 3DES, no export ciphers. Use AEAD ciphers (GCM, ChaCha20-Poly1305) where possible.

Certificate pinning prevents CA compromise but creates operational risk: mismanaged pins cause outages. If pinning, pin intermediate CA certificates, not leaf certificates, and implement backup pins.

HSTS headers (`Strict-Transport-Security`) prevent downgrade attacks. Set `max-age` to at least one year and include `includeSubDomains` if all subdomains support HTTPS.

## Authentication & Authorization

### Session Management

Generate session IDs with 128+ bits of entropy from cryptographically secure sources (`secrets` in Python, `crypto.randomBytes` in Node). Predictable session IDs enable hijacking.

Regenerate session IDs on privilege escalation: login, role change, password reset. Implement both absolute timeout (maximum session lifetime) and idle timeout (inactivity limit). Typical values: 8-24 hours absolute, 30 minutes idle.

### JWT Patterns

Algorithm confusion attacks exploit improper validation: attackers change `alg` header from `RS256` (asymmetric) to `HS256` (symmetric) and sign with the public key. Always specify allowed algorithms explicitly, never trust the header's `alg` field alone.

Validate all standard claims: `iss` (issuer), `aud` (audience), `exp` (expiration), `nbf` (not before). Missing `exp` creates permanent tokens. Implement clock skew tolerance (30-60 seconds) but not more.

Key rotation requires version identifiers (`kid` claim). Maintain multiple valid keys during rotation: new keys sign, but old keys still verify until all tokens expire.

### OAuth Considerations

The `state` parameter prevents CSRF during authorization code flow—generate unpredictable values, store server-side, verify on callback. Missing or weak state enables session fixation.

PKCE (Proof Key for Code Exchange) protects public clients from authorization code interception. Mandatory for mobile/SPA apps, recommended for all clients. Code verifier requires 43-128 characters of high entropy.

Request minimum necessary scopes. Overly broad scopes violate least privilege—reading user email shouldn't grant write access to all resources.

### RBAC/ABAC Design

Default deny: explicitly grant permissions, never assume. Check authorization at every layer: API gateway, service layer, data access layer. Front-end hiding is not security.

Principle of least privilege applies to service accounts and API keys, not just users. Audit log all privilege changes: role assignments, permission grants, scope expansions. Include timestamp, actor, target, and reason.

## Input Validation & Injection

### SQL Injection

Parameterized queries separate SQL structure from data—the only reliable defense. ORMs reduce risk but don't eliminate it: raw queries, query builders with string concatenation, and dynamic identifiers bypass protection.

Never construct queries via string formatting or concatenation. Dynamic table or column names require allowlisting against known valid values—parameterization doesn't work for identifiers.

### Command Injection

Never pass user input to shell interpreters (`system`, `exec`, backticks). If external commands are necessary, use array-based APIs (`execFile`, `subprocess.run` with list arguments) that bypass shell parsing.

Escaping is insufficient—shell metacharacters vary across platforms and contexts. Even seemingly safe operations like filename validation fail against creative exploitation. Eliminate the shell entirely.

### XSS Prevention

Context determines encoding: HTML entity encoding for element content, JavaScript escaping for script contexts, URL encoding for href attributes, CSS escaping for style contexts. No single encoding function works everywhere.

Content-Security-Policy headers provide defense in depth: restrict script sources, disable inline scripts, prevent data: URIs. Start restrictive and selectively loosen.

React's `dangerouslySetInnerHTML`, Vue's `v-html`, Angular's `bypassSecurityTrust*` all disable XSS protection. Flag for review—usually indicates architectural problems.

### Path Traversal

Canonicalize paths before validation: resolve symlinks, collapse `..` sequences, normalize separators. Check that canonicalized path starts with intended base directory. Race conditions exist between check and use.

Allowlist approaches beat blocklists: define valid paths explicitly rather than filtering `..` and other traversal sequences. Blocklists fail against encoding variations (`%2e%2e`, UTF-8 overlong encoding).

### Deserialization Risks

Deserializing untrusted data enables arbitrary code execution in many languages. Python's `pickle`, Ruby's `Marshal`, Java's native serialization all execute code during deserialization.

Use safe subsets: `yaml.safe_load` not `yaml.load`, `JSON.parse` (generally safe), MessagePack, Protocol Buffers. If native serialization is necessary, implement allowlisting of permitted classes.

## Secret Management

### Environment Variables

Environment variables propagate to child processes—avoid spawning untrusted code. Never log environment variable contents, even in debug mode. Sanitize before error reporting.

Validate secret presence at application startup. Fail fast with clear errors rather than partial functionality with missing credentials. Don't fall back to defaults.

### Secret Rotation

Implement dual-read during rotation: accept both old and new secrets for validation while tokens using old secret remain valid. Single-read causes outages during rotation windows.

Automate rotation where possible: database passwords, API keys, certificates. Manual rotation doesn't happen regularly enough. Audit unrotated secrets—long-lived secrets indicate technical debt.

### Common Exposure Vectors

Git history persists secrets even after removal from current tree. Rewriting history doesn't help if repository was public—assume compromised, rotate secrets.

Error messages and stack traces leak secrets when exceptions occur during authentication or connection setup. Sanitize before logging or displaying.

Client-side JavaScript bundles are public. API keys, tokens, or credentials embedded in frontend code are compromised. Use backend proxies for sensitive operations.

Docker layers cache intermediate filesystem states. Secrets added and deleted in separate layers remain accessible via layer inspection. Use multi-stage builds or BuildKit secrets.

### Detection Patterns

High entropy strings (Shannon entropy > 4.5) in commits indicate potential secrets. Combine with length thresholds: short high-entropy strings are common in code.

Known prefixes enable automated detection: `sk_` (Stripe), `ghp_` (GitHub personal access tokens), `AKIA` (AWS access keys), `xox` (Slack). Maintain prefix database for common services.

Base64-encoded credentials appear as alphanumeric strings ending in `=` padding. Decode and check for structured formats (JSON, key-value pairs) or additional entropy patterns.
