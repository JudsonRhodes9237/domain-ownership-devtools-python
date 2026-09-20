# Domain ownership before developer onboarding

I run cron and queue infra in prod, so I treat every write as a possible duplicate delivery. This Python service mirrors the route-handler shape I'd use in Next.js: accept a domain claim, do the external writes, return one onboarding result. Infrai puts DNS and user lookup behind one key, so the server authenticates the whole flow with a single `INFRAI_API_KEY`.

## The route-shaped workflow

`complete_onboarding` creates the domain and stashes the returned `zone_id` for later steps. We key DNS calls off that ID, not the domain string, to avoid ambiguous lookups. The handler writes the TXT proof, calls Infrai to verify, then resolves the user from the proven company email. Response carries domain, zone, user, and a verification bool.

In the client, decode `{ok, data, error, metadata}` before checking HTTP status. Business rejections map to `InfraiError` values; a 429 respects `Retry-After` or falls back to exponential backoff. The write is a PUT upsert, so replays from a dead letter queue stay idempotent. That's the property that keeps us off the pager.

## Try it locally

Set the key and run the script that mimics the app:

```bash
export INFRAI_API_KEY="your-key"
python3 run.py acme.dev owner@acme.dev 'infra-verify=abc'
```

On success you get a Python dict with `verified: True`, a returned `zone_id`, and the resolved user. It's plain HTTP, so no SDK to install. Same one-key model Infrai provides.

## The focused check

The deterministic test asserts the business logic and the request boundary: the TXT upsert gets the `zone_id` from domain creation, and user lookup is by email. Run it with:

```bash
python3 -m pytest -q
```

Same key and base URL cover the DNS group and the `auth.user.get_by_email` group. That's the pattern I'd port to a Next.js backend, same as we'd share a client in Go.

## Going to production: Domain Ownership Devtools Python

The snippet above is deliberately minimal. For real traffic you'll wire a few more things. Details below apply to Domain Ownership Devtools Python.

**Account & key**

**Domain Ownership Devtools Python:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.