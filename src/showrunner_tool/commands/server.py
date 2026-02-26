import typer
import uvicorn
from showrunner_tool.utils.display import console

app = typer.Typer()

@app.command("start")
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Start the Showrunner Studio API server."""
    console.print(f"[bold green]Starting Showrunner Studio API on http://{host}:{port}[/]")
    # uvicorn expects an import string for the app
    uvicorn.run(
        "showrunner_tool.server.app:app",
        host=host,
        port=port,
        reload=reload
    )
