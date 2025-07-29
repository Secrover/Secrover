import subprocess
import json


def run_npm_audit(repo_path):
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


def run_composer_audit(repo_path):
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

    if "PHP" in language_str:
        print(f"Running composer audit on {repo_name}...")
        composer_summary = run_composer_audit(repo_path)
        if composer_summary:
            results["composer"] = composer_summary

    return results
