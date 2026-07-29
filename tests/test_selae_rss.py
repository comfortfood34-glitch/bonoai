from datetime import UTC, date, datetime
from pathlib import Path
from unittest import TestCase

from bonoai.domain.data import DataContractError, SourceConflictError
from bonoai.infrastructure.selae_rss import SELAE_BONOLOTO_RSS_URL, SelaeRssSource, parse_selae_rss

FIXTURE = Path(__file__).parent / "fixtures" / "selae_bonoloto.xml"
RETRIEVED_AT = datetime(2026, 7, 29, 10, 0, tzinfo=UTC)


class SelaeRssParserTests(TestCase):
    def test_parses_official_layout_and_sorts_chronologically(self) -> None:
        records = parse_selae_rss(FIXTURE.read_bytes(), retrieved_at_utc=RETRIEVED_AT)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].draw.contest_id, "bonoloto:2026-07-27")
        self.assertEqual(records[0].draw.numbers, (15, 20, 33, 35, 42, 48))
        self.assertEqual(records[0].draw.complementary, 4)
        self.assertEqual(records[0].draw.reintegro, 6)
        self.assertEqual(records[-1].draw.held_on, date(2026, 7, 28))
        self.assertEqual(records[-1].provenance.source_name, "selae")
        self.assertEqual(len(records[-1].provenance.source_sha256), 64)

    def test_rejects_invalid_xml(self) -> None:
        with self.assertRaisesRegex(DataContractError, "valid XML"):
            parse_selae_rss(b"<rss>", retrieved_at_utc=RETRIEVED_AT)

    def test_rejects_feed_without_items(self) -> None:
        with self.assertRaisesRegex(DataContractError, "no draw items"):
            parse_selae_rss(b"<rss><channel /></rss>", retrieved_at_utc=RETRIEVED_AT)

    def test_rejects_missing_required_item_field(self) -> None:
        payload = b"<rss><channel><item><title>title</title></item></channel></rss>"
        with self.assertRaisesRegex(DataContractError, "missing description"):
            parse_selae_rss(payload, retrieved_at_utc=RETRIEVED_AT)

    def test_rejects_unknown_result_layout(self) -> None:
        payload = FIXTURE.read_bytes().replace(b"Complementario:", b"Extra:")
        with self.assertRaisesRegex(DataContractError, "unrecognized result layout"):
            parse_selae_rss(payload, retrieved_at_utc=RETRIEVED_AT)

    def test_rejects_unknown_month(self) -> None:
        payload = FIXTURE.read_bytes().replace(b"julio", b"mesinventado")
        with self.assertRaisesRegex(DataContractError, "unknown Spanish month"):
            parse_selae_rss(payload, retrieved_at_utc=RETRIEVED_AT)

    def test_rejects_conflicting_duplicate_contest(self) -> None:
        payload = FIXTURE.read_bytes()
        second = payload[
            payload.index(b"<item>", payload.index(b"<item>") + 1) : payload.rindex(b"</item>") + 7
        ]
        conflicting = second.replace(b"27 de julio", b"28 de julio")
        payload = payload.replace(b"</channel>", conflicting + b"</channel>")

        with self.assertRaisesRegex(SourceConflictError, "conflicting values"):
            parse_selae_rss(payload, retrieved_at_utc=RETRIEVED_AT)


class SelaeRssSourceTests(TestCase):
    def test_fetches_with_injected_transport_and_clock(self) -> None:
        calls: list[tuple[str, float]] = []

        def transport(url: str, timeout: float) -> bytes:
            calls.append((url, timeout))
            return FIXTURE.read_bytes()

        source = SelaeRssSource(
            timeout_seconds=7.5,
            transport=transport,
            clock=lambda: RETRIEVED_AT,
        )
        batch = source.fetch()

        self.assertEqual(calls, [(SELAE_BONOLOTO_RSS_URL, 7.5)])
        self.assertEqual(batch.document.retrieved_at_utc, RETRIEVED_AT)
        self.assertEqual(len(batch.records), 2)

    def test_rejects_non_positive_timeout(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            SelaeRssSource(timeout_seconds=0)
