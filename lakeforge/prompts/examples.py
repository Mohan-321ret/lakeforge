"""Few-shot examples for SQL generation by question type."""

# Examples for DESCRIBE queries
DESCRIBE_EXAMPLES = [
    {
        "question": "What columns are in the users table?",
        "sql": "DESCRIBE users;",
        "note": "Simple schema inspection",
    },
    {
        "question": "Show me the schema of products",
        "sql": "PRAGMA table_info(products);",
        "note": "DuckDB uses PRAGMA for schema",
    },
    {
        "question": "What data types does the orders table have?",
        "sql": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders';",
        "note": "Information schema query",
    },
]

# Examples for AGGREGATE queries
AGGREGATE_EXAMPLES = [
    {
        "question": "How many users are there?",
        "sql": "SELECT COUNT(*) as total_users FROM users;",
        "note": "Simple count",
    },
    {
        "question": "What is the average order value?",
        "sql": "SELECT AVG(amount) as average_order_value FROM orders;",
        "note": "Average calculation",
    },
    {
        "question": "How many active users are there?",
        "sql": "SELECT COUNT(*) as active_users FROM users WHERE status = 'active';",
        "note": "Count with filter",
    },
    {
        "question": "What are the min and max product prices?",
        "sql": "SELECT MIN(price) as min_price, MAX(price) as max_price FROM products;",
        "note": "Multiple aggregates",
    },
    {
        "question": "How many orders per month?",
        "sql": "SELECT DATE_TRUNC('month', order_date) as month, COUNT(*) as order_count FROM orders GROUP BY DATE_TRUNC('month', order_date) ORDER BY month;",
        "note": "Time-based aggregation",
    },
]

# Examples for FILTER queries
FILTER_EXAMPLES = [
    {
        "question": "List all users from California",
        "sql": "SELECT * FROM users WHERE state = 'CA' LIMIT 100;",
        "note": "Simple filter",
    },
    {
        "question": "Show products under $100",
        "sql": "SELECT * FROM products WHERE price < 100 LIMIT 100;",
        "note": "Numeric filter",
    },
    {
        "question": "Find orders from the last 30 days",
        "sql": "SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days' LIMIT 100;",
        "note": "Date filter",
    },
    {
        "question": "List customers who spent more than $1000",
        "sql": "SELECT customer_id, SUM(amount) as total_spent FROM orders GROUP BY customer_id HAVING SUM(amount) > 1000 LIMIT 100;",
        "note": "Filter with aggregation",
    },
]

# Examples for JOIN queries
JOIN_EXAMPLES = [
    {
        "question": "Show users with their orders",
        "sql": "SELECT u.name, o.order_id, o.amount FROM users u LEFT JOIN orders o ON u.user_id = o.user_id LIMIT 100;",
        "note": "Simple JOIN",
    },
    {
        "question": "List products and their categories",
        "sql": "SELECT p.name, c.category_name FROM products p JOIN categories c ON p.category_id = c.category_id LIMIT 100;",
        "note": "INNER JOIN",
    },
    {
        "question": "Show all customers and their total spending",
        "sql": "SELECT u.name, COUNT(o.order_id) as order_count, SUM(o.amount) as total_spent FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.user_id, u.name LIMIT 100;",
        "note": "JOIN with aggregation",
    },
]

# Examples for CUSTOM queries (complex)
CUSTOM_EXAMPLES = [
    {
        "question": "What is the average order value by region, ordered by region?",
        "sql": "SELECT region, AVG(amount) as avg_order_value, COUNT(*) as order_count FROM orders GROUP BY region ORDER BY region;",
        "note": "GROUP BY with ORDER BY",
    },
    {
        "question": "Top 5 customers by total spending",
        "sql": "SELECT u.name, SUM(o.amount) as total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.user_id, u.name ORDER BY total_spent DESC LIMIT 5;",
        "note": "Complex with JOIN and aggregation",
    },
    {
        "question": "Revenue by product category in the last quarter",
        "sql": "SELECT c.category_name, SUM(o.amount) as revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN categories c ON p.category_id = c.category_id WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days' GROUP BY c.category_id, c.category_name ORDER BY revenue DESC;",
        "note": "Multiple JOINs with time filter",
    },
]


def get_examples_for_category(category: str) -> list[dict]:
    """Get few-shot examples for a query category.
    
    Args:
        category: Query category (DESCRIBE, AGGREGATE, FILTER, JOIN, CUSTOM)
        
    Returns:
        List of example dicts with 'question', 'sql', 'note' keys
    """
    mapping = {
        "DESCRIBE": DESCRIBE_EXAMPLES,
        "AGGREGATE": AGGREGATE_EXAMPLES,
        "FILTER": FILTER_EXAMPLES,
        "JOIN": JOIN_EXAMPLES,
        "CUSTOM": CUSTOM_EXAMPLES,
    }
    
    return mapping.get(category, CUSTOM_EXAMPLES)


def format_examples_for_prompt(category: str, max_examples: int = 3) -> str:
    """Format examples for inclusion in LLM prompt.
    
    Args:
        category: Query category
        max_examples: Maximum number of examples to include
        
    Returns:
        Formatted string of examples
    """
    examples = get_examples_for_category(category)[:max_examples]
    
    formatted = "\n".join([
        f"Q: {ex['question']}\nSQL: {ex['sql']}\n"
        for ex in examples
    ])
    
    return formatted
