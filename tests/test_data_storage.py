import csv
import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.infrastructure.csv_repository import CANONICAL_COLUMNS, CsvDrawRepository
from bonoai.infrastructure.raw_archive import FilesystemRawArchive
from bonoai.ports.data import FetchedDocument

RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


def make_record(
    contest_id: str,
    held_on: date,
    numbers: tuple[int, ...],
) -> CanonicalDrawRecord:
    return CanonicalDrawRecord(
        draw=Draw(
            contest_id=contest_id,
            held_on=held_on,
            numbers=numbers,
            complementary=49 if 49 not in numbers else 48,
            reintegro=3,
        ),
        provenances=(
            SourceProvenance(
                source_name="selae",
                source_url="https://www.selae.es/lotobonoloto",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="b" * 64,
                source_type="official",
                schema_version=2,
            ),
        ),
    )


class CsvDrawRepositoryTests(TestCase):
    def test_appends_sorted_records_and_round_trips(self) -> None:
        with TemporaryDirectory() as directory:
            repository = CsvDrawRepository(Path(directory) / "draws.csv")
            later = make_record("later", date(2026, 7, 28), (1, 17, 35, 36, 44, 49))
            earlier = make_record("earlier", date(2026, 7, 27), (15, 20, 33, 35, 42, 48))

            result = repository.append_validated((later, earlier))

            self.assertEqual(result.inserted, 2)
            self.assertEqual(result.total, 2)
            self.assertEqual(repository.list_all(), (earlier, later))

    def test_identical_duplicate_is_counted_without_rewrite(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)
            record = make_record("same", date(2026, 7, 28), (1, 17, 35, 36, 44, 49))
            repository.append_validated((record,))
            original_bytes = path.read_bytes()

            result = repository.append_validated((record,))

            self.assertEqual(result.duplicates, 1)
            self.assertEqual(result.inserted, 0)
            self.assertEqual(path.read_bytes(), original_bytes)

    def test_conflict_fails_without_mutating_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)
            original = make_record("same", date(2026, 7, 28), (1, 17, 35, 36, 44, 49))
            conflict = make_record("same", date(2026, 7, 28), (2, 17, 35, 36, 44, 49))
            repository.append_validated((original,))
            original_bytes = path.read_bytes()

            with self.assertRaisesRegex(SourceConflictError, "conflicting result"):
                repository.append_validated((conflict,))

            self.assertEqual(path.read_bytes(), original_bytes)

    def test_rejects_wrong_header(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            path.write_text("wrong,header\n1,2\n", encoding="utf-8")

            with self.assertRaisesRegex(DataContractError, "header"):
                CsvDrawRepository(path).list_all()

    def test_rejects_invalid_row(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                writer.writerow({column: "invalid" for column in CANONICAL_COLUMNS})

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_empty_missing_repository(self) -> None:
        with TemporaryDirectory() as directory:
            repository = CsvDrawRepository(Path(directory) / "missing.csv")
            self.assertEqual(repository.list_all(), ())

    def test_rejects_empty_complementary_field_in_csv(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "",
                    "reintegro": "3",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "source_type": "auxiliary",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_rejects_empty_reintegro_field_in_csv(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CANONICAL_COLUMNS)
                writer.writeheader()
                row = {
                    "contest_id": "test:2026-07-28",
                    "held_on": "2026-07-28",
                    "n1": "1",
                    "n2": "17",
                    "n3": "35",
                    "n4": "36",
                    "n5": "44",
                    "n6": "49",
                    "complementary": "14",
                    "reintegro": "",
                    "source_name": "test",
                    "source_url": "https://example.test/feed",
                    "retrieved_at_utc": "2026-07-29T10:00:00+00:00",
                    "source_sha256": "b" * 64,
                    "source_type": "auxiliary",
                    "schema_version": "2",
                }
                writer.writerow(row)

            with self.assertRaisesRegex(DataContractError, "line 2"):
                CsvDrawRepository(path).list_all()

    def test_multiple_provenances_same_contest(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            official = make_record("same", date(2026, 7, 28), (1, 17, 35, 36, 44, 49))
            auxiliary = CanonicalDrawRecord(
                draw=official.draw,
                provenances=(
                    official.provenances[0],
                    SourceProvenance(
                        source_name="lotoideas",
                        source_url="https://example.test/historical",
                        retrieved_at_utc=RETRIEVED_AT,
                        source_sha256="c" * 64,
                        source_type="auxiliary",
                        schema_version=2,
                    ),
                ),
            )

            repository.append_validated((auxiliary,))
            records = repository.list_all()

            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0].provenances), 2)
            self.assertEqual(records[0].provenances[0].source_type, "official")
            self.assertEqual(records[0].provenances[1].source_type, "auxiliary")

    def test_round_trip_multiple_provenances(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "draws.csv"
            repository = CsvDrawRepository(path)

            official = make_record("test", date(2026, 7, 28), (1, 2, 3, 4, 5, 6))
            auxiliary_provenance = SourceProvenance(
                source_name="lotoideas",
                source_url="https://example.test/historical",
                retrieved_at_utc=RETRIEVED_AT,
                source_sha256="d" * 64,
                source_type="auxiliary",
                schema_version=2,
            )
            with_multiple = CanonicalDrawRecord(
                draw=official.draw,
                provenances=(*official.provenances, auxiliary_provenance),
            )

            repository.append_validated((with_multiple,))
            loaded = repository.list_all()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(len(loaded[0].provenances), 2)
            self.assertEqual(loaded[0].draw, official.draw)
            self.assertEqual(loaded[0].provenances[0].source_name, "selae")
            self.assertEqual(loaded[0].provenances[1].source_name, "lotoideas")


class RawArchiveTests(TestCase):
    def test_stores_exact_payload_and_manifest_idempotently(self) -> None:
        with TemporaryDirectory() as directory:
            document = FetchedDocument(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=RETRIEVED_AT,
                payload=b"<rss />",
                media_type="application/rss+xml",
            )
            archive = FilesystemRawArchive(Path(directory))

            first_path = archive.store(document)
            second_path = archive.store(document)

            self.assertEqual(first_path, second_path)
            self.assertEqual(first_path.read_bytes(), b"<rss />")
            manifest = json.loads(first_path.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["size_bytes"], 7)
            self.assertEqual(len(manifest["source_sha256"]), 64)

    def test_rejects_non_utc_retrieval_time(self) -> None:
        with TemporaryDirectory() as directory:
            document = FetchedDocument(
                source_name="selae",
                source_url="https://example.test/feed",
                retrieved_at_utc=datetime(
                    2026,
                    7,
                    29,
                    12,
                    0,
                    tzinfo=timezone(timedelta(hours=2)),
                ),
                payload=b"<rss />",
                media_type="application/rss+xml",
            )
            with self.assertRaisesRegex(DataContractError, "must use UTC"):
                FilesystemRawArchive(Path(directory)).store(document)
