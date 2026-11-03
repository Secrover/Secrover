from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from git import GitCommandError, Repo

from secrover.constants import MAX_PARALLEL_CHECKS
from secrover.style import style


def get_repo_name_from_url(url):
    url = url.rstrip("/")
    repo_name = url.split("/")[-1]
    repo_name = repo_name.removesuffix(".git")
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


def _sync_repo(repo, repos_path: Path, token) -> bool:
    original_url = repo["url"]
    normalized_url = normalize_repo_url(original_url)
    if token:
        normalized_url = inject_token_into_url(normalized_url, token)
    branch = repo.get("branch", "main")
    repo_name = repo.get("name") or get_repo_name_from_url(original_url)
    dest_path = repos_path / repo_name

    if dest_path.exists():
        try:
            local_repo = Repo(dest_path)
            local_repo.git.reset("--hard")
            pull_info = local_repo.remotes.origin.pull(branch)

            # Count updates
            changes_count = sum(
                1 for info in pull_info if info.flags & info.FAST_FORWARD
            )
            if changes_count:
                style.info(f"Pulled {changes_count} updates for {repo_name}", indent=1)
            else:
                style.info(f"No updates for {repo_name}", indent=1)
            return True
        except GitCommandError as error:
            style.error(f"Failed to pull {repo_name}: {error}", indent=1)
            return False

    try:
        Repo.clone_from(normalized_url, dest_path, branch=branch, single_branch=True)
        style.info(f"Cloned {repo_name}", indent=1)
        return True
    except GitCommandError as error:
        style.error(f"Can't clone {normalized_url}: {error}", indent=1)
        return False


def clone_repos(repos_path: Path, repos, token):
    repos_path.mkdir(parents=True, exist_ok=True)
    total = len(repos)
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CHECKS) as executor:
        futures = {}
        for i, repo in enumerate(repos):
            repo_name = repo.get("name") or get_repo_name_from_url(repo["url"])
            style.normal(f"[{i + 1}/{total}] Syncing repo: {repo_name}...")
            futures[executor.submit(_sync_repo, repo, repos_path, token)] = i
        succeeded = set()
        for future in as_completed(futures):
            if future.result():
                succeeded.add(futures[future])
    return [repo for i, repo in enumerate(repos) if i in succeeded]
