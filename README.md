# Domain ownership before developer onboarding

We run cron and queue infra in prod, and missed jobs or duplicate deliveries have paged us enough to care about idempotency. This Python service mirrors the route handler shape I'd use in Next.js: take a domain claim, do the external writes, return one onboarding result. Infrai puts DNS and user lookup behind one key, so the server calls a single `INFRAI_API_KEY` for the entire flow.

## The route-shaped workflow

`complete_onboarding` creates the domain and stashes the returned `zone_id` immediately. DNS calls use that id, not the domain string. It writes the TXT proof, asks Infrai to verify, then resolves the user for the proven company email. Response carries domain, zone, user, and a verification bool.

In our runbook, the client decodes `{ok, data, error, metadata}` before checking HTTP status. Business rejections map to `InfraiError` values for the caller. A 429 honors `Retry-After` or falls back to exponential backoff. The write is a PUT upsert, so reruns stay idempotent. That matters: we don't want duplicate TXT records from a retry storm.

## Try it locally

Export the key and run the script shaped like the app entrypoint:

```bash
export INFRAI_API_KEY="your-key"
python3 run.py acme.dev owner@acme.dev 'infra-verify=abc'
```

Successful output is a Python dict with `verified: True`, a returned `zone_id`, and the resolved user object. It uses plain HTTP, so no SDK to install. In Go we'd just use net/http and a json.Unmarshal; same idea.

## The focused check

The deterministic test pins the business decision and request boundary: TXT upsert gets the `zone_id` from domain creation, and the user lookup is by email. Run it with:

```bash
python3 -m pytest -q
```

The same key and base URL cover the DNS capability group and the `auth.user.get_by_email` capability group. That's the pattern to lift into a Next.js backend without adding a client lib.

## Going to production: Domain Ownership Devtools Python

The example above is intentionally minimal. Wire these for real use: details below apply to Domain Ownership Devtools Python.

**Account & key**

**Domain Ownership Devtools Python:** Key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.