import subprocess
from pathlib import Path
from datetime import datetime, timezone
import re

from secrover.style import style


def expand_shell_date(path: Path) -> Path:
    def replacer(match):
        fmt = match.group(1)
        return datetime.now(timezone.utc).strftime(fmt)

    pattern = re.compile(r"\$\(\s*date\s+\+([^)]+)\s*\)")
    expanded_str = pattern.sub(replacer, str(path))
    return Path(expanded_str).resolve()


def export_reports(output_dir: Path, remotes: list[str], remote_path: Path):
    if not remotes:
        style.error("RCLONE_REMOTES not configured.")
        return

    # Expand any $(date +FORMAT) expressions
    target_path = expand_shell_date(remote_path)

    for remote in remotes:
        target = f"{remote}:{target_path}/"
        style.normal(f"Uploading {output_dir} → {target}")

        cmd = [
            "rclone",
            "copy",
            str(output_dir),
            target,
            "-v",
            "--create-empty-src-dirs",
        ]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            style.success(f"Export to {remote} successful.")
        else:
            style.error(f"Export to {remote} failed with code {result.returncode}.")
