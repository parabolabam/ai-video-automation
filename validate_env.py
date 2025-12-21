#!/usr/bin/env python3
"""
Environment variable validation script.
Fails container startup if required environment variables are missing.
Run this before starting the application.
"""

import os
import sys
from typing import List, Tuple

# Required environment variables (cannot be empty)
REQUIRED_VARS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "KIE_API_KEY",
    "OPENAI_API_KEY",
]

# Optional but recommended variables (warnings only)
RECOMMENDED_VARS = [
    "SUPABASE_KEY",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
]


def validate_env() -> Tuple[bool, List[str], List[str]]:
    """
    Validate environment variables.

    Returns:
        Tuple of (success, missing_required, missing_recommended)
    """
    missing_required = []
    missing_recommended = []

    # Check required variables
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_required.append(var)

    # Check recommended variables
    for var in RECOMMENDED_VARS:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_recommended.append(var)

    success = len(missing_required) == 0
    return success, missing_required, missing_recommended


def main():
    """Main validation function."""
    print("=" * 60)
    print("Environment Variable Validation")
    print("=" * 60)

    success, missing_required, missing_recommended = validate_env()

    # Report required variables
    if missing_required:
        print("\n❌ MISSING REQUIRED ENVIRONMENT VARIABLES:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nContainer startup will FAIL.")
        print("Please set these environment variables and try again.")
    else:
        print("\n✅ All required environment variables are set.")

    # Report recommended variables
    if missing_recommended:
        print("\n⚠️  MISSING RECOMMENDED ENVIRONMENT VARIABLES:")
        for var in missing_recommended:
            print(f"   - {var}")
        print("\nThese are optional but some features may not work.")

    # Report current configuration
    print("\n" + "=" * 60)
    print("Current Configuration:")
    print("=" * 60)

    all_vars = REQUIRED_VARS + RECOMMENDED_VARS
    for var in sorted(all_vars):
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if len(value) > 10:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
            else:
                masked = "*" * len(value)
            print(f"  {var}: {masked}")
        else:
            print(f"  {var}: NOT SET")

    print("=" * 60)

    # Exit with error code if validation failed
    if not success:
        print("\n💥 Environment validation FAILED!")
        print("Exiting with code 1...")
        sys.exit(1)
    else:
        print("\n✅ Environment validation PASSED!")
        print("Starting application...")
        sys.exit(0)


if __name__ == "__main__":
    main()
