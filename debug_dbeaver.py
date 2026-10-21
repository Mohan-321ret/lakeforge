#!/usr/bin/env python3
"""Debug script to inspect DBeaver config structure."""

import os
import json
import sys

path = os.path.expanduser(r"~\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json")

print(f"\n🔍 Checking DBeaver config at: {path}")
print(f"📁 File exists: {os.path.exists(path)}\n")

if os.path.exists(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find SQL Server connections
        found_any = False
        if 'connections' in data:
            for conn_id, conn in data['connections'].items():
                driver = conn.get('driver', '').lower()
                if 'sqlserver' in driver or 'mssql' in driver or 'microsoft' in driver:
                    found_any = True
                    print(f"\n✅ Found SQL Server connection:")
                    print(f"   ID: {conn_id}")
                    print(f"   Name: {conn.get('name')}")
                    print(f"   Driver: {conn.get('driver')}")
                    
                    # Check the properties/parameters structure
                    params = conn.get('properties', {}).get('parameters', {})
                    print(f"\n   📋 Parameters keys: {list(params.keys())}")
                    print(f"\n   📄 Full parameters object:")
                    print(json.dumps(params, indent=4))
                    print("\n" + "="*80)
        
        if not found_any:
            print("❌ No SQL Server connections found in DBeaver config")
            print(f"\n   All connections in file: {list(data.get('connections', {}).keys())}")
    
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
else:
    print(f"❌ File not found at: {path}")
    print("\n   Check if DBeaver is installed and has saved connections")
