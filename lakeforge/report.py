"""Report writer for generating Markdown and JSON artifacts."""

import json
from datetime import datetime, date, time
from pathlib import Path
from typing import Any, Optional

from lakeforge.discover import Catalog
from lakeforge.profile import L2Profile


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> str:
        """Encode datetime objects as strings."""
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return super().default(obj)


def write_report(
    catalog: Catalog,
    profile: Optional[L2Profile] = None,
    output_dir: Path = Path("./.lakeforge"),
) -> Path:
    """Write catalog to report files (Markdown + JSON).

    Args:
        catalog: Catalog object from discover.
        profile: Optional L2Profile object from profile_source.
        output_dir: Output directory.

    Returns:
        Path to report.md.
    """
    # Create output directory
    output_dir = Path(output_dir)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = output_dir / f"report-{run_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Write catalog.json
    catalog_path = report_dir / "catalog.json"
    with open(catalog_path, "w") as f:
        json.dump(catalog.to_dict(), f, indent=2, cls=DateTimeEncoder)

    # Write profile.json if available
    if profile:
        profile_path = report_dir / "profile.json"
        with open(profile_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2, cls=DateTimeEncoder)

    # Write report.md
    report_path = report_dir / "report.md"
    report_md = _generate_report_markdown(catalog, profile)
    with open(report_path, "w") as f:
        f.write(report_md)

    # Write masked samples if profile available
    if profile:
        samples_dir = report_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        _write_masked_samples(profile, samples_dir)

    return report_path


def _generate_report_markdown(catalog: Catalog, profile: Optional[L2Profile] = None) -> str:
    """Generate Markdown report from catalog and optional profile.

    Args:
        catalog: Catalog object.
        profile: Optional L2Profile object.

    Returns:
        Markdown string.
    """
    lines = []

    # Header
    lines.append("# Lakeforge Inspection Report")
    lines.append("")
    lines.append(f"**Source:** `{catalog.source}`")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if profile:
        lines.append("**Profile:** Included (statistics + PII detection)")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Tables:** {len(catalog.tables)}")
    total_columns = sum(len(table.columns) for table in catalog.tables.values())
    lines.append(f"- **Columns:** {total_columns}")
    total_rows = sum(table.row_count for table in catalog.tables.values())
    lines.append(f"- **Total Rows:** {total_rows:,}")

    if profile:
        total_pii_columns = sum(
            len(table_profile.pii_columns)
            for table_profile in profile.tables.values()
        )
        lines.append(f"- **PII Columns Detected:** {total_pii_columns}")

    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    for table_name in catalog.tables.keys():
        lines.append(f"- [{table_name}](#{table_name})")
    lines.append("")

    # Table Details
    lines.append("## Table Details")
    lines.append("")

    for table_name, table in catalog.tables.items():
        lines.append(f"### {table_name}")
        lines.append("")
        lines.append(f"**Rows:** {table.row_count:,}")

        if profile and table_name in profile.tables:
            table_profile = profile.tables[table_name]
            lines.append(f"**Sampled:** {table_profile.sample_count} rows")
            if table_profile.pii_columns:
                pii_cols = ", ".join(
                    f"{col} ({pii_type})" for col, pii_type in table_profile.pii_columns.items()
                )
                lines.append(f"**PII Columns:** {pii_cols}")

        lines.append("")
        lines.append("| Column | Type | Nullable |")
        lines.append("|--------|------|----------|")

        for col_name, col in table.columns.items():
            nullable = "YES" if col.nullable else "NO"
            lines.append(f"| {col_name} | {col.type} | {nullable} |")

            # Add stats if available
            if profile and table_name in profile.tables:
                table_profile = profile.tables[table_name]
                if col_name in table_profile.columns:
                    col_profile = table_profile.columns[col_name]
                    stats = col_profile.stats

                    stats_text = []
                    if stats.get("null_rate"):
                        stats_text.append(f"Nulls: {stats['null_rate']:.1%}")
                    if stats.get("unique_count"):
                        stats_text.append(f"Unique: {stats['unique_count']}")
                    if stats.get("min_value"):
                        stats_text.append(f"Min: {stats['min_value']}")
                    if stats.get("max_value"):
                        stats_text.append(f"Max: {stats['max_value']}")

                    if stats_text:
                        lines.append(f"| | *(Stats: {' | '.join(stats_text)})* | |")

        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by [Lakeforge](https://github.com/yourusername/lakeforge)*")

    return "\n".join(lines)


def _write_masked_samples(profile: L2Profile, samples_dir: Path) -> None:
    """Write masked sample rows to files.

    Args:
        profile: L2Profile object.
        samples_dir: Directory to write samples to.
    """
    from lakeforge.pii import PIIMasker

    masker = PIIMasker()

    for table_name, table_profile in profile.tables.items():
        # Reconstruct rows from column sample values
        sample_rows = []

        # Get max number of samples
        if table_profile.columns:
            first_col = next(iter(table_profile.columns.values()))
            max_samples = len(first_col.sample_values)

            for i in range(max_samples):
                row = {}
                for col_name, col_profile in table_profile.columns.items():
                    if i < len(col_profile.sample_values):
                        row[col_name] = col_profile.sample_values[i]
                if row:
                    sample_rows.append(row)

        # Mask PII columns
        masked_rows = []
        for row in sample_rows:
            masked_row = masker.mask_row(row, table_profile.pii_columns)
            masked_rows.append(masked_row)

        # Write to JSON
        samples_file = samples_dir / f"{table_name}.json"
        with open(samples_file, "w") as f:
            json.dump(masked_rows, f, indent=2, cls=DateTimeEncoder)

