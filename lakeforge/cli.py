"""Command-line interface for Lakeforge."""

import sys
import traceback
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from lakeforge import __version__
from lakeforge.config import get_config
from lakeforge.discover import discover_source, profile_source
from lakeforge.errors import (
    LakeforgeException,
    SourceNotFoundError,
    InvalidSourceURIError,
    ConnectorNotAvailableError,
    AuthenticationError,
    get_error_suggestion,
)
from lakeforge.report import write_report
from lakeforge.session import QASession
from lakeforge.sources.registry import get_connector


def _version_callback(value: bool) -> None:
    """Handle --version flag."""
    if value:
        console.print(f"[cyan]Lakeforge[/cyan] v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    help="Lakeforge: Data Engineer's Source Inspection & Insight Tool",
    rich_markup_mode="rich",
)
console = Console()

# Add version callback
app.command()(lambda: None)  # Dummy to avoid issues


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Lakeforge: Data Engineer's Source Inspection & Insight Tool."""
    pass


@app.command()
def version() -> None:
    """Show Lakeforge version."""
    console.print(f"[cyan]Lakeforge[/cyan] v{__version__}")


@app.command()
def inspect(
    source: str = typer.Argument(
        ...,
        help="Source URI: local file (data.csv), S3 (s3://bucket/key), Databricks (databricks://workspace/catalog/schema/table), or Postgres (postgres://user@host/db/schema)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for report (default: .lakeforge/report-<runid>/)",
    ),
    ask: Optional[str] = typer.Option(
        None,
        "--ask",
        "-q",
        help="Ask a single question in one-shot mode (default: interactive REPL)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging and debug output",
    ),
    profile: bool = typer.Option(
        False,
        "--profile",
        "-p",
        help="Include statistical profiling and PII detection (slower)",
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config YAML file",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Query timeout in seconds (default: 30)",
    ),
) -> None:
    """Inspect a data source and generate a report with schema, profile, and insights.

    Enter interactive REPL mode by default for asking questions.
    Use --ask for one-shot mode to ask a single question and exit.

    EXAMPLES:

      # Interactive mode (REPL)
      $ lakeforge inspect users.csv
      $ lakeforge inspect s3://my-bucket/data.parquet

      # One-shot mode (single question)
      $ lakeforge inspect users.csv --ask "How many rows?"
      $ lakeforge inspect data.csv --ask "Show me the schema"

      # With profiling and verbose output
      $ lakeforge inspect data.csv --profile --verbose

      # Remote sources
      $ lakeforge inspect databricks://workspace/catalog/schema/table
      $ lakeforge inspect postgres://user:pass@localhost/dbname/schema

    AUTHENTICATION:

      Databricks: Set DATABRICKS_TOKEN and DATABRICKS_HOST env vars
      Postgres: Set POSTGRES_CONNECTION_STRING or use URI credentials
      S3: Uses boto3 (AWS credentials from environment or ~/.aws/credentials)
    """
    try:
        # Load config
        config = get_config()

        if verbose:
            console.print("[blue]Starting inspection...[/blue]")
            console.print(f"[dim]Source:[/dim] {source}")
            console.print(f"[dim]Provider:[/dim] {config.llm_provider}")
            console.print(f"[dim]Timeout:[/dim] {timeout}s")

        # Validate source exists/accessible
        try:
            validation_result = _validate_source(source, verbose)
            if not validation_result["valid"]:
                error_msg = validation_result["message"]
                suggestion = validation_result.get("suggestion")
                _print_error(error_msg, suggestion, verbose)
                raise typer.Exit(code=1)
        except Exception as e:
            _print_error(f"Failed to validate source: {str(e)}", None, verbose)
            raise typer.Exit(code=1)

        # Generate inspection report
        output_dir = Path(output) if output else config.output_dir
        connector = get_connector(source)
        try:
            if profile:
                catalog, profile_obj = profile_source(connector, verbose=verbose)
            else:
                catalog = discover_source(connector, verbose=verbose)
                profile_obj = None

            report_path = write_report(catalog, profile=profile_obj, output_dir=output_dir)
            catalog_path = report_path.parent / "catalog.json"
            console.print(f"[green]Report generated:[/green] {report_path}")
            if verbose:
                console.print(f"[green]Catalog schema:[/green] {catalog_path}")
        finally:
            connector.close()

        # Determine mode: one-shot or REPL
        if ask:
            # One-shot mode: ask question and exit
            _run_oneshot(source, ask, output, verbose, profile, timeout)
        elif sys.stdin and sys.stdin.isatty():
            # REPL mode: interactive Q&A loop
            _run_repl(source, output, verbose, profile, timeout)

    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted by user[/yellow]")
        raise typer.Exit(code=0)
    except LakeforgeException as e:
        _print_error(e.message, e.suggestion, verbose)
        raise typer.Exit(code=1)
    except Exception as e:
        suggestion = get_error_suggestion(e)
        _print_error(f"Unexpected error: {str(e)}", suggestion, verbose)
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


