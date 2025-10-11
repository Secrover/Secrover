from git import Repo, GitCommandError
from secrover.constants import REPOS_FOLDER
from urllib.parse import urlparse, urlunparse


def get_repo_name_from_url(url):
    url = url.rstrip("/")
    repo_name = url.split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    return repo_name


def normalize_repo_url(url):
    if not url.endswith(".git"):
        return url + ".git"
    return url


def inject_token_into_url(url, token):
    # Only inject token if HTTPS url
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return url

    # Insert token as username in URL, e.g. https://<token>@github.com/...
    # We ignore username and password if already present.
    netloc = f"{token}@{parsed.netloc}"
    new_url = urlunparse(parsed._replace(netloc=netloc))
    return new_url


def clone_repos(repos, token):
    valid_repos = []
    REPOS_FOLDER.mkdir(parents=True, exist_ok=True)
    for repo in repos:
        original_url = repo["url"]
        normalized_url = normalize_repo_url(original_url)
        if token:
            normalized_url = inject_token_into_url(normalized_url, token)
        branch = repo.get("branch", "main")
        repo_name = repo.get("name") or get_repo_name_from_url(original_url)
        dest_path = REPOS_FOLDER / repo_name

        if dest_path.exists():
            try:
                print(f"Repo '{repo_name}' exists, pulling latest changes...")
                local_repo = Repo(dest_path)
                origin = local_repo.remotes.origin
                origin.pull(branch)
                valid_repos.append(repo)
            except GitCommandError as error:
                print(f"Failed to pull {repo_name}: {error}")
            continue

        print(f"Cloning {original_url} into {dest_path} (branch {branch}) ...")
        try:
            Repo.clone_from(
                normalized_url, dest_path, branch=branch, single_branch=True
            )
            valid_repos.append(repo)
        except GitCommandError as error:
            print(f"Can't clone {normalized_url}:", error)

    return valid_repos
