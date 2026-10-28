import ipaddress
import re
import subprocess
from pathlib import Path

CERTS_DIR = Path('certs')
CERT_DAYS = 365
HOST_RE = re.compile(r'^[A-Za-z0-9.*:-]+$')


def _openssl(*args):
    try:
        return subprocess.run(['openssl', *args], capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit('openssl binary not found; it is required to generate certificates')


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def cert_paths(hostname):
    """Return (pem, key, cer) paths for a hostname under ./certs/."""
    name = re.sub(r'[^A-Za-z0-9.-]', '_', hostname)
    return (CERTS_DIR / f'{name}.pem', CERTS_DIR / f'{name}.key', CERTS_DIR / f'{name}.cer')


def _cert_is_valid_for(hostname, pem, key):
    """True if an existing cert/key pair matches hostname, is unexpired and the key belongs to the cert."""
    if not (pem.is_file() and key.is_file()):
        return False

    if _openssl('x509', '-in', str(pem), '-noout', '-checkend', '0').returncode != 0:
        return False

    check = '-checkip' if _is_ip(hostname) else '-checkhost'
    result = _openssl('x509', '-in', str(pem), '-noout', check, hostname)
    if result.returncode != 0 or 'does match certificate' not in result.stdout:
        return False

    cert_pub = _openssl('x509', '-in', str(pem), '-noout', '-pubkey')
    key_pub = _openssl('pkey', '-in', str(key), '-pubout')
    return cert_pub.returncode == 0 and key_pub.returncode == 0 and cert_pub.stdout == key_pub.stdout


def ensure_cert(hostname):
    """Reuse ./certs/<hostname>.pem if it is valid for hostname, otherwise generate a new self-signed one.

    Writes <hostname>.pem (certificate), <hostname>.key (private key) and <hostname>.cer (DER certificate).
    Returns (certfile, keyfile) as strings."""
    if not HOST_RE.match(hostname):
        raise SystemExit(f'invalid --ssl-host value: {hostname!r}')

    pem, key, cer = cert_paths(hostname)

    if _cert_is_valid_for(hostname, pem, key):
        print(f'[ssl] reusing existing certificate for {hostname}: {pem}')
        return str(pem), str(key)

    CERTS_DIR.mkdir(exist_ok=True)
    san = f'IP:{hostname}' if _is_ip(hostname) else f'DNS:{hostname}'
    result = _openssl(
        'req', '-x509', '-newkey', 'rsa:2048', '-sha256', '-nodes',
        '-days', str(CERT_DAYS),
        '-keyout', str(key), '-out', str(pem),
        '-subj', f'/CN={hostname}',
        '-addext', f'subjectAltName={san}',
    )
    if result.returncode != 0:
        raise SystemExit(f'openssl failed to generate certificate:\n{result.stderr}')

    result = _openssl('x509', '-in', str(pem), '-outform', 'der', '-out', str(cer))
    if result.returncode != 0:
        raise SystemExit(f'openssl failed to write DER certificate:\n{result.stderr}')

    print(f'[ssl] generated self-signed certificate for {hostname}: {pem}')
    return str(pem), str(key)
