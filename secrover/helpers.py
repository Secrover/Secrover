import re


def extract_semver(version_str: str) -> str:
    pattern = r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9\.]+)?(?:\+[a-zA-Z0-9\.]+)?"
    match = re.search(pattern, version_str)
    return match.group(0) if match else version_str


def country_code_to_emoji(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "❓"
    # Unicode flag calculation
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)
