"""Plain-text reports for Smart File Organizer."""
from datetime import datetime
from pathlib import Path

def write_report(result: dict, destination: str | Path) -> Path:
    """Write a readable TXT report inside the selected destination."""
    folder = Path(destination).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    report_path = folder / f"smart_file_organizer_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
    lines = ["Smart File Organizer - Report", f"Created: {datetime.now():%Y-%m-%d %H:%M:%S}", ""]
    lines.append("Mode: PREVIEW (no files were moved)" if result.get("dry_run") else "Mode: ORGANIZATION")
    planned = result.get("plan", [])
    lines.extend([f"Planned files: {len(planned)}", ""])
    if planned:
        lines.append("Preview:")
        lines.extend(f"  [{row['category']}] {row['source']} -> {row['destination']}" for row in planned)
    moved = result.get("moved", [])
    if moved:
        lines.extend(["", "Moved:"])
        lines.extend(f"  [{row['category']}] {row['source']} -> {row['destination']}" for row in moved)
    errors = result.get("errors", [])
    if errors:
        lines.extend(["", "Issues:"])
        lines.extend(f"  {error}" for error in errors)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
