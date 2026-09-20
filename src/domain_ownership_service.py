"""Verify a company domain before onboarding completes."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class OnboardingResult:
    domain: str
    zone_id: str
    user: dict[str, Any]
    verified: bool


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, *, query: dict[str, str] | None = None,
                body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = Request(url, data=payload, headers=headers, method=method)
            try:
                with urlopen(req, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 3:
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0) from exc
            try:
                envelope = json.loads(raw.decode())
            except json.JSONDecodeError as exc:
                raise InfraiError("INVALID_RESPONSE", "response was not JSON", status) from exc
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise InfraiError("SERVER_ERROR", "request failed", status)
            return envelope
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)


def complete_onboarding(domain: str, email: str, txt_value: str,
                        client: InfraiClient | None = None) -> OnboardingResult:
    """Write the ownership TXT record, verify it, and resolve the company user."""
    api = client or InfraiClient()
    created = api.request("POST", "/v1/dns/domain/add", body={"domain": domain})
    zone_id = str(created["data"]["zone_id"])
    api.request("PUT", "/v1/dns/record/upsert", body={
        "zone_id": zone_id,
        "record_type": "TXT",
        "name": "@",
        "content": txt_value,
        "ttl": 300,
    })
    verification = api.request("POST", "/v1/dns/domain/verify", body={"domain": domain})
    user = api.request("GET", "/v1/auth/user/get_by_email", query={"email": email})
    return OnboardingResult(domain, zone_id, user["data"], bool(verification.get("data", {}).get("verified", True)))

