import subprocess
from pathlib import Path
from datetime import datetime, timezone
import re


def expand_shell_date(path: str) -> str:
    def replacer(match):
        fmt = match.group(1)
        return datetime.now(timezone.utc).strftime(fmt)

    pattern = re.compile(r"\$\(\s*date\s+\+([^)]+)\s*\)")
    return pattern.sub(replacer, path)


def export_reports(output_dir: Path, remotes: list[str], remote_path: str):
    if not remotes:
        print("[export] RCLONE_REMOTES not configured.")
        return

    if not remote_path:
        print("[export] RCLONE_PATH not configured.")
        return

    # Expand any $(date +FORMAT) expressions
    target_path = expand_shell_date(remote_path.rstrip("/"))

    for remote in remotes:
        target = f"{remote}:{target_path}/"
        print(f"[export] Uploading {output_dir} → {target}")

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
            print(f"[export] ✅ Export to {remote} successful.")
        else:
            print(
                f"[export] ❌ Export to {remote} failed with code {result.returncode}."
            )
