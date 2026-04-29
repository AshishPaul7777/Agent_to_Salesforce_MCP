"""Writer <-> Editor self-review loop."""
from __future__ import annotations

import re

from langgraph.graph import END, StateGraph

from console import print_editor, print_writer
from graphs.llm import generate
from graphs.state import ReviewState

MAX_ITERATIONS = 3
APPROVAL_THRESHOLD = 8


# ---------------------------------------------------------------------------
# Writer node
# ---------------------------------------------------------------------------

async def writer_node(state: ReviewState) -> dict:
    iteration = state["iteration"]

    if iteration == 0:
        prompt = f"""Write a detailed, polished travel itinerary based on the following:

{state['topic']}

Make it engaging, practical, and well-structured with clear sections."""
    else:
        prompt = f"""Revise the following travel itinerary draft based on the editor's feedback.
Address every point raised. Do not just acknowledge the feedback — actually fix it.

CURRENT DRAFT:
{state['draft']}

EDITOR FEEDBACK:
{state['feedback']}

Produce the improved version in full."""

    print_writer(iteration + 1, "Writing draft..." if iteration == 0 else "Revising based on feedback...")
    draft = await generate(prompt, temperature=0.5)

    return {
        **state,
        "draft": draft,
        "iteration": iteration + 1,
    }


# ---------------------------------------------------------------------------
# Editor node
# ---------------------------------------------------------------------------

async def editor_node(state: ReviewState) -> dict:
    prompt = f"""You are a professional travel editor. Review the following itinerary draft critically.

DRAFT:
{state['draft']}

Score it on these three dimensions (1-10 each):
1. Accuracy and practical usefulness (are times, costs, and logistics realistic?)
2. Clarity and readability (is it easy to follow?)
3. Completeness (does it cover transport, weather, packing, hidden gems?)

Then provide your assessment in exactly this format:

QUALITY_SCORE: <integer 1-10, average of the three scores>
APPROVED: <YES if score >= {APPROVAL_THRESHOLD}, else NO>
FEEDBACK: <specific, actionable suggestions — be direct, not vague>"""

    response_text = await generate(prompt, temperature=0.2)

    score = None
    approved = False
    feedback = response_text

    score_match = re.search(r"QUALITY_SCORE:\s*(\d+)", response_text)
    if score_match:
        score = int(score_match.group(1))

    approved_match = re.search(r"APPROVED:\s*(YES|NO)", response_text, re.IGNORECASE)
    if approved_match:
        approved = approved_match.group(1).upper() == "YES"

    feedback_match = re.search(r"FEEDBACK:\s*(.*)", response_text, re.DOTALL)
    if feedback_match:
        feedback = feedback_match.group(1).strip()

    force_approve = state["iteration"] >= MAX_ITERATIONS
    final_approved = approved or force_approve

    print_editor(
        score,
        final_approved,
        "(max iterations reached, accepting)" if force_approve and not approved else feedback[:120] + "...",
    )

    return {
        **state,
        "feedback": feedback,
        "approved": final_approved,
        "quality_score": score,
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route(state: ReviewState) -> str:
    return END if state["approved"] else "writer"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_review_loop():
    graph = StateGraph(ReviewState)

    graph.add_node("writer", writer_node)
    graph.add_node("editor", editor_node)

    graph.set_entry_point("writer")
    graph.add_edge("writer", "editor")
    graph.add_conditional_edges("editor", _route, {END: END, "writer": "writer"})

    return graph.compile()


async def run_review_loop(topic: str) -> str:
    app = build_review_loop()
    final_state = await app.ainvoke(
        {
            "topic": topic,
            "draft": "",
            "feedback": "",
            "iteration": 0,
            "approved": False,
            "quality_score": None,
        }
    )
    return final_state["draft"]
