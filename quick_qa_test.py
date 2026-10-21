"""Quick Q&A test with Groq API key"""

import requests
import time
import json

time.sleep(2)  # Wait for backend

BASE_URL = 'http://localhost:8000/api'

print('\n=== LAKEFORGE Q&A TEST ===\n')

# Create source
print('[1] Creating data source...')
resp = requests.post(f'{BASE_URL}/sources', json={
    'name': 'SQLite Sample',
    'uri': 'sqlite:///c:/Users/MohanaPrasanthSivaku/Desktop/lakeforge/sample_data.db'
})
source_id = resp.json()['id']
print(f'    [OK] Source created: {source_id}')

# Test connection
print('\n[2] Testing connection...')
resp = requests.post(f'{BASE_URL}/sources/{source_id}/test')
print(f'    [OK] {resp.json().get("message")}')

# Test Q&A
print('\n[3] Testing Q&A - "How many customers are in the database?"')
resp = requests.post(f'{BASE_URL}/qa', json={
    'source_id': source_id,
    'question': 'How many customers are in the database?'
})
result = resp.json()

print(f'    Execution Status: {result.get("execution_status")}')
print(f'    Generated SQL: {result.get("generated_sql")}')
print(f'    Results: {result.get("results")}')
print(f'    Execution Time: {result.get("execution_time_ms")}ms')

if result.get('error_message'):
    print(f'    Error: {result.get("error_message")}')
else:
    print(f'    [OK] Q&A successful!')

print('\n=== TEST COMPLETE ===\n')
