from typer import Typer

from forecasting_harness import __version__


app = Typer()


@app.callback()
def main_command() -> None:
    return None


@app.command()
def version() -> None:
    print(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
