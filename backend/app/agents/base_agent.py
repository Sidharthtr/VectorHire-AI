"""
FUTURE: Base Agent Interface
============================
This module is a placeholder for the future multi-agent architecture.

When implemented, agents will:
- Inherit from BaseAgent
- Be composed into supervisor-worker hierarchies using LangGraph
- Have access to MCP tools via the mcp/ registry
- Maintain their own memory and context

Current nodes in app/graph/nodes/ are designed to be convertible
into agents by wrapping them with this interface.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for VectorHire AI agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent does — used by supervisor for task routing."""
        ...

    @abstractmethod
    async def run(self, input: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's task and return updated state."""
        ...
