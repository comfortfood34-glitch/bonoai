from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from bonoai.application.ingestion import ingest_draws
from bonoai.infrastructure.csv_repository import CsvDrawRepository
from bonoai.infrastructure.raw_archive import FilesystemRawArchive
from bonoai.infrastructure.selae_rss import SelaeRssSource

FIXTURE = Path(__file__).parent / "fixtures" / "selae_bonoloto.xml"
RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


class IngestionTests(TestCase):
    def test_complete_incremental_pipeline(self) -> None:
        source = SelaeRssSource(
            transport=lambda _url, _timeout: FIXTURE.read_bytes(),
            clock=lambda: RETRIEVED_AT,
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repository = CsvDrawRepository(root / "processed" / "draws.csv")
            archive = FilesystemRawArchive(root / "raw")

            first = ingest_draws(source=source, repository=repository, raw_archive=archive)
            second = ingest_draws(source=source, repository=repository, raw_archive=archive)

            self.assertEqual(first.fetched, 2)
            self.assertEqual(first.inserted, 2)
            self.assertEqual(first.total, 2)
            latest = first.latest_draw
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest.isoformat(), "2026-07-28")
            self.assertTrue(first.raw_archive_path.exists())
            self.assertEqual(second.inserted, 0)
            self.assertEqual(second.duplicates, 2)
            self.assertEqual(second.total, 2)
            self.assertEqual(second.as_dict()["latest_draw"], "2026-07-28")
