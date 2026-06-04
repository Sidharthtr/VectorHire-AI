"""
MCP Tool Base Class — Phase 2 Stub.

Model Context Protocol (MCP) is Anthropic's open standard for connecting
AI models to external tools and data sources.

In Phase 4, agents will call these tools to:
  - Search live jobs on LinkedIn / Indeed
  - Fetch a candidate's GitHub contributions
  - Look up salary benchmarks
  - Recommend courses for skill gaps

This stub defines the interface. Concrete implementations come in Phase 4.

Migration path from Phase 2 → Phase 4:
1. Implement execute() in each concrete tool class.
2. Register tools with an MCP server (e.g. FastMCP).
3. Connect BaseAgent.run() to the MCP registry.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MCPTool(ABC):
    """Abstract base class for all MCP-compatible tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier used by agents to call this tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Natural language description — used by LLM for tool selection."""
        ...

    @property
    def input_schema(self) -> dict:
        """JSON Schema for tool input. Override in concrete tools."""
        return {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the tool and return structured results.
        All tools are async — network calls should not block the event loop.
        """
        ...

    def __repr__(self) -> str:
        return f"<MCPTool name={self.name!r}>"
