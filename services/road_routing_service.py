"""
Road Routing & Geocoding Service Module
Provides real road-based driving routes, geocoding for Indian & global locations,
fastest and shortest route identification, and live traffic integration (Mapbox / OSRM).
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple


class RoadRoutingService:
    def __init__(self):
        self.geocode_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.route_cache: Dict[str, Dict[str, Any]] = {}

    def get_mapbox_token(self) -> str:
        return os.environ.get("MAPBOX_ACCESS_TOKEN", "").strip()

    def geocode(self, query: str) -> List[Dict[str, Any]]:
        """
        Geocodes a location query into real geographic coordinates.
        Supports Indian cities, towns, roads, stations, landmarks, and parking locations.
        Uses Mapbox Geocoding if token available, else OpenStreetMap Nominatim.
        """
        q = query.strip()
        if not q or len(q) < 2:
            return []

        cache_key = q.lower()
        if cache_key in self.geocode_cache:
            return self.geocode_cache[cache_key]

        results: List[Dict[str, Any]] = []

        # 1. Try Mapbox Geocoding if token is present
        token = self.get_mapbox_token()
        if token:
            try:
                encoded_q = urllib.parse.quote(q)
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_q}.json?access_token={token}&limit=6&country=in"
                req = urllib.request.Request(url, headers={"User-Agent": "SmartParkSystem/2.5"})
                with urllib.request.urlopen(req, timeout=6) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    for feat in data.get("features", []):
                        coords = feat.get("center", [0, 0])
                        results.append({
                            "id": feat.get("id"),
                            "label": feat.get("text", q),
                            "display_name": feat.get("place_name", q),
                            "lng": coords[0],
                            "lat": coords[1],
                            "type": feat.get("place_type", ["place"])[0].upper(),
                            "provider": "Mapbox"
                        })
                if results:
                    self.geocode_cache[cache_key] = results
                    return results
            except Exception as e:
                print(f"[RoadRoutingService] Mapbox geocoding failed, trying fallback: {e}")

        # 2. Fallback to OpenStreetMap Nominatim Geocoding
        try:
            params = {
                "format": "json",
                "q": q,
                "addressdetails": 1,
                "limit": 6
            }
            url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartParkingManagementSystem/2.5 (contact@smartpark.edu)"})
            with urllib.request.urlopen(req, timeout=8) as response:
                items = json.loads(response.read().decode("utf-8"))
                for it in items:
                    results.append({
                        "id": str(it.get("osm_id", it.get("place_id"))),
                        "label": it.get("name") or it.get("display_name", "").split(",")[0],
                        "display_name": it.get("display_name", ""),
                        "lng": float(it.get("lon")),
                        "lat": float(it.get("lat")),
                        "type": (it.get("type") or it.get("class") or "LOCATION").upper(),
                        "provider": "OpenStreetMap"
                    })
        except Exception as e:
            print(f"[RoadRoutingService] Nominatim geocoding failed: {e}")

        self.geocode_cache[cache_key] = results
        return results

    def calculate_road_routes(
        self,
        start_lng: float,
        start_lat: float,
        dest_lng: float,
        dest_lat: float,
        alternatives: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates road-based driving routes between start and destination coordinates.
        Identifies the Fastest Route and Shortest Route.
        Uses Mapbox Directions API (with traffic) if token present, or OSRM Driving Engine.
        """
        token = self.get_mapbox_token()
        has_live_traffic = False
        traffic_msg = "Standard road routing active. Live traffic requires MAPBOX_ACCESS_TOKEN."

        routes_list: List[Dict[str, Any]] = []

        # 1. Try Mapbox Directions API (with traffic-aware routing)
        if token:
            try:
                coords_str = f"{start_lng},{start_lat};{dest_lng},{dest_lat}"
                url = (
                    f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coords_str}?"
                    f"alternatives={'true' if alternatives else 'false'}&geometries=geojson&overview=full&steps=true&access_token={token}"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "SmartParkSystem/2.5"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("code") == "Ok" and data.get("routes"):
                        has_live_traffic = True
                        traffic_msg = "Live traffic conditions active (Mapbox Driving-Traffic)."
                        for idx, r in enumerate(data["routes"]):
                            routes_list.append(self._format_route(r, provider="Mapbox Traffic", index=idx))
            except Exception as e:
                print(f"[RoadRoutingService] Mapbox directions failed, falling back to OSRM: {e}")

        # 2. Fallback to OSRM Driving Engine
        if not routes_list:
            try:
                coords_str = f"{start_lng},{start_lat};{dest_lng},{dest_lat}"
                url = (
                    f"https://router.project-osrm.org/route/v1/driving/{coords_str}?"
                    f"overview=full&geometries=geojson&alternatives={'true' if alternatives else 'false'}&steps=true"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "SmartParkingManagementSystem/2.5"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("code") == "Ok" and data.get("routes"):
                        for idx, r in enumerate(data["routes"]):
                            routes_list.append(self._format_route(r, provider="OSRM Driving", index=idx))
            except Exception as e:
                print(f"[RoadRoutingService] OSRM primary routing failed: {e}")

        # If only 1 route returned and distance is significant, generate an alternative route via an offset waypoint
        if len(routes_list) == 1 and alternatives:
            try:
                dist = routes_list[0]["distance_meters"]
                if dist > 5000:  # If distance > 5km, check alternate corridor
                    mid_lng = (start_lng + dest_lng) / 2.0
                    mid_lat = (start_lat + dest_lat) / 2.0
                    # Slight perpendicular offset (~1.5-2.5 km) to discover alternate highway/bypass
                    d_lng = dest_lng - start_lng
                    d_lat = dest_lat - start_lat
                    offset_lng = mid_lng - d_lat * 0.12
                    offset_lat = mid_lat + d_lng * 0.12

                    url2 = (
                        f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};"
                        f"{round(offset_lng, 6)},{round(offset_lat, 6)};{dest_lng},{dest_lat}?"
                        f"overview=full&geometries=geojson&steps=true"
                    )
                    req2 = urllib.request.Request(url2, headers={"User-Agent": "SmartParkingManagementSystem/2.5"})
                    with urllib.request.urlopen(req2, timeout=6) as response2:
                        data2 = json.loads(response2.read().decode("utf-8"))
                        if data2.get("code") == "Ok" and data2.get("routes"):
                            alt_r = data2["routes"][0]
                            # Ensure it's not identical in distance (< 3% difference)
                            if abs(alt_r["distance"] - routes_list[0]["distance_meters"]) > 500:
                                formatted_alt = self._format_route(alt_r, provider="OSRM Alternate Corridor", index=1)
                                routes_list.append(formatted_alt)
            except Exception as e:
                pass  # Alternate route is optional

        if not routes_list:
            return {
                "success": False,
                "error": "No road driving route found between the selected coordinates. The locations may be unreachable by road.",
                "routes": []
            }

        # 3. Label Fastest and Shortest Routes accurately
        self._classify_routes(routes_list)

        return {
            "success": True,
            "routes_count": len(routes_list),
            "has_live_traffic": has_live_traffic,
            "traffic_status_message": traffic_msg,
            "routes": routes_list
        }

    def _format_route(self, raw_route: Dict[str, Any], provider: str, index: int) -> Dict[str, Any]:
        """Converts raw API route into normalized structure."""
        dist_m = float(raw_route.get("distance", 0))
        dur_s = float(raw_route.get("duration", 0))

        # Extract step by step instructions
        steps = []
        for leg in raw_route.get("legs", []):
            for st in leg.get("steps", []):
                instruction = ""
                maneuver = st.get("maneuver", {})
                m_type = maneuver.get("type", "")
                m_mod = maneuver.get("modifier", "")
                st_name = st.get("name", "")

                if m_type == "depart":
                    instruction = f"Head on {st_name or 'road'}"
                elif m_type == "arrive":
                    instruction = "Arrive at destination"
                elif m_type == "turn":
                    instruction = f"Turn {m_mod} onto {st_name or 'road'}"
                else:
                    instruction = f"{m_type.capitalize()} {m_mod} on {st_name or 'road'}"

                steps.append({
                    "instruction": instruction.strip(),
                    "distance_meters": round(st.get("distance", 0), 1),
                    "duration_seconds": round(st.get("duration", 0), 1),
                    "street_name": st_name
                })

        geometry = raw_route.get("geometry", {})

        return {
            "id": f"route-{index + 1}",
            "route_name": raw_route.get("name") or (f"Route via {steps[1]['street_name']}" if len(steps) > 2 and steps[1]['street_name'] else f"Route Option {index + 1}"),
            "distance_meters": round(dist_m, 1),
            "distance_km": round(dist_m / 1000.0, 2),
            "duration_seconds": round(dur_s, 1),
            "duration_minutes": round(dur_s / 60.0, 1),
            "duration_text": self._format_duration(dur_s),
            "geometry": geometry,
            "steps": steps,
            "provider": provider,
            "is_fastest": False,
            "is_shortest": False,
            "route_type": "Standard"
        }

    def _classify_routes(self, routes: List[Dict[str, Any]]) -> None:
        """Determines which route is the Fastest and which is the Shortest."""
        if not routes:
            return

        min_duration = min(r["duration_seconds"] for r in routes)
        min_distance = min(r["distance_meters"] for r in routes)

        for r in routes:
            is_fast = (abs(r["duration_seconds"] - min_duration) < 1.0)
            is_short = (abs(r["distance_meters"] - min_distance) < 5.0)

            r["is_fastest"] = is_fast
            r["is_shortest"] = is_short

            if is_fast and is_short:
                r["route_type"] = "Fastest & Shortest Route"
            elif is_fast:
                r["route_type"] = "Fastest Route"
            elif is_short:
                r["route_type"] = "Shortest Distance Route"
            else:
                r["route_type"] = "Alternative Route"


    def _format_duration(self, seconds: float) -> str:
        mins = int(round(seconds / 60.0))
        if mins < 60:
            return f"{mins} min"
        hours = mins // 60
        rem_mins = mins % 60
        if rem_mins == 0:
            return f"{hours} hr"
        return f"{hours} hr {rem_mins} min"


road_routing_service = RoadRoutingService()
