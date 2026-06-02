"""Let's Encrypt certificate manager — DNS-01 challenge via Cloudflare."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

ACME_PROD = "https://acme-v02.api.letsencrypt.org/directory"
ACME_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"
_RENEW_DAYS = 30  # renew when fewer than this many days remain


def is_configured(settings) -> bool:  # type: ignore[type-arg]
    return bool(
        settings.brainless_mcp_acme_email
        and settings.brainless_mcp_acme_domain
        and settings.cloudflare_api_token
    )


def needs_renewal(certfile: str, days: int = _RENEW_DAYS) -> bool:
    """Return True if the cert is missing or expires within *days* days."""
    path = Path(certfile)
    if not path.exists():
        return True
    try:
        from cryptography import x509

        cert = x509.load_pem_x509_certificate(path.read_bytes())
        try:
            expiry = cert.not_valid_after_utc
        except AttributeError:
            expiry = cert.not_valid_after.replace(tzinfo=UTC)  # type: ignore[attr-defined]
        return (expiry - datetime.now(UTC)).days < days
    except Exception:
        return True


def ensure_certificate(settings) -> tuple[str, str] | tuple[None, None]:  # type: ignore[type-arg]
    """Obtain or renew a Let's Encrypt cert if ACME is configured.

    Returns (certfile_path, keyfile_path) when ACME is active, else (None, None).
    The returned paths override whatever is set in BRAINLESS_MCP_SSL_CERTFILE/KEYFILE.
    """
    if not is_configured(settings):
        return None, None

    cert_dir = Path(
        settings.brainless_mcp_acme_cert_dir
        or Path.home() / ".brainless-mcp" / "certs"
    )
    certfile = settings.brainless_mcp_ssl_certfile or str(cert_dir / "cert.pem")
    keyfile = settings.brainless_mcp_ssl_keyfile or str(cert_dir / "domain.key")

    if not needs_renewal(certfile):
        logger.info("TLS certificate is valid; skipping renewal.")
        return certfile, keyfile

    logger.info(
        "Obtaining Let's Encrypt certificate for %s",
        settings.brainless_mcp_acme_domain,
    )
    _obtain(settings, cert_dir, certfile, keyfile)
    return certfile, keyfile


def _obtain(settings, cert_dir: Path, certfile: str, keyfile: str) -> None:  # type: ignore[type-arg]
    try:
        import josepy as jose
        from acme import challenges, client, messages
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.x509.oid import NameOID
    except ImportError as exc:
        raise RuntimeError(
            "ACME/TLS dependencies are not installed. "
            "Run: pip install 'brainless-mcp[tls]'"
        ) from exc

    domain = settings.brainless_mcp_acme_domain
    email = settings.brainless_mcp_acme_email
    cf_token = settings.cloudflare_api_token
    staging = settings.brainless_mcp_acme_staging
    dns_wait = settings.brainless_mcp_acme_dns_wait

    cert_dir.mkdir(parents=True, exist_ok=True)

    # ── Account key ───────────────────────────────────────────────────────────
    account_key_path = cert_dir / "account.key"
    if account_key_path.exists():
        acct_priv = load_pem_private_key(account_key_path.read_bytes(), password=None)
    else:
        acct_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        account_key_path.write_bytes(
            acct_priv.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
    account_key = jose.JWKRSA(key=acct_priv)

    # ── Domain key ────────────────────────────────────────────────────────────
    domain_key_path = Path(keyfile)
    domain_key_path.parent.mkdir(parents=True, exist_ok=True)
    if domain_key_path.exists():
        domain_priv = load_pem_private_key(domain_key_path.read_bytes(), password=None)
    else:
        domain_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        domain_key_path.write_bytes(
            domain_priv.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )

    # ── CSR ───────────────────────────────────────────────────────────────────
    csr_pem = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain)]))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(domain)]),
            critical=False,
        )
        .sign(domain_priv, hashes.SHA256())
        .public_bytes(serialization.Encoding.PEM)
    )

    # ── ACME client ───────────────────────────────────────────────────────────
    directory_url = ACME_STAGING if staging else ACME_PROD
    net = client.ClientNetwork(account_key, user_agent="brainless-mcp/1.0")
    directory = messages.Directory.from_json(net.get(directory_url).json())
    acme_client = client.ClientV2(directory, net)

    acme_client.new_account(
        messages.NewRegistration.from_data(email=email, terms_of_service_agreed=True)
    )

    # ── Order & DNS-01 challenge ──────────────────────────────────────────────
    order = acme_client.new_order(csr_pem)

    dns01_body = None
    for authz in order.authorizations:
        for chall_body in authz.body.challenges:
            if isinstance(chall_body.chall, challenges.DNS01):
                dns01_body = chall_body
                break
        if dns01_body:
            break

    if dns01_body is None:
        raise RuntimeError("ACME server did not offer a DNS-01 challenge.")

    txt_value = dns01_body.chall.validation(account_key)
    # Strip wildcard prefix so _acme-challenge goes on the base domain
    base_domain = domain.lstrip("*.")
    record_name = f"_acme-challenge.{base_domain}"

    # ── Cloudflare DNS ────────────────────────────────────────────────────────
    cf = _CloudflareClient(cf_token)
    zone_id = cf.get_zone_id(base_domain)
    record_id = cf.create_txt(zone_id, record_name, txt_value)
    logger.info("DNS TXT record created; waiting %ds for propagation…", dns_wait)
    time.sleep(dns_wait)

    try:
        acme_client.answer_challenge(dns01_body, dns01_body.response(account_key))
        finalized = acme_client.poll_and_finalize(order)
    finally:
        try:
            cf.delete_txt(zone_id, record_id)
            logger.debug("DNS TXT record removed.")
        except Exception as exc:
            logger.warning("Failed to remove DNS TXT record: %s", exc)

    Path(certfile).parent.mkdir(parents=True, exist_ok=True)
    Path(certfile).write_text(finalized.fullchain_pem)
    logger.info("Certificate written to %s", certfile)


class _CloudflareClient:
    """Minimal Cloudflare DNS API client (uses httpx, no extra deps)."""

    _BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, token: str) -> None:
        self._h = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_zone_id(self, domain: str) -> str:
        """Walk from domain up to apex to find the matching zone."""
        parts = domain.split(".")
        for i in range(len(parts) - 1):
            name = ".".join(parts[i:])
            resp = httpx.get(
                f"{self._BASE}/zones", headers=self._h, params={"name": name}
            )
            resp.raise_for_status()
            result = resp.json().get("result", [])
            if result:
                return result[0]["id"]
        raise ValueError(f"No Cloudflare zone found for domain: {domain}")

    def create_txt(self, zone_id: str, name: str, value: str) -> str:
        """Create a TXT record and return its ID."""
        resp = httpx.post(
            f"{self._BASE}/zones/{zone_id}/dns_records",
            headers=self._h,
            json={"type": "TXT", "name": name, "content": value, "ttl": 60},
        )
        resp.raise_for_status()
        return resp.json()["result"]["id"]

    def delete_txt(self, zone_id: str, record_id: str) -> None:
        resp = httpx.delete(
            f"{self._BASE}/zones/{zone_id}/dns_records/{record_id}",
            headers=self._h,
        )
        resp.raise_for_status()
