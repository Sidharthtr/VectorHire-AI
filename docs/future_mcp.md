# Future: MCP Tool Integrations

## What is MCP?

Model Context Protocol (MCP) is an open standard that lets AI agents connect to external data sources and APIs through a standardized interface.

## Planned Integrations

### Phase 2 Tools

#### `linkedin_job_search`
- Real-time job listings from LinkedIn
- Filter by location, experience, company size
- Extract structured job data for vector indexing

#### `github_profile`
- Fetch candidate's GitHub profile
- Analyze repos: languages, stars, commit frequency
- Extract project descriptions for skill inference
- Improve resume analysis with real code evidence

#### `web_search`
- General web search for company research
- Find salary data from Glassdoor, Levels.fyi
- Research company culture and tech stacks

### Phase 3 Tools

#### `gmail_tracker`
- Track job application emails
- Detect interview invitations and follow-up prompts
- Auto-update job application status database

#### `browser_use`
- Autonomous browser navigation for job boards
- Fill out job applications
- Scrape job boards not covered by APIs

#### `calendar_integration`
- Schedule interview preparation sessions
- Set reminders for application deadlines
- Sync with Google Calendar

## Integration Architecture

```python
# In app/mcp/client.py (future)
class MCPClient:
    registry: dict[str, MCPTool]

    async def call(self, tool_name: str, **kwargs) -> dict:
        tool = self.registry[tool_name]
        return await tool.execute(**kwargs)
```

## Why MCP?

- Standardized interface — swap tool implementations without agent changes
- Composable — mix and match tools across agents
- Community ecosystem — growing library of pre-built MCP servers
