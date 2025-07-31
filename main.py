import argparse
import time
from pathlib import Path

from secrover.config import load_config
from secrover.audits.dependencies import check_dependencies
from secrover.audits.code import check_code
from secrover.audits.domains import check_domains
from secrover.git import clone_repos
from secrover.report import generate_html_report
from secrover.constants import VERSION


def main():
    start_time = time.perf_counter()  # Start timer

    # Program options
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

    config_path = Path(args.config).resolve()
    output_path = Path(args.output).resolve()

    # Load config
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(e)
        exit(1)

    print(f"----- Secrover (Version {VERSION}) -----")

    print(f"- Using config: {config_path}")
    print(f"- Reports will be saved in: {output_path}")

    repos = config["repos"]
    domains = config["domains"]

    #  Clone repos
    print("\n# Clone repos")
    repos = clone_repos(repos)

    # Audits
    print("\n# Launching checks")

    # 1 - Dependencies
    print("\n1 / Dependencies check")
    dependencies_summary = check_dependencies(repos, output_path)

    # 2 - Code
    print("\n2 / Code check")
    code_summary = check_code(repos, output_path)

    # 3 - Domains
    print("\n3 / Domains check")
    domains_summary = check_domains(domains, output_path)

    # Main report
    generate_html_report("index", {
        "dependencies_summary": dependencies_summary,
        "code_summary": code_summary,
        "domains_summary": domains_summary,
    }, output_path)

    end_time = time.perf_counter()  # End timer
    seconds = end_time - start_time

    print(f"\nAll check have finished in {seconds:.2f} seconds.")


if __name__ == "__main__":
    main()
