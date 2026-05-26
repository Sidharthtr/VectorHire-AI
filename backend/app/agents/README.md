# Agents — Future Implementation

This directory is reserved for the multi-agent architecture phase.

## Planned Agents

| Agent | Role |
|-------|------|
| `ResumeParserAgent` | Converts `parse_resume_node` into an autonomous agent |
| `SkillExtractorAgent` | LLM-powered skill extraction with self-correction loops |
| `JobRetrieverAgent` | Semantic retrieval with live web search fallback |
| `RankingAgent` | Multi-criteria job ranking with reasoning traces |
| `ExplainerAgent` | Generates personalized explanations and coaching |
| `SupervisorAgent` | Orchestrates all specialist agents via LangGraph supervisor pattern |

## Architecture Plan

```
SupervisorAgent
├── ResumeParserAgent
├── SkillExtractorAgent
├── JobRetrieverAgent
│   └── [Future] LiveWebSearchTool (via MCP)
├── RankingAgent
└── ExplainerAgent
    └── [Future] LinkedInProfileTool (via MCP)
```

## How to Convert a Node into an Agent

Each node in `app/graph/nodes/` is already isolated and modular.
To convert to an agent:
1. Wrap the node function in a class that extends `BaseAgent`
2. Add a `tools` list (MCP tools, web tools, etc.)
3. Optionally add a reflection loop for self-correction
4. Register the agent with the SupervisorAgent

## References

- [LangGraph Multi-Agent Docs](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- `app/mcp/` — MCP tool registry for agent tool use
- `docs/future_agents.md` — Full design document
