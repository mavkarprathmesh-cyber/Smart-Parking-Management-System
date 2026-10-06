"""
DSA Graph Module
Implements:
1. Weighted Graph with Adjacency List (representing gates, lanes, junctions, zones, and parking slots)
2. Breadth-First Search (BFS) for minimum-hop unweighted navigation
3. Depth-First Search (DFS) for zone exploration and reachability/connectivity checking
4. Dijkstra's Algorithm (using Min-Heap) for finding shortest weighted physical distance routes
5. Blocked/Congested Lane handling
"""

from typing import Dict, List, Tuple, Optional, Set, Any
import heapq


class GraphNode:
    def __init__(self, node_id: str, label: str, node_type: str, x: float = 0, y: float = 0):
        self.node_id = str(node_id).strip()
        self.label = label
        self.node_type = node_type  # 'GATE', 'JUNCTION', 'LANE', 'ZONE', 'SLOT'
        self.x = x
        self.y = y

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "label": self.label,
            "type": self.node_type,
            "x": self.x,
            "y": self.y
        }


class GraphEdge:
    def __init__(self, u: str, v: str, weight: float, is_blocked: bool = False, lane_name: str = ""):
        self.u = str(u).strip()
        self.v = str(v).strip()
        self.weight = float(weight)
        self.is_blocked = is_blocked
        self.lane_name = lane_name or f"{u}->{v}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.u,
            "to": self.v,
            "weight": self.weight,
            "is_blocked": self.is_blocked,
            "lane_name": self.lane_name
        }


