# Contributing to Milotic

This project is a high-scale Trading MCP Gateway designed to support 150+ APIs. To maintain quality and consistency, all new tools and features must follow these standards.

## Tool Development Standards

### 1. Naming Convention
All tools must follow the `category_action_entity` pattern.
- **Example**: `market_get_quote`, `account_list_positions`, `trading_post_order`.
- **Allowed Categories**: `system`, `market`, `account`, `trading`, `research`.

### 2. Mandatory Decorators
Every tool must use both the `@tool` decorator from `fastmcp.tools` and the custom `@milotic_tool` decorator.
```python
from fastmcp.tools import tool
from milotic.utils.decorators import milotic_tool

@tool()
@milotic_tool
def category_action_entity(arg: str) -> dict:
    ...
```

### 3. Pydantic Validation
Use Pydantic models for complex request/response payloads. This ensures the LLM receives clean, validated data.

### 4. Docstrings
Docstrings are the primary way the LLM understands your tool.
- **Must** include a clear description of *what* the tool does.
- **Must** explain *why* an LLM would want to use it.
- **Should** mention any rate-limiting or specific constraints.

## Project Structure
- `src/milotic/mcp/`: Place new tool files here. They are automatically discovered.
- `src/milotic/services/`: Place core business logic, technical analysis, and signal processing here.
- `src/milotic/api/`: Place backend HTTP clients (using `httpx`) here.

## Testing
Always add a test case in `tests/` for any new tool. Run `uv run pytest` to verify your changes.
