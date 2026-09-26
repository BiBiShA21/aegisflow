"""
AegisFlow - LangGraph Multi-Agent Orchestrator
Coordinates the workflow between Detection, Fix Generation (RAG + Sandbox), and Pull Request creation.
"""
import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import os

from backend.agents.detection_agent import detect_vulnerabilities, detect_language
from backend.agents.fix_agent import generate_fix
from backend.services.pr_service import create_remediation_pr

# Define the State that is passed between agents
class PipelineState(TypedDict):
    code: str
    language: str
    repo_name: str
    file_path: str
    github_token: str
    scan_id: str
    vulnerabilities: List[Dict[str, Any]]
    fixed_code: Optional[str]
    confidence: float
    pr_url: Optional[str]
    messages: Annotated[List[str], operator.add]

def detect_node(state: PipelineState):
    """Agent 1: Detects vulnerabilities in the code"""
    code = state["code"]
    language = state.get("language") or detect_language(code)
    
    vulnerabilities = detect_vulnerabilities(code)
    return {
        "vulnerabilities": vulnerabilities,
        "language": language,
        "messages": [f"[Detect Agent] Found {len(vulnerabilities)} vulnerabilities in {language} code."]
    }

def fix_node(state: PipelineState):
    """Agent 2 & 3: Retrieves RAG context, generates a fix, and runs Docker Sandbox validation"""
    if not state.get("vulnerabilities"):
        return {"confidence": 0.0, "messages": ["[Fix Agent] No vulnerabilities to fix."]}
        
    result = generate_fix(
        code=state["code"],
        vulnerabilities=state["vulnerabilities"],
        language=state["language"]
    )
    
    return {
        "fixed_code": result["fixed_code"],
        "confidence": result["confidence"],
        "messages": ["[Fix Agent] Generated fix, retrieved OWASP guidelines, and completed Sandbox validation."]
    }

def pr_node(state: PipelineState):
    """Agent 4: Raises a Pull Request on GitHub"""
    if not state.get("fixed_code"):
        return {"messages": ["[PR Agent] No fixed code to PR."]}
        
    vuln_details = "\n".join([f"- {v['type']}: {v['description']}" for v in state.get("vulnerabilities", [])])
    
    try:
        pr_url = create_remediation_pr(
            github_token=state.get("github_token"),
            repo_name=state.get("repo_name"),
            file_path=state.get("file_path"),
            fixed_code=state["fixed_code"],
            vulnerability_details=vuln_details
        )
        return {"pr_url": pr_url, "messages": [f"[PR Agent] Successfully created PR: {pr_url}"]}
    except Exception as e:
        return {"messages": [f"[PR Agent ERROR] {str(e)}"]}

# --- Routing Logic ---

def should_fix(state: PipelineState):
    if len(state.get("vulnerabilities", [])) > 0:
        return "fix"
    return "end"

def should_pr(state: PipelineState):
    # Only PR if confidence is decent and we have a repo target
    if state.get("confidence", 0.0) >= 0.80 and state.get("repo_name"):
        return "pr"
    return "end"

# --- Build the StateGraph ---

workflow = StateGraph(PipelineState)

# Add Nodes
workflow.add_node("detect", detect_node)
workflow.add_node("fix", fix_node)
workflow.add_node("pr", pr_node)

# Add Edges
workflow.set_entry_point("detect")
workflow.add_conditional_edges("detect", should_fix, {"fix": "fix", "end": END})
workflow.add_conditional_edges("fix", should_pr, {"pr": "pr", "end": END})
workflow.add_edge("pr", END)

# Compile Graph
remediation_pipeline = workflow.compile()

def run_autonomous_pipeline(payload: dict) -> dict:
    """Entry point to trigger the whole multi-agent graph"""
    initial_state = {
        "code": payload.get("code", ""),
        "language": payload.get("language", ""),
        "repo_name": payload.get("repo_name", ""),
        "file_path": payload.get("file_path", ""),
        "github_token": payload.get("github_token", ""),
        "scan_id": payload.get("scan_id", "manual"),
        "vulnerabilities": [],
        "messages": ["[System] Initiating Autonomous Pipeline..."]
    }
    
    final_state = remediation_pipeline.invoke(initial_state)
    return final_state
