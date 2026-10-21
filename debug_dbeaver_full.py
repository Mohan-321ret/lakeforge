#!/usr/bin/env python3
"""Debug script to inspect ALL DBeaver connection fields."""

import os
import json

path = os.path.expanduser(r"~\AppData\Roaming\DBeaverData\workspace6\General\.dbeaver\data-sources.json")

if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'connections' in data:
        for conn_id, conn in data['connections'].items():
            if 'microsoft' in conn.get('driver', '').lower():
                print(f"\n✅ Connection: {conn.get('name')}")
                print(f"\n📋 TOP-LEVEL KEYS:")
                for key in sorted(conn.keys()):
                    value = conn[key]
                    if isinstance(value, (dict, list)):
                        print(f"   {key}: {type(value).__name__}")
                    else:
                        print(f"   {key}: {value}")
                
                print(f"\n📄 FULL CONNECTION OBJECT:")
                print(json.dumps(conn, indent=2))
