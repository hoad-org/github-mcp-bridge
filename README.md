# GitHub MCP Bridge

An MCP (Model Context Protocol) server that bridges Claude Code to GitHub by wrapping the authenticated local `gh` CLI. This enables native GitHub operations within Claude Code sessions while leveraging your existing GitHub authentication.

## The Problem This Solves

Claude has two separate GitHub integrations:

1. **Cloud Connector** (claude.ai web app)
   - Configured at https://claude.ai/settings
   - OAuth-based authentication
   - Works in web sessions only
   - NOT accessible from Claude Code (CLI)

2. **GitHub CLI** (local machine)
   - Authenticated via `gh auth login`
   - Works in terminal/bash
   - Claude Code can call via bash but it's not "native"
   - No structured MCP interface

**The Gap:** Claude Code couldn't natively interact with GitHub. Users had to either:
- Use bash commands to call `gh` CLI (works but clunky)
- Use the cloud connector (only in web app)
- Fall back to manual GitHub operations

**The Solution:** GitHub MCP Bridge acts as a bridge—it takes your local `gh` CLI authentication and exposes it as a native MCP server that Claude Code can use directly.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│ Claude Code Session                                     │
│ ┌──────────────────────────────────────────────────┐   │
│ │ GitHub MCP Bridge (loaded as MCP server)         │   │
│ │ • list_repos()                                   │   │
│ │ • get_repo()                                     │   │
│ │ • list_prs()                                     │   │
│ │ • get_pr()                                       │   │
│ └──────────────────────────────────────────────────┘   │
│         ↓                                               │
│ ┌──────────────────────────────────────────────────┐   │
│ │ GitHub Client (gh_client.py)                     │   │
│ │ Wraps subprocess calls to gh CLI                 │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ Local Machine                                           │
│ ┌──────────────────────────────────────────────────┐   │
│ │ GitHub CLI (gh) - already authenticated          │   │
│ │ $ gh auth status ✅                              │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ GitHub Cloud Infrastructure                             │
│ (API calls via authenticated gh CLI)                   │
└─────────────────────────────────────────────────────────┘
```

## Architecture

### 1. **GitHub Client** (`src/github_mcp/gh_client.py`)
Wraps the local `gh` CLI with Python methods:
```python
class GitHubClient:
    def list_repos(org: str, limit: int) -> list[dict]
    def get_repo(repo: str) -> dict
    def list_prs(repo: str, state: str) -> list[dict]
    def get_pr(repo: str, pr_number: int) -> dict
```

**Why subprocess:** The `gh` CLI handles:
- Authentication (already cached on your machine)
- API rate limiting
- Response parsing
- Error handling
- Multi-account support

We leverage all of this instead of reimplementing.

### 2. **MCP Server** (`src/github_mcp/mcp.py`)
Implements the MCP protocol:
- Defines tools (list_repos, get_repo, list_prs, get_pr)
- Handles tool invocation
- Converts subprocess results to MCP responses
- Routes Claude requests to GitHub Client

### 3. **Registration** (`~/.claude/settings.json`)
Claude Code loads the MCP on startup:
```json
{
  "mcpServers": {
    "github-bridge": {
      "command": "python3",
      "args": ["-m", "github_mcp.mcp"],
      "cwd": "/Users/craighoad/Repos/github-mcp-bridge",
      "description": "GitHub MCP bridge"
    }
  }
}
```

## Setup

### Prerequisites
- `gh` CLI installed and authenticated: `gh auth status` ✅
- Python 3.12+
- Claude Code

### Installation

```bash
# Clone the repo
cd /Users/craighoad/Repos
git clone https://github.com/hoad-org/github-mcp-bridge.git
cd github-mcp-bridge

# Install
pip install -e .

