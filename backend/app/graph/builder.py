"""
Wires the 5 pipeline nodes into a linear LangGraph StateGraph.

What it does:
- Declares each node and the edges between them (parse -> extract -> retrieve -> rank -> explain -> END).
- Returns an uncompiled StateGraph for workflow.py to compile and cache.

Upstream (who imports this): app/graph/workflow.py
Downstream (what this imports): langgraph, WorkflowState, the 5 node functions, constants
"""
# StateGraph: LangGraph's directed graph over a typed state dict. END: sentinel marking the terminal edge
from langgraph.graph import StateGraph, END
# WorkflowState: the TypedDict schema StateGraph enforces on every node's input/output
from app.graph.state import WorkflowState
# Node 1: PDF bytes -> raw text
from app.graph.nodes.parse_resume_node import parse_resume_node
# Node 2: raw text -> structured ParsedResume (skills, experience, education)
from app.graph.nodes.extract_skills_node import extract_skills_node
# Node 3: ParsedResume -> top-K candidate jobs from vector store
from app.graph.nodes.retrieve_jobs_node import retrieve_jobs_node
# Node 4: candidate jobs -> scored, sorted RankedJob list
from app.graph.nodes.rank_jobs_node import rank_jobs_node
# Node 5: ranked jobs -> per-job explanations, skill gaps, suggestions
from app.graph.nodes.explain_match_node import explain_match_node
# WORKFLOW_RECURSION_LIMIT: imported here for parity with workflow.py; consumed when graph is invoked
from app.core.constants import WORKFLOW_RECURSION_LIMIT


def build_workflow() -> StateGraph:
    """
    Constructs the VectorHire LangGraph workflow.

    Flow: parse_resume → extract_skills → retrieve_jobs → rank_jobs → explain_match → END

    Each node is isolated and independently replaceable with an agent.
    """
    graph = StateGraph(WorkflowState)

    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("extract_skills", extract_skills_node)
    graph.add_node("retrieve_jobs", retrieve_jobs_node)
    graph.add_node("rank_jobs", rank_jobs_node)
    graph.add_node("explain_match", explain_match_node)

    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "extract_skills")
    graph.add_edge("extract_skills", "retrieve_jobs")
    graph.add_edge("retrieve_jobs", "rank_jobs")
    graph.add_edge("rank_jobs", "explain_match")
    graph.add_edge("explain_match", END)

    return graph
