"""
FUTURE: MCP Tool Registry
==========================
Registry of MCP-enabled tools available to agents.

Planned tools:
- LinkedInJobSearchTool: Live job search via LinkedIn API
- GitHubProfileTool: Fetch candidate GitHub projects and contributions
- WebSearchTool: General-purpose web search for job research
- GmailTool: Read/write emails for job application tracking
- BrowserUseTool: Autonomous browser navigation for job boards
"""

PLANNED_TOOLS = [
    {
        "name": "linkedin_job_search",
        "description": "Search for live job postings on LinkedIn",
        "phase": "Phase 2",
    },
    {
        "name": "github_profile",
        "description": "Fetch GitHub profile, repos, and contribution history",
        "phase": "Phase 2",
    },
    {
        "name": "web_search",
        "description": "General web search for job and company research",
        "phase": "Phase 2",
    },
    {
        "name": "gmail_tracker",
        "description": "Track job application emails and follow-ups",
        "phase": "Phase 3",
    },
    {
        "name": "browser_use",
        "description": "Autonomous browser for scraping job boards",
        "phase": "Phase 3",
    },
]
