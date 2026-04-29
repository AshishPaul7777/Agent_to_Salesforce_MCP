# MCP + LangGraph Itinerary Agent

An AI travel itinerary agent that combines the Model Context Protocol (MCP), Retrieval-Augmented Generation (RAG), live weather data, and a LangGraph writer-editor review loop to produce detailed, weather-aware travel itineraries.

---

## What It Does

Type a query like *"Plan a 2-day trip to Hyderabad"* and the agent:

1. Fetches live weather for the city via OpenWeatherMap
2. Searches a curated knowledge base (Jaipur off-beat places) using semantic similarity
3. Retrieves local transport options and costs
4. Runs a 3-node LangGraph pipeline: Research → Analyze → Report
5. Passes the report through a Writer ↔ Editor review loop that iteratively improves quality
6. Prints the final itinerary in the terminal and saves it to `itinerary_output.md`

If the query is about a city not in the knowledge base, the system detects low relevance scores and falls back to the LLM's own training knowledge — still combining it with real weather and transport data.

---

## Architecture

```
User Query
    ↓
main.py
    ↓
MCPClient  ──────────────────────────────────────────────────────┐
    ↓                                                            │
LangGraph Pipeline                                    MCP Server │
  [Research Node] ──── asyncio.gather() ──────────► rag_search  │
       │                                 ──────────► get_weather │
       │                                 ──────────► get_transport
       ↓
  [Analyze Node]  ──── Gemini LLM call #1
       ↓
  [Report Node]   ──── Gemini LLM call #2
       ↓
LangGraph Review Loop
  [Writer Node]   ──── Gemini LLM call #3
       ↓
  [Editor Node]   ──── Gemini LLM call #4  ── score < 8 → back to Writer
       ↓                                   ── score ≥ 8 → Final Output
  Final Itinerary
```

**LLM calls per run:** minimum 4 (editor approves first attempt), maximum 8 (editor rejects twice, accepts on third).

---

## Technologies

| Technology | Role |
|---|---|
| **MCP (Model Context Protocol)** | Standard interface for the agent to call external tools |
| **LangGraph** | Directed graph orchestration for multi-node AI pipelines and loops |
| **Google Gemini** | LLM for analysis, report generation, writing, and editing |
| **Gemini Embeddings** | Converts text to vectors for semantic similarity search |
| **ChromaDB** | Vector database that stores and searches embeddings |
| **RAG** | Retrieves relevant place knowledge before LLM generation |
| **OpenWeatherMap API** | Live weather and 3-day forecast data |
| **Rich** | Colored terminal output |

---

## Project Structure

```
├── main.py                      Entry point
├── config.py                    All environment variables and constants
├── console.py                   Rich terminal color helpers
├── requirements.txt
├── .env.example                 Template for required environment variables
│
├── data/
│   └── jaipur_places.txt        Curated off-beat Jaipur place descriptions (RAG source)
│
├── mcp_server/
│   ├── server.py                MCP server — registers and routes tool calls
│   └── tools/
│       ├── rag_tool.py          ChromaDB + Gemini embeddings (ingest + search)
│       ├── weather_tool.py      OpenWeatherMap API integration
│       └── transport_tool.py    Local and intercity transport data
│
├── agent/
│   └── mcp_client.py            Async MCP client wrapper
│
└── graphs/
    ├── state.py                 TypedDict state schemas for both graphs
    ├── llm.py                   Shared Gemini async helper with retry and model fallback
    ├── pipeline.py              Research → Analyze → Report LangGraph graph
    └── review_loop.py           Writer ↔ Editor review loop graph
```

---

## Setup

### Prerequisites

- Python 3.10+
- A [Google AI Studio](https://aistudio.google.com) API key (free)
- An [OpenWeatherMap](https://openweathermap.org/api) API key (free tier: 60 calls/min)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Agent_to_Salesforce_MCP

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Fill in your API keys in .env
```

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweathermap_api_key
CHROMA_PERSIST_DIR=./chroma_db
GEMINI_LLM_MODEL=gemini-2.0-flash
GEMINI_FALLBACK_MODEL=gemini-2.0-flash-lite
GEMINI_EMBED_MODEL=gemini-embedding-001
RAG_RELEVANCE_THRESHOLD=0.75
```

`GEMINI_LLM_MODEL` and `GEMINI_FALLBACK_MODEL` can be changed to any model your API key supports. To list available models:

```bash
python list_models.py
```

---

## Running

```bash
python main.py
```

You will be prompted to enter a travel query. Press Enter to use the default example query.

**Example queries:**
- `Plan a 1-day off-beat Jaipur itinerary for a couple who enjoys history and architecture.`
- `Suggest hidden gems in Jaipur for a solo backpacker on a budget.`
- `Plan a 2-day trip to Hyderabad.`
- `What should a photography enthusiast visit in Jaipur in the early morning?`

The final itinerary is printed to the terminal and saved to `itinerary_output.md`.

---

## How the RAG Works

On the **first run**, the agent ingests `data/jaipur_places.txt`:
- Splits the file into paragraphs
- Converts each paragraph to a 768-dimensional vector using Gemini embeddings
- Stores all vectors in ChromaDB (persisted to `chroma_db/` on disk)

On every **subsequent run**, it loads from disk — no re-ingestion.

When a query arrives, it is also embedded and compared against stored vectors using cosine similarity. Results with a score below `RAG_RELEVANCE_THRESHOLD` (default 0.75) are discarded. This prevents Jaipur-specific docs from polluting itineraries for other cities.

---

## Extending the Knowledge Base

To add a new city, create a text file in `data/` with paragraphs describing places (one place per paragraph, separated by a blank line), then delete `chroma_db/` to force re-ingestion on the next run:

```bash
# Add your file
echo "Your place description..." > data/bengaluru_places.txt

# Force re-ingestion
rm -rf chroma_db/

python main.py
```

---

## How the Review Loop Works

The Writer node drafts the itinerary. The Editor node scores it on three dimensions:

| Dimension | What it checks |
|---|---|
| Accuracy | Are times, costs, and logistics realistic? |
| Clarity | Is it easy to follow? |
| Completeness | Does it cover transport, weather, packing, hidden gems? |

If the average score is **8 or above**, the draft is approved. If below, the editor provides specific feedback and the writer revises. This repeats up to **3 iterations** maximum, after which the current draft is accepted regardless.
