import subprocess
import json

from secrover.git import get_repo_name_from_url
from secrover.report import generate_html_report
from secrover.languages import detect_language_by_files
from secrover.constants import REPOS_FOLDER

sarif_to_severity = {
    "error": "high",
    "warning": "moderate",
    "note": "low",
}
severity_order = ["high", "moderate", "low"]
severity_emojis = {
    "high": "🔥",
    "moderate": "⚠️",
    "low": "↘️",
}


def parse_sarif_findings(sarif_data):
    findings = []
    for run in sarif_data.get("runs", []):
        for result in run.get("results", []):
            level = result.get("level", "warning").lower()
            severity = sarif_to_severity.get(level, "moderate")
            message = result.get("message", {}).get("text", "No message")
            rule_id = result.get("ruleId", "Unknown Rule")
            locations = result.get("locations", [])
            if locations:
                loc = locations[0].get("physicalLocation", {}).get(
                    "artifactLocation", {}).get("uri", "Unknown file")
                start_line = locations[0].get("physicalLocation", {}).get(
                    "region", {}).get("startLine")
            else:
                loc = "Unknown file"
                start_line = None

            findings.append({
                "severity": severity,
                "rule_id": rule_id,
                "message": message,
                "location": {
                    "file": loc,
                    "line": start_line,
                }
            })
    return findings


def aggregate_global_summary(data):
    summary = {level: 0 for level in severity_order}
    summary["total"] = 0

    for repo_data in data.values():
        findings_by_severity = repo_data.get("findings_by_severity", {})
        total_findings = repo_data.get("findings_count", 0)

        for level in severity_order:
            summary[level] += findings_by_severity.get(level, 0)

        summary["total"] += total_findings

    return summary


def check_code(repos, output_path):
    data = {}
    total = len(repos)
    for i, repo in enumerate(repos, 1):
        repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
        print(f"[{i}/{total}] Scanning repo: {repo_name} ...")
        repo_description = repo.get("description") or ""
        repo_path = REPOS_FOLDER / repo_name
        language = detect_language_by_files(repo_path)

        try:
            result = subprocess.run(
                ["semgrep", "scan", "--sarif"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            sarif_data = json.loads(result.stdout)
            runs = sarif_data.get("runs", [])

            # Flatten all results across runs
            all_results = []
            for run in runs:
                all_results.extend(run.get("results", []))

            # Count findings per severity
            findings_by_severity = {sev: 0 for sev in severity_order}
            for res in all_results:
                # default 'warning'
                level = res.get("level", "warning").lower()
                sev = sarif_to_severity.get(level, "moderate")
                findings_by_severity[sev] += 1

            total_findings = len(all_results)

            # Extract detailed findings for template display
            detailed_findings = parse_sarif_findings(sarif_data)

            data[repo_name] = {
                "language": language,
                "description": repo_description,
                "sarif": sarif_data,
                "findings_count": total_findings,
                "findings_by_severity": findings_by_severity,
                "findings": detailed_findings,
            }
            print(f"  Found {total_findings} issues")

        except subprocess.CalledProcessError as e:
            print(f"Code scan failed for {repo_name}: {e.stderr}")
            data[repo_name] = {
                "error": str(e),
                "findings_count": 0,
                "findings_by_severity": {sev: 0 for sev in severity_order},
                "findings": [],
            }

        except Exception as e:
            print(f"Unexpected error scanning {repo_name}: {e}")
            data[repo_name] = {
                "error": str(e),
                "findings_count": 0,
                "findings_by_severity": {sev: 0 for sev in severity_order},
                "findings": [],
            }

    global_summary = aggregate_global_summary(data)

    generate_html_report("code", {
        "data": data,
        "severity_order": severity_order,
        "severity_emojis": severity_emojis,
        "global_summary": global_summary,
    }, output_path)
