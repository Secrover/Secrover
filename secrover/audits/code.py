import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from secrover.constants import CODE_SEVERITY_ORDER, MAX_PARALLEL_CHECKS
from secrover.git import get_repo_name_from_url
from secrover.report import generate_html_report
from secrover.style import style

sarif_to_severity = {
    "error": "high",
    "warning": "moderate",
    "note": "low",
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
                loc = (
                    locations[0]
                    .get("physicalLocation", {})
                    .get("artifactLocation", {})
                    .get("uri", "Unknown file")
                )
                start_line = (
                    locations[0]
                    .get("physicalLocation", {})
                    .get("region", {})
                    .get("startLine")
                )
            else:
                loc = "Unknown file"
                start_line = None

            findings.append(
                {
                    "severity": severity,
                    "rule_id": rule_id,
                    "message": message,
                    "location": {
                        "file": loc,
                        "line": start_line,
                    },
                }
            )
    return findings


def aggregate_global_summary(data):
    summary = {level: 0 for level in CODE_SEVERITY_ORDER}
    summary["total"] = 0

    for repo_data in data.values():
        findings_by_severity = repo_data.get("findings_by_severity", {})
        total_findings = repo_data.get("findings_count", 0)

        for level in CODE_SEVERITY_ORDER:
            summary[level] += findings_by_severity.get(level, 0)

        summary["total"] += total_findings

    return summary


def _scan_repo_code(repo, repos_path: Path):
    repo_url = repo.get("url")
    repo_name = repo.get("name") or get_repo_name_from_url(repo_url)
    repo_description = repo.get("description") or ""
    repo_path = repos_path / repo_name

    try:
        result = subprocess.run(
            ["opengrep", "scan", "--sarif"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        sarif_data = json.loads(result.stdout)
        runs = sarif_data.get("runs", [])

        # Flatten all results across runs
        all_results = []
        for run in runs:
            all_results.extend(run.get("results", []))

        # Count findings per severity
        findings_by_severity = {sev: 0 for sev in CODE_SEVERITY_ORDER}
        for res in all_results:
            # default 'warning'
            level = res.get("level", "warning").lower()
            sev = sarif_to_severity.get(level, "moderate")
            findings_by_severity[sev] += 1

        total_findings = len(all_results)

        # Extract detailed findings for template display
        detailed_findings = parse_sarif_findings(sarif_data)

        entry = {
            "url": repo_url,
            "description": repo_description,
            "findings_count": total_findings,
            "findings_by_severity": findings_by_severity,
            "findings": detailed_findings,
        }
        style.info(f"Found {total_findings} issues in {repo_name}", indent=1)

    except subprocess.TimeoutExpired as e:
        style.error(
            f"Scan of {repo_name} aborted: exceeded the allowed time limit.",
            indent=1,
        )
        entry = {
            "url": repo_url,
            "description": repo_description,
            "error": str(e),
            "findings_count": 0,
            "findings_by_severity": {sev: 0 for sev in CODE_SEVERITY_ORDER},
            "findings": [],
        }
    except subprocess.CalledProcessError as e:
        style.error(f"Code scan failed for {repo_name}: {e.stderr}", indent=1)
        entry = {
            "url": repo_url,
            "description": repo_description,
            "error": str(e),
            "findings_count": 0,
            "findings_by_severity": {sev: 0 for sev in CODE_SEVERITY_ORDER},
            "findings": [],
        }
    except Exception as e:
        style.error(f"Unexpected error scanning {repo_name}: {e}", indent=1)
        entry = {
            "url": repo_url,
            "description": repo_description,
            "error": str(e),
            "findings_count": 0,
            "findings_by_severity": {sev: 0 for sev in CODE_SEVERITY_ORDER},
            "findings": [],
        }

    return repo_name, entry


def check_code(project, repos, repos_path: Path, output_path: Path, enabled_checks):
    total = len(repos)
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CHECKS) as executor:
        futures = {}
        for i, repo in enumerate(repos, 1):
            repo_name = repo.get("name") or get_repo_name_from_url(repo.get("url"))
            style.normal(f"[{i}/{total}] Scanning repo: {repo_name}...")
            futures[executor.submit(_scan_repo_code, repo, repos_path)] = repo_name
        for future in as_completed(futures):
            repo_name, entry = future.result()
            results[repo_name] = entry
    # keep the original config order in the report
    data = {}
    for repo in repos:
        repo_name = repo.get("name") or get_repo_name_from_url(repo.get("url"))
        if repo_name in results:
            data[repo_name] = results[repo_name]

    summary = aggregate_global_summary(data)
    summary.update({"nbRepos": total})

    generate_html_report(
        "code",
        {
            "project": project,
            "data": data,
            "severity_order": CODE_SEVERITY_ORDER,
            "global_summary": summary,
            "enabled_checks": enabled_checks,
        },
        output_path,
    )

    return summary
