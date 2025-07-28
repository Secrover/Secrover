import subprocess
import json
import os


def run_npm_audit(repo_path):
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False  # don't raise on vuln exit code
        )
        audit_data = json.loads(result.stdout)

        vulns = audit_data.get("vulnerabilities", {})
        packages = set()
        severity_counts = {
            "critical": 0,
            "high": 0,
            "moderate": 0,
            "low": 0,
            "info": 0
        }

        for pkg, details in vulns.items():
            # fallback to 1 if key missing
            count = details.get("vulnerabilities", 1)
            severity = details.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += count
            else:
                severity_counts["info"] += count
            packages.add(pkg)

        total_vulns = sum(severity_counts.values())

        return {
            "total_vulnerabilities": total_vulns,
            "vulnerabilities_by_severity": severity_counts,
            "packages_impacted": sorted(packages)
        }

    except json.JSONDecodeError as e:
        print(f"Failed to parse npm audit output as JSON: {e}")
        print(f"Output was:\n{result.stdout}")
        return None
    except Exception as e:
        print(f"npm audit failed unexpectedly: {e}")
        return None


def run_composer_audit(repo_path):
    try:
        subprocess.run(
            ["composer", "install", "--no-interaction",
                "--no-progress", "--prefer-dist"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["composer", "audit", "--format=json"],
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
        total_vulns = 0
        severity_counts = {
            "critical": 0,
            "high": 0,
            "moderate": 0,
            "low": 0,
            "info": 0
        }

        for vuln in advisories:
            total_vulns += 1
            severity = vuln.get("severity", "info").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            pkg_name = vuln.get("package", {}).get("name")
            if pkg_name:
                packages.add(pkg_name)

        return {
            "total_vulnerabilities": total_vulns,
            "vulnerabilities_by_severity": severity_counts,
            "packages_impacted": sorted(packages),
            "abandoned_packages": abandoned
        }

    except subprocess.CalledProcessError as e:
        print(f"composer audit command failed in {repo_path}: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return None

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
        else:
            print("No npm audit results.")

    if "PHP" in language_str:
        composer_lock_path = os.path.join(repo_path, "composer.lock")
        if os.path.exists(composer_lock_path):
            print(f"Running composer audit on {repo_name}...")
            composer_summary = run_composer_audit(repo_path)
            if composer_summary:
                results["composer"] = composer_summary
            else:
                print("No composer audit results.")
        else:
            print(
                f"No composer.lock found in {repo_name}, skipping composer audit.")

    return results
