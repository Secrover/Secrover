import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from secrover.constants import DEPENDENCIES_SEVERITY_ORDER
from secrover.git import get_repo_name_from_url
from secrover.report import generate_html_report
from secrover.style import style

sarif_to_severity = {
    "error": "high",
    "warning": "moderate",
    "note": "low",
    "none": "info",
}

# ossatrisk ecosystems: manifest file to look for in each repo
OSSATRISK_ECOSYSTEMS = {
    "js": "package.json",
    "php": "composer.json",
}
OSSATRISK_EXCLUDED_DIRS = {".git", "node_modules", "vendor"}


def ossatrisk_score_to_severity(score) -> str:
    # ossatrisk score is a 1-100 percentile among flagged risky packages
    if score >= 80:
        return "high"
    if score >= 60:
        return "moderate"
    if score >= 40:
        return "low"
    return "info"


def init_severity_counts():
    return {sev: 0 for sev in DEPENDENCIES_SEVERITY_ORDER}


def normalize_severity(severity: str):
    sev = (severity or "info").lower()
    if sev in DEPENDENCIES_SEVERITY_ORDER:
        return sev
    return sarif_to_severity.get(sev, "info")


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
        repo_url = repo.get("url")
        repo_name = repo.get("name") or get_repo_name_from_url(repo_url)
        style.normal(f"[{i}/{total}] Scanning repo: {repo_name}...")
        repo_description = repo.get("description") or ""
        repo_path = repos_path / repo_name
        audit_results = run_audit(repo_path)
        risky_summary = run_ossatrisk(repo_path)
        if audit_results is None and risky_summary is not None:
            audit_results = build_audit_summary(init_severity_counts(), {})
        if audit_results is not None and risky_summary is not None:
            audit_results.update(risky_summary)
        data[repo_name] = {
            "url": repo_url,
            "description": repo_description,
            "audit": audit_results,
        }
        if audit_results and audit_results["total_vulnerabilities"] > 0:
            style.info(
                f"Found {audit_results['total_vulnerabilities']} issues", indent=1
            )
        else:
            style.info("No issues found", indent=1)
        if risky_summary and risky_summary["total_risky_packages"] > 0:
            style.info(
                f"Found {risky_summary['total_risky_packages']} risky packages (ossatrisk)",
                indent=1,
            )

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
            [
                "osv-scanner",
                "scan",
                "source",
                "--format",
                "sarif",
                "-r",
                str(repo_path),
                "--no-ignore",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        if not result.stdout.strip():
            # osv-scanner exits 128 when it finds no package sources to scan,
            # and 0/1 on normal completions (0 = no findings, 1 = findings).
            # In all three cases the scan ran: there is simply nothing to report.
            if result.returncode == 128:
                style.debug(
                    f"osv-scanner found no packages to scan in {repo_path}",
                    indent=1,
                )
                return build_audit_summary(
                    init_severity_counts(),
                    {},
                    {"note": "No dependencies files found - nothing to audit."},
                )
            if result.returncode in (0, 1):
                style.debug(f"osv-scanner returned no output in {repo_path}", indent=1)
                return build_audit_summary(init_severity_counts(), {})
            style.error(
                f"osv-scanner exited with code {result.returncode}: "
                f"{result.stderr.strip()}",
                indent=1,
            )
            return None

        try:
            sarif_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            style.error(f"Failed to parse SARIF output: {e}", indent=1)
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
    except subprocess.TimeoutExpired:
        style.error(
            "The operation was aborted because it exceeded the allowed time limit.",
            indent=1,
        )
    except Exception as e:
        style.error(f"osv-scanner failed unexpectedly: {e}", indent=1)

    return None


def find_ossatrisk_manifests(repo_path: Path, manifest_name: str):
    return [
        p
        for p in repo_path.rglob(manifest_name)
        if not OSSATRISK_EXCLUDED_DIRS & set(p.relative_to(repo_path).parts[:-1])
    ]


def run_ossatrisk(repo_path: Path):
    """
    Run ossatrisk on every manifest found in the repo (js and php ecosystems)
    and return a summary of risky packages suitable for templating in HTML.
    Returns None if the tool is not available.
    """
    try:
        risky = {}
        for ecosystem, manifest_name in OSSATRISK_ECOSYSTEMS.items():
            for manifest_path in find_ossatrisk_manifests(repo_path, manifest_name):
                try:
                    result = subprocess.run(
                        [
                            "ossatrisk",
                            "scan",
                            "--ecosystem",
                            ecosystem,
                            "--format",
                            "json",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=60,
                        cwd=manifest_path.parent,
                    )
                except subprocess.TimeoutExpired:
                    style.error(
                        "ossatrisk scan timed out "
                        f"for {manifest_path.relative_to(repo_path)}",
                        indent=1,
                    )
                    continue

                # ossatrisk prints log lines on stdout around the JSON payload,
                # so extract the array starting at the first '['
                idx = result.stdout.find("[")
                if idx == -1:
                    continue  # no manifest matched or error message only
                try:
                    packages, _ = json.JSONDecoder().raw_decode(result.stdout[idx:])
                except json.JSONDecodeError as e:
                    style.error(
                        f"Failed to parse ossatrisk output for "
                        f"{manifest_path.relative_to(repo_path)}: {e}",
                        indent=1,
                    )
                    continue

                rel_file = str(manifest_path.relative_to(repo_path))
                for pkg in packages:
                    name = pkg.get("name")
                    if not name:
                        continue
                    score = pkg.get("score") or 0
                    key = (ecosystem, name)
                    if key in risky and risky[key]["score"] >= score:
                        continue
                    risky[key] = {
                        "name": name,
                        "ecosystem": ecosystem,
                        "score": score,
                        "severity": ossatrisk_score_to_severity(score),
                        "cves_count": pkg.get("cves_count") or 0,
                        "abandoned": bool(pkg.get("abandoned")),
                        "suggested": pkg.get("suggested"),
                        "file": rel_file,
                    }
    except FileNotFoundError:
        style.error(
            "ossatrisk is not installed, skipping package risk assessment.", indent=1
        )
        return None

    risky_list = sorted(risky.values(), key=lambda p: (-p["score"], p["name"]))
    risky_counts = init_severity_counts()
    for pkg in risky_list:
        risky_counts[pkg["severity"]] += 1

    return {
        "total_risky_packages": len(risky_list),
        "risky_by_severity": risky_counts,
        "risky_packages": risky_list,
    }


def build_audit_summary(severity_counts, packages_by_file, extras=None):
    all_packages = [pkg for pkgs in packages_by_file.values() for pkg in pkgs]

    result = {
        "total_vulnerabilities": sum(severity_counts.values()),
        "vulnerabilities_by_severity": severity_counts,
        "packages_by_file": dict(packages_by_file),
        "packages_impacted": sorted(
            all_packages,
            key=lambda p: (severity_rank(p["severity"]), p["name"]),
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
            global_counts["risky_total"] += audit.get("total_risky_packages", 0)
    global_counts["total"] = sum(
        global_counts[level] for level in DEPENDENCIES_SEVERITY_ORDER
    )
    return global_counts
