import os
from git import Repo

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
            print(f"Repo '{repo_name}' already exists at {dest_path}, skipping clone.")
            continue

        print(f"Cloning {repo_url} into {dest_path} (branch {branch}) ...")
        Repo.clone_from(repo_url, dest_path, branch=branch)
