"""Entry point — Jaipur off-beat itinerary agent."""
from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

from agent.mcp_client import MCPClient
from console import console, print_error, print_final, print_step
from graphs.pipeline import build_pipeline
from graphs.review_loop import run_review_loop
from graphs.state import ResearchState

EXAMPLE_QUERIES = [
    "Plan a 1-day off-beat Jaipur itinerary for a couple who enjoys history and architecture.",
    "Suggest hidden gems in Jaipur for a solo backpacker on a budget.",
    "What should a photography enthusiast visit in Jaipur in the early morning?",
    "Create a Jaipur itinerary focused on stepwells and Mughal heritage.",
]


async def run(query: str, city: str = "Jaipur") -> None:
    client = MCPClient()

    print_step("Connecting", "Starting MCP server and connecting client...")
    await client.connect()

    tools_listed = [t.name for t in client.tools]
    print_step("Connected", f"Tools available: {', '.join(tools_listed)}")

    try:
        # ── Stage 1: Research → Analyze → Report ────────────────────────────
        console.rule("[node]Stage 1: Research Pipeline[/node]")
        pipeline = build_pipeline(client)

        initial_state: ResearchState = {
            "query": query,
            "city": city,
            "raw_docs": [],
            "weather_data": {},
            "transport_data": {},
            "analysis": "",
            "final_report": "",
            "error": None,
        }

        result = await pipeline.ainvoke(initial_state)

        if result.get("error"):
            print_error(result["error"])
            return

        initial_report = result["final_report"]
        print_step("Pipeline", "Initial report generated.")

        # ── Stage 2: Writer ↔ Editor review loop ────────────────────────────
        console.rule("[writer]Stage 2: Writer / Editor Review Loop[/writer]")
        topic = (
            f"Refine and expand this Jaipur itinerary into the best possible version.\n\n"
            f"{initial_report}"
        )
        polished = await run_review_loop(topic=topic)

        # ── Final output ─────────────────────────────────────────────────────
        console.rule("[success]Final Output[/success]")
        print_final(polished)

        with open("itinerary_output.md", "w", encoding="utf-8") as f:
            f.write(f"# Query\n\n{query}\n\n---\n\n{polished}\n")

        print_step("Saved", "Itinerary written to itinerary_output.md")

    finally:
        await client.close()


def main() -> None:
    console.rule("[bold cyan]Jaipur Off-Beat Itinerary Agent[/bold cyan]")

    console.print("\n[dim]Example queries:[/dim]")
    for i, q in enumerate(EXAMPLE_QUERIES, 1):
        console.print(f"  [dim]{i}. {q}[/dim]")

    console.print()
    query = console.input("[step]Enter your travel query (or press Enter for default): [/step]").strip()

    if not query:
        query = EXAMPLE_QUERIES[0]
        console.print(f"[dim]Using: {query}[/dim]\n")

    asyncio.run(run(query))


if __name__ == "__main__":
    main()
