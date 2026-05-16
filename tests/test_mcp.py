"""Tests for MCP server."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from github_mcp.mcp import list_tools, call_tool


@pytest.mark.asyncio
async def test_list_tools() -> None:
    """Test that list_tools returns expected tool definitions."""
    tools = await list_tools()
    tool_names = [t.name for t in tools]

    assert "list_repos" in tool_names
    assert "get_repo" in tool_names
    assert "list_prs" in tool_names
    assert "get_pr" in tool_names


@pytest.mark.asyncio
async def test_call_tool_list_repos() -> None:
    """Test calling list_repos tool."""
    with patch("github_mcp.mcp.github") as mock_github:
        mock_github.list_repos.return_value = [{"name": "test-repo"}]

        result = await call_tool("list_repos", {"org": "test-org"})

        assert len(result) == 1
        assert "test-repo" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_unknown() -> None:
    """Test calling unknown tool."""
    result = await call_tool("unknown_tool", {})

    assert len(result) == 1
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_error_handling() -> None:
    """Test error handling in tool calls."""
    with patch("github_mcp.mcp.github") as mock_github:
        mock_github.list_repos.side_effect = RuntimeError("API error")

        result = await call_tool("list_repos", {"org": "test-org"})

        assert len(result) == 1
        assert "Error" in result[0].text
