import subprocess
from importlib.metadata import PackageNotFoundError, version

from secrover.helpers import extract_semver


def get_python_package_version(package_name: str) -> str:
    """Return the installed version of a Python package (e.g. ossatrisk),
    falling back to the CLI if the package is not installed as a module."""
    try:
        return version(package_name)
    except PackageNotFoundError:
        return get_tool_version(package_name)


def get_tool_version(tool_name: str) -> str:
    version_flags = ["--version", "-v", "version"]
    for flag in version_flags:
        try:
            result = subprocess.run(
                [tool_name, flag],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                return extract_semver(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return f"Could not determine version for {tool_name}."
