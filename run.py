import argparse

from src.domain_ownership_service import complete_onboarding


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a developer-tools domain before onboarding.")
    parser.add_argument("domain")
    parser.add_argument("email")
    parser.add_argument("txt_value")
    args = parser.parse_args()
    result = complete_onboarding(args.domain, args.email, args.txt_value)
    print({"domain": result.domain, "zone_id": result.zone_id, "verified": result.verified, "user": result.user})


if __name__ == "__main__":
    main()

