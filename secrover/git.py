from git import Repo
from git.exc import GitCommandError

from secrover.constants import REPOS_FOLDER


def get_repo_name_from_url(url):
    url = url.rstrip('/')
    repo_name = url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def clone_repos(repos):
    valid_repos = []
    REPOS_FOLDER.mkdir(parents=True, exist_ok=True)
    for repo in repos:
        repo_url = repo["url"]
        branch = repo.get("branch", "main")
        repo_name = repo.get("name") or get_repo_name_from_url(repo_url)
        dest_path = REPOS_FOLDER / repo_name

        if dest_path.exists():
            valid_repos.append(repo)
            print(
                f"Repo '{repo_name}' already exists at {dest_path}, skipping clone.")
            continue

        print(f"Cloning {repo_url} into {dest_path} (branch {branch}) ...")
        try:
            Repo.clone_from(repo_url, dest_path, branch=branch)
            valid_repos.append(repo)
        except Exception as error:
            print(f"Can't clone {repo_url}:", error)
    return valid_repos
