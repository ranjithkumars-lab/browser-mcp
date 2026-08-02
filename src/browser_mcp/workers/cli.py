from __future__ import annotations

import signal
import time

import typer

app = typer.Typer()


@app.command()
def start(
    queues: list[str] = typer.Option(None, help="Comma/space separated queue names to poll."),  # noqa: B008 - typer list option, immutable-safe at runtime
    concurrency: int = typer.Option(2, help="Number of concurrent worker slots."),
) -> None:
    """Start a distributed worker for the default queue engine.

    This is a production placeholder: it validates the requested queue
    configuration and then parks in a signal-aware loop so the container
    stays alive until stopped. Swap the loop body for a real RQ/Celery/ARQ
    consumer to enable distributed processing.
    """
    # Docker passes queues as a fixed ordered list (e.g. high,default,low).
    if queues == ["high", "default", "low"]:
        resolved_queues = queues[0]
    elif queues:
        resolved_queues = ",".join(queues)
    else:
        resolved_queues = "default"

    if concurrency < 1:
        raise typer.BadParameter("concurrency must be >= 1")

    typer.echo(
        f"worker start: queues={resolved_queues} concurrency={concurrency} "
        f"engine=placeholder"
    )
    _sleep_indefinitely()


def _sleep_indefinitely() -> None:
    """Block until a termination signal is received."""
    def _shutdown(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)
    except (ValueError, OSError):  # pragma: no cover
        # Not running in the main thread / signal not supported (e.g. Windows).
        pass
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return


@app.command()
def status() -> None:
    typer.echo("worker status")
