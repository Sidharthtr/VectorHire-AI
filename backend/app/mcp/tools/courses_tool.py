"""
Course Recommendation MCP Tool — Phase 4 stub.

FUTURE IMPLEMENTATION:
  - Given a list of missing skills, recommend relevant courses
  - Sources: Coursera, Udemy, YouTube, freeCodeCamp, fast.ai
  - Filter by free/paid, difficulty, duration
  - Sort by relevance to the specific missing skill

Coursera has a free tier API; Udemy affiliate API is open.
"""
from __future__ import annotations

from typing import Any
from app.mcp.tools.base_tool import MCPTool


class CourseRecommendationTool(MCPTool):
    """Recommend online courses for a list of skills to learn. (Phase 4)"""

    @property
    def name(self) -> str:
        return "course_recommendation"

    @property
    def description(self) -> str:
        return (
            "Recommend online courses (Coursera, Udemy, YouTube) for a given list "
            "of skills. Returns course title, provider, URL, duration, and rating. "
            "Prioritises free options when available."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills to learn",
                },
                "free_only": {
                    "type": "boolean",
                    "description": "Only return free courses",
                    "default": False,
                },
                "max_per_skill": {
                    "type": "integer",
                    "description": "Max course recommendations per skill",
                    "default": 3,
                },
            },
            "required": ["skills"],
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        # TODO Phase 4: call Coursera / Udemy APIs
        raise NotImplementedError("CourseRecommendationTool will be implemented in Phase 4")
