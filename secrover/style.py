import click


class CLIStyle:
    """Reusable CLI styling helpers for consistent output across the project."""

    @staticmethod
    def _format_message(message: str, indent: int = 0, **kwargs) -> str:
        indent_str = "  " * indent  # 2 spaces per indent level
        return f"{indent_str}{message}"

    @staticmethod
    def normal(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.echo(formatted, **kwargs)

    @staticmethod
    def success(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(formatted, fg="green", bold=True, **kwargs)

    @staticmethod
    def error(message: str, indent: int = 0, **kwargs) -> None:
        kwargs.setdefault("err", True)
        formatted = CLIStyle._format_message(message, indent)
        click.secho(formatted, fg="red", bold=True, **kwargs)

    @staticmethod
    def warning(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(formatted, fg="yellow", bold=True, **kwargs)

    @staticmethod
    def info(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(formatted, fg="blue", **kwargs)

    @staticmethod
    def debug(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(formatted, fg="magenta", **kwargs)

    @staticmethod
    def h1(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(f"{formatted}\n", fg="cyan", bold=True, underline=True, **kwargs)

    @staticmethod
    def h2(message: str, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(message, indent)
        click.secho(f"{formatted}\n", fg="magenta", bold=True, **kwargs)

    @staticmethod
    def separator(char: str = "-", length: int = 50, indent: int = 0, **kwargs) -> None:
        formatted = CLIStyle._format_message(f"\n{char * length}\n", indent)
        click.echo(formatted, **kwargs)

    @staticmethod
    def line_return(**kwargs) -> None:
        click.echo("", **kwargs)


style = CLIStyle()
