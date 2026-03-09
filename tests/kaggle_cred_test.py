"""Kaggle Credential Test
Safely verifies that Kaggle API credentials are set without printing the secret key.

Usage (PowerShell):
  $Env:KAGGLE_USERNAME = "your_username"
  $Env:KAGGLE_KEY = "<secret>"
  python kaggle_cred_test.py

Or ensure ~/.kaggle/kaggle.json exists. This script will attempt a lightweight
`kaggle datasets list -s math` call and summarize success/failure.
"""

import os
import subprocess
import json
from pathlib import Path

def has_kaggle_json() -> bool:
    home = Path.home()
    return (home / ".kaggle" / "kaggle.json").is_file()

def read_kaggle_json():
    try:
        path = Path.home() / ".kaggle" / "kaggle.json"
        data = json.loads(path.read_text())
        return {k: data.get(k) for k in ("username", "key")}
    except Exception:
        return None

def main():
    env_user = os.getenv("KAGGLE_USERNAME")
    env_key_present = os.getenv("KAGGLE_KEY") is not None  # don't expose key
    json_creds = read_kaggle_json() if has_kaggle_json() else None

    print("Checking Kaggle credentials...")
    print(f" - ENV username: {'set' if env_user else 'missing'}")
    print(f" - ENV key: {'set' if env_key_present else 'missing'} (never printed)")
    print(f" - kaggle.json present: {'yes' if json_creds else 'no'}")
    if json_creds:
        print(f"   * File username: {json_creds.get('username') or 'missing'}")
        print(f"   * File key: {'present' if json_creds.get('key') else 'missing'}")

    # Decide which source to rely on
    if not env_user and json_creds and json_creds.get("username"):
        print("Using kaggle.json credentials (ENV not set).")
    elif env_user and env_key_present:
        print("Using environment credentials.")
    else:
        print("❌ Insufficient credentials. Set ENV vars or kaggle.json first.")
        return

    print("\nAttempting lightweight Kaggle API call (datasets list)...")
    try:
        # Use a short search term to reduce output
        result = subprocess.run([
            "kaggle", "datasets", "list", "-s", "math", "-p", "10"
        ], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.splitlines()[:6]
            print("✅ API call succeeded. Sample output:")
            for line in lines:
                print("   ", line)
        else:
            print("❌ API call failed.")
            print("stderr:")
            print(result.stderr.strip())
    except FileNotFoundError:
        print("❌ 'kaggle' CLI not found. Install with: pip install kaggle")
    except subprocess.TimeoutExpired:
        print("❌ Timed out calling Kaggle API.")

if __name__ == "__main__":
    main()
