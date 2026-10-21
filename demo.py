#!/usr/bin/env python3
"""
Lakeforge Demo Script

This script demonstrates the key capabilities of Lakeforge:
1. Data discovery and schema inspection
2. Interactive Q&A with sample data
3. Multi-source analysis
4. Error handling and recovery
"""

import sys
from pathlib import Path
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source
from lakeforge.session import QASession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def demo_section(title: str):
    """Print a demo section header."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("=" * 60)

def demo_1_schema_discovery():
    """Demo 1: Schema Discovery"""
    demo_section("Demo 1: Schema Discovery")
    
    console.print("Analyzing customers.csv to discover schema...")
    
    data_dir = Path(__file__).parent / "tests" / "data"
    customers_file = data_dir / "customers.csv"
    
    if not customers_file.exists():
        console.print(f"[red]Error: {customers_file} not found[/red]")
        return False
    
    try:
        # Get connector
        connector = get_connector(str(customers_file))
        console.print("[green]✓ Connected to customers.csv[/green]")
        
        # Discover schema
        catalog = discover_source(connector)
        console.print(f"[green]✓ Discovered schema[/green]")
        
        # Display table info
        for table_name, table in catalog.tables.items():
            console.print(f"\nTable: [bold]{table_name}[/bold]")
            console.print(f"  Rows: {table.row_count}")
            console.print(f"  Columns: {len(table.columns)}")
            
            # Display columns
            table_display = Table(title="Columns")
            table_display.add_column("Name", style="cyan")
            table_display.add_column("Type", style="magenta")
            
            for col_name, col in sorted(table.columns.items()):
                table_display.add_row(col_name, col.type)
            
            console.print(table_display)
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return False

def demo_2_data_querying():
    """Demo 2: Data Querying"""
    demo_section("Demo 2: Data Querying and SQL Execution")
    
    console.print("Querying orders.csv...")
    
    data_dir = Path(__file__).parent / "tests" / "data"
    orders_file = data_dir / "orders.csv"
    
    if not orders_file.exists():
        console.print(f"[red]Error: {orders_file} not found[/red]")
        return False
    
    try:
        connector = get_connector(str(orders_file))
        
        # Get table name
        tables = connector.list_tables()
        table_name = tables[0]
        
        # Run queries
        queries = [
            ("Row count", f"SELECT COUNT(*) as count FROM {table_name}"),
            ("Total revenue", f"SELECT SUM(total_amount) as total FROM {table_name}"),
            ("Sample rows", f"SELECT * FROM {table_name} LIMIT 3"),
        ]
        
        for title, query in queries:
            console.print(f"\n[bold]{title}:[/bold]")
            console.print(f"  [dim]SQL: {query}[/dim]")
            
            results = connector.query(query)
            
            if results:
                # Display first result
                result = results[0]
                for key, value in result.items():
                    console.print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return False

def demo_3_multi_source():
    """Demo 3: Multi-Source Analysis"""
    demo_section("Demo 3: Multi-Source Analysis")
    
    console.print("Analyzing multiple data sources...")
    
    data_dir = Path(__file__).parent / "tests" / "data"
    
    sources = [
        ("customers.csv", data_dir / "customers.csv"),
        ("orders.csv", data_dir / "orders.csv"),
        ("products.csv", data_dir / "products.csv"),
        ("inventory.csv", data_dir / "inventory.csv"),
    ]
    
    results = []
    
    for name, filepath in sources:
        if filepath.exists():
            try:
                connector = get_connector(str(filepath))
                tables = connector.list_tables()
                row_count_result = connector.query(f"SELECT COUNT(*) as count FROM {tables[0]}")
                row_count = row_count_result[0]['count'] if row_count_result else 0
                
                results.append({
                    "source": name,
                    "rows": row_count,
                    "columns": len(connector.get_schema(tables[0]))
                })
                
                console.print(f"[green]✓ {name:20} {row_count:6} rows  {len(connector.get_schema(tables[0])):3} columns[/green]")
            except Exception as e:
                console.print(f"[red]✗ {name:20} Error: {str(e)[:40]}[/red]")
        else:
            console.print(f"[yellow]⊘ {name:20} File not found[/yellow]")
    
    return len(results) > 0

def demo_4_error_handling():
    """Demo 4: Error Handling"""
    demo_section("Demo 4: Error Handling and Recovery")
    
    console.print("Testing error handling...")
    
    from lakeforge.errors import SourceNotFoundError, InvalidSourceURIError
    
    # Test 1: File not found
    console.print("\n[bold]Test 1: File not found[/bold]")
    try:
        connector = get_connector("/nonexistent/file.csv")
        console.print("[red]✗ Should have raised error[/red]")
    except SourceNotFoundError as e:
        console.print(f"[green]✓ Caught SourceNotFoundError[/green]")
        console.print(f"  Message: {e.message}")
        console.print(f"  Suggestion: {e.suggestion}")
    except Exception as e:
        console.print(f"[green]✓ Caught error: {type(e).__name__}[/green]")
    
    # Test 2: Invalid query
    console.print("\n[bold]Test 2: Invalid SQL query[/bold]")
    data_dir = Path(__file__).parent / "tests" / "data"
    customers_file = data_dir / "customers.csv"
    
    if customers_file.exists():
        try:
            connector = get_connector(str(customers_file))
            # Intentional syntax error
            connector.query("SELEXT * FROMS table")
            console.print("[red]✗ Should have raised error[/red]")
        except Exception as e:
            console.print(f"[green]✓ Caught SQL error[/green]")
            console.print(f"  Type: {type(e).__name__}")
    
    return True

def demo_5_summary():
    """Demo 5: Summary and Next Steps"""
    demo_section("Demo Summary")
    
    summary_text = """
