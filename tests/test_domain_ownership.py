from src.domain_ownership_service import complete_onboarding


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        if path.endswith("/domain/add"):
            return {"ok": True, "data": {"zone_id": "zone_123"}, "error": None, "metadata": {}}
        if path.endswith("/domain/verify"):
            return {"ok": True, "data": {"verified": True}, "error": None, "metadata": {}}
        if path.endswith("/user/get_by_email"):
            return {"ok": True, "data": {"id": "user_7", "email": query["email"]}, "error": None, "metadata": {}}
        return {"ok": True, "data": {}, "error": None, "metadata": {}}


def test_domain_verification_uses_zone_and_resolves_user():
    fake = FakeClient()
    result = complete_onboarding("acme.dev", "owner@acme.dev", "infra-verify=abc", fake)
    assert result.verified is True
    assert result.zone_id == "zone_123"
    upsert = fake.calls[1]
    assert upsert[0:2] == ("PUT", "/v1/dns/record/upsert")
    assert upsert[3]["zone_id"] == "zone_123"
    assert upsert[3]["record_type"] == "TXT"
    assert result.user["email"] == "owner@acme.dev"

