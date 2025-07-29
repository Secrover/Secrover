import ssl
import socket
from datetime import datetime, timezone
from pathlib import Path
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from secrover.report import generate_html_report


def is_port_open(domain, port):
    try:
        with socket.create_connection((domain, port), timeout=0.5):
            return port, True
    except Exception:
        return port, False


def check_open_ports(domain):
    # Common ports to test
    ports = [
        21,    # FTP
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        53,    # DNS
        80,    # HTTP
        110,   # POP3
        143,   # IMAP
        443,   # HTTPS
        465,   # SMTPS
        587,   # SMTP (mail submission)
        993,   # IMAPS
        995,   # POP3S
        3306,  # MySQL
        3389,  # RDP (Windows Remote Desktop)
        5900,  # VNC
        6379,  # Redis
        8080,  # HTTP alternative port
        8443,  # HTTPS alternative port
        27017  # MongoDB
    ]

    open_ports = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(
            is_port_open, domain, port) for port in ports]
        for future in as_completed(futures):
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
    return {"open_ports": sorted(open_ports)}


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
                not_after = not_after.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
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

    total = len(domains)
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{total}] Scanning domain: {domain} ...")
        info = get_ssl_info(domain)
        if info["valid"]:
            info.update(check_hsts(domain))
            info.update(check_tls_versions(domain))
            info.update(check_open_ports(domain))
        else:
            # even if SSL invalid, ports may be open
            info.update(check_open_ports(domain))
        data.append(info)

    generate_html_report("domains", {
        "data": data,
    }, output_path)