class ParkingGraph:
    """
    Graph representation of parking campus layout.
    Time Complexity:
      - Add Vertex / Edge: O(1)
      - BFS: O(V + E)
      - DFS: O(V + E)
      - Dijkstra: O((V + E) log V) with min-heap
    Space Complexity: O(V + E)
    """
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        # Adjacency list: u -> list of (v, weight, edge_obj)
        self.adj: Dict[str, List[Tuple[str, float, GraphEdge]]] = {}

    def add_node(self, node_id: str, label: str, node_type: str, x: float = 0, y: float = 0) -> None:
        node_id = str(node_id).strip()
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(node_id, label, node_type, x, y)
            self.adj[node_id] = []

    def add_edge(self, u: str, v: str, weight: float, bidirectional: bool = True, is_blocked: bool = False, lane_name: str = "") -> None:
        u = str(u).strip()
        v = str(v).strip()
        if u not in self.nodes:
            self.add_node(u, u, "JUNCTION")
        if v not in self.nodes:
            self.add_node(v, v, "JUNCTION")

        edge_fwd = GraphEdge(u, v, weight, is_blocked, lane_name)
        self.adj[u].append((v, weight, edge_fwd))

        if bidirectional:
            edge_rev = GraphEdge(v, u, weight, is_blocked, lane_name)
            self.adj[v].append((u, weight, edge_rev))

    def set_edge_blocked(self, u: str, v: str, is_blocked: bool) -> bool:
        u, v = str(u).strip(), str(v).strip()
        found = False
        if u in self.adj:
            for i, (neigh, w, edge) in enumerate(self.adj[u]):
                if neigh == v:
                    edge.is_blocked = is_blocked
                    found = True
        if v in self.adj:
            for i, (neigh, w, edge) in enumerate(self.adj[v]):
                if neigh == u:
                    edge.is_blocked = is_blocked
                    found = True
        return found

    # ==========================================
    # 1. BREADTH-FIRST SEARCH (BFS)
    # ==========================================
    def bfs_shortest_hops(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Finds path with minimum number of hops (unweighted) using a FIFO queue.
        Returns path, total_hops, nodes_visited, and execution stats.
        """
        start_node, end_node = str(start_node).strip(), str(end_node).strip()
        if start_node not in self.nodes or end_node not in self.nodes:
            return {"success": False, "error": "Start or End node does not exist"}

        visited: Set[str] = set()
        queue: List[Tuple[str, List[str], float]] = [(start_node, [start_node], 0.0)]
        visited.add(start_node)
        traversal_order: List[str] = []
        operations = 0

        while queue:
            operations += 1
            curr, path, total_dist = queue.pop(0)
            traversal_order.append(curr)

            if curr == end_node:
                return {
                    "success": True,
                    "algorithm": "BFS (Minimum Hops)",
                    "path": path,
                    "hop_count": len(path) - 1,
                    "total_distance": round(total_dist, 2),
                    "traversal_order": traversal_order,
                    "nodes_visited_count": len(visited),
                    "operations_count": operations,
                    "complexity": "O(V + E)"
                }

            for neigh, weight, edge in self.adj.get(curr, []):
                if not edge.is_blocked and neigh not in visited:
                    visited.add(neigh)
                    queue.append((neigh, path + [neigh], total_dist + weight))

        return {
            "success": False,
            "error": "No reachable path found between nodes (route may be blocked)",
            "traversal_order": traversal_order,
            "nodes_visited_count": len(visited),
            "operations_count": operations
        }

    # ==========================================
    # 2. DEPTH-FIRST SEARCH (DFS)
    # ==========================================
    def dfs_path(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Explores paths deeply using recursion/call stack.
        """
        start_node, end_node = str(start_node).strip(), str(end_node).strip()
        if start_node not in self.nodes or end_node not in self.nodes:
            return {"success": False, "error": "Start or End node does not exist"}

        visited: Set[str] = set()
        traversal_order: List[str] = []
        operations = [0]

        def dfs_recursive(curr: str, target: str, current_path: List[str], current_dist: float) -> Optional[Tuple[List[str], float]]:
            operations[0] += 1
            visited.add(curr)
            traversal_order.append(curr)

            if curr == target:
                return current_path, current_dist

            for neigh, weight, edge in self.adj.get(curr, []):
                if not edge.is_blocked and neigh not in visited:
                    res = dfs_recursive(neigh, target, current_path + [neigh], current_dist + weight)
                    if res is not None:
                        return res
            return None

        result = dfs_recursive(start_node, end_node, [start_node], 0.0)

        if result:
            path, total_dist = result
            return {
                "success": True,
                "algorithm": "DFS (Depth-First Search)",
                "path": path,
                "hop_count": len(path) - 1,
                "total_distance": round(total_dist, 2),
                "traversal_order": traversal_order,
                "nodes_visited_count": len(visited),
                "operations_count": operations[0],
                "complexity": "O(V + E)"
            }
        else:
            return {
                "success": False,
                "error": "Destination unreachable via DFS traversal",
                "traversal_order": traversal_order,
                "nodes_visited_count": len(visited),
                "operations_count": operations[0]
            }

    # ==========================================
    # 3. DIJKSTRA'S ALGORITHM (Shortest Weighted Route)
    # ==========================================
    def dijkstra_shortest_path(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Computes the absolute shortest physical route by meter distance using a Priority Queue / Min Heap.
        Time Complexity: O((V + E) log V)
        """
        start_node, end_node = str(start_node).strip(), str(end_node).strip()
        if start_node not in self.nodes or end_node not in self.nodes:
            return {"success": False, "error": f"Node '{start_node}' or '{end_node}' not found in graph"}

        distances: Dict[str, float] = {node: float('inf') for node in self.nodes}
        previous: Dict[str, Optional[str]] = {node: None for node in self.nodes}
        distances[start_node] = 0.0

        # Min heap stores (distance, counter, node_id)
        pq = [(0.0, 0, start_node)]
        counter = 0
        visited: Set[str] = set()
        traversal_order: List[str] = []
        operations = 0

        while pq:
            operations += 1
            curr_dist, _, u = heapq.heappop(pq)

            if u in visited:
                continue
            visited.add(u)
            traversal_order.append(u)

            if u == end_node:
                break

            for v, weight, edge in self.adj.get(u, []):
                if edge.is_blocked:
                    continue  # Skip blocked lanes

                new_dist = curr_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    previous[v] = u
                    counter += 1
                    heapq.heappush(pq, (new_dist, counter, v))

        if distances[end_node] == float('inf'):
            return {
                "success": False,
                "error": f"No available route found to {end_node}. Check if connecting lanes are blocked.",
                "traversal_order": traversal_order,
                "nodes_visited_count": len(visited),
                "operations_count": operations
            }

        # Reconstruct path from end to start
        path = []
        curr = end_node
        while curr is not None:
            path.append(curr)
            curr = previous[curr]
        path.reverse()

        # Build detailed step by step directions
        steps = []
        for i in range(len(path) - 1):
            n1, n2 = path[i], path[i+1]
            seg_dist = 0
            for v, w, e in self.adj.get(n1, []):
                if v == n2:
                    seg_dist = w
                    break
            steps.append({
                "from": n1,
                "to": n2,
                "from_label": self.nodes.get(n1, GraphNode(n1, n1, "")).label,
                "to_label": self.nodes.get(n2, GraphNode(n2, n2, "")).label,
                "segment_distance": seg_dist
            })

        return {
            "success": True,
            "algorithm": "Dijkstra's Algorithm (Min-Heap)",
            "start": start_node,
            "destination": end_node,
            "path": path,
            "total_distance_meters": round(distances[end_node], 2),
            "hop_count": len(path) - 1,
            "steps": steps,
            "traversal_order": traversal_order,
            "nodes_visited_count": len(visited),
            "operations_count": operations,
            "complexity": "O((V + E) log V)"
        }

    def get_full_graph_data(self) -> Dict[str, Any]:
        node_list = [node.to_dict() for node in self.nodes.values()]
        edge_list = []
        seen_edges = set()
        for u in self.adj:
            for v, w, edge in self.adj[u]:
                edge_id = tuple(sorted([u, v]))
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edge_list.append(edge.to_dict())

        return {
            "nodes": node_list,
            "edges": edge_list,
            "total_nodes": len(node_list),
            "total_edges": len(edge_list)
        }