# Verify gh CLI is authenticated
gh auth status
```

The MCP is automatically registered in `~/.claude/settings.json`.

### First Run

Restart Claude Code. On startup, the bridge loads and you'll have GitHub tools available:

```
Can you list my repos in hoad-org and show me the Claude-related ones?
```

## API Reference

### `list_repos(org, limit=100)`
Lists repositories in an organization.

**Parameters:**
- `org` (string): Organization name (e.g., "hoad-org")
- `limit` (integer): Max repos to return (default: 100)

**Returns:** List of repo objects with: name, description, url, isPrivate, updatedAt

**Example:**
```python
repos = github.list_repos("hoad-org", limit=50)
# Returns:
# [
#   {
#     "name": "cloudctl-skill",
#     "description": "Claude skill for cloud context management",
#     "url": "https://github.com/hoad-org/cloudctl-skill",
#     "isPrivate": false,
#     "updatedAt": "2026-05-14T03:38:34Z"
#   },
#   ...
# ]
```

### `get_repo(repo)`
Gets repository details.

**Parameters:**
- `repo` (string): Repository in format "owner/name"

**Returns:** Repo object with: name, description, url, isPrivate, owner, updatedAt

### `list_prs(repo, state="open")`
Lists pull requests in a repository.

**Parameters:**
- `repo` (string): Repository in format "owner/name"
- `state` (string): PR state - "open", "closed", or "merged" (default: "open")

**Returns:** List of PR objects with: number, title, state, url, author, updatedAt

### `get_pr(repo, number)`
Gets pull request details.

**Parameters:**
- `repo` (string): Repository in format "owner/name"
- `number` (integer): PR number

**Returns:** PR object with: number, title, state, url, author, body

## Maintenance Guide

### Adding a New Tool

1. **Add method to `GitHubClient`** (`gh_client.py`):
```python
def new_operation(self, param: str) -> dict[str, Any]:
    """Get something from GitHub."""
    return self._run_command(
        ["gh", "api", "repos/owner/repo/endpoint", "--jq", "..."]
    )
```

2. **Add tool to MCP server** (`mcp.py`):
```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ... existing tools ...
        Tool(
            name="new_operation",
            description="Do something on GitHub",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "..."}
                },
                "required": ["param"]
            }
        )
    ]
```

3. **Add handler in `call_tool`**:
```python
elif name == "new_operation":
    result = github.new_operation(param=arguments["param"])
    return [TextContent(type="text", text=str(result))]
```

4. **Add tests** (`tests/test_mcp.py`, `tests/test_gh_client.py`)

5. **Test locally:**
```bash
python3 -c "from github_mcp.gh_client import GitHubClient; print(GitHubClient().new_operation('test'))"
```

### Debugging

**Check gh CLI authentication:**
```bash
gh auth status
```

**Test directly without MCP:**
```bash
python3 << 'EOF'
from github_mcp.gh_client import GitHubClient
client = GitHubClient()
print(client.list_repos("hoad-org"))
EOF
```

**Check MCP server loads:**
```bash
python3 -m github_mcp.mcp
```

### Updating Dependencies

```bash
# Update pyproject.toml
# Then reinstall
pip install -e . --upgrade
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/github_mcp

# Run specific test file
pytest tests/test_gh_client.py -v
```

### CI/CD Pipeline

GitHub Actions automatically runs on push/PR:
- **test.yml** — Unit tests, type checking, linting (Python 3.12-3.13)
- **security.yml** — Bandit, pip-audit security scans

All must pass before merging.

## Limitations & Known Issues

1. **Authentication:** Requires local `gh` CLI to be authenticated. If token expires, run `gh auth refresh`.

2. **Rate Limiting:** Subject to GitHub API rate limits (60 requests/hour unauthenticated, 5000/hour authenticated). The bridge doesn't implement caching—add if needed.

3. **async/await:** MCP server uses asyncio but gh CLI calls are synchronous (blocking). For high-volume operations, consider optimizing.

4. **JSON Parsing:** Assumes gh CLI output is valid JSON. Malformed responses will error—add error handling if needed.

## Future Enhancements

- [ ] Add caching for expensive queries (repos, org members)
- [ ] Support GraphQL queries directly
- [ ] Add rate limit detection and backoff
- [ ] Support additional operations (issues, discussions, actions)
- [ ] Add progress indicators for long operations
- [ ] Support batch operations

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass: `pytest tests/ --cov=src/github_mcp`
5. Ensure code quality: `ruff check . && black . && mypy src/github_mcp`
6. Open a PR

## License

MIT

## References

- [gh CLI Documentation](https://cli.github.com/manual/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [GitHub API Reference](https://docs.github.com/en/rest)
