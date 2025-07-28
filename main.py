import argparse
import yaml
import os
from git import Repo

from secrover.config import load_config
from secrover.audits import run_language_audits
from secrover.report import generate_html_report_from_template
from secrover.git import clone_repos, get_repo_name_from_url
from secrover.languages import detect_language_by_files


def main():
    parser = argparse.ArgumentParser(description="Secrover Security Scanner")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to config YAML file"
    )
    parser.add_argument(
        "-o", "--output",
        default="output/",
        help="Path to output folder"
    )

    args = parser.parse_args()

    config_path = args.config
    output_path = args.output

    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(e)
        exit(1)

    print(f"Using config: {config_path}")
    print(f"Report will be saved to: {output_path}")

    repos = config["repos"]
    base_dir = "repos"

    clone_repos(repos, base_dir=base_dir)

    all_results = {}
    for repo in repos:
        repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
        repo_description = repo.get("description") or ""
        repo_path = os.path.join(base_dir, repo_name)

        language = detect_language_by_files(repo_path)
        print(f"Detected language(s) for '{repo_name}': {language}")

        audit_results = run_language_audits(language, repo_path, repo_name)
        all_results[repo_name] = {
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

    generate_html_report_from_template(all_results, output_path)

    print("All repos processed.")


if __name__ == "__main__":
    main()
