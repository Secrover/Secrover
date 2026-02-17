import base64
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from datetime import datetime
from secrover.constants import VERSION
from secrover.tools import get_tool_version


def pluralize(count, singular, plural=None):
    if count == 1:
        return singular

    if plural is None:
        # Handle words ending in consonant + y (e.g., "baby" -> "babies")
        if singular.endswith("y") and len(singular) > 1:
            # Check if the letter before 'y' is a consonant
            if singular[-2] not in "aeiou":
                plural = singular[:-1] + "ies"
            else:
                # Vowel + y just adds 's' (e.g., "day" -> "days")
                plural = singular + "s"
        else:
            plural = singular + "s"

    return plural


def get_base64_image(path: Path) -> str:
    with path.open("rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def generate_html_report(report_type: str, results: dict, output_path: Path):
    template_dir = Path("templates")
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml"),
            default_for_string=True,
        ),
    )
    env.filters["pluralize"] = pluralize

    template = env.get_template(f"{report_type}.html")

    context = {
        "version": VERSION,
        "osv_version": get_tool_version("osv-scanner"),
        "opengrep_version": get_tool_version("opengrep"),
        "audit_datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "logo_b64": get_base64_image(Path("assets/secrover.svg")),
        "favicon_b64": get_base64_image(Path("assets/favicon.svg")),
        "git_icon_b64": get_base64_image(Path("assets/git-repo.svg")),
    }
    context.update(results)

    output_html = template.render(context)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / (
        f"{report_type}.html"
        if report_type == "index"
        else f"{report_type}_report.html"
    )

    report_file.write_text(output_html, encoding="utf-8")

    print(f"\n✅ {report_type.capitalize()} HTML report generated.")
