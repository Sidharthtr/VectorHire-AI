"""
LinkedIn Job Search MCP Tool — Phase 4 stub.

FUTURE IMPLEMENTATION:
  - Use LinkedIn Jobs API or unofficial scraper
  - Return live job postings matching a query + location
  - Feed results directly into the ingestion pipeline

Required env vars (Phase 4):
    LINKEDIN_CLIENT_ID=...
    LINKEDIN_CLIENT_SECRET=...
"""
from __future__ import annotations

from typing import Any
from app.mcp.tools.base_tool import MCPTool


class LinkedInJobSearchTool(MCPTool):
    """Search for live job postings on LinkedIn. (Phase 4 — not yet implemented)"""

    @property
    def name(self) -> str:
        return "linkedin_job_search"

    @property
    def description(self) -> str:
        return (
            "Search LinkedIn for live job postings matching a title and location. "
            "Returns job title, company, location, description, and application URL."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query":    {"type": "string", "description": "Job title or keywords"},
                "location": {"type": "string", "description": "City, country, or 'remote'"},
                "limit":    {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        # TODO Phase 4: integrate LinkedIn API
        raise NotImplementedError("LinkedInJobSearchTool will be implemented in Phase 4")