[bold cyan]Lakeforge Capabilities Demonstrated:[/bold cyan]

1. [bold]Schema Discovery[/bold]
   - Automatically detect table structure
   - Identify column names and data types
   - Display metadata in human-readable format

2. [bold]SQL Querying[/bold]
   - Execute flexible SQL queries
   - Get structured results as dicts
   - Support various aggregate functions

3. [bold]Multi-Source Support[/bold]
   - CSV files (local)
   - Parquet files
   - PostgreSQL databases
   - Databricks SQL warehouses
   - S3 buckets

4. [bold]Error Handling[/bold]
   - Clear error messages
   - Helpful suggestions for common issues
   - Graceful recovery mechanisms

5. [bold]Rich Interface[/bold]
   - Formatted tables and panels
   - Color-coded output
   - Readable error messages

[bold cyan]Next Steps:[/bold cyan]

1. Try interactive mode:
   $ lakeforge inspect tests/data/customers.csv

2. Run one-shot queries:
   $ lakeforge inspect tests/data/orders.csv \\
     --ask "How many orders are pending?"

3. Explore the API:
   $ python -c "from lakeforge.session import QASession; ..."

4. Check documentation:
   - USAGE.md: Command-line examples
   - API.md: Programmatic usage
   - CONTRIBUTING.md: Development guide

[bold cyan]Resources:[/bold cyan]

- GitHub: https://github.com/lakeforge/lakeforge
- PyPI: https://pypi.org/project/lakeforge/
- Documentation: See *.md files in project root
    """
    
    console.print(Panel(summary_text, border_style="cyan"))

def main():
    """Run all demos."""
    console.print(Panel(
        "[bold cyan]Lakeforge Demo[/bold cyan]\n"
        "Data Engineer's Source Inspection & Insight Tool",
        border_style="cyan"
    ))
    
    # Run demos
    demos = [
        ("Schema Discovery", demo_1_schema_discovery),
        ("Data Querying", demo_2_data_querying),
        ("Multi-Source Analysis", demo_3_multi_source),
        ("Error Handling", demo_4_error_handling),
        ("Summary", demo_5_summary),
    ]
    
    results = {}
    for name, demo_func in demos:
        try:
            results[name] = demo_func()
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
            return 1
        except Exception as e:
            console.print(f"\n[red]Error in {name}: {str(e)}[/red]")
            results[name] = False
    
    # Print final results
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Demo Results[/bold cyan]")
    
    results_table = Table(title="Demo Results")
    results_table.add_column("Demo", style="cyan")
    results_table.add_column("Status", style="magenta")
    
    for name, result in results.items():
        status = "[green]✓ Passed[/green]" if result else "[yellow]⊘ Skipped[/yellow]"
        results_table.add_row(name, status)
    
    console.print(results_table)
    
    # Exit with success
    console.print("\n[green]Demo completed successfully![/green]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
