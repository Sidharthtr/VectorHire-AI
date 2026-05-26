# VectorHire AI — LangGraph Workflow

## Workflow Diagram

```
START
  │
  ▼
┌─────────────────────┐
│  parse_resume_node   │  PyMuPDF PDF → raw text
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ extract_skills_node  │  Gemini → ParsedResume (skills, edu, exp)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ retrieve_jobs_node   │  sentence-transformers + ChromaDB → top-K jobs
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   rank_jobs_node     │  Gemini → matched/missing skills, fit score
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ explain_match_node   │  Gemini → explanations, suggestions, summary
└──────────┬──────────┘
           │
           ▼
          END
```

## Typed State (`app/graph/state.py`)

The `WorkflowState` TypedDict flows through every node:

| Field | Type | Set By |
|-------|------|--------|
| `resume_bytes` | `bytes` | Input |
| `resume_filename` | `str` | Input |
| `search_query` | `Optional[str]` | Input |
| `top_k` | `int` | Input |
| `experience_filter` | `Optional[str]` | Input |
| `resume_id` | `str` | `parse_resume_node` |
| `raw_text` | `str` | `parse_resume_node` |
| `parsed_resume` | `ParsedResume` | `extract_skills_node` |
| `retrieved_jobs` | `list[tuple[JobDocument, float]]` | `retrieve_jobs_node` |
| `ranked_jobs` | `list[RankedJob]` | `rank_jobs_node` |
| `explained_jobs` | `list[RankedJob]` | `explain_match_node` |
| `overall_summary` | `str` | `explain_match_node` |
| `top_missing_skills` | `list[str]` | `explain_match_node` |
| `improvement_suggestions` | `list[str]` | `explain_match_node` |
| `errors` | `list[str]` | Any node (append-only) |
| `processing_steps` | `list[str]` | Any node (append-only) |

## Node Design Principles

Each node:
1. **Reads** only from `WorkflowState` (no external state)
2. **Returns** a `dict` with only the keys it updates
3. **Handles** its own errors — never raises to crash the workflow
4. **Logs** its status via `logger`
5. **Has a fallback** when LLM calls fail

## Future: Converting Nodes to Agents

Each node is pre-structured for agent conversion:

```python
# Current (Node)
def rank_jobs_node(state: WorkflowState) -> dict:
    ...

# Future (Agent)
class RankingAgent(BaseAgent):
    name = "ranking_agent"
    tools = [linkedin_job_search_tool, web_research_tool]

    async def run(self, state: WorkflowState) -> dict:
        # same logic + tool use + reflection loops
```
