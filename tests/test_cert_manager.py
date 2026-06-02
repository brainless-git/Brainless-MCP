"""Tests for the Let's Encrypt / Cloudflare cert manager."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from brainless_mcp.config.settings import Settings
from brainless_mcp.core.cert_manager import (
    _CloudflareClient,
    ensure_certificate,
    is_configured,
    needs_renewal,
)

# ── is_configured ─────────────────────────────────────────────────────────────

def test_is_configured_all_set():
    s = Settings(
        brainless_mcp_acme_email="user@example.com",
        brainless_mcp_acme_domain="mcp.example.com",
        cloudflare_api_token="cf_token",
    )
    assert is_configured(s) is True


def test_is_configured_missing_email():
    s = Settings(brainless_mcp_acme_domain="mcp.example.com", cloudflare_api_token="tok")
    assert is_configured(s) is False


def test_is_configured_missing_domain():
    s = Settings(brainless_mcp_acme_email="u@e.com", cloudflare_api_token="tok")
    assert is_configured(s) is False


def test_is_configured_missing_token():
    s = Settings(brainless_mcp_acme_email="u@e.com", brainless_mcp_acme_domain="mcp.example.com")
    assert is_configured(s) is False


def test_is_configured_all_empty():
    assert is_configured(Settings()) is False


# ── needs_renewal ─────────────────────────────────────────────────────────────

def test_needs_renewal_missing_file():
    assert needs_renewal("/nonexistent/cert.pem") is True


def test_needs_renewal_valid_cert(tmp_path):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC))
        .not_valid_after(datetime.now(UTC) + timedelta(days=90))
        .sign(key, hashes.SHA256())
    )
    certfile = tmp_path / "cert.pem"
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    assert needs_renewal(str(certfile), days=30) is False


def test_needs_renewal_expiring_cert(tmp_path):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=60))
        .not_valid_after(datetime.now(UTC) + timedelta(days=10))
        .sign(key, hashes.SHA256())
    )
    certfile = tmp_path / "cert.pem"
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    assert needs_renewal(str(certfile), days=30) is True


# ── ensure_certificate ────────────────────────────────────────────────────────

def test_ensure_certificate_not_configured():
    result = ensure_certificate(Settings())
    assert result == (None, None)


def test_ensure_certificate_skips_when_valid(tmp_path):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "mcp.example.com")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "mcp.example.com")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC))
        .not_valid_after(datetime.now(UTC) + timedelta(days=90))
        .sign(key, hashes.SHA256())
    )
    certfile = tmp_path / "cert.pem"
    keyfile = tmp_path / "domain.key"
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )

    s = Settings(
        brainless_mcp_acme_email="u@example.com",
        brainless_mcp_acme_domain="mcp.example.com",
        cloudflare_api_token="tok",
        brainless_mcp_ssl_certfile=str(certfile),
        brainless_mcp_ssl_keyfile=str(keyfile),
    )
    result_certfile, result_keyfile = ensure_certificate(s)
    assert result_certfile == str(certfile)
    assert result_keyfile == str(keyfile)


# ── _CloudflareClient.get_zone_id ─────────────────────────────────────────────

def test_cloudflare_get_zone_id_found():
    cf = _CloudflareClient("fake_token")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": [{"id": "zone123"}]}

    with patch("httpx.get", return_value=mock_resp):
        zone_id = cf.get_zone_id("mcp.example.com")

    assert zone_id == "zone123"


def test_cloudflare_get_zone_id_not_found():
    cf = _CloudflareClient("fake_token")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": []}

    with patch("httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="No Cloudflare zone"):
            cf.get_zone_id("mcp.example.com")


def test_cloudflare_create_txt():
    cf = _CloudflareClient("fake_token")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": {"id": "rec456"}}

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        record_id = cf.create_txt("zone123", "_acme-challenge.example.com", "abc123")

    assert record_id == "rec456"
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["type"] == "TXT"
    assert call_kwargs.kwargs["json"]["content"] == "abc123"


def test_cloudflare_delete_txt():
    cf = _CloudflareClient("fake_token")
    mock_resp = MagicMock()

    with patch("httpx.delete", return_value=mock_resp) as mock_del:
        cf.delete_txt("zone123", "rec456")

    assert "rec456" in mock_del.call_args.args[0]
