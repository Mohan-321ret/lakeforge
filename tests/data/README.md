# Lakeforge Sample Dataset

This directory contains sample CSV files for testing and demonstrating Lakeforge capabilities.

## Dataset Overview

The sample dataset represents an e-commerce company with the following tables:

### 1. `customers.csv`
Customer master data with 15 records.

**Columns:**
- `customer_id` (INT): Unique customer identifier
- `first_name` (VARCHAR): Customer first name
- `last_name` (VARCHAR): Customer last name
- `email` (VARCHAR): Customer email address
- `phone` (VARCHAR): Customer phone number
- `country` (VARCHAR): Customer country
- `registration_date` (DATE): Date customer registered
- `account_status` (VARCHAR): Active or inactive status

**Sample Questions:**
- How many active customers are there?
- Which country has the most customers?
- How many customers registered in 2020?
- List all inactive customers

### 2. `orders.csv`
Customer orders with 20 records.

**Columns:**
- `order_id` (INT): Unique order identifier
- `customer_id` (INT): Reference to customer
- `order_date` (DATE): Date order was placed
- `ship_date` (DATE): Date order was shipped (NULL if not yet shipped)
- `total_amount` (DECIMAL): Order total in USD
- `status` (VARCHAR): Order status (delivered, pending, cancelled)
- `region` (VARCHAR): Geographic region (North, South, East, West)

**Sample Questions:**
- What is the average order value?
- How many orders are pending?
- What is the total revenue by region?
- Which customer has placed the most orders?
- Show me orders that haven't shipped yet

### 3. `products.csv`
Product catalog with 15 records.

**Columns:**
- `product_id` (VARCHAR): Unique product identifier
- `product_name` (VARCHAR): Product name
- `category` (VARCHAR): Product category (Electronics, Furniture, Accessories, Supplies)
- `price` (DECIMAL): Product price in USD
- `stock_quantity` (INT): Total stock available
- `manufacturer` (VARCHAR): Manufacturing company
- `sku` (VARCHAR): Stock keeping unit

**Sample Questions:**
- What is the average product price by category?
- Which products are low on stock?
- List all products by manufacturer
- What is the total inventory value?

### 4. `inventory.csv`
Inventory tracking by warehouse with 15 records.

**Columns:**
- `inventory_id` (VARCHAR): Unique inventory record identifier
- `product_id` (VARCHAR): Reference to product
- `warehouse_location` (VARCHAR): Warehouse location (Warehouse-A, B, C)
- `quantity_available` (INT): Available quantity
- `quantity_reserved` (INT): Reserved/allocated quantity
- `last_updated` (DATE): Last inventory update
- `reorder_level` (INT): Minimum stock level

**Sample Questions:**
- How much stock is available by warehouse?
- Which products need reordering?
- What is the utilization rate across warehouses?
- Which warehouse has the largest inventory?

## Dataset Statistics

- **Total Records**: ~60 rows across 4 tables
- **Time Period**: January 2020 - November 2021
- **Geographic Coverage**: USA, Canada, UK, Australia
- **Data Quality**:
  - Some NULL values (e.g., ship_date for pending orders)
  - Mix of active/inactive statuses
  - Various order statuses (delivered, pending, cancelled)

## Usage Examples

### View Customer Data
```bash
lakeforge inspect customers.csv
> Show me all customers
> How many customers are from USA?
```

### Analysis Queries
```bash
lakeforge inspect orders.csv --ask "What is total revenue by status?"
lakeforge inspect products.csv --ask "List products by category with average price"
```

### Combined Analysis
```bash
# Create a DuckDB view combining customers and orders
lakeforge inspect orders.csv
> Join with customer data to show order history per customer
```

## Creating Parquet Versions

To convert CSV files to Parquet format:

```python
import pandas as pd

for csv_file in ['customers.csv', 'orders.csv', 'products.csv', 'inventory.csv']:
    df = pd.read_csv(csv_file)
    df.to_parquet(csv_file.replace('.csv', '.parquet'))
```

## Integration with Tests

These datasets are used in:
- `tests/test_phase10_cli.py` - CLI integration tests
- `tests/test_discover.py` - Source discovery tests
- `tests/test_phase12_*.py` - Phase 12 integration tests

## Notes

- All datetime fields use ISO 8601 format (YYYY-MM-DD)
- Numeric values use standard US formatting (period for decimal)
- Email domains are fictional but follow standard format
- Phone numbers use North American format (555-XXXX)
- Prices are in USD throughout the dataset

## Future Enhancements

- [ ] Add Parquet versions of all tables
- [ ] Add larger TPC-H derived dataset
- [ ] Add JSON format versions
- [ ] Add multi-table foreign key relationships
- [ ] Add time-series data for analytics
- [ ] Add PII-containing data for PII detection testing
