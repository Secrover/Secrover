import os
from string import Template
from collections import defaultdict
from datetime import datetime

# Define severity levels and corresponding emojis
severity_order = ["critical", "high", "moderate", "low", "info"]
severity_emojis = {
    "critical": "🚨",
    "high": "⚠️",
    "moderate": "▶️",
    "low": "↘️",
    "info": "ℹ️",
}


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


def render_badges(severity, total):
    return "".join(
        f"<span class=\"badge badge-{level}\">{severity_emojis.get(level, '')} {level.capitalize()}: {severity.get(level, 0)}</span>"
        for level in severity_order
    ) + f"<span class=\"badge badge-total\">📈 Total: {total}</span>"


def render_packages_list(packages):
    if packages:
        return "".join(f"<div>{pkg}</div>" for pkg in sorted(packages))
    return "<p class=\"no-issues mb-0\">None - All clear! 🎉</p>"


def render_card_header(repo_name, tool_name=None):
    badge_html = f'<span class="badge-small badge-basic">{tool_name}</span>' if tool_name else ""
    return f"""
    <div class="project-header">
        <h3>{repo_name}</h3>
        {badge_html}
    </div>
    """


def render_project_card(repo_name, description, tool_name=None, audit=None):
    header_html = render_card_header(repo_name, tool_name)

    if audit is None:
        body_html = f"""
        <p class="project-description">{description}</p>
        <p class="mb-0">No audit data available{f' for {tool_name}' if tool_name else ''}.</p>
        """
    else:
        severity_html = render_badges(
            audit.get("vulnerabilities_by_severity", {}),
            audit.get("total_vulnerabilities", 0)
        )
        packages_html = render_packages_list(
            audit.get("packages_impacted", []))
        abandoned_html = render_packages_list(
            audit.get("abandoned_packages", []))

        body_html = f"""
        <p class="project-description">{description}</p>
        <p><strong>🎯 Severity Breakdown:</strong></p>
        <div class="vulnerability-badges mb-20">
            {severity_html}
        </div>
        <p><strong>📦 Impacted Packages:</strong></p>
        <div class="packages-list mb-20">
            {packages_html}
        </div>
        <p><strong>📦 Abandoned Packages:</strong></p>
        <div class="packages-list">
            {abandoned_html}
        </div>
        """

    return f"""
    <div class="project-card">
        {header_html}
        {body_html}
    </div>
    """


def generate_html_report_from_template(results, output_path):
    template_path = "templates/vulnerabilities.html"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    audit_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo_sections = []

    for repo_name, repo_data in results.items():
        description = repo_data.get("description", "")
        audits = repo_data.get("audits", {})

        if not audits:
            repo_sections.append(render_project_card(repo_name, description))
            continue

        for tool_name, audit in audits.items():
            repo_sections.append(render_project_card(
                repo_name, description, tool_name, audit))

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
    with open(os.path.join(output_path, "vulnerabilities.html"), "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"HTML report generated in {output_path}")
