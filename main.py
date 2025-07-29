import argparse

from pathlib import Path

from secrover.config import load_config
from secrover.audits.vulnerabilities import check_vulnerabilities
from secrover.audits.domains import check_domains
from secrover.git import clone_repos


def main():
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

    print(f"Using config: {config_path}")
    print(f"Report will be saved to: {output_path}")

    repos = config["repos"]
    domains = config["domains"]

    #  Clone repos
    clone_repos(repos)

    # Audits

    # 1 - Vulnerabilities
    check_vulnerabilities(repos, output_path)

    # 2 - Domains
    check_domains(domains, output_path)


if __name__ == "__main__":
    main()