def _run_oneshot(
    source: str,
    question: str,
    output: Optional[str],
    verbose: bool,
    profile: bool,
    timeout: int = 30,
) -> None:
    """Run one-shot Q&A mode.

    Args:
        source: Data source
        question: Question to ask
        output: Output directory
        verbose: Verbose logging
        profile: Include profiling
        timeout: Query timeout in seconds
    """
    if verbose:
        console.print("[blue]One-shot mode[/blue]")

    output_dir = Path(output) if output else get_config().output_dir

    # Create session
    try:
        session = QASession(
            source=source,
            output_dir=output_dir,
            verbose=verbose,
            profile=profile,
        )
    except LakeforgeException as e:
        _print_error(e.message, e.suggestion, verbose)
        raise typer.Exit(code=1)
    except Exception as e:
        suggestion = get_error_suggestion(e)
        _print_error(f"Failed to initialize session: {str(e)}", suggestion, verbose)
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)

    try:
        # Ask question
        if verbose:
            console.print(f"[cyan]Question:[/cyan] {question}")

        response = session.ask(question)

        # Print results
        _print_result(response)

        # Print summary
        if verbose:
            summary = session.get_summary()
            console.print(f"\n[dim]Session:[/dim] {summary['session_id']}")
            console.print(f"[dim]Logs:[/dim] {summary['qa_log']}")

    except LakeforgeException as e:
        _print_error(e.message, e.suggestion, verbose)
        raise typer.Exit(code=1)
    except Exception as e:
        suggestion = get_error_suggestion(e)
        _print_error(f"Error during question: {str(e)}", suggestion, verbose)
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)
    finally:
        session.close()


def _run_repl(
    source: str,
    output: Optional[str],
    verbose: bool,
    profile: bool,
    timeout: int = 30,
) -> None:
    """Run interactive REPL mode.

    Args:
        source: Data source
        output: Output directory
        verbose: Verbose logging
        profile: Include profiling
        timeout: Query timeout in seconds
    """
    if verbose:
        console.print("[blue]Interactive REPL mode[/blue]")

    output_dir = Path(output) if output else get_config().output_dir

    # Create session
    try:
        session = QASession(
            source=source,
            output_dir=output_dir,
            verbose=verbose,
            profile=profile,
        )
    except LakeforgeException as e:
        _print_error(e.message, e.suggestion, verbose)
        raise typer.Exit(code=1)
    except Exception as e:
        suggestion = get_error_suggestion(e)
        _print_error(f"Failed to initialize session: {str(e)}", suggestion, verbose)
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)

    try:
        # Print welcome
        console.print(f"\n[cyan]Lakeforge Q&A REPL[/cyan] | Source: {source}")
        console.print("[dim]Type 'exit' or Ctrl+C to quit[/dim]")
        console.print("[dim]For help, type 'help' or visit: https://github.com/lakeforge/lakeforge[/dim]\n")

        # REPL loop
        question_count = 0
        while True:
            try:
                # Read question
                question = console.input("[cyan]> [/cyan]").strip()

                if not question:
                    continue

                # Check for commands
                if question.lower() in ("exit", "quit", "q"):
                    console.print("[yellow]Exiting...[/yellow]")
                    break

                if question.lower() == "help":
                    _print_help()
                    continue

                # Ask question
                question_count += 1
                try:
                    response = session.ask(question)
                    _print_result(response)
                except LakeforgeException as e:
                    _print_error(e.message, e.suggestion, verbose)
                except Exception as e:
                    suggestion = get_error_suggestion(e)
                    _print_error(f"Error: {str(e)}", suggestion, verbose)
                    if verbose:
                        console.print_exception()

                console.print()

            except EOFError:
                # Ctrl+D (EOF)
                console.print("\n[yellow]EOF - Exiting[/yellow]")
                break

        # Print session summary
        summary = session.get_summary()
        console.print(f"\n[dim]Session Summary[/dim]")
        console.print(f"  Questions: {summary['questions_asked']}")
        console.print(f"  Tables: {summary['tables']}")
        console.print(f"  Log: {summary['qa_log']}")

    finally:
        session.close()


