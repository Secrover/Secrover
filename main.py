import time
from pathlib import Path
from dotenv import load_dotenv
from os import getenv

from secrover.config import load_config
from secrover.audits.dependencies import check_dependencies
from secrover.audits.code import check_code
from secrover.audits.domains import check_domains
from secrover.git import clone_repos
from secrover.report import generate_html_report
from secrover.constants import VERSION
from secrover.exporter import export_reports


def main():
    start_time = time.perf_counter()  # Start timer

    # Env vars
    load_dotenv()
    config_path = Path(getenv("CONFIG_FILE")).resolve()
    output_path = Path(getenv("OUTPUT_DIR")).resolve()
    repos_path = Path(getenv("REPOS_DIR")).resolve()

    token = getenv("GITHUB_TOKEN")

    export_enabled = getenv("EXPORT_ENABLED").lower() in ("true", "1", "yes")
    rclone_remotes = [r.strip() for r in getenv("RCLONE_REMOTES").split(",") if r.strip()]
    rclone_path = getenv("RCLONE_PATH")

    # Load config
    try:
        config = load_config(config_path)
        if config is None:
            raise ValueError("No config found")
    except Exception as e:
        print(f"Error loading config: {e}")
        exit(1)

    print(f"----- Secrover ({VERSION}) -----")

    print(f"- Using config: {config_path}")
    print(f"- Reports will be saved in: {output_path}")

    project = config.get("project", [])
    repos = config.get("repos", [])
    domains = config.get("domains", [])

    # Clone repos
    print("\n# Clone repos")
    if repos:
        repos = clone_repos(repos_path, repos, token)
    else:
        print("No repositories to clone.")

    enabled_checks = {
        "dependencies": bool(repos),
        "code": bool(repos),
        "domains": bool(domains),
    }

    # Audits
    print("\n# Launching checks")

    # 1 - Dependencies
    if repos:
        print("\n1 / Dependencies check")
        dependencies_summary = check_dependencies(
            project, repos, repos_path, output_path, enabled_checks)
    else:
        print("\n1 / Dependencies check skipped (no repositories).")
        dependencies_summary = None

    # 2 - Code
    if repos:
        print("\n2 / Code check")
        code_summary = check_code(project, repos, repos_path, output_path, enabled_checks)
    else:
        print("\n2 / Code check skipped (no repositories).")
        code_summary = None

    # 3 - Domains
    if domains:
        print("\n3 / Domains check")
        domains_summary = check_domains(
            project, domains, output_path, enabled_checks)
    else:
        print("\n3 / Domains check skipped (no domains).")
        domains_summary = None

    # Only generate the main report if any check was run
    if any(enabled_checks.values()):
        generate_html_report("index", {
            "project": project,
            "dependencies_summary": dependencies_summary,
            "code_summary": code_summary,
            "domains_summary": domains_summary,
            "enabled_checks": enabled_checks,
        }, output_path)

        # Remote Export
        if export_enabled:
            print("\n# Remote Export")
            export_reports(output_path, rclone_remotes, rclone_path)
    else:
        print("\nNo checks were enabled, skipping report generation.")

    end_time = time.perf_counter()  # End timer
    seconds = end_time - start_time

    print(f"\nAll checks have finished in {seconds:.2f} seconds.")


if __name__ == "__main__":
    main()
