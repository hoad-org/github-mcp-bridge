"""Wrapper around gh CLI for GitHub operations."""

import json
import subprocess
from typing import Any


class GitHubClient:
    """GitHub CLI wrapper."""

    def __init__(self) -> None:
        """Initialize GitHub client."""
        self._verify_auth()

    def _verify_auth(self) -> None:
        """Verify gh CLI is authenticated."""
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError("gh CLI not authenticated. Run: gh auth login")

    def _run_command(self, args: list[str]) -> dict[str, Any]:
        """Run a gh command and return parsed JSON output."""
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")
        if not result.stdout.strip():
            return {}
        return json.loads(result.stdout)

    def list_repos(self, org: str, limit: int = 100) -> list[dict[str, Any]]:
        """List repositories in an organization."""
        result = self._run_command(
            ["gh", "repo", "list", org, "--limit", str(limit), "--json", "name,description,url,isPrivate,updatedAt"]
        )
        return result if isinstance(result, list) else [result]

    def get_repo(self, repo: str) -> dict[str, Any]:
        """Get repository details."""
        return self._run_command(
            ["gh", "repo", "view", repo, "--json", "name,description,url,isPrivate,owner,updatedAt"]
        )

    def list_branches(self, repo: str) -> list[dict[str, Any]]:
        """List branches in a repository."""
        result = self._run_command(["gh", "repo", "view", repo, "--json", "defaultBranchRef"])
        return result if isinstance(result, list) else [result]

    def list_prs(self, repo: str, state: str = "open") -> list[dict[str, Any]]:
        """List pull requests in a repository."""
        result = self._run_command(
            ["gh", "pr", "list", "-R", repo, "-s", state, "--json", "number,title,state,url,author,updatedAt"]
        )
        return result if isinstance(result, list) else [result]

    def get_pr(self, repo: str, pr_number: int) -> dict[str, Any]:
        """Get pull request details."""
        return self._run_command(
            ["gh", "pr", "view", str(pr_number), "-R", repo, "--json", "number,title,state,url,author,body"]
        )
