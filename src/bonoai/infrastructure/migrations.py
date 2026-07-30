"""Schema migrations for canonical CSV."""

import csv
import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from bonoai.domain.data import DataContractError
from bonoai.infrastructure.source_allowlist import validate_source


def _classify_source_v1_to_v2(source_name: str, source_url: str) -> str:
    """Classify source_type for v1 → v2 migration.

    Validates source via allowlist before classification.
    Returns "official" only for SELAE with allowlist-approved hostname.
    Returns "auxiliary" for known auxiliary sources.
    Raises DataContractError for unknown sources or allowlist violations.
    """
    source_name_lower = source_name.strip().lower()

    if source_name_lower == "selae":
        try:
            validate_source("official", "selae", source_url)
        except ValueError as e:
            raise DataContractError(
                f"source_type fail-closed: SELAE validation failed: {e}"
            ) from e
        return "official"

    # Known auxiliary sources
    if source_name_lower == "lotoideas":
        try:
            validate_source("auxiliary", "lotoideas", source_url)
        except ValueError as e:
            raise DataContractError(
                f"source_type fail-closed: Lotoideas validation failed: {e}"
            ) from e
        return "auxiliary"

    if source_name_lower == "sorteo-bonoloto":
        try:
            validate_source("auxiliary", "sorteo-bonoloto", source_url)
        except ValueError as e:
            raise DataContractError(
                f"source_type fail-closed: sorteo-bonoloto validation failed: {e}"
            ) from e
        return "auxiliary"

    raise DataContractError(
        f"source_type fail-closed: unknown source {source_name} cannot be classified"
    )


def migrate_v1_to_v2(path: Path) -> None:
    """Migrate v1 CSV to v2 schema.

    Atomically:
    1. Create v1 backup with SHA-256 hash
    2. Detect schema version from header
    3. Transform rows: classify source_type for each row
    4. Write v2 temporary file
    5. Validate v2 schema
    6. Replace original with v2

    Idempotent: re-running produces identical output.
    Deterministic: same input always produces same output.
    Reversible: v1.backup preserved.
    """
    if not path.exists():
        return

    with path.open("rb") as f:
        original_content = f.read()
    original_hash = hashlib.sha256(original_content).hexdigest()

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = tuple(reader.fieldnames or ())
        rows = list(reader)

    # Detect schema version
    if "source_type" in fieldnames and "schema_version" in fieldnames:
        # Already v2 (or already has both columns)
        return

    if "source_type" not in fieldnames:
        # v1 schema, needs migration
        backup_path = path.with_suffix(f".v1.{original_hash[:8]}.backup")
        if not backup_path.exists():
            backup_path.write_bytes(original_content)

        # Transform rows: add source_type, set schema_version to 2
        has_schema_version = "schema_version" in fieldnames
        schema_version_idx = fieldnames.index("schema_version") if has_schema_version else None
        new_rows = []
        try:
            for row in rows:
                source_type = _classify_source_v1_to_v2(row["source_name"], row["source_url"])
                row["source_type"] = source_type
                if schema_version_idx is not None:
                    row["schema_version"] = "2"
                else:
                    row["schema_version"] = "2"
                new_rows.append(row)
        except KeyError as error:
            raise DataContractError(
                f"canonical CSV header is invalid or missing fields: {error}"
            ) from error

        # New fieldnames for v2
        if "source_type" not in fieldnames:
            fieldnames = (*fieldnames, "source_type")
        if "schema_version" not in fieldnames:
            fieldnames = (*fieldnames, "schema_version")

        # Write v2 to temporary file
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(new_rows)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()


def get_migration_info(path: Path) -> dict[str, str | None]:
    """Get migration status: schema version and backup info."""
    if not path.exists():
        return {"schema_version": None, "backup": None}

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = tuple(reader.fieldnames or ())

    if "schema_version" not in fieldnames:
        backup_files = list(path.parent.glob(f"{path.name}.v1.*.backup"))
        return {
            "schema_version": "1",
            "backup": str(backup_files[0]) if backup_files else None,
        }

    first_row = next(csv.DictReader(path.open("r", encoding="utf-8", newline="")), None)
    schema_version = first_row.get("schema_version", "unknown") if first_row else "unknown"

    return {"schema_version": schema_version, "backup": None}
