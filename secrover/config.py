from pathlib import Path
import yaml


def load_config(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist.")
    with path.open("r") as file:
        return yaml.safe_load(file)
