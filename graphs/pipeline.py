"""Research → Analyze → Report LangGraph pipeline."""
from __future__ import annotations

import asyncio
import json
from functools import partial

from langgraph.graph import END, StateGraph

from agent.mcp_client import MCPClient
from config import RAG_RELEVANCE_THRESHOLD
from console import print_node
from graphs.llm import generate
from graphs.state import ResearchState


# ---------------------------------------------------------------------------
# Node 1 — Research
# ---------------------------------------------------------------------------

def _parse_json(raw: str, label: str) -> dict | list:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"{label} tool returned invalid JSON. Response was:\n{raw[:300]}")


async def research_node(state: ResearchState, mcp: MCPClient) -> dict:
    print_node("Research", f"Fetching data for: {state['query']}")

    city = state.get("city", "Jaipur")

    rag_raw, weather_raw, transport_raw = await asyncio.gather(
        mcp.call("rag_search", query=state["query"], top_k=4),
        mcp.call("get_weather", city=city),
        mcp.call("get_transport_options", city=city),
    )

    rag_hits = _parse_json(rag_raw, "rag_search")
    weather_data = _parse_json(weather_raw, "get_weather")
    transport_data = _parse_json(transport_raw, "get_transport_options")

    # Only use RAG results that are actually relevant (score >= 0.5).
    # Below that threshold the knowledge base has nothing useful for this query
    # and the LLM is better off relying on its own training knowledge.
    relevant_hits = [h for h in rag_hits if h.get("score", 0) >= RAG_RELEVANCE_THRESHOLD]
    raw_docs = [h["text"] for h in relevant_hits]

    if raw_docs:
        print_node("Research", f"Retrieved {len(raw_docs)} relevant docs (of {len(rag_hits)}) | weather OK | transport OK")
    else:
        print_node("Research", f"No relevant docs found in knowledge base (scores too low) — LLM will use its own knowledge | weather OK | transport OK")

    return {
        **state,
        "raw_docs": raw_docs,
        "weather_data": weather_data,
        "transport_data": transport_data,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Node 2 — Analyze
# ---------------------------------------------------------------------------

async def analyze_node(state: ResearchState) -> dict:
    print_node("Analyze", "Synthesizing place knowledge with weather and transport data")

    curr = state["weather_data"]["current"]
    transport_modes = [
        f"  - {t['mode']}: {t['avg_cost_inr']} INR ({t['best_for']})"
        for t in state["transport_data"].get("local", [])
    ]
    transport_text = "\n".join(transport_modes)

    if state["raw_docs"]:
        knowledge_section = f"RETRIEVED PLACE KNOWLEDGE (from local knowledge base):\n{chr(10).join('---' + d for d in state['raw_docs'])}"
    else:
        knowledge_section = "RETRIEVED PLACE KNOWLEDGE: None available for this city — use your own training knowledge to recommend places."

    prompt = f"""You are an expert travel analyst specializing in off-beat destinations.

{knowledge_section}

CURRENT WEATHER IN {state['city'].upper()}:
Temperature: {curr['temp_c']}°C, feels like {curr['feels_like_c']}°C
Condition: {curr['condition']}
Humidity: {curr['humidity_pct']}%, Wind: {curr['wind_kph']} km/h
Advisory: {state['weather_data']['advisory']}

AVAILABLE TRANSPORT:
{transport_text}

USER QUERY: {state['query']}

Produce a structured analysis with:
1. Top 3-4 recommended places (with weather suitability score 1-5 and reasoning)
2. Best time of day for each place given current conditions
3. Recommended transport for each leg of the journey with estimated cost
4. One hidden gem the user might otherwise miss
5. Any weather-specific precautions

Be specific and practical."""

    analysis = await generate(prompt, temperature=0.3)
    print_node("Analyze", "Analysis complete")
    return {**state, "analysis": analysis}


# ---------------------------------------------------------------------------
# Node 3 — Report
# ---------------------------------------------------------------------------

async def report_node(state: ResearchState) -> dict:
    print_node("Report", "Generating formatted itinerary report")

    transport_summary = ", ".join(
        t["mode"] for t in state["transport_data"].get("local", [])[:3]
    )
    curr = state["weather_data"]["current"]

    prompt = f"""Transform the following travel analysis into a clean, well-structured itinerary report.

ANALYSIS:
{state['analysis']}

WEATHER: {curr['temp_c']}°C, {curr['condition']} | Advisory: {state['weather_data']['advisory']}
TRANSPORT AVAILABLE: {transport_summary}

Format the report exactly as:

DESTINATION: {state['city']} Off-Beat Itinerary
WEATHER TODAY: [one-line summary]
─────────────────────────────────────────────

PLACE 1: [Name]
  Why visit: ...
  Best time: ...
  Weather suitability: [score]/5
  Getting there: [transport mode + estimated cost]

PLACE 2: [Name]
  ...

PLACE 3: [Name]
  ...

─────────────────────────────────────────────
SUGGESTED SCHEDULE
[Time-based schedule]

TRANSPORT PLAN
[Leg-by-leg transport guide with costs]

PACKING LIST (weather-adjusted)
[Bullet list]

HIDDEN GEM
[One paragraph]

Keep it practical, specific, and honest about crowds and conditions."""

    report = await generate(prompt, temperature=0.4)
    print_node("Report", "Initial report ready")
    return {**state, "final_report": report}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_pipeline(mcp_client: MCPClient):
    graph = StateGraph(ResearchState)

    graph.add_node("research", partial(research_node, mcp=mcp_client))
    graph.add_node("analyze", analyze_node)
    graph.add_node("report", report_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "analyze")
    graph.add_edge("analyze", "report")
    graph.add_edge("report", END)

    return graph.compile()
