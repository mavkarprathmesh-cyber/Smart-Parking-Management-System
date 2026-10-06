"""
Graph Navigation Service Module
Builds the campus road network graph from SQLite database and runs pathfinding algorithms:
- Dijkstra's Algorithm (Min-Heap) for shortest physical distance
- BFS for minimum hop count
- DFS for path exploration & connectivity
- Blocked lane simulation
"""

from typing import Dict, Any, List, Optional
import sqlite3
from database.db import get_db_connection
from dsa.graph import ParkingGraph


class GraphService:
    def __init__(self):
        self.graph = ParkingGraph()
        self.load_graph_from_db()

    def load_graph_from_db(self):
        """Rebuilds the in-memory graph from database tables."""
        from database.db import init_db
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Load nodes
        cursor.execute("SELECT * FROM graph_nodes")
        nodes = [dict(row) for row in cursor.fetchall()]

        # Load edges
        cursor.execute("SELECT * FROM graph_edges")
        edges = [dict(row) for row in cursor.fetchall()]
        conn.close()

        self.graph = ParkingGraph()

        for n in nodes:
            self.graph.add_node(n["node_id"], n["label"], n["node_type"], float(n["x"]), float(n["y"]))

        for e in edges:
            self.graph.add_edge(
                u=e["u"],
                v=e["v"],
                weight=float(e["weight"]),
                bidirectional=bool(e["bidirectional"]),
                is_blocked=bool(e["is_blocked"]),
                lane_name=e["lane_name"] or f"{e['u']}->{e['v']}"
            )

    def get_shortest_route(self, start_node: str, end_node: str, algorithm: str = "DIJKSTRA") -> Dict[str, Any]:
        """
        Calculates path between nodes using selected algorithm: DIJKSTRA, BFS, or DFS.
        """
        algo = algorithm.upper()
        if algo == "DIJKSTRA":
            res = self.graph.dijkstra_shortest_path(start_node, end_node)
        elif algo == "BFS":
            res = self.graph.bfs_shortest_hops(start_node, end_node)
        elif algo == "DFS":
            res = self.graph.dfs_path(start_node, end_node)
        else:
            return {"success": False, "error": f"Unknown algorithm: {algorithm}"}

        # Add node coordinate details for frontend canvas/SVG drawing
        if res.get("success") and "path" in res:
            path_coords = []
            for node_id in res["path"]:
                node_obj = self.graph.nodes.get(node_id)
                if node_obj:
                    path_coords.append({
                        "node_id": node_id,
                        "label": node_obj.label,
                        "type": node_obj.node_type,
                        "x": node_obj.x,
                        "y": node_obj.y
                    })
            res["path_coordinates"] = path_coords

        return res

    def compare_navigation_algorithms(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Runs Dijkstra, BFS, and DFS simultaneously on the same route for academic comparison.
        """
        dijkstra_res = self.graph.dijkstra_shortest_path(start_node, end_node)
        bfs_res = self.graph.bfs_shortest_hops(start_node, end_node)
        dfs_res = self.graph.dfs_path(start_node, end_node)

        return {
            "start_node": start_node,
            "end_node": end_node,
            "dijkstra": dijkstra_res,
            "bfs": bfs_res,
            "dfs": dfs_res,
            "comparison_summary": {
                "dijkstra_optimal_distance": dijkstra_res.get("total_distance_meters") if dijkstra_res.get("success") else None,
                "bfs_hop_count": bfs_res.get("hop_count") if bfs_res.get("success") else None,
                "dijkstra_ops": dijkstra_res.get("operations_count", 0),
                "bfs_ops": bfs_res.get("operations_count", 0),
                "dfs_ops": dfs_res.get("operations_count", 0)
            }
        }

    def toggle_edge_blocked(self, u: str, v: str, is_blocked: bool) -> Dict[str, Any]:
        """
        Toggles blocked state of an edge in database and updates graph in memory.
        """
        u, v = u.strip().upper(), v.strip().upper()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE graph_edges
        SET is_blocked = ?
        WHERE (u = ? AND v = ?) OR (u = ? AND v = ?)
        """, (1 if is_blocked else 0, u, v, v, u))
        conn.commit()
        conn.close()

        self.graph.set_edge_blocked(u, v, is_blocked)
        state_str = "BLOCKED" if is_blocked else "OPEN"
        return {
            "success": True,
            "message": f"Lane segment '{u} <-> {v}' is now {state_str}.",
            "u": u,
            "v": v,
            "is_blocked": is_blocked
        }

    def get_all_graph_elements(self) -> Dict[str, Any]:
        return self.graph.get_full_graph_data()


graph_service = GraphService()
