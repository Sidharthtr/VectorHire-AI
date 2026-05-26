# MCP — Model Context Protocol Integration (Future)

This directory is reserved for MCP (Model Context Protocol) integrations.

## What is MCP?

MCP is an open standard for connecting AI agents to external data sources and tools.
It enables agents to call real-world APIs, browse the web, read files, and more.

## Planned MCP Integrations

| Tool | Purpose | Phase |
|------|---------|-------|
| `linkedin_job_search` | Live job listings from LinkedIn | Phase 2 |
| `github_profile` | Candidate GitHub analysis | Phase 2 |
| `web_search` | Real-time job/company research | Phase 2 |
| `gmail_tracker` | Job application email tracking | Phase 3 |
| `browser_use` | Autonomous job board scraping | Phase 3 |

## Architecture

```
Agent
└── MCPClient
    ├── LinkedInJobSearchTool  → LinkedIn API
    ├── GitHubProfileTool      → GitHub API
    ├── WebSearchTool          → Search API
    └── BrowserUseTool         → Playwright/Puppeteer
```

## References

- [MCP Specification](https://modelcontextprotocol.io)
- `app/agents/README.md` — How agents use MCP tools
- `docs/future_mcp.md` — Full integration design
