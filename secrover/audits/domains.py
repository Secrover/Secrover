import ssl
import socket
from datetime import datetime
from pathlib import Path
import requests

from secrover.report import generate_html_report


def check_hsts(domain):
    try:
        response = requests.get(f"https://{domain}", timeout=5)
        hsts = response.headers.get("Strict-Transport-Security")
        return {
            "hsts_present": bool(hsts),
            "hsts_value": hsts or ""
        }
    except Exception as e:
        return {
            "hsts_present": False,
            "error": str(e)
        }


def check_tls_versions(domain, port=443):
    versions = {
        "TLSv1": ssl.TLSVersion.TLSv1,
        "TLSv1.1": ssl.TLSVersion.TLSv1_1,
        "TLSv1.2": ssl.TLSVersion.TLSv1_2,
        "TLSv1.3": ssl.TLSVersion.TLSv1_3,
    }

    supported = []

    for label, version in versions.items():
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.minimum_version = version
            ctx.maximum_version = version
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with socket.create_connection((domain, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain):
                    supported.append(label)
        except Exception:
            pass  # Not supported

    return {
        "supported_tls_versions": supported
    }


def get_ssl_info(domain, port=443, timeout=5):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(
                    cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                now = datetime.utcnow()
                days_remaining = (not_after - now).days

                issuer_raw = cert.get("issuer", [])
                issuer = {
                    key: value for pair in issuer_raw for key, value in pair}

                return {
                    "domain": domain,
                    "valid": True,
                    "issuer": issuer,
                    "not_after": not_after.isoformat(),
                    "days_remaining": days_remaining
                }
    except Exception as e:
        return {
            "domain": domain,
            "valid": False,
            "error": str(e)
        }


def check_domains(domains, output_path: Path):
    output_path.mkdir(parents=True, exist_ok=True)
    data = []

    for domain in domains:
        info = get_ssl_info(domain)
        if info["valid"]:
            info.update(check_hsts(domain))
            info.update(check_tls_versions(domain))

        data.append(info)

    generate_html_report("domains", {
        "data": data,
    }, output_path)
