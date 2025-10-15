import subprocess
import json
import re
from pathlib import Path
from collections import defaultdict

from secrover.constants import DEPENDENCIES_SEVERITY_ORDER
from secrover.git import get_repo_name_from_url
from secrover.report import generate_html_report

DEPENDENCIES_SEVERITY_ORDER = ["critical", "high", "moderate", "low", "info"]


def init_severity_counts():
    return {sev: 0 for sev in DEPENDENCIES_SEVERITY_ORDER}


def normalize_severity(severity: str):
    sev = (severity or "info").lower()
    return sev if sev in DEPENDENCIES_SEVERITY_ORDER else "info"


def severity_rank(sev):
    return DEPENDENCIES_SEVERITY_ORDER.index(normalize_severity(sev))


def merge_severity(existing, new):
    return new if severity_rank(new) < severity_rank(existing) else existing


def check_dependencies(
    project, repos, repos_path: Path, output_path: Path, enabled_checks
):
    data = {}
    total = len(repos)
    for i, repo in enumerate(repos, 1):
        repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
        print(f"[{i}/{total}] Scanning repo: {repo_name} ...")
        repo_description = repo.get("description") or ""
        repo_path = repos_path / repo_name
        audit_results = run_audit(repo_path)
        data[repo_name] = {
            "description": repo_description,
            "audit": audit_results,
        }
        print(f"  Found {audit_results['total_vulnerabilities']} issues")

    summary = aggregate_global_summary(data)
    summary.update({"nbRepos": total})

    generate_html_report(
        "dependencies",
        {
            "project": project,
            "data": data,
            "severity_order": DEPENDENCIES_SEVERITY_ORDER,
            "global_summary": summary,
            "enabled_checks": enabled_checks,
        },
        output_path,
    )

    return summary


def run_audit(repo_path: Path):
    """
    Run osv-scanner in SARIF format and return a structured summary
    suitable for templating in HTML.
    """
    try:
        result = subprocess.run(
            ["osv-scanner", "scan", "--format", "sarif", "-r", str(repo_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if not result.stdout.strip():
            print(f"osv-scanner returned no output in {repo_path}")
            return None

        try:
            sarif_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Failed to parse SARIF output: {e}")
            return None

        severity_counts = init_severity_counts()
        packages_by_file = defaultdict(list)

        for run in sarif_data.get("runs", []):
            rules = run.get("tool", {}).get("driver", {}).get("rules", [])
            for res in run.get("results", []):
                msg = res.get("message", {}).get("text", "")
                level = res.get("level", "note")
                severity = normalize_severity(level)

                # Extract package name and version from message
                match = re.search(r"Package '(.+?)@(.+?)' is vulnerable", msg)
                if not match:
                    continue
                name, version = match.groups()
                version = version.rstrip(",")  # known quirk

                # Extract file / artifact where the package is defined
                filename = None
                for loc in res.get("locations", []):
                    uri = (
                        loc.get("physicalLocation", {})
                        .get("artifactLocation", {})
                        .get("uri")
                    )
                    if uri:
                        uri = uri.replace("file://", "")
                        filename = Path(uri).name
                        break

                # Extract CVE / vulnerability IDs
                rule_index = res.get("ruleIndex")
                cves = []
                url = None
                if rule_index is not None and rule_index < len(rules):
                    rule = rules[rule_index]
                    # deprecatedIds usually contains CVE/GHSA/RUSTSEC IDs
                    cves = rule.get("deprecatedIds", [])
                    if cves:
                        # Construct a simple advisory URL using the first CVE/OSV ID
                        url = f"https://osv.dev/vulnerability/{cves[0]}"

                pkg_entry = {
                    "name": name,
                    "version": version,
                    "severity": severity,
                    "file": filename,
                    "cves": cves,
                    "url": url,
                }
                packages_by_file[filename].append(pkg_entry)
                severity_counts[severity] += 1

        return build_audit_summary(severity_counts, packages_by_file)

    except Exception as e:
        print(f"osv-scanner failed unexpectedly: {e}")
        if result.stderr:
            print(f"stderr:\n{result.stderr}")

    return None


def build_audit_summary(severity_counts, packages_by_file, extras=None):
    all_packages = [pkg for pkgs in packages_by_file.values() for pkg in pkgs]

    result = {
        "total_vulnerabilities": sum(severity_counts.values()),
        "vulnerabilities_by_severity": severity_counts,
        "packages_by_file": dict(packages_by_file),
        "packages_impacted": sorted(
            all_packages, key=lambda p: (p["severity"], p["name"])
        ),
    }
    if extras:
        result.update(extras)
    return result


def aggregate_global_summary(data):
    global_counts = defaultdict(int)
    for repo_data in data.values():
        audit = repo_data.get("audit", {})
        if audit:
            sev = audit.get("vulnerabilities_by_severity", {})
            for level in DEPENDENCIES_SEVERITY_ORDER:
                global_counts[level] += sev.get(level, 0)
    global_counts["total"] = sum(global_counts[level] for level in DEPENDENCIES_SEVERITY_ORDER)
    return global_counts
