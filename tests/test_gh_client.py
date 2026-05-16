"""Tests for GitHub client."""

import pytest
from unittest.mock import patch, MagicMock
from github_mcp.gh_client import GitHubClient


def test_init_checks_auth() -> None:
    """Test that init verifies gh CLI is authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        client = GitHubClient()
        assert client is not None


def test_init_raises_on_no_auth() -> None:
    """Test that init raises if gh CLI is not authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="not authenticated")
        with pytest.raises(RuntimeError, match="not authenticated"):
            GitHubClient()


def test_list_repos() -> None:
    """Test listing repos."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0),  # auth check
            MagicMock(returncode=0, stdout='[{"name":"repo1"},{"name":"repo2"}]'),  # list repos
        ]
        client = GitHubClient()
        repos = client.list_repos("hoad-org", limit=10)
        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"
