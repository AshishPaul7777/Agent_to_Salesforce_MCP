from __future__ import annotations

import json

from duckduckgo_search import DDGS


class WebSearchTool:
    def search_places(self, city: str, query: str, max_results: int = 5) -> str:
        full_query = f"{query} {city} travel places to visit"
        results = []

        with DDGS() as ddgs:
            for r in ddgs.text(full_query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })

        if not results:
            return json.dumps({"city": city, "results": [], "note": "No results found."})

        return json.dumps({"city": city, "results": results}, ensure_ascii=False, indent=2)
