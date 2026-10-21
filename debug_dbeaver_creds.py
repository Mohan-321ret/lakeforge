#!/usr/bin/env python3
"""Check for DBeaver credentials in alternative locations."""

import os
import json

dbeaver_base = os.path.expanduser(r"~\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver")

print(f"🔍 Checking DBeaver config directory: {dbeaver_base}\n")

if os.path.exists(dbeaver_base):
    for file in os.listdir(dbeaver_base):
        file_path = os.path.join(dbeaver_base, file)
        if os.path.isfile(file_path):
            print(f"   📄 {file} ({os.path.getsize(file_path)} bytes)")
        else:
            print(f"   📁 {file}/")

# Check for credentials files
for possible_cred_file in ['credentials.json', 'secure-storage.json', 'credentials-config.json', 'secrets.json']:
    full_path = os.path.join(dbeaver_base, possible_cred_file)
    if os.path.exists(full_path):
        print(f"\n✅ Found credentials file: {full_path}")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
            print(json.dumps(creds, indent=2))
        except Exception as e:
            print(f"❌ Error reading: {e}")

# Check for credential-config.xml or security-config files
for file in os.listdir(dbeaver_base):
    if 'cred' in file.lower() or 'secure' in file.lower() or 'secret' in file.lower():
        print(f"\n🔐 Found potential credentials file: {file}")
        file_path = os.path.join(dbeaver_base, file)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[:500]
                print(f"   Content (first 500 chars): {content}")
        except:
            print(f"   (Binary or unreadable file)")
