"""
DSA Complexity Reference & Runtime Profiling Module
Provides theoretical Big-O, Ω, and Θ complexities for all data structures and algorithms,
plus educational explanations for college viva and project demonstrations.
"""

from typing import Dict, Any, List
import time


DSA_METRICS_MAP: Dict[str, Dict[str, Any]] = {
    "Array": {
        "module": "Parking Slot Records / Direct Indexing",
        "description": "Contiguous memory allocation allowing instant random access by slot index.",
        "time_access": "O(1)",
        "time_search": "O(n)",
        "time_insert": "O(n) (end: O(1))",
        "time_delete": "O(n)",
        "space": "O(n)",
        "why_used": "Used for the primary parking slot inventory and status matrix for instant indexed lookups."
    },
    "Singly Linked List": {
        "module": "Vehicle & Parking History",
        "description": "Sequential chain of nodes with next pointers.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1) (prepend/append with tail)",
        "time_delete": "O(n)",
        "space": "O(n)",
        "why_used": "Ideal for dynamic sequential logging of vehicle entries and exits without pre-allocating buffer sizes."
    },
    "Doubly Linked List": {
        "module": "Bidirectional Navigation & Audit Trail",
        "description": "Nodes with both next and previous pointers.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1)",
        "time_delete": "O(1) (with direct node ref)",
        "space": "O(n)",
        "why_used": "Enables seamless forward and backward stepping through parking transactions and navigation waypoints."
    },
    "Circular Linked List": {
        "module": "Cyclic Zone Traversal",
        "description": "Tail node points back to head node forming a closed loop.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1) / O(n)",
        "time_delete": "O(n)",
        "space": "O(n)",
        "why_used": "Enables continuous cyclic inspection of parking zones (Zone A -> B -> C -> D -> A) for guards and patrol bots."
    },
    "Stack": {
        "module": "Undo Operations & Action Reversals",
        "description": "LIFO (Last-In-First-Out) linear container.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1) (Push)",
        "time_delete": "O(1) (Pop)",
        "space": "O(n)",
        "why_used": "Maintains action history allowing operators to undo accidental slot status changes or cancellations."
    },
    "Queue (FIFO)": {
        "module": "Normal Parking Request Queue",
        "description": "FIFO (First-In-First-Out) linear container.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1) (Enqueue)",
        "time_delete": "O(1) (Dequeue)",
        "space": "O(n)",
        "why_used": "Ensures fairness (FCFS) for vehicles arriving at the parking barrier."
    },
    "Circular Queue": {
        "module": "Vehicle-Entry Batch Processing Buffer",
        "description": "Fixed size ring-buffer queue with front/rear wrap-around.",
        "time_access": "O(1)",
        "time_search": "O(n)",
        "time_insert": "O(1)",
        "time_delete": "O(1)",
        "space": "O(k) fixed capacity",
        "why_used": "Prevents memory reallocations at high-traffic entry boom barriers with fixed hardware buffers."
    },
    "Priority Queue (Min-Heap)": {
        "module": "Emergency & VIP Request Prioritization",
        "description": "Binary Heap ordered by priority level (Emergency > Accessibility > VIP > Normal).",
        "time_access": "O(1) (Peek Min)",
        "time_search": "O(n)",
        "time_insert": "O(log n) (Push)",
        "time_delete": "O(log n) (Extract Min)",
        "space": "O(n)",
        "why_used": "Guarantees emergency vehicles and disabled drivers receive immediate priority slot allocation before normal queues."
    },
    "Deque": {
        "module": "Double-Ended Request Processing",
        "description": "Queue supporting O(1) front and rear insertions and removals.",
        "time_access": "O(n)",
        "time_search": "O(n)",
        "time_insert": "O(1) (Front/Rear)",
        "time_delete": "O(1) (Front/Rear)",
        "space": "O(n)",
        "why_used": "Allows high-priority override requests to be pushed directly to the front or deferred to the rear."
    },
    "Binary Search Tree (BST)": {
        "module": "Vehicle & Slot Search Indexing",
        "description": "Hierarchical node structure where left < root < right.",
        "time_access": "O(log n) avg / O(n) worst",
        "time_search": "O(log n) avg / O(n) worst",
        "time_insert": "O(log n) avg / O(n) worst",
        "time_delete": "O(log n) avg / O(n) worst",
        "space": "O(n)",
        "why_used": "Provides ordered indexing and logarithmic search over vehicle registration numbers."
    },
    "AVL Tree": {
        "module": "Self-Balancing Fast Indexing",
        "description": "Strictly balanced BST maintaining height difference (balance factor) <= 1 via rotations.",
        "time_access": "O(log n) guaranteed",
        "time_search": "O(log n) guaranteed",
        "time_insert": "O(log n) guaranteed",
        "time_delete": "O(log n) guaranteed",
        "space": "O(n)",
        "why_used": "Eliminates worst-case O(n) skewness of BSTs, guaranteeing predictable sub-millisecond search times."
    },
    "Hash Table": {
        "module": "Instant Vehicle / Slot Lookup",
        "description": "Key-value indexing with polynomial hash function and separate chaining collision resolution.",
        "time_access": "O(1) avg / O(n) worst",
        "time_search": "O(1) avg / O(n) worst",
        "time_insert": "O(1) avg / O(n) worst",
        "time_delete": "O(1) avg / O(n) worst",
        "space": "O(n)",
        "why_used": "Provides instant O(1) retrieval when vehicle license plates are scanned at entry/exit gates."
    },
    "Min Heap": {
        "module": "Nearest / Best Candidate Slot Selection",
        "description": "Complete binary tree satisfying min-heap property.",
        "time_access": "O(1) (Peek)",
        "time_search": "O(n)",
        "time_insert": "O(log n)",
        "time_delete": "O(log n)",
        "space": "O(n)",
        "why_used": "Extracts the closest candidate slot by physical distance in logarithmic time."
    },
    "Graph (Weighted Adjacency List)": {
        "module": "Parking Campus Road Network & Lanes",
        "description": "Vertices (Gates, Junctions, Zones, Slots) and Weighted Edges (Distances in meters).",
        "time_access": "O(1) (Adjacency lookup)",
        "time_search": "O(V + E)",
        "time_insert": "O(1)",
        "time_delete": "O(V + E)",
        "space": "O(V + E)",
        "why_used": "Accurately models the physical road network, lanes, one-way paths, and blocked roads."
    },
    "Dijkstra's Algorithm": {
        "module": "Shortest Physical Route Navigation",
        "description": "Greedy single-source shortest path algorithm using a Min-Heap priority queue.",
        "time_complexity": "O((V + E) log V)",
        "space_complexity": "O(V)",
        "why_used": "Finds the exact shortest driving route in meters from entry gate to the assigned parking bay."
    },
    "Breadth-First Search (BFS)": {
        "module": "Minimum-Hop Lane Navigation",
        "description": "Level-order graph exploration using a FIFO queue.",
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "why_used": "Finds the route with the minimum number of turns/junctions regardless of distance."
    },
    "Depth-First Search (DFS)": {
        "module": "Zone Connectivity & Exploration",
        "description": "Deep graph traversal using recursive call stack.",
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V)",
        "why_used": "Validates reachability and detects disconnected parking zones."
    },
    "Merge Sort": {
        "module": "Performance Lab & Report Ordering",
        "description": "Stable divide-and-conquer sorting algorithm.",
        "time_complexity": "O(n log n) best/avg/worst",
        "space_complexity": "O(n)",
        "why_used": "Guarantees consistent O(n log n) sorting for generating analytical reports."
    },
    "Quick Sort": {
        "module": "Performance Lab & In-place Sorting",
        "description": "Fast divide-and-conquer algorithm with in-place pivot partitioning.",
        "time_complexity": "Ω(n log n) best, Θ(n log n) avg, O(n²) worst",
        "space_complexity": "O(log n)",
        "why_used": "Standard high-performance cache-friendly sorting algorithm."
    },
    "Binary Search": {
        "module": "Sorted Record Search",
        "description": "Divide-and-conquer search on sorted array.",
        "time_complexity": "Ω(1) best, Θ(log n) avg, O(log n) worst",
        "space_complexity": "O(1)",
        "why_used": "Allows logarithmic search over sorted vehicle timestamps and license registrations."
    },
    "Greedy Algorithm": {
        "module": "Smart Candidate Slot Allocation",
        "description": "Makes locally optimal choice (closest compatible bay) at each step.",
        "time_complexity": "O(n) candidate scan / O(log n) with heap",
        "space_complexity": "O(1)",
        "why_used": "Ensures drivers are directed to the nearest available space instantly upon arrival."
    }
}


def get_all_dsa_explanations() -> List[Dict[str, Any]]:
    result = []
    for name, data in DSA_METRICS_MAP.items():
        entry = dict(data)
        entry["name"] = name
        result.append(entry)
    return result
