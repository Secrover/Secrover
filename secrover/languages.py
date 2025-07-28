import os

def detect_language_by_files(repo_path):
    try:
        files = set(os.listdir(repo_path))
    except FileNotFoundError:
        return "Unknown (repo path not found)"

    lang_files = {
        "JavaScript": {"package.json", "yarn.lock"},
        "PHP": {"composer.json"},
    }

    detected = [lang for lang, markers in lang_files.items() if markers & files]
    return ", ".join(detected) if detected else "Unknown"
