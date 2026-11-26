"""Safe, top-level file organization for Smart File Organizer."""
from __future__ import annotations
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif", ".svg", ".tif", ".tiff"},
    "Documents": {".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".csv"},
    "PDFs": {".pdf"},
    "Videos": {".mp4", ".m4v", ".mkv", ".mov", ".avi", ".webm", ".3gp", ".mpeg", ".mpg"},
    "Audio": {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac", ".opus", ".wma"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"},
}
UNDO_FILENAME = ".smart_file_organizer_undo.json"

class OrganizerError(Exception):
    """An expected problem that is safe to show to the user."""

def category_for(path: Path) -> str:
    for category, extensions in CATEGORIES.items():
        if path.suffix.lower() in extensions:
            return category
    return "Other files"

def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)

def _validate_folders(source: Path, destination: Path) -> tuple[Path, Path]:
    source, destination = _resolved(source), _resolved(destination)
    if not source.is_dir():
        raise OrganizerError(f"Source folder does not exist or is not a folder: {source}")
    if source == destination or source in destination.parents or destination in source.parents:
        raise OrganizerError("Source and destination must be separate, non-nested folders.")
    return source, destination

def _unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    original = Path(filename)
    number = 1
    while True:
        candidate = directory / f"{original.stem} ({number}){original.suffix}"
        if not candidate.exists():
            return candidate
        number += 1

def plan_organization(source: str | Path, destination: str | Path) -> list[dict[str, str]]:
    """List top-level regular files and proposed destinations; move nothing."""
    source_path, destination_path = _validate_folders(Path(source), Path(destination))
    plan = []
    try:
        entries = sorted(source_path.iterdir(), key=lambda item: item.name.casefold())
        for item in entries:
            if item.is_symlink() or not item.is_file():
                continue
            category = category_for(item)
            target_dir = destination_path / category
            used = {row["destination"] for row in plan}
            candidate = _unique_path(target_dir, item.name)
            while str(candidate) in used:
                candidate = _unique_path(target_dir, candidate.name)
            plan.append({"source": str(item), "destination": str(candidate), "category": category})
    except PermissionError as exc:
        raise OrganizerError(f"Permission denied while reading the source folder: {exc}") from exc
    return plan

def _copy_without_overwrite(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with source.open("rb") as src, os.fdopen(fd, "wb") as dst:
            shutil.copyfileobj(src, dst)
        shutil.copystat(source, destination, follow_symlinks=False)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            destination.unlink()
        except OSError:
            pass
        raise

def _move_safely(source: Path, desired: Path) -> Path:
    target = desired
    while True:
        try:
            _copy_without_overwrite(source, target)
            break
        except FileExistsError:
            target = _unique_path(target.parent, target.name)
    try:
        source.unlink()
    except OSError:
        raise OrganizerError(f"Copied to {target}, but could not remove original {source}. Both copies were kept.")
    return target

def _write_manifest(destination: Path, manifest: dict) -> None:
    path = destination / UNDO_FILENAME
    temporary = destination / (UNDO_FILENAME + ".tmp")
    try:
        temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise OrganizerError(f"Could not save undo information in destination folder: {exc}") from exc

def organize(source: str | Path, destination: str | Path, dry_run: bool = True) -> dict:
    """Preview or perform organization. Preview is enabled by default."""
    source_path, destination_path = _validate_folders(Path(source), Path(destination))
    plan = plan_organization(source_path, destination_path)
    result = {"dry_run": dry_run, "moved": [], "errors": [], "plan": plan}
    if dry_run:
        return result
    try:
        destination_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OrganizerError(f"Could not create destination folder: {exc}") from exc
    moved = []
    for row in plan:
        original, desired = Path(row["source"]), Path(row["destination"])
        try:
            if original.is_symlink() or not original.is_file():
                continue
            actual = _move_safely(original, desired)
            moved.append({"source": str(original), "destination": str(actual), "category": row["category"]})
        except (OSError, OrganizerError) as exc:
            result["errors"].append(f"{original.name}: {exc}")
    result["moved"] = moved
    if moved:
        _write_manifest(destination_path, {"created": datetime.now().isoformat(timespec="seconds"), "source": str(source_path), "destination": str(destination_path), "moves": moved})
    return result

def undo_last(destination: str | Path) -> dict:
    """Restore the latest operation from the manifest stored in destination."""
    destination_path = _resolved(Path(destination))
    manifest_path = destination_path / UNDO_FILENAME
    if not destination_path.is_dir():
        raise OrganizerError("Destination folder does not exist.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OrganizerError("No saved organization operation was found to undo.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise OrganizerError(f"Could not read undo information: {exc}") from exc
    source_root = _resolved(Path(manifest["source"]))
    destination_root = _resolved(Path(manifest["destination"]))
    if destination_path != destination_root:
        raise OrganizerError("Selected folder does not match the operation's destination.")
    remaining, restored, errors = [], [], []
    for row in reversed(manifest.get("moves", [])):
        current, original = _resolved(Path(row["destination"])), _resolved(Path(row["source"]))
        if destination_root not in current.parents or source_root not in original.parents:
            errors.append(f"Skipped unsafe path: {current}")
            remaining.insert(0, row)
            continue
        if not current.is_file():
            errors.append(f"Moved file is missing: {current}")
            remaining.insert(0, row)
            continue
        try:
            actual = _move_safely(current, original)
            restored.append({"from": str(current), "to": str(actual)})
        except (OSError, OrganizerError) as exc:
            errors.append(f"{current.name}: {exc}")
            remaining.insert(0, row)
    if remaining:
        manifest["moves"] = remaining
        _write_manifest(destination_root, manifest)
    else:
        try:
            manifest_path.unlink()
        except OSError as exc:
            errors.append(f"Could not remove completed undo information: {exc}")
    return {"restored": restored, "errors": errors}
