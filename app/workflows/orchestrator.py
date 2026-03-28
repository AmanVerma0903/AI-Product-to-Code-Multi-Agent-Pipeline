from langgraph.graph import StateGraph, END
from app.workflows.state import AgentState
from app.agents.research_agent import ResearchAgent
from app.agents.epic_agent import EpicAgent
from app.agents.story_agent import StoryAgent
from app.agents.spec_agent import SpecAgent
from app.agents.code_agent import CodeAgent
from app.agents.validation_agent import ValidationAgent

from app.db.session import AsyncSessionLocal
from app.models.artifact import Artifact
from app.models.run import Run, RunStatus
from app.core.ws_manager import ws_manager


def _get_run_questions_context(run_id: int) -> str:
    questions = ws_manager.get_run_questions(run_id)
    if questions:
        return "\n\nUser Questions:\n" + "\n".join([f"- {q}" for q in questions])
    return ""


# ===================== NODES =====================

async def research_node(state: AgentState):
    agent = ResearchAgent()
    requirement = state["requirement"] + _get_run_questions_context(state["run_id"])
    result = await agent.run(requirement, state["documents"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Research", content=result))
        run = await db.get(Run, state["run_id"])
        run.current_stage = "Epic"
        run.status = RunStatus.RUNNING
        await db.commit()

    state["research_summary"] = result
    state["current_stage"] = "Epic"
    state["logs"].append("Research completed")
    return state


async def epic_node(state: AgentState):
    agent = EpicAgent()
    result = await agent.run(state["requirement"], state["research_summary"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Epic", content=result))
        run = await db.get(Run, state["run_id"])
        run.current_stage = "Story"
        await db.commit()

    state["epics"] = result
    state["current_stage"] = "Story"
    return state


async def story_node(state: AgentState):
    agent = StoryAgent()
    result = await agent.run(state["epics"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Story", content=result))
        run = await db.get(Run, state["run_id"])
        run.current_stage = "Spec"
        await db.commit()

    state["stories"] = result
    state["current_stage"] = "Spec"
    return state


async def spec_node(state: AgentState):
    agent = SpecAgent()
    result = await agent.run(state["stories"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Spec", content=result))
        run = await db.get(Run, state["run_id"])
        run.current_stage = "Code"
        await db.commit()

    state["spec"] = result
    state["current_stage"] = "Code"
    return state


async def code_node(state: AgentState):
    agent = CodeAgent()
    result = await agent.run(state["spec"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Code", content={"files": result}))
        run = await db.get(Run, state["run_id"])
        run.current_stage = "Validation"
        await db.commit()

    state["code_files"] = result
    state["current_stage"] = "Validation"
    return state


async def validation_node(state: AgentState):
    agent = ValidationAgent()
    result = await agent.run(state["code_files"])

    async with AsyncSessionLocal() as db:
        db.add(Artifact(run_id=state["run_id"], type="Validation", content=result))
        run = await db.get(Run, state["run_id"])
        run.status = RunStatus.COMPLETED
        run.current_stage = "Completed"
        await db.commit()

    state["validation_report"] = result
    return state


# ===================== GRAPH =====================

def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("research", research_node)
    workflow.add_node("epic", epic_node)
    workflow.add_node("story", story_node)
    workflow.add_node("spec", spec_node)
    workflow.add_node("code", code_node)
    workflow.add_node("validation", validation_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "epic")
    workflow.add_edge("epic", "story")
    workflow.add_edge("story", "spec")
    workflow.add_edge("spec", "code")
    workflow.add_edge("code", "validation")
    workflow.add_edge("validation", END)

    return workflow.compile()


async def execute_workflow(run_id: int, requirement: str, documents: list = None):
    workflow = create_workflow()
    await workflow.ainvoke({
        "run_id": run_id,
        "requirement": requirement,
        "documents": documents or [],
        "research_summary": None,
        "epics": None,
        "stories": None,
        "spec": None,
        "code_files": None,
        "validation_report": None,
        "current_stage": "Research",
        "logs": ["Workflow started"]
    })
