"""Source allowlist validation for migrations and ingestion."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWLIST: dict[tuple[str, str], dict[str, list[str]]] = {
    ("official", "selae"): {
        "hostnames": ["www.selae.es", "selae.es", "loteriasyapuestas.es"],
    },
    ("auxiliary", "lotoideas"): {
        "hostnames": ["lotoideas.com", "www.lotoideas.com"],
    },
    ("auxiliary", "sorteo-bonoloto"): {
        "hostnames": [],
    },
    ("manual", "manual"): {
        "hostnames": [],
    },
}


def validate_source(source_type: str, source_name: str, source_url: str) -> bool:
    """Validate source by allowlist: exact type+name, scheme, port, and hostname.

    Scheme policy:
      - https: permits port None or 443
      - http: permits port None or 80 (only if allowed per source)
      - other schemes: rejected

    Rejects URLs with username or password.
    Requires exact lowercase hostname match from allowlist.

    Args:
        source_type: "official", "auxiliary", or "manual"
        source_name: identifier like "selae" or "lotoideas"
        source_url: absolute URL with scheme

    Returns:
        True if source is in allowlist with valid scheme, port, and hostname.

    Raises:
        ValueError: if source_type/name unknown, URL invalid, credentials present,
                   invalid scheme, invalid port for scheme, hostname absent,
                   or hostname not in allowlist.
    """
    key = (source_type, source_name)
    if key not in ALLOWLIST:
        raise ValueError(
            f"unknown source: type={source_type}, name={source_name}"
        )

    allowed_hostnames = ALLOWLIST[key]["hostnames"]

    try:
        parsed = urlparse(source_url)
    except Exception as error:
        raise ValueError(f"invalid URL: {source_url}") from error

    if parsed.username is not None:
        raise ValueError(f"URL contains username: {source_url}")

    if parsed.password is not None:
        raise ValueError(f"URL contains password: {source_url}")

    scheme = parsed.scheme.lower() if parsed.scheme else None
    if scheme not in ("http", "https"):
        raise ValueError(
            f"invalid scheme {scheme}: only http or https permitted"
        )

    https_only_sources = [("official", "selae"), ("auxiliary", "lotoideas")]
    if (source_type, source_name) in https_only_sources and scheme != "https":
        raise ValueError(
            f"{source_name} requires https scheme, got {scheme}"
        )

    if scheme == "https" and parsed.port is not None and parsed.port != 443:
        raise ValueError(
            f"invalid port {parsed.port} for https: only 443 permitted"
        )
    if scheme == "http" and parsed.port is not None and parsed.port != 80:
        raise ValueError(
            f"invalid port {parsed.port} for http: only 80 permitted"
        )

    hostname = parsed.hostname.lower() if parsed.hostname else None

    if not hostname:
        raise ValueError(f"no hostname in URL: {source_url}")

    if not allowed_hostnames:
        raise ValueError(
            f"no authorized hostnames for {key}. "
            f"source {source_name} not enabled in allowlist"
        )

    if hostname not in allowed_hostnames:
        raise ValueError(
            f"hostname {hostname} not in allowlist for {key}. "
            f"allowed: {allowed_hostnames}"
        )

    return True
