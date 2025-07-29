import subprocess
import json
from pathlib import Path

from secrover.git import get_repo_name_from_url
from secrover.report import generate_html_report
from secrover.languages import detect_language_by_files
from secrover.constants import REPOS_FOLDER
from collections import defaultdict

severity_order = ["critical", "high", "moderate", "low", "info"]
severity_emojis = {
    "critical": "🚨",
    "high": "⚠️",
    "moderate": "▶️",
    "low": "↘️",
    "info": "ℹ️",
}


def init_severity_counts():
    return {sev: 0 for sev in severity_order}


def normalize_severity(severity: str):
    sev = (severity or "info").lower()
    return sev if sev in severity_order else "info"


def severity_rank(sev):
    return severity_order.index(normalize_severity(sev))


def merge_severity(existing, new):
    return new if severity_rank(new) < severity_rank(existing) else existing


def build_audit_summary(severity_counts, package_map, extras=None):
    packages_impacted = [
        {"name": name, "severity": sev}
        for name, sev in sorted(package_map.items())
    ]
    result = {
        "total_vulnerabilities": sum(severity_counts.values()),
        "vulnerabilities_by_severity": severity_counts,
        "packages_impacted": packages_impacted,
    }
    if extras:
        result.update(extras)
    return result


def check_dependencies(repos, output_path):
    data = {}
    for repo in repos:
        repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
        repo_description = repo.get("description") or ""
        repo_path = REPOS_FOLDER / repo_name

        language = detect_language_by_files(repo_path)
        print(f"Detected language(s) for '{repo_name}': {language}")

        audit_results = run_language_audit(language, repo_path, repo_name)
        data[repo_name] = {
            "language": language,
            "description": repo_description,
            "audit": audit_results
        }

        print(f"\n{language} audit summary for {repo_name}:")
        print(
            f"  Total vulnerabilities: {audit_results['total_vulnerabilities']}")
        print(f"  By severity: {audit_results['vulnerabilities_by_severity']}")
        print(
            f"  Impacted packages: {[pkg['name'] for pkg in audit_results['packages_impacted']]}")
        if language == "composer" and audit_results.get("abandoned_packages"):
            print(
                f"  Abandoned packages: {audit_results['abandoned_packages']}")
        print()

    print("\nAll repos processed.")

    generate_html_report("dependencies", {
        "data": data,
        "severity_order": severity_order,
        "severity_emojis": severity_emojis,
        "global_summary": aggregate_global_summary(data),
    }, output_path)


def run_pip_audit(repo_path: Path):
    if not any((repo_path / fname).exists() for fname in ["requirements.txt", "pyproject.toml"]):
        print(
            f"No Python dependency files found in {repo_path}, skipping pip audit.")
        return None

    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        if not result.stdout.strip():
            print(f"pip-audit returned no output in {repo_path}")
            return None

        audit_data = json.loads(result.stdout)
        if not isinstance(audit_data, dict) or "dependencies" not in audit_data:
            print(
                f"Unexpected pip-audit JSON format in {repo_path}: {audit_data}")
            return None

        severity_counts = init_severity_counts()
        packages = {}

        for dep in audit_data["dependencies"]:
            name = dep.get("name")
            for vuln in dep.get("vulns", []):
                severity = normalize_severity(vuln.get("severity"))
                severity_counts[severity] += 1
                if name:
                    current = packages.get(name, "info")
                    packages[name] = merge_severity(current, severity)

        return build_audit_summary(severity_counts, packages)

    except json.JSONDecodeError as e:
        print(f"Failed to parse pip-audit output as JSON: {e}")
        print(f"Output was:\n{result.stdout}")
    except Exception as e:
        print(f"pip-audit failed unexpectedly: {e}")

    return None


def run_npm_audit(repo_path: Path):
    if not (repo_path / "package.json").exists():
        print(f"No package.json found in {repo_path}, skipping npm audit.")
        return None

    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        audit_data = json.loads(result.stdout)
        vulns = audit_data.get("vulnerabilities", {})

        severity_counts = init_severity_counts()
        packages = {}

        for pkg, details in vulns.items():
            count = details.get("vulnerabilities", 1)
            severity = normalize_severity(details.get("severity"))
            severity_counts[severity] += count
            current = packages.get(pkg, "info")
            packages[pkg] = merge_severity(current, severity)

        return build_audit_summary(severity_counts, packages)

    except json.JSONDecodeError as e:
        print(f"Failed to parse npm audit output as JSON: {e}")
        print(f"Output was:\n{result.stdout}")
    except Exception as e:
        print(f"npm audit failed unexpectedly: {e}")

    return None


def run_composer_audit(repo_path: Path):
    if not (repo_path / "composer.lock").exists():
        print(
            f"No composer.lock found in {repo_path}, skipping composer audit.")
        return None

    try:
        result = subprocess.run(
            ["composer", "audit", "--format=json", "--locked"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        if not output:
            print(f"composer audit returned empty output for {repo_path}")
            return None

        audit_data = json.loads(output)
        advisories = audit_data.get("advisories", [])
        abandoned = audit_data.get("abandoned", [])

        severity_counts = init_severity_counts()
        packages = {}

        for vuln in advisories:
            severity = normalize_severity(vuln.get("severity"))
            severity_counts[severity] += 1
            pkg_name = vuln.get("package", {}).get("name")
            if pkg_name:
                current = packages.get(pkg_name, "info")
                packages[pkg_name] = merge_severity(current, severity)

        return build_audit_summary(severity_counts, packages, {"abandoned_packages": abandoned})

    except subprocess.CalledProcessError as e:
        print(f"composer audit command failed in {repo_path}: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(
            f"Failed to parse composer audit output as JSON in {repo_path}: {e}")
        print(f"Output was:\n{result.stdout}")

    return None


def run_language_audit(language_str, repo_path, repo_name):
    if "JavaScript" in language_str:
        print(f"Running npm audit on {repo_name}...")
        summary = run_npm_audit(repo_path)
    elif "PHP" in language_str:
        print(f"Running composer audit on {repo_name}...")
        summary = run_composer_audit(repo_path)
    elif "Python" in language_str:
        print(f"Running pip audit on {repo_name}...")
        summary = run_pip_audit(repo_path)
    else:
        print(f"No supported language found for {repo_name}, skipping.")
        return None

    return summary


def aggregate_global_summary(data):
    global_counts = defaultdict(int)
    for repo_data in data.values():
        audit = repo_data.get("audit", {})
        if audit:
            sev = audit.get("vulnerabilities_by_severity", {})
            for level in severity_order:
                global_counts[level] += sev.get(level, 0)
    global_counts["total"] = sum(global_counts[level]
                                 for level in severity_order)
    return global_counts
