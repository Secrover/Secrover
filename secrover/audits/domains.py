import ssl
import socket
from datetime import datetime, timezone
from pathlib import Path
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from secrover.report import generate_html_report


def check_http_to_https_redirect(domain):
    url = f"http://{domain}"
    try:
        # We use 'allow_redirects=False' to catch the first response redirect header
        response = requests.get(url, allow_redirects=False, timeout=5)
        if response.status_code in range(300, 400):
            location = response.headers.get("Location", "")
            if location.startswith("https://"):
                return True
        return False
    except requests.RequestException:
        return False


def is_domain_active(domain, timeout=3):
    """
    Check if a domain is active by trying HTTPS then HTTP GET requests.
    Returns True if any responds with status code < 404, else False.
    """
    for scheme in ["https", "http"]:
        try:
            resp = requests.get(f"{scheme}://{domain}", timeout=timeout)
            if resp.status_code < 404:
                return True
        except Exception:
            continue
    return False


def is_port_open(domain, port):
    try:
        with socket.create_connection((domain, port), timeout=0.5):
            return port, True
    except Exception:
        return port, False


def check_open_ports(domain):
    # Common ports to test
    ports = [
        21,  # FTP
        22,  # SSH
        23,  # Telnet
        25,  # SMTP
        53,  # DNS
        80,  # HTTP
        110,  # POP3
        143,  # IMAP
        443,  # HTTPS
        465,  # SMTPS
        587,  # SMTP (mail submission)
        993,  # IMAPS
        995,  # POP3S
        3306,  # MySQL
        3389,  # RDP (Windows Remote Desktop)
        5900,  # VNC
        6379,  # Redis
        8080,  # HTTP alternative port
        8443,  # HTTPS alternative port
        27017,  # MongoDB
    ]

    open_ports = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(is_port_open, domain, port) for port in ports]
        for future in as_completed(futures):
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
    return sorted(open_ports)


def check_security_headers(url):
    """
    Fetch response headers from the given full URL (including scheme),
    and extract key security headers.
    """
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers

        return {
            "hsts_present": bool(headers.get("Strict-Transport-Security")),
            "hsts_value": headers.get("Strict-Transport-Security", ""),
            "csp": headers.get("Content-Security-Policy"),
            "x_content_type_options": headers.get("X-Content-Type-Options"),
            "x_frame_options": headers.get("X-Frame-Options"),
            "referrer_policy": headers.get("Referrer-Policy"),
            "permissions_policy": headers.get("Permissions-Policy"),
        }
    except Exception as e:
        return {
            "hsts_present": False,
            "hsts_value": "",
            "csp": None,
            "x_content_type_options": None,
            "x_frame_options": None,
            "referrer_policy": None,
            "permissions_policy": None,
            "error": str(e),
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

    return supported


def get_ssl_info(domain, port=443, timeout=5):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                not_after = not_after.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_remaining = (not_after - now).days

                issuer_raw = cert.get("issuer", [])
                issuer = {key: value for pair in issuer_raw for key, value in pair}

                return {
                    "valid": True,
                    "issuer": issuer,
                    "not_after": not_after.date().isoformat(),
                    "days_remaining": days_remaining,
                }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_domains(project, domains, output_path: Path, enabled_checks):
    output_path.mkdir(parents=True, exist_ok=True)
    data = []

    total = len(domains)
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{total}] Scanning domain: {domain} ...")
        info = {
            "domain": domain,
            "active": False,
            "https_available": False,
            "http_to_https_redirect": False,
            "supported_tls_versions": [],
            "hsts_present": False,
            "hsts_value": "",
            "csp": None,
            "x_content_type_options": None,
            "x_frame_options": None,
            "referrer_policy": None,
            "permissions_policy": None,
            "open_ports": [],
            "valid": False,
            "issuer": {},
            "not_after": None,
            "days_remaining": None,
            "error": None,
        }

        info["active"] = is_domain_active(domain)
        if info["active"]:
            info["open_ports"] = check_open_ports(domain)
            info["https_available"] = 443 in info["open_ports"]

            # Check HTTP to HTTPS redirect only if port 80 is open
            if 80 in info["open_ports"]:
                info["http_to_https_redirect"] = check_http_to_https_redirect(domain)

            if info["https_available"]:
                ssl_info = get_ssl_info(domain)
                info["valid"] = ssl_info.get("valid", False)
                info["error"] = ssl_info.get("error")

                if info["valid"]:
                    url = f"https://{domain}"
                    info["issuer"] = ssl_info.get("issuer", {})
                    info["not_after"] = ssl_info.get("not_after")
                    info["days_remaining"] = ssl_info.get("days_remaining")
                    info["supported_tls_versions"] = check_tls_versions(domain)
                else:
                    # SSL invalid but HTTPS port is open, fallback to HTTP
                    url = f"http://{domain}"
            else:
                # HTTPS not available, fallback to HTTP
                url = f"http://{domain}"

            # Check security headers for the chosen URL (https if SSL valid, else http)
            sec_headers = check_security_headers(url)
            info["hsts_present"] = sec_headers.get("hsts_present", False)
            info["hsts_value"] = sec_headers.get("hsts_value", "")
            info["csp"] = sec_headers.get("csp")
            info["x_content_type_options"] = sec_headers.get("x_content_type_options")
            info["x_frame_options"] = sec_headers.get("x_frame_options")
            info["referrer_policy"] = sec_headers.get("referrer_policy")
            info["permissions_policy"] = sec_headers.get("permissions_policy")

        else:
            # Domain inactive: keep all defaults
            pass

        data.append(info)

    summary = {
        "nbDomains": total,
    }

    generate_html_report(
        "domains",
        {"project": project, "data": data, "enabled_checks": enabled_checks},
        output_path,
    )

    return summary
