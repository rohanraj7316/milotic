import pytest
from milotic.app import mcp

@pytest.mark.asyncio
async def test_tool_registration():
    """Verify that tools are correctly registered via FileSystemProvider."""
    # Check if system_get_health is present
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "system_get_health" in tool_names

@pytest.mark.asyncio
async def test_tool_naming_convention():
    """Ensure all registered tools follow the category_action_entity pattern."""
    tools = await mcp.list_tools()
    for tool in tools:
        name = tool.name
        # Simple check for the pattern: 2+ underscores
        # We expect names like 'system_get_health', 'market_get_quote'
        parts = name.split("_")
        assert len(parts) >= 3, f"Tool name '{name}' does not follow 'category_action_entity' convention."
        
        # Check specific categories if needed
        allowed_categories = {"system", "market", "account", "trading", "research"}
        assert parts[0] in allowed_categories, f"Unknown category '{parts[0]}' in tool '{name}'."
