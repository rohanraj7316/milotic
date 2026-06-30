"""FastMCP entrypoint."""

import os

from dotenv import load_dotenv

from app import mcp
from utils.logging import logger, setup_logging

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

def main() -> None:
    logger.info("server_starting", name="Milotic", version="0.1.0")
    mcp.run()

if __name__ == "__main__":
    main()
