"""Victory Crest One - Seed Initial Enterprise Administrator Script
Usage: python scripts/create_admin.py [--username admin] [--email admin@victorycrest.internal] [--password secret]
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.security import hash_password
from backend.app.services.user_service import user_service
from backend.app.schemas.user import UserCreate
from shared.enums import UserRole


def main():
    parser = argparse.ArgumentParser(description="Create or verify Victory Crest ONE administrator")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@victorycrest.internal", help="Admin email")
    parser.add_argument("--password", default="AdminPassword123!", help="Admin password")
    parser.add_argument("--fullname", default="Chief Administrator", help="Admin full name")
    args = parser.parse_args()

    print("Checking or provisioning administrator account...")
    try:
        user = user_service.create_user(
            UserCreate(
                username=args.username,
                email=args.email,
                password=args.password,
                full_name=args.fullname,
                role=UserRole.SYSTEM_ADMIN.value
            ),
            creator_email="system-cli"
        )
        print(f"✅ Administrator '{user.username}' ({user.email}) provisioned successfully with Argon2 hash!")
    except Exception as e:
        if "already exists" in str(e).lower() or "already registered" in str(e).lower():
            print(f"ℹ️ Administrator '{args.username}' already exists in the system registry.")
        else:
            print(f"❌ Error creating administrator: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
