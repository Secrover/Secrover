import os
from string import Template
from collections import defaultdict
from datetime import datetime


def aggregate_global_summary(results):
    """
    Aggregate vulnerability counts across all repos and tools.
    """
    severity_order = ["critical", "high", "moderate", "low", "info"]
    global_counts = defaultdict(int)

    for repo_data in results.values():
        audits = repo_data.get("audits", {})
        for audit_summary in audits.values():
            sev = audit_summary.get("vulnerabilities_by_severity", {})
            for level in severity_order:
                global_counts[level] += sev.get(level, 0)

    global_counts["total"] = sum(global_counts[level]
                                 for level in severity_order)
    return global_counts


def generate_html_report_from_template(results, output_path):
    template_path = "templates/vulnerabilities.html"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Get current datetime formatted
    audit_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    severity_order = ["critical", "high", "moderate", "low", "info"]
    severity_emojis = {
        "critical": "🚨",
        "high": "⚠️",
        "moderate": "▶️",
        "low": "↘️",
        "info": "ℹ️",
    }
    repo_sections = []

    for repo_name, repo_data in results.items():
        description = repo_data.get("description", "")
        audits = repo_data.get("audits", {})

        if not audits:
            repo_sections.append(
                f"<h2>{repo_name}</h2><p>No audit results available.</p>")
            continue

        for tool_name, audit in audits.items():
            if not audit:
                repo_sections.append(
                    f"<h3>{tool_name.capitalize()} audit for {repo_name} - no data</h3>")
                continue

            vulns = audit.get("total_vulnerabilities", 0)
            severity = audit.get("vulnerabilities_by_severity", {})
            packages = audit.get("packages_impacted", [])
            abandoned = audit.get("abandoned_packages", [])

            # Build severity list sorted by severity order
            severity_html = "".join(
                f"<span class=\"badge badge-{level}\">{severity_emojis.get(level, '')} {level.capitalize()}: {severity.get(level, 0)}</span>"
                for level in severity_order
            )
            severity_html += f"<span class=\"badge badge-total\">📈 Total: {vulns}</span>"

            packages_html = "".join(f"<div>{pkg}</div>" for pkg in sorted(
                packages)) + "" if packages else "<p class=\"no-issues mb-0\">None - All clear! 🎉</p>"
            abandoned_html = "".join(f"<div>{pkg}</div>" for pkg in sorted(
                abandoned)) + "" if abandoned else "<p class=\"no-issues mb-0\">None - All clear! 🎉</p>"

            section = f"""
            <div class="project-card">
                <div class="project-header">
                    <h3>{repo_name}</h3>
                    <span>{tool_name}</span>
                </div>
                <p class="project-description">{description}</p>
                <p><strong>🎯 Severity Breakdown:</strong></p>
                <div class="vulnerability-badges mb-20">
                    {severity_html}
                </div>
                <p><strong>📦 Impacted Packages:</strong></p>
                <div class="packages-list mb-20">
                    {packages_html}
                </div>
                <p><strong>📦 Abandoned packages:</strong></p>
                <div class="packages-list">
                    {abandoned_html}
                </div>
            </div>
            """
            repo_sections.append(section)

    # Aggregate global summary for recap
    global_summary = aggregate_global_summary(results)

    template = Template(template_content)
    output_html = template.substitute(
        critical=global_summary.get("critical", 0),
        high=global_summary.get("high", 0),
        moderate=global_summary.get("moderate", 0),
        low=global_summary.get("low", 0),
        info=global_summary.get("info", 0),
        total=global_summary.get("total", 0),
        repo_sections="\n".join(repo_sections),
        audit_datetime=audit_datetime,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path + "/vulnerabilities.html", "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"HTML report generated in {output_path}")
