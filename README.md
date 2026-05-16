# GitHub MCP Bridge

An MCP (Model Context Protocol) server that bridges Claude Code to your cloud GitHub connector via the local `gh` CLI.

## What It Does

- Exposes GitHub operations as native MCP tools in Claude Code
- Uses your authenticated `gh` CLI (same as your cloud connector)
- Provides: list repos, get repo details, list PRs, get PR details
- Properly handles authentication and errors

## Setup

1. Install the package:
```bash
cd /Users/craighoad/Repos/github-mcp-bridge
pip install -e .
```

2. The MCP is automatically registered in `~/.claude/settings.json`

3. Restart Claude Code to load it

## Usage

Once loaded, you'll have access to GitHub tools in Claude Code:
- `list_repos` - List repositories in an org
- `get_repo` - Get repository details
- `list_prs` - List pull requests
- `get_pr` - Get PR details

## Architecture

```
Claude Code
    ↓
MCP Server (github-mcp-bridge)
    ↓
GitHub CLI (gh) - already authenticated
    ↓
Cloud GitHub Connector
```

## Requirements

- `gh` CLI installed and authenticated
- Python 3.12+
- MCP 1.0.0+
