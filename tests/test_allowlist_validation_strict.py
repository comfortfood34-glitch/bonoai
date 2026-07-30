"""Strict tests for source allowlist validation edge cases."""

from unittest import TestCase

from bonoai.infrastructure.source_allowlist import validate_source


class AllowlistStrictValidationTests(TestCase):
    """Test strict validation for port, credentials, and hostname policies."""

    def test_reject_url_with_username(self) -> None:
        """Reject URLs containing username."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://user@www.selae.es",
            )
        self.assertIn("username", str(ctx.exception))

    def test_reject_url_with_password_only(self) -> None:
        """Reject URLs containing password (even without username)."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://:mypassword@www.selae.es",
            )
        self.assertIn("password", str(ctx.exception))

    def test_reject_url_with_credentials(self) -> None:
        """Reject URLs containing credentials (username or password)."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://user:pass@www.selae.es",
            )
        error_msg = str(ctx.exception)
        self.assertTrue(
            "username" in error_msg or "password" in error_msg
        )

    def test_reject_non_standard_port_8080(self) -> None:
        """Reject non-standard port 8080."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://www.selae.es:8080",
            )
        self.assertIn("invalid port", str(ctx.exception))

    def test_accept_standard_https_port_443(self) -> None:
        """Accept standard HTTPS port 443."""
        result = validate_source(
            "official",
            "selae",
            "https://www.selae.es:443",
        )
        self.assertTrue(result)

    def test_reject_selae_http_with_port_80(self) -> None:
        """Reject SELAE with HTTP scheme even with standard port 80."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "http://www.selae.es:80",
            )
        error_msg = str(ctx.exception).lower()
        self.assertTrue("selae" in error_msg or "https" in error_msg)

    def test_accept_no_explicit_port(self) -> None:
        """Accept URL with no explicit port."""
        result = validate_source(
            "official",
            "selae",
            "https://www.selae.es",
        )
        self.assertTrue(result)

    def test_reject_url_without_hostname(self) -> None:
        """Reject URL with no hostname."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://",
            )
        self.assertIn("hostname", str(ctx.exception))

    def test_hostname_case_insensitive_lowercase_match(self) -> None:
        """Hostname matching is case-insensitive."""
        result = validate_source(
            "official",
            "selae",
            "https://WWW.SELAE.ES",
        )
        self.assertTrue(result)

    def test_reject_invalid_scheme(self) -> None:
        """Reject URLs with invalid scheme."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "ftp://www.selae.es",
            )
        self.assertIn("invalid scheme", str(ctx.exception))

    def test_reject_https_with_port_80(self) -> None:
        """Reject HTTPS URL with HTTP port 80."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "https://www.selae.es:80",
            )
        self.assertIn("invalid port", str(ctx.exception))

    def test_reject_selae_http_with_port_443(self) -> None:
        """Reject SELAE with HTTP URL with HTTPS port 443."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "http://www.selae.es:443",
            )
        error_msg = str(ctx.exception).lower()
        self.assertTrue("selae" in error_msg or "https" in error_msg or "invalid" in error_msg)

    def test_reject_selae_http_url(self) -> None:
        """Reject SELAE HTTP URL regardless of port."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "http://www.selae.es:80",
            )
        error_msg = str(ctx.exception).lower()
        self.assertTrue("selae" in error_msg or "https" in error_msg)

    def test_reject_url_no_scheme(self) -> None:
        """Reject URL without scheme (invalid scheme is '')."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "//www.selae.es",
            )
        self.assertIn("invalid scheme", str(ctx.exception))

    def test_reject_selae_with_http(self) -> None:
        """Reject SELAE with HTTP scheme - requires HTTPS."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "official",
                "selae",
                "http://www.selae.es",
            )
        self.assertIn("selae", str(ctx.exception).lower())
        self.assertIn("https", str(ctx.exception).lower())

    def test_accept_selae_with_https(self) -> None:
        """Accept SELAE with HTTPS scheme."""
        result = validate_source(
            "official",
            "selae",
            "https://www.selae.es",
        )
        self.assertTrue(result)

    def test_reject_lotoideas_with_http(self) -> None:
        """Reject Lotoideas with HTTP scheme - requires HTTPS."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "auxiliary",
                "lotoideas",
                "http://www.lotoideas.com",
            )
        self.assertIn("lotoideas", str(ctx.exception).lower())
        self.assertIn("https", str(ctx.exception).lower())

    def test_accept_lotoideas_with_https(self) -> None:
        """Accept Lotoideas with HTTPS scheme."""
        result = validate_source(
            "auxiliary",
            "lotoideas",
            "https://www.lotoideas.com",
        )
        self.assertTrue(result)

    def test_manual_source_with_empty_hostnames(self) -> None:
        """Manual source with empty hostnames raises error."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "manual",
                "manual",
                "https://example.com",
            )
        self.assertIn("authorized hostnames", str(ctx.exception).lower())

    def test_unknown_source_type_name(self) -> None:
        """Unknown source type/name combination raises error."""
        with self.assertRaises(ValueError) as ctx:
            validate_source(
                "unknown_type",
                "unknown_name",
                "https://example.com",
            )
        self.assertIn("unknown source", str(ctx.exception).lower())
