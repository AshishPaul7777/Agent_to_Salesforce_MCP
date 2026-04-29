from __future__ import annotations

import json

_CITY_TRANSPORT: dict[str, dict] = {
    "jaipur": {
        "local": [
            {
                "mode": "Auto-rickshaw",
                "best_for": "Short hops within the city (1-5 km)",
                "avg_cost_inr": "30-100",
                "how_to_get": "Street hail or Ola/Rapido app",
                "tip": "Negotiate the fare before boarding — meter is rarely used.",
            },
            {
                "mode": "App cab (Ola / Uber)",
                "best_for": "Comfortable, metered, longer rides",
                "avg_cost_inr": "80-350",
                "how_to_get": "Ola or Uber app",
                "tip": "Surge pricing applies during morning and evening rush.",
            },
            {
                "mode": "Rental scooter / bike",
                "best_for": "Flexible exploration of outskirts and Amber",
                "avg_cost_inr": "300-600 per day",
                "how_to_get": "Bounce app or local shops near Sindhi Camp",
                "tip": "Carry a photocopy of your driving license.",
            },
            {
                "mode": "City bus (JCTSL)",
                "best_for": "Budget travel on main routes",
                "avg_cost_inr": "10-30",
                "how_to_get": "Board at any JCTSL stop; route info on JCTSL website",
                "tip": "AC buses run on major routes including Amer and MI Road.",
            },
            {
                "mode": "Tonga (horse carriage)",
                "best_for": "Heritage experience through the old walled city",
                "avg_cost_inr": "100-250",
                "how_to_get": "Street hail near Hawa Mahal or Johri Bazaar",
                "tip": "Fix the fare firmly before boarding; typically a 30-minute circuit.",
            },
            {
                "mode": "Cycle-rickshaw",
                "best_for": "Slow exploration of the old bazaars",
                "avg_cost_inr": "20-60",
                "how_to_get": "Street hail anywhere in the walled city",
                "tip": "Ideal for Johri Bazaar to Hawa Mahal stretch.",
            },
        ],
        "intercity_from_jaipur": [
            {
                "destination": "Amber Fort area",
                "distance_km": 11,
                "options": ["Auto-rickshaw (150-200 INR)", "Ola/Uber (120-180 INR)", "Local bus Route 5"],
            },
            {
                "destination": "Abhaneri (Chand Baori)",
                "distance_km": 95,
                "options": ["Hired taxi (1200-1500 INR round trip)", "Bus from Sindhi Camp to Dausa then local auto"],
            },
            {
                "destination": "Nahargarh Fort",
                "distance_km": 19,
                "options": ["Ola/Uber (200-300 INR)", "Hired taxi (400-500 INR round trip)", "No direct bus"],
            },
        ],
    }
}

_DEFAULT_LOCAL = [
    {
        "mode": "App cab (Ola / Uber)",
        "best_for": "Most reliable option in any Indian city",
        "avg_cost_inr": "80-400",
        "how_to_get": "Ola or Uber app",
        "tip": "Download both apps before travel as availability varies by city.",
    },
    {
        "mode": "Auto-rickshaw",
        "best_for": "Short distances under 5 km",
        "avg_cost_inr": "30-120",
        "how_to_get": "Street hail",
        "tip": "Negotiate fare or insist on meter.",
    },
]


class TransportTool:
    def get_transport_options(self, city: str) -> str:
        data = _CITY_TRANSPORT.get(city.lower())
        if data:
            return json.dumps({"city": city, **data}, indent=2)
        return json.dumps(
            {"city": city, "local": _DEFAULT_LOCAL, "note": "Detailed data not available; showing general options."},
            indent=2,
        )
