from langgraph.graph import StateGraph, END
from app.graph.state import WorkflowState
from app.graph.nodes.parse_resume_node import parse_resume_node
from app.graph.nodes.extract_skills_node import extract_skills_node
from app.graph.nodes.retrieve_jobs_node import retrieve_jobs_node
from app.graph.nodes.rank_jobs_node import rank_jobs_node
from app.graph.nodes.explain_match_node import explain_match_node
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
