import subprocess

from secrover.helpers import extract_semver


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
        except subprocess.CalledProcessError:
            continue
    return f"Could not determine version for {tool_name}."
