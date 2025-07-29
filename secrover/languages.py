from pathlib import Path


def detect_language_by_files(repo_path: Path):
    try:
        files = set(p.name for p in repo_path.iterdir() if p.is_file())
    except FileNotFoundError:
        return "Unknown (repo path not found)"

    lang_files = {
        "JavaScript": {"package.json", "yarn.lock"},
        "PHP": {"composer.json"},
    }

    detected = [lang for lang, markers in lang_files.items()
                if markers & files]
    return ", ".join(detected) if detected else "Unknown"
