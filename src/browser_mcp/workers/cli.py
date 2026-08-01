import typer

app = typer.Typer()


@app.command()
def start() -> None:
    typer.echo("worker start")


@app.command()
def status() -> None:
    typer.echo("worker status")
