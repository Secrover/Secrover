import base64
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime

severity_order = ["critical", "high", "moderate", "low", "info"]
severity_emojis = {
    "critical": "🚨",
    "high": "⚠️",
    "moderate": "▶️",
    "low": "↘️",
    "info": "ℹ️",
}

def get_base64_image(path: Path) -> str:
    with path.open("rb") as img_file:
        encoded_bytes = base64.b64encode(img_file.read())
        return encoded_bytes.decode("utf-8")

def aggregate_global_summary(results):
    from collections import defaultdict
    global_counts = defaultdict(int)
    for repo_data in results.values():
        audits = repo_data.get("audits", {})
        for audit_summary in audits.values():
            sev = audit_summary.get("vulnerabilities_by_severity", {})
            for level in severity_order:
                global_counts[level] += sev.get(level, 0)
    global_counts["total"] = sum(global_counts[level] for level in severity_order)
    return global_counts

def generate_html_report_from_template(results, output_path: Path):
    template_dir = Path("templates")
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("vulnerabilities.html")

    global_summary = aggregate_global_summary(results)
    audit_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    favicon_b64 = get_base64_image(Path("assets/favicon.svg"))
    logo_b64 = get_base64_image(Path("assets/secrover.svg"))

    # Render template with context
    output_html = template.render(
        results=results,
        global_summary=global_summary,
        audit_datetime=audit_datetime,
        severity_order=severity_order,
        severity_emojis=severity_emojis,
        favicon_b64=favicon_b64,
        logo_b64=logo_b64,
    )

    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / "vulnerabilities.html"
    report_file.write_text(output_html, encoding="utf-8")

    print(f"HTML report generated in \"{output_path}\" folder")
