import base64
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime


def get_base64_image(path: Path) -> str:
    with path.open("rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def generate_html_report(report_type: str, results, output_path: Path):
    template_dir = Path("templates")
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(f"{report_type}.html")

    context = {
        "audit_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "logo_b64": get_base64_image(Path("assets/secrover.svg")),
        "favicon_b64": get_base64_image(Path("assets/favicon.svg")),
    }
    context.update(results)

    output_html = template.render(context)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / f"{report_type}_report.html"
    report_file.write_text(output_html, encoding="utf-8")

    print(f"{report_type.capitalize()} HTML report generated in \"{output_path}\" folder.")
