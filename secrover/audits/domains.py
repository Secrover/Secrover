import ssl
import socket
from datetime import datetime
from pathlib import Path
from secrover.report import generate_html_report


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
        data.append(info)

    generate_html_report("domains", {
        "data": data,
    }, output_path)
