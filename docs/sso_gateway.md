# SSO / API Gateway Integration (RBAC-lite)

This repo is designed so you can place an API gateway (or SSO proxy) in front of the service:

- Gateway verifies the JWT (signature, issuer, audience, expiry)
- Gateway injects trusted headers to the API

## Recommended headers

- `Authorization: Bearer <jwt>` (optional; pass-through)
- `X-User-Id: <subject>`
- `X-User-Email: <email>`
- `X-User-Role: operator | supervisor | system`
- `X-Channel: ui | supervisor | system` (optional, legacy semantics)

The API uses these for:
- **RBAC-lite** permission checks for approve/execute
- **Audit** payload enrichment (`payload.actor`)

## Local verification (optional)

For internal environments you may enable local HS256 verification:

- `JWT_VERIFY=1`
- `JWT_SECRET=...`
- `JWT_ALG=HS256`

In production, prefer gateway verification + headers.


## Idempotency scope (enterprise)

Idempotency is scoped to **endpoint + subject + card_id** so two different users cannot collide on the same raw `Idempotency-Key`.

- Materialization endpoints persist scope in `materializations(endpoint, subject, card_id, idempotency_key)`.
- Pending action decision/execute use a scoped SHA-256 key derived from the same scope fields.


## Group/Entitlement to role mapping
If your API gateway can pass group or entitlement claims, you may forward them as:
- X-User-Groups: comma-separated groups
- X-User-Entitlements: comma-separated entitlements
The API maps these to roles based on governance/policy.yaml -> rbac.role_mapping.

## Audit allowlist (safe for SIEM)

The API records audit metadata under payload._audit. To avoid leaking sensitive tokens, only allowlisted request headers and query keys are recorded. Configure:

- `audit.request.allowlist_headers`
- `audit.request.allowlist_query`

in `governance/policy.yaml`.


## Actor normalization (OIDC / SAML)

Actor fields are normalized to `{sub,email,role,groups,entitlements}` using trusted gateway headers first, then JWT claims. Claim mappings per provider are configured under `identity.providers.oidc` and `identity.providers.saml` in `governance/policy.yaml`.

Recommended gateway headers:
- `X-User-Id`
- `X-User-Email`
- `X-User-Role`
- `X-User-Groups`
- `X-User-Entitlements`

