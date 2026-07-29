"""Official SELAE Bonoloto RSS adapter."""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Final, cast
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from bonoai.domain.data import (
    CanonicalDrawRecord,
    DataContractError,
    SourceConflictError,
    SourceProvenance,
)
from bonoai.domain.models import Draw
from bonoai.ports.data import DrawBatch, FetchedDocument

SELAE_BONOLOTO_RSS_URL: Final = (
    "https://www.loteriasyapuestas.es/es/bonoloto/resultados/.formatoRSS"
)
SELAE_SOURCE_NAME: Final = "selae"

SPANISH_MONTHS: Final = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

TITLE_DATE_PATTERN: Final = re.compile(
    r"\bdel?\s+(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})\b",
    re.IGNORECASE,
)
NUMBERS_PATTERN: Final = re.compile(
    r"<(?:b|strong)>\s*((?:\d{1,2}\s*-\s*){5}\d{1,2})\s*</(?:b|strong)>",
    re.IGNORECASE,
)
COMPLEMENTARY_PATTERN: Final = re.compile(
    r"Complementario:\s*<(?:b|strong)>\s*C\((\d{1,2})\)\s*</(?:b|strong)>",
    re.IGNORECASE,
)
REINTEGRO_PATTERN: Final = re.compile(
    r"Reintegro:\s*<(?:b|strong)>\s*R\((\d)\)\s*</(?:b|strong)>",
    re.IGNORECASE,
)

Transport = Callable[[str, float], bytes]
Clock = Callable[[], datetime]


def _default_transport(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/rss+xml, application/xml, text/xml",
            "User-Agent": "BonoAI/0.1 (+https://github.com/comfortfood34-glitch/bonoai)",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return cast(bytes, response.read())


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_title_date(title: str) -> date:
    match = TITLE_DATE_PATTERN.search(title)
    if match is None:
        raise DataContractError(f"could not parse draw date from SELAE title: {title!r}")
    day_text, month_text, year_text = match.groups()
    month = SPANISH_MONTHS.get(month_text.casefold())
    if month is None:
        raise DataContractError(f"unknown Spanish month in SELAE title: {month_text!r}")
    try:
        return date(int(year_text), month, int(day_text))
    except ValueError as error:
        raise DataContractError(f"invalid draw date in SELAE title: {title!r}") from error


def _required_text(item: ElementTree.Element, tag: str, index: int) -> str:
    value = item.findtext(tag)
    if value is None or not value.strip():
        raise DataContractError(f"SELAE RSS item {index} is missing {tag}")
    return value.strip()


def _parse_description(description: str, index: int) -> tuple[tuple[int, ...], int, int]:
    decoded = html.unescape(description)
    numbers_match = NUMBERS_PATTERN.search(decoded)
    complementary_match = COMPLEMENTARY_PATTERN.search(decoded)
    reintegro_match = REINTEGRO_PATTERN.search(decoded)
    if numbers_match is None or complementary_match is None or reintegro_match is None:
        raise DataContractError(f"SELAE RSS item {index} has an unrecognized result layout")

    numbers = tuple(int(value.strip()) for value in numbers_match.group(1).split("-"))
    return numbers, int(complementary_match.group(1)), int(reintegro_match.group(1))


def parse_selae_rss(
    payload: bytes,
    *,
    retrieved_at_utc: datetime,
    source_url: str = SELAE_BONOLOTO_RSS_URL,
) -> tuple[CanonicalDrawRecord, ...]:
    """Parse every item or fail the complete document without partial output."""
    source_sha256 = hashlib.sha256(payload).hexdigest()
    provenance = SourceProvenance(
        source_name=SELAE_SOURCE_NAME,
        source_url=source_url,
        retrieved_at_utc=retrieved_at_utc,
        source_sha256=source_sha256,
    )
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as error:
        raise DataContractError("SELAE RSS is not valid XML") from error

    items = root.findall("./channel/item")
    if not items:
        raise DataContractError("SELAE RSS contains no draw items")

    records: list[CanonicalDrawRecord] = []
    by_contest: dict[str, Draw] = {}
    for index, item in enumerate(items, start=1):
        title = _required_text(item, "title", index)
        description = _required_text(item, "description", index)
        held_on = _parse_title_date(title)
        numbers, complementary, reintegro = _parse_description(description, index)
        draw = Draw(
            contest_id=f"bonoloto:{held_on.isoformat()}",
            held_on=held_on,
            numbers=numbers,
            complementary=complementary,
            reintegro=reintegro,
        )

        previous = by_contest.get(draw.contest_id)
        if previous is not None:
            if previous != draw:
                raise SourceConflictError(
                    f"SELAE RSS contains conflicting values for {draw.contest_id}"
                )
            continue
        by_contest[draw.contest_id] = draw
        records.append(CanonicalDrawRecord(draw=draw, provenance=provenance))

    return tuple(sorted(records, key=lambda record: (record.draw.held_on, record.draw.contest_id)))


class SelaeRssSource:
    """Fetch and parse the official SELAE Bonoloto results feed."""

    def __init__(
        self,
        *,
        url: str = SELAE_BONOLOTO_RSS_URL,
        timeout_seconds: float = 20.0,
        transport: Transport = _default_transport,
        clock: Clock = _utc_now,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._url = url
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._clock = clock

    def fetch(self) -> DrawBatch:
        retrieved_at_utc = self._clock()
        payload = self._transport(self._url, self._timeout_seconds)
        document = FetchedDocument(
            source_name=SELAE_SOURCE_NAME,
            source_url=self._url,
            retrieved_at_utc=retrieved_at_utc,
            payload=payload,
            media_type="application/rss+xml",
        )
        records = parse_selae_rss(
            payload,
            retrieved_at_utc=retrieved_at_utc,
            source_url=self._url,
        )
        return DrawBatch(document=document, records=records)
