"""Provision named staff accounts and organizations for a local pilot.

Accounts are created from the command line rather than through a public sign-up
route: there is no registration flow, and there should not be one before the
deployment and identity-provider decisions in docs/BUILD_BACKLOG.md (B01c).
"""
from pathlib import Path
import argparse
import secrets
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.accounts import Directory
from app.config import Settings
from app.identity import ROLES, totp_now
from app.storage import Store, DEFAULT_ORG_ID


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--totp-code', metavar='SECRET',
                        help='print the current 6-digit code for a secret and exit')
    parser.add_argument('--list', action='store_true', help='list organizations and staff')
    parser.add_argument('--create-org', metavar='NAME', help='create an organization')
    parser.add_argument('--org', default=DEFAULT_ORG_ID, help=f'organization id (default: {DEFAULT_ORG_ID})')
    parser.add_argument('--email')
    parser.add_argument('--name', default='Staff member')
    parser.add_argument('--role', choices=sorted(ROLES), default='analyst')
    parser.add_argument('--password', help='omit to generate one')
    args = parser.parse_args()

    if args.totp_code:
        print(totp_now(args.totp_code))
        return

    settings = Settings.from_env()
    directory = Directory(Store(settings.database, settings.report_ttl_days))

    if args.create_org:
        print('Created organization:', directory.create_org(args.create_org))
        return

    if args.list:
        for org in directory.organizations():
            print(f"\n{org['id']}  {org['name']}")
            for person in directory.staff_list(org['id']) or []:
                state = 'disabled' if person['disabled'] else 'active'
                print(f"  {person['email']:<32} {person['role']:<8} {state}")
        return

    if not args.email:
        parser.error('provide --email, or use --list / --create-org / --totp-code')

    password = args.password or secrets.token_urlsafe(15)
    account = directory.create_staff(args.org, args.email, args.name, password, args.role)
    print(f"Created {account['email']} as {account['role']} in {account['org_id']}")
    print(f"  Password    {password}")
    print(f"  MFA secret  {account['totp_secret']}")
    print(f"  Enrol with  {account['provisioning_uri']}")
    print('These values are shown once.')


if __name__ == '__main__':
    main()
