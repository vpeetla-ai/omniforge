
import pytest
from omniforge.mcp.bridge import call_tool, list_tools


def test_list_tools():
    tools = list_tools()
    assert "mcp_time" in tools
    assert "mcp_calc" in tools


@pytest.mark.asyncio
async def test_calc():
    out = await call_tool("mcp_calc", {"expression": "3*7"})
    assert out["result"]["value"] == 21
