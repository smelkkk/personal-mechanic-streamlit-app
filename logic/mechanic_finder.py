import os
import json
import requests
from typing import Dict, List, Tuple

from openai import OpenAI, AuthenticationError, APIConnectionError, RateLimitError

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_nearby_mechanics",
        "description": (
            "Search for nearby auto repair shops using OpenStreetMap. "
            "Call this with the appropriate radius and whether to prioritise "
            "open-now shops based on the urgency of the driver's situation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "radius_meters": {
                    "type": "integer",
                    "description": (
                        "Search radius in metres. Use 2000 for Stop Now, "
                        "5000 for Service Soon, 10000 for Drive OK."
                    ),
                },
                "open_now_priority": {
                    "type": "boolean",
                    "description": "If true, note that the driver needs a shop open right now.",
                },
                "search_rationale": {
                    "type": "string",
                    "description": "Brief sentence explaining why these parameters were chosen.",
                },
            },
            "required": ["radius_meters", "open_now_priority", "search_rationale"],
        },
    },
}

def _query_overpass(lat: float, lon: float, radius_meters: int) -> List[Dict]:
    """Return list of auto-repair shops from OpenStreetMap within radius."""
    query = f"""
[out:json][timeout:15];
(
  node["shop"="car_repair"](around:{radius_meters},{lat},{lon});
  way["shop"="car_repair"](around:{radius_meters},{lat},{lon});
  node["amenity"="car_repair"](around:{radius_meters},{lat},{lon});
  way["amenity"="car_repair"](around:{radius_meters},{lat},{lon});
);
out center 10;
"""
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=20,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return []

    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed repair shop")
        if el["type"] == "node":
            el_lat, el_lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            el_lat, el_lon = center.get("lat"), center.get("lon")

        if el_lat is None or el_lon is None:
            continue

        dist_km = _haversine(lat, lon, el_lat, el_lon)

        results.append({
            "name": name,
            "address": (tags.get("addr:street", "") + " " + tags.get("addr:housenumber", "")).strip(),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "opening_hours": tags.get("opening_hours", ""),
            "distance_km": round(dist_km, 2),
            "lat": el_lat,
            "lon": el_lon,
        })

    results.sort(key=lambda x: x["distance_km"])
    return results[:8]


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Approximate distance in km between two lat/lon points."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def find_mechanics(
    lat: float,
    lon: float,
    urgency: str,
    warning_type: str,
    symptoms: List[str],
) -> Tuple[bool, Dict, str]:
    """
    Two-call LLM tool-use pipeline:
      1. LLM decides search parameters via tool call (radius, urgency flags)
      2. We execute the real Overpass/OSM search with those parameters
      3. LLM ranks and summarises results in plain language for the driver

    Returns: (success, result_dict, error_message)
    result_dict keys: mechanics, summary, rationale, radius_km, open_now_priority
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, {}, "OpenAI API key not set. Enable AI mode to use mechanic finder."

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an automotive assistant helping a driver find a nearby mechanic. "
        "You have access to a tool that searches OpenStreetMap for repair shops. "
        "Choose search parameters that match the urgency of the situation."
    )

    user_message = (
        f"The driver has urgency level: {urgency}.\n"
        f"Warning type: {warning_type}.\n"
        f"Symptoms: {', '.join(symptoms) if symptoms else 'none'}.\n"
        "Please call the search tool with appropriate parameters."
    )

    # --- LLM Call 1: Decide tool parameters ---
    try:
        response1 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            tools=[SEARCH_TOOL],
            tool_choice={"type": "function", "function": {"name": "search_nearby_mechanics"}},
        )
    except AuthenticationError:
        return False, {}, "Invalid OpenAI API key."
    except RateLimitError:
        return False, {}, "Rate limit reached. Try again in a moment."
    except APIConnectionError:
        return False, {}, "Could not connect to OpenAI. Check your internet connection."
    except Exception as e:
        return False, {}, f"Unexpected error during tool call: {str(e)}"

    tool_call = response1.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    radius = args.get("radius_meters", 5000)
    open_now_priority = args.get("open_now_priority", False)
    rationale = args.get("search_rationale", "")

    # --- Execute real Overpass search ---
    mechanics = _query_overpass(lat, lon, radius)

    if not mechanics:
        return True, {
            "mechanics": [],
            "summary": (
                "No repair shops were found in OpenStreetMap within the search area. "
                "Try a manual search or call roadside assistance."
            ),
            "rationale": rationale,
            "radius_km": radius // 1000,
            "open_now_priority": open_now_priority,
        }, ""

    shops_text = "\n".join(
        f"{i+1}. {m['name']} — {m['distance_km']} km away"
        + (f", phone: {m['phone']}" if m["phone"] else "")
        + (f", hours: {m['opening_hours']}" if m["opening_hours"] else "")
        for i, m in enumerate(mechanics)
    )

    # --- LLM Call 2: Rank and summarise for the driver ---
    ranking_prompt = (
        f"The driver has urgency: {urgency}. Warning: {warning_type}.\n"
        f"Here are nearby repair shops found via OpenStreetMap:\n{shops_text}\n\n"
        "Write a short, calm 2-3 sentence recommendation: which shop(s) to consider "
        "first and why, given the urgency. Do not invent information not in the list."
    )

    try:
        response2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a calm automotive assistant."},
                {"role": "user", "content": ranking_prompt},
            ],
        )
        summary = response2.choices[0].message.content.strip()
    except Exception:
        summary = (
            f"Found {len(mechanics)} repair shop(s) nearby. "
            f"The closest is {mechanics[0]['name']} at {mechanics[0]['distance_km']} km."
        )

    return True, {
        "mechanics": mechanics,
        "summary": summary,
        "rationale": rationale,
        "radius_km": radius // 1000,
        "open_now_priority": open_now_priority,
    }, ""
