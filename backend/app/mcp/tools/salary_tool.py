"""
Salary Benchmarking MCP Tool — Phase 4 stub.

FUTURE IMPLEMENTATION:
  - Query salary data from Levels.fyi, Glassdoor, or LinkedIn Salary
  - Return p25/median/p75 for a given role + location
  - Show candidates where their target salary sits in the market

Free data sources to consider:
  - Glassdoor API (requires partner access)
  - levels.fyi scraping (unofficial)
  - Open salary survey datasets (Kaggle)
"""
from __future__ import annotations

from typing import Any
from app.mcp.tools.base_tool import MCPTool


class SalaryBenchmarkTool(MCPTool):
    """Look up salary benchmarks for a job title and location. (Phase 4)"""

    @property
    def name(self) -> str:
        return "salary_benchmark"

    @property
    def description(self) -> str:
        return (
            "Get salary benchmarks (25th percentile, median, 75th percentile) "
            "for a given job title and location. Helps candidates evaluate offers."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Job title"},
                "location": {"type": "string", "description": "City or country"},
                "years_of_experience": {"type": "integer", "description": "Years of experience"},
            },
            "required": ["title"],
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        # TODO Phase 4: query salary data source
        raise NotImplementedError("SalaryBenchmarkTool will be implemented in Phase 4")
