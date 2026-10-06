"""
Search Service Module
Demonstrates and benchmarks multi-structure indexing across:
1. Hash Table (Separate Chaining)
2. Binary Search Tree (BST)
3. AVL Tree (Self-Balancing BST)
4. Binary Search (on sorted array)
5. Linear Search (sequential scan)
"""

import time
from typing import Dict, Any, List, Optional
import sqlite3

from database.db import get_db_connection
from dsa.hash_table import HashTable
from dsa.trees import BinarySearchTree, AVLTree
from dsa.algorithms import linear_search, binary_search


class SearchService:
    def __init__(self):
        self.hash_table = HashTable(initial_capacity=67)
        self.bst = BinarySearchTree()
        self.avl = AVLTree()
        self.sorted_records_list: List[Dict[str, Any]] = []
        self.raw_records_list: List[Dict[str, Any]] = []
        self.rebuild_search_indices()

    def rebuild_search_indices(self):
        """Re-indexes all vehicles, slots, and users from the SQLite database."""
        from database.db import init_db
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch vehicles joined with users & slots
        cursor.execute("""
        SELECT v.vehicle_id, v.vehicle_number, v.vehicle_type, v.model_name, v.color,
               u.user_id, u.full_name as owner_name, u.phone, u.role,
               s.slot_id, s.zone_id, s.status as slot_status
        FROM vehicles v
        JOIN users u ON v.user_id = u.user_id
        LEFT JOIN parking_slots s ON s.assigned_vehicle_id = v.vehicle_id
        """)
        vehicle_records = [dict(row) for row in cursor.fetchall()]

        # Fetch all parking slots
        cursor.execute("""
        SELECT s.slot_id, s.zone_id, s.vehicle_type, s.status, s.distance_from_gate, s.priority,
               v.vehicle_number, u.full_name as owner_name
        FROM parking_slots s
        LEFT JOIN vehicles v ON s.assigned_vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        """)
        slot_records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Reset DSA indexes
        self.hash_table = HashTable(initial_capacity=67)
        self.bst = BinarySearchTree()
        self.avl = AVLTree()
        self.raw_records_list = []

        # Index Vehicles by Vehicle Number & Vehicle ID
        for v in vehicle_records:
            item = {"type": "VEHICLE", "data": v}
            # Key 1: Vehicle Number (e.g. KA-01-MG-2024)
            v_num = v["vehicle_number"].upper().strip()
            self.hash_table.insert(v_num, item)
            self.bst.insert(v_num, item)
            self.avl.insert(v_num, item)
            self.raw_records_list.append({"key": v_num, "item": item})

            # Key 2: Vehicle ID (e.g. V-101)
            v_id = v["vehicle_id"].upper().strip()
            self.hash_table.insert(v_id, item)
            self.bst.insert(v_id, item)
            self.avl.insert(v_id, item)
            self.raw_records_list.append({"key": v_id, "item": item})

            # Key 3: Owner Name
            owner = v["owner_name"].upper().strip()
            self.hash_table.insert(owner, item)
            self.bst.insert(owner, item)
            self.avl.insert(owner, item)

        # Index Slots by Slot ID
        for s in slot_records:
            item = {"type": "SLOT", "data": s}
            s_id = s["slot_id"].upper().strip()
            self.hash_table.insert(s_id, item)
            self.bst.insert(s_id, item)
            self.avl.insert(s_id, item)
            self.raw_records_list.append({"key": s_id, "item": item})

        # Prepare sorted list for Binary Search
        self.sorted_records_list = sorted(self.raw_records_list, key=lambda x: x["key"])

    def multi_search_compare(self, query: str) -> Dict[str, Any]:
        """
        Executes query simultaneously across 5 distinct DSA search methods and measures performance.
        """
        self.rebuild_search_indices()  # Ensure index is fresh
        clean_query = str(query).upper().strip()

        # 1. Hash Table Lookup
        t0 = time.perf_counter()
        hash_res, hash_comps, bucket_idx = self.hash_table.search(clean_query)
        hash_time_us = round((time.perf_counter() - t0) * 1_000_000, 2)

        # 2. Binary Search Tree (BST) Lookup
        t0 = time.perf_counter()
        bst_res, bst_comps = self.bst.search(clean_query)
        bst_time_us = round((time.perf_counter() - t0) * 1_000_000, 2)

        # 3. AVL Tree Lookup
        t0 = time.perf_counter()
        avl_res, avl_comps = self.avl.search(clean_query)
        avl_time_us = round((time.perf_counter() - t0) * 1_000_000, 2)

        # 4. Binary Search (on pre-sorted array)
        bin_search_res = binary_search(self.sorted_records_list, clean_query, key_fn=lambda x: x["key"])

        # 5. Linear Search (on array)
        lin_search_res = linear_search(self.raw_records_list, clean_query, key_fn=lambda x: x["key"])

        found = hash_res is not None or avl_res is not None or bst_res is not None
        match_data = hash_res or avl_res or bst_res

        return {
            "query": query,
            "found": found,
            "result_data": match_data,
            "total_indexed_elements": len(self.raw_records_list),
            "benchmarks": [
                {
                    "structure": "Hash Table (Separate Chaining)",
                    "time_microseconds": hash_time_us,
                    "comparisons": hash_comps,
                    "theoretical_best": "Ω(1)",
                    "theoretical_average": "Θ(1)",
                    "theoretical_worst": "O(n)",
                    "space_complexity": "O(n)",
                    "diagnostic": f"Mapped to Bucket #{bucket_idx} in hash table of size {self.hash_table.capacity}"
                },
                {
                    "structure": "AVL Tree (Self-Balancing BST)",
                    "time_microseconds": avl_time_us,
                    "comparisons": avl_comps,
                    "theoretical_best": "Ω(1)",
                    "theoretical_average": "Θ(log n)",
                    "theoretical_worst": "O(log n) (Guaranteed)",
                    "space_complexity": "O(n)",
                    "diagnostic": f"AVL Tree Height: {self.avl.height(self.avl.root)}, Rotations performed: {self.avl.rotations_count}"
                },
                {
                    "structure": "Binary Search Tree (BST)",
                    "time_microseconds": bst_time_us,
                    "comparisons": bst_comps,
                    "theoretical_best": "Ω(1)",
                    "theoretical_average": "Θ(log n)",
                    "theoretical_worst": "O(n)",
                    "space_complexity": "O(n)",
                    "diagnostic": f"BST Tree Height: {self.bst.get_height()}"
                },
                {
                    "structure": "Binary Search (Sorted Array)",
                    "time_microseconds": round(bin_search_res["execution_time_ms"] * 1000, 2),
                    "comparisons": bin_search_res["comparisons"],
                    "theoretical_best": "Ω(1)",
                    "theoretical_average": "Θ(log n)",
                    "theoretical_worst": "O(log n)",
                    "space_complexity": "O(1)",
                    "diagnostic": f"Array Index: {bin_search_res['index'] if bin_search_res['found'] else 'Not Found'}"
                },
                {
                    "structure": "Linear Search (Unsorted Scan)",
                    "time_microseconds": round(lin_search_res["execution_time_ms"] * 1000, 2),
                    "comparisons": lin_search_res["comparisons"],
                    "theoretical_best": "Ω(1)",
                    "theoretical_average": "Θ(n)",
                    "theoretical_worst": "O(n)",
                    "space_complexity": "O(1)",
                    "diagnostic": f"Iterated sequentially up to index {lin_search_res['index'] if lin_search_res['found'] else len(self.raw_records_list)}"
                }
            ]
        }


search_service = SearchService()
