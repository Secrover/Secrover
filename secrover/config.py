import os
import yaml

def load_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file {path} does not exist.")
    with open(path, "r") as file:
        return yaml.safe_load(file)
