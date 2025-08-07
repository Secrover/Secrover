from pathlib import Path


def detect_language_by_files(repo_path: Path):
    try:
        files = set(p.name for p in repo_path.iterdir() if p.is_file())
    except FileNotFoundError:
        return None

    lang_files = {
        "JavaScript": {"package.json"},
        "PHP": {"composer.json"},
        "Python": {"requirements.txt", "pyproject.toml"},
    }

    detected = [lang for lang, markers in lang_files.items()
                if markers & files]
    return ", ".join(detected) if detected else None
