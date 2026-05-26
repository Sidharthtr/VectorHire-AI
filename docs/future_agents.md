# Future: Multi-Agent Architecture

## Overview

The current LangGraph nodes are designed to be converted into full autonomous agents in Phase 2.

## Planned Agent Roster

### SupervisorAgent
- Orchestrates all specialist agents
- Routes tasks, handles failures, aggregates results
- Uses LangGraph's supervisor pattern

### ResumeParserAgent
- Converts `parse_resume_node` into an agent
- Can handle different resume formats (PDF, DOCX, LinkedIn URL)
- Self-corrects malformed PDFs using retry logic

### SkillExtractorAgent
- Extracts skills with higher precision using multi-prompt strategies
- Cross-references skills with live job market data
- Identifies implicit skills from project descriptions

### JobRetrieverAgent
- Combines ChromaDB semantic search with live LinkedIn job scraping
- Uses MCP tools for real-time job board access
- Deduplicates and ranks across multiple sources

### RankingAgent
- Multi-criteria ranking with explicit reasoning traces
- Considers culture fit, growth trajectory, not just skill match
- Queries company websites for additional context

### ExplainerAgent
- Personalized career coaching with follow-up Q&A capability
- Generates study plans and learning paths
- Integrates with resource databases (courses, books, projects)

## Architecture Plan

```
User Request
    │
    ▼
SupervisorAgent (LangGraph)
    ├── ResumeParserAgent
    │       └── [MCP] FileReaderTool
    ├── SkillExtractorAgent
    │       └── [MCP] SkillsDatabaseTool
    ├── JobRetrieverAgent
    │       ├── ChromaDB (existing)
    │       └── [MCP] LinkedInSearchTool
    ├── RankingAgent
    │       └── [MCP] CompanyResearchTool
    └── ExplainerAgent
            └── [MCP] CoursesSearchTool
```

## Implementation Path

1. Create `SupervisorAgent` in `app/agents/`
2. Wrap existing nodes as `BaseAgent` subclasses
3. Add tool use via MCP registry
4. Add reflection/self-correction loops
5. Test with LangSmith tracing