def _print_result(response: dict) -> None:
    """Print Q&A result in formatted output.

    Args:
        response: Q&A response dict
    """
    if response.get("error"):
        console.print(f"[red]{response['answer']}[/red]")
    else:
        console.print(f"[green]{response['answer']}[/green]")

        # Print SQL if available (for transparency)
        if response.get("sql"):
            console.print(f"\n[dim]SQL:[/dim] {response['sql']}")


def _print_error(message: str, suggestion: Optional[str] = None, verbose: bool = False) -> None:
    """Print error message with optional suggestion.

    Args:
        message: Error message
        suggestion: Helpful suggestion
        verbose: Whether to include extra details
    """
    console.print(f"[red]Error:[/red] {message}")
    if suggestion:
        console.print(f"[yellow]Suggestion:[/yellow] {suggestion}")


def _print_help() -> None:
    """Print help text in REPL mode."""
    console.print("""
[cyan]Lakeforge Q&A Help[/cyan]

Commands:
  [bold]exit, quit, q[/bold]     Exit the REPL
  [bold]help[/bold]              Show this help message

Question Examples:
  [dim]> Show me the schema[/dim]
  [dim]> How many rows in users table?[/dim]
  [dim]> List all column names[/dim]
  [dim]> What are the data types?[/dim]
  [dim]> Show me 5 sample rows[/dim]
  [dim]> Count distinct values in status column[/dim]

Tips:
  • Use specific column and table names when available
  • Ask one question at a time
  • Type 'exit' or press Ctrl+C to quit
  
For more help, visit: https://github.com/lakeforge/lakeforge
""")



def _validate_source(source: str, verbose: bool = False) -> dict:
    """Validate that source is accessible and properly formatted.

    Args:
        source: Source URI or local file path.
        verbose: Print verbose validation details

    Returns:
        Dict with keys: valid (bool), message (str), suggestion (Optional[str])
    """
    # If local path
    if "://" not in source:
        file_path = Path(source)
        if file_path.exists():
            if verbose:
                console.print(f"[dim]✓ Source exists: {file_path.absolute()}[/dim]")
            return {"valid": True, "message": "Source accessible"}
        else:
            return {
                "valid": False,
                "message": f"File not found: {source}",
                "suggestion": "Check the file path exists. Use absolute paths for clarity.",
            }

    # Parse URI
    if source.startswith("s3://"):
        # S3 paths are validated lazily
        if verbose:
            console.print(f"[dim]ℹ S3 source (validation deferred to connector): {source}[/dim]")
        return {"valid": True, "message": "S3 source format valid"}

    if source.startswith("databricks://"):
        # Databricks URI validation
        parts = source.split("/")
        if len(parts) < 5:  # databricks://workspace/catalog/schema/table
            return {
                "valid": False,
                "message": "Invalid Databricks URI format",
                "suggestion": "Expected format: databricks://workspace/catalog/schema/table",
            }
        if verbose:
            console.print(
                f"[dim]✓ Databricks URI format valid (credentials checked at connect time)[/dim]"
            )
        return {"valid": True, "message": "Databricks URI format valid"}

    if source.startswith("postgres://"):
        # Postgres URI validation
        if "@" not in source and "://" in source:
            if verbose:
                console.print(f"[dim]ℹ Postgres URI (auth validation deferred to connector)[/dim]")
        return {"valid": True, "message": "Postgres URI format valid"}

    # Unknown scheme
    return {
        "valid": False,
        "message": f"Unknown source type: {source}",
        "suggestion": "Supported formats: local files, s3://path, databricks://..., postgres://...",
    }


if __name__ == "__main__":
    app()
