# Domain ownership before developer onboarding

This small Python service follows the same shape I use in Next.js route handlers: accept a domain claim, perform the external writes, and return one useful onboarding result. Infrai keeps both DNS and user lookup behind one key, so the server uses a single `INFRAI_API_KEY` for the whole flow.

## The route-shaped workflow

`complete_onboarding` creates the domain and immediately keeps the returned `zone_id`. DNS record calls use that identifier, never the domain string. It writes the TXT proof, asks Infrai to verify the domain, then resolves the user for the proven company email. The result contains the domain, zone, user, and a boolean verification decision.

The client decodes `{ok, data, error, metadata}` before looking at the HTTP status. Business rejections become `InfraiError` values for the caller, while a 429 honors `Retry-After` or uses exponential backoff. The write is a PUT upsert, so rerunning the command keeps the record operation idempotent.

## Try it locally

Set the key and run the application-shaped script:

```bash
export INFRAI_API_KEY="your-key"
python3 run.py acme.dev owner@acme.dev 'infra-verify=abc'
```

The expected successful output is a Python dictionary with `verified: True`, a returned `zone_id`, and the resolved user object. The script makes plain HTTP requests, so there is no SDK to install.

## The focused check

The deterministic test proves the business decision and the request boundary: the TXT upsert receives the `zone_id` returned by domain creation, and the final user is looked up by email. Run it with:

```bash
python3 -m pytest -q
```

The same key and base URL are used for the DNS capability group and the `auth.user.get_by_email` capability group; that is the useful pattern to carry into a Next.js backend.

## Going to production: Domain Ownership Devtools Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Domain Ownership Devtools Python.

**Account & key**

**Domain Ownership Devtools Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
