import yaml
import os
from git import Repo
from string import Template

from secrover.audits import run_language_audits
from secrover.report import generate_html_report_from_template


def get_repo_name_from_url(url):
    url = url.rstrip('/')
    repo_name = url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def clone_repos(repos, base_dir="repos"):
    os.makedirs(base_dir, exist_ok=True)

    for repo in repos:
        repo_url = repo["url"]
        branch = repo.get("branch", "main")
        repo_name = repo.get("name") or get_repo_name_from_url(repo_url)
        dest_path = os.path.join(base_dir, repo_name)

        if os.path.exists(dest_path):
            print(
                f"Repo '{repo_name}' already exists at {dest_path}, skipping clone.")
            continue

        print(f"Cloning {repo_url} into {dest_path} (branch {branch}) ...")
        Repo.clone_from(repo_url, dest_path, branch=branch)


def detect_language_by_files(repo_path):
    try:
        files = set(os.listdir(repo_path))
    except FileNotFoundError:
        return "Unknown (repo path not found)"

    # Mapping of language to their typical dependency files
    lang_files = {
        "JavaScript": {"package.json", "yarn.lock"},
        "PHP": {"composer.json"},
    }

    detected_languages = []

    for lang, dep_files in lang_files.items():
        if dep_files.intersection(files):
            detected_languages.append(lang)

    if not detected_languages:
        return "Unknown"

    return ", ".join(detected_languages)


def main():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

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

    generate_html_report_from_template(all_results)

    print("All repos processed.")


if __name__ == "__main__":
    main()
