"""
GitHub Profile MCP Tool — Phase 4 stub.

FUTURE IMPLEMENTATION:
  - Fetch a candidate's public GitHub repos, stars, languages, contributions
  - Use this to enrich the resume with open-source work
  - Infer skills from repo languages and README content

Uses GitHub public API (no auth for public data, 60 req/hr unauthenticated).
"""
from __future__ import annotations

from typing import Any
from app.mcp.tools.base_tool import MCPTool


class GitHubProfileTool(MCPTool):
    """Fetch GitHub profile, repositories, and contribution data. (Phase 4)"""

    @property
    def name(self) -> str:
        return "github_profile"

    @property
    def description(self) -> str:
        return (
            "Retrieve a GitHub user's public profile: repositories, primary languages, "
            "stars received, and recent contribution activity. Useful for enriching "
            "a candidate profile beyond their resume."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "GitHub username"},
                "max_repos": {"type": "integer", "description": "Max repos to return", "default": 10},
            },
            "required": ["username"],
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        # TODO Phase 4: call https://api.github.com/users/{username}/repos
        raise NotImplementedError("GitHubProfileTool will be implemented in Phase 4")
