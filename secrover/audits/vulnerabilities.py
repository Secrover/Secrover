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


def check_vulnerabilities(repos, output_path):
    data = {}
    for repo in repos:
        repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
        repo_description = repo.get("description") or ""
        repo_path = REPOS_FOLDER / repo_name

        language = detect_language_by_files(repo_path)
        print(f"Detected language(s) for '{repo_name}': {language}")

        audit_results = run_language_audits(language, repo_path, repo_name)
        data[repo_name] = {
            "description": repo_description,
            "audits": audit_results
        }
        # Print nicely
        for tool, summary in audit_results.items():
            print(f"\n{tool} audit summary for {repo_name}:")
            print(
                f"  Total vulnerabilities: {summary['total_vulnerabilities']}")
            print(f"  By severity: {summary['vulnerabilities_by_severity']}")
            print(f"  Impacted packages: {summary['packages_impacted']}")
            if tool == "composer" and summary.get("abandoned_packages"):
                print(f"  Abandoned packages: {summary['abandoned_packages']}")
        print()

    print("\nAll repos processed.")

    generate_html_report("vulnerabilities", {
        "data": data,
        "severity_order": severity_order,
        "severity_emojis": severity_emojis,
        "global_summary": aggregate_global_summary(data),
    }, output_path)


def run_pip_audit(repo_path: Path):
    # Detect if Python project exists by common files
    if not any((repo_path / fname).exists() for fname in ["requirements.txt", "pyproject.toml"]):
        print(f"No Python dependency files found in {repo_path}, skipping pip audit.")
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
            print(f"Unexpected pip-audit JSON format in {repo_path}: {audit_data}")
            return None

        severity_counts = {sev: 0 for sev in severity_order}
        packages = set()

        for dep in audit_data["dependencies"]:
            vulns = dep.get("vulns", [])
            for vuln in vulns:
                severity = vuln.get("severity", "info").lower()
                if severity not in severity_counts:
                    severity = "info"
                severity_counts[severity] += 1
                packages.add(dep.get("name"))

        return {
            "total_vulnerabilities": sum(severity_counts.values()),
            "vulnerabilities_by_severity": severity_counts,
            "packages_impacted": sorted(packages),
        }

    except json.JSONDecodeError as e:
        print(f"Failed to parse pip-audit output as JSON: {e}")
        print(f"Output was:\n{result.stdout}")
    except Exception as e:
        print(f"pip-audit failed unexpectedly: {e}")

    return None


def run_npm_audit(repo_path: Path):
    package_json = repo_path / "package.json"
    if not package_json.exists():
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
        packages = set()
        severity_counts = {
            "critical": 0, "high": 0, "moderate": 0, "low": 0, "info": 0
        }

        for pkg, details in vulns.items():
            count = details.get("vulnerabilities", 1)
            severity = details.get("severity", "info").lower()
            severity_counts[severity if severity in severity_counts else "info"] += count
            packages.add(pkg)

        return {
            "total_vulnerabilities": sum(severity_counts.values()),
            "vulnerabilities_by_severity": severity_counts,
            "packages_impacted": sorted(packages)
        }

    except json.JSONDecodeError as e:
        print(f"Failed to parse npm audit output as JSON: {e}")
        print(f"Output was:\n{result.stdout}")
    except Exception as e:
        print(f"npm audit failed unexpectedly: {e}")

    return None


def run_composer_audit(repo_path: Path):
    composer_lock = repo_path / "composer.lock"
    if not composer_lock.exists():
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

        packages = set()
        severity_counts = {
            "critical": 0, "high": 0, "moderate": 0, "low": 0, "info": 0
        }

        for vuln in advisories:
            severity = vuln.get("severity", "info").lower()
            severity_counts[severity if severity in severity_counts else "info"] += 1
            pkg_name = vuln.get("package", {}).get("name")
            if pkg_name:
                packages.add(pkg_name)

        return {
            "total_vulnerabilities": sum(severity_counts.values()),
            "vulnerabilities_by_severity": severity_counts,
            "packages_impacted": sorted(packages),
            "abandoned_packages": abandoned
        }

    except subprocess.CalledProcessError as e:
        print(f"composer audit command failed in {repo_path}: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(
            f"Failed to parse composer audit output as JSON in {repo_path}: {e}")
        print(f"Output was:\n{result.stdout}")

    return None


def run_language_audits(language_str, repo_path, repo_name):
    results = {}

    if "JavaScript" in language_str:
        print(f"Running npm audit on {repo_name}...")
        npm_summary = run_npm_audit(repo_path)
        if npm_summary:
            results["npm"] = npm_summary
    elif "PHP" in language_str:
        print(f"Running composer audit on {repo_name}...")
        composer_summary = run_composer_audit(repo_path)
        if composer_summary:
            results["composer"] = composer_summary
    elif "Python" in language_str:
        print(f"Running pip audit on {repo_name}...")
        pip_summary = run_pip_audit(repo_path)
        if pip_summary:
            results["pip"] = pip_summary

    return results


def aggregate_global_summary(results):
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
