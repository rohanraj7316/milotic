"""FastMCP app instance configuration."""

from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

# Initialize FastMCP with the FileSystemProvider for automatic tool discovery
mcp = FastMCP(
    "Milotic",
    providers=[
        FileSystemProvider(
            root=Path(__file__).parent / "components",
            reload=True  # Enables hot-reloading for rapid development
        )
    ]
)
