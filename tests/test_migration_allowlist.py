"""Tests for source allowlist validation in migrations."""

from unittest import TestCase

from bonoai.infrastructure.source_allowlist import validate_source


class MigrationAllowlistTests(TestCase):
    """Test cases for hostname and name matching in allowlist."""

    def test_allowlist_official_selae_valid_hostname(self) -> None:
        """SELAE official with exact hostname is allowed."""
        validate_source(
            "official",
            "selae",
            "https://www.selae.es/lotobonoloto"
        )

    def test_allowlist_official_selae_alternative_hostname(self) -> None:
        """SELAE official with alternative registered hostname is allowed."""
        validate_source(
            "official",
            "selae",
            "https://selae.es/data"
        )

    def test_allowlist_official_selae_loteriasyapuestas(self) -> None:
        """SELAE official via loteriasyapuestas.es is allowed."""
        validate_source(
            "official",
            "selae",
            "https://loteriasyapuestas.es/bonoloto"
        )

    def test_allowlist_auxiliary_lotoideas_valid(self) -> None:
        """Lotoideas auxiliary with exact hostname is allowed."""
        validate_source(
            "auxiliary",
            "lotoideas",
            "https://lotoideas.com/historical"
        )

    def test_allowlist_auxiliary_lotoideas_www(self) -> None:
        """Lotoideas auxiliary with www prefix is allowed."""
        validate_source(
            "auxiliary",
            "lotoideas",
            "https://www.lotoideas.com/data"
        )

    def test_allowlist_reject_wrong_hostname_for_name(self) -> None:
        """Rejects name/hostname mismatch: lotoideas name with selae hostname."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "auxiliary",
                "lotoideas",
                "https://www.selae.es/hijacked"
            )

    def test_allowlist_reject_similar_hostname_evil(self) -> None:
        """Rejects similar but malicious hostname: loteriasyapuestas.es.evil.example."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "official",
                "selae",
                "https://loteriasyapuestas.es.evil.example/data"
            )

    def test_allowlist_reject_evil_lotoideas_com(self) -> None:
        """Rejects malicious lookalike: evil-lotoideas.com."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "auxiliary",
                "lotoideas",
                "https://evil-lotoideas.com/data"
            )

    def test_allowlist_reject_hostname_correct_name_wrong(self) -> None:
        """Rejects correct hostname but wrong name: selae hostname with lotoideas name."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "auxiliary",
                "lotoideas",
                "https://www.selae.es/historical"
            )

    def test_allowlist_reject_name_correct_hostname_wrong(self) -> None:
        """Rejects correct name but wrong hostname: selae name with lotoideas hostname."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "official",
                "selae",
                "https://lotoideas.com/data"
            )

    def test_allowlist_reject_unknown_source_type(self) -> None:
        """Rejects unknown source type."""
        with self.assertRaisesRegex(ValueError, "unknown source"):
            validate_source(
                "unknown_type",
                "selae",
                "https://www.selae.es/data"
            )

    def test_allowlist_reject_unknown_source_name(self) -> None:
        """Rejects unknown source name."""
        with self.assertRaisesRegex(ValueError, "unknown source"):
            validate_source(
                "official",
                "unknown_name",
                "https://example.test/data"
            )

    def test_allowlist_manual_not_enabled(self) -> None:
        """Manual source has no authorized hostnames; requires explicit contract."""
        with self.assertRaisesRegex(ValueError, "no authorized hostnames"):
            validate_source(
                "manual",
                "manual",
                "https://anywhere.example/data"
            )

    def test_allowlist_reject_invalid_url(self) -> None:
        """Rejects malformed URL (no scheme)."""
        with self.assertRaisesRegex(ValueError, "invalid scheme"):
            validate_source(
                "official",
                "selae",
                "not a url at all"
            )

    def test_allowlist_reject_url_without_hostname(self) -> None:
        """Rejects URL with invalid scheme (file://)."""
        with self.assertRaisesRegex(ValueError, "invalid scheme"):
            validate_source(
                "official",
                "selae",
                "file:///local/path"
            )

    def test_allowlist_subdomain_not_in_list_rejected(self) -> None:
        """Rejects subdomain not explicitly in allowlist."""
        with self.assertRaisesRegex(ValueError, "hostname.*not in allowlist"):
            validate_source(
                "official",
                "selae",
                "https://subdomain.www.selae.es/data"
            )
