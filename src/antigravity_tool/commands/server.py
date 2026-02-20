import typer
import uvicorn
from antigravity_tool.utils.display import console

app = typer.Typer()

@app.command("start")
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Start the Antigravity Studio API server."""
    console.print(f"[bold green]Starting Antigravity Studio API on http://{host}:{port}[/]")
    # uvicorn expects an import string for the app
    uvicorn.run(
        "antigravity_tool.server.app:app",
        host=host,
        port=port,
        reload=reload
    )
