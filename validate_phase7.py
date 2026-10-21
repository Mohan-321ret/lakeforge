#!/usr/bin/env python3
"""Validate Phase 7 SQL generation module."""

from lakeforge.llm.router import QueryType
from lakeforge.llm.sql_gen import SQLGenerator
from unittest.mock import MagicMock

# Test schema
schema = {
    "users": [
        {"name": "id", "type": "INTEGER", "nullable": False, "description": "User ID"},
        {"name": "name", "type": "TEXT", "nullable": False, "description": "User name"},
        {"name": "email", "type": "TEXT", "nullable": True, "description": "Email address"},
        {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "description": "Creation timestamp"}
    ],
    "orders": [
        {"name": "id", "type": "INTEGER", "nullable": False, "description": "Order ID"},
        {"name": "user_id", "type": "INTEGER", "nullable": False, "description": "User ID"},
        {"name": "amount", "type": "DECIMAL", "nullable": False, "description": "Order amount"},
        {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "description": "Order date"}
    ]
}

# Test validation with mock LLM
mock_llm = MagicMock()
mock_router = MagicMock()
gen = SQLGenerator(llm=mock_llm, router=mock_router)

# Test cases
test_cases = [
    ("SELECT COUNT(*) FROM users;", QueryType.AGGREGATE, True),
    ("SELECT * FROM users LIMIT 10;", QueryType.DESCRIBE, True),
    ("SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;", QueryType.JOIN, True),
    ("DELETE FROM users WHERE id = 1;", QueryType.AGGREGATE, False),
    ("INSERT INTO users VALUES (1, 'test');", QueryType.AGGREGATE, False),
    ("WITH user_stats AS (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id) SELECT * FROM user_stats;", QueryType.CUSTOM, True),
]

print("SQL Validation Tests:")
print("-" * 80)
passed = 0
for sql, query_type, expected_valid in test_cases:
    is_valid = gen._validate_sql(sql)
    status = "✓" if is_valid == expected_valid else "✗"
    if is_valid == expected_valid:
        passed += 1
    print(f"{status} Type: {query_type.value:10} Valid: {is_valid:5} Expected: {expected_valid:5}")
    print(f"   SQL: {sql[:60]}...")
    print()

print(f"\nValidation tests: {passed}/{len(test_cases)} passed")

print("\nSQL extraction tests:")
print("-" * 80)

test_extracts = [
    ("SELECT * FROM users;", "SELECT * FROM users;"),
    ("```sql\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
    ("Here's the query:\n```sql\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
]

passed_extract = 0
for input_text, expected_sql in test_extracts:
    extracted = gen._extract_sql(input_text)
    status = "✓" if extracted == expected_sql else "✗"
    if extracted == expected_sql:
        passed_extract += 1
    print(f"{status} Input: {input_text[:40]}...")
    print(f"   Expected: {expected_sql}")
    print(f"   Got:      {extracted}")
    print()

print(f"\nExtraction tests: {passed_extract}/{len(test_extracts)} passed")

print("\n" + "="*80)
if passed == len(test_cases) and passed_extract == len(test_extracts):
    print("✓ Phase 7 SQL generation module validation: ALL TESTS PASSED")
else:
    print("✗ Some tests failed")
