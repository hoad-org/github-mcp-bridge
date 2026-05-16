"""MCP server for GitHub bridge."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from .gh_client import GitHubClient

# Initialize server
server = Server("github-bridge")
github = GitHubClient()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list_repos",
            description="List repositories in an organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "org": {"type": "string", "description": "Organization name"},
                    "limit": {"type": "integer", "description": "Max repos to return", "default": 100},
                },
                "required": ["org"],
            },
        ),
        Tool(
            name="get_repo",
            description="Get repository details",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository (owner/name)"},
                },
                "required": ["repo"],
            },
        ),
        Tool(
            name="list_prs",
            description="List pull requests in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository (owner/name)"},
                    "state": {"type": "string", "description": "PR state (open/closed/merged)", "default": "open"},
                },
                "required": ["repo"],
            },
        ),
        Tool(
            name="get_pr",
            description="Get pull request details",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository (owner/name)"},
                    "number": {"type": "integer", "description": "PR number"},
                },
                "required": ["repo", "number"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_repos":
            result = github.list_repos(
                org=arguments["org"],
                limit=arguments.get("limit", 100),
            )
            return [TextContent(type="text", text=str(result))]
        elif name == "get_repo":
            result = github.get_repo(repo=arguments["repo"])
            return [TextContent(type="text", text=str(result))]
        elif name == "list_prs":
            result = github.list_prs(
                repo=arguments["repo"],
                state=arguments.get("state", "open"),
            )
            return [TextContent(type="text", text=str(result))]
        elif name == "get_pr":
            result = github.get_pr(repo=arguments["repo"], pr_number=arguments["number"])
            return [TextContent(type="text", text=str(result))]
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main() -> None:
    """Run the MCP server."""
    async with server:
        print("GitHub MCP bridge started")
        await server.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
