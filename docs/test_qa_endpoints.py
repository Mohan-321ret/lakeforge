"""Test Q&A endpoints."""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
DB_PATH = Path(__file__).resolve().parent / "sample_data.db"
URI = f"sqlite:///{DB_PATH.as_posix()}"

def test_qa_endpoints():
    """Test all Q&A endpoints."""
    
    print("\n" + "="*60)
    print("TESTING Q&A ENDPOINTS")
    print("="*60)
    
    # Step 1: Create a data source (SQLite sample)
    print("\n[1] Creating SQLite sample data source...")
    source_data = {
        "name": "SQLite Sample DB",
        "uri": URI,
        "description": "Sample database for Q&A testing"
    }
    
    resp = requests.post(f"{BASE_URL}/sources", json=source_data)
    print(f"    Status: {resp.status_code}")
    
    if resp.status_code != 201:
        print(f"    Error: {resp.text}")
        return False
    
    source_id = resp.json()["id"]
    print(f"    [OK] Created source: {source_id}")
    
    # Step 2: Test connection
    print(f"\n[2] Testing connection to source {source_id}...")
    resp = requests.post(f"{BASE_URL}/sources/{source_id}/test")
    print(f"    Status: {resp.status_code}")
    print(f"    Result: {resp.json()}")
    
    # Step 3: Ask simple questions
    test_questions = [
        "How many customers are in the database?",
        "What is the total amount of all orders?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i+2}] Asking: '{question}'")
        
        qa_request = {
            "source_id": source_id,
            "question": question,
        }
        
        resp = requests.post(f"{BASE_URL}/qa", json=qa_request)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"    Generated SQL: {result.get('generated_sql', 'N/A')}")
            print(f"    Execution Status: {result.get('execution_status')}")
            
            if result.get('execution_status') == 'success':
                results = result.get('results', [])
                print(f"    Results ({len(results)} rows): {results}")
                print(f"    [OK] Query successful ({result.get('execution_time_ms', 0):.1f}ms)")
            else:
                error = result.get('error_message', 'Unknown error')
                print(f"    [ERROR] {error}")
        else:
            print(f"    [ERROR] HTTP {resp.status_code}")
            print(f"    Response: {resp.text}")
    
    print("\n" + "="*60)
    print("Q&A ENDPOINT TESTS COMPLETE")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        test_qa_endpoints()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
