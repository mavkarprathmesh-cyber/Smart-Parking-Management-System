"""
Algorithm Lab Service Module
Provides interactive execution and benchmarking testbed for:
- 7 Sorting Algorithms (Bubble, Selection, Insertion, Merge, Quick, Heap, Radix)
- 2 Array Search Algorithms (Linear, Binary)
- 3 Graph Traversal / Shortest Path Algorithms (BFS, DFS, Dijkstra)
"""

import random
import time
from typing import List, Dict, Any, Optional

from dsa.algorithms import (
    bubble_sort,
    selection_sort,
    insertion_sort,
    merge_sort,
    quick_sort,
    heap_sort,
    radix_sort,
    linear_search,
    binary_search
)
from .graph_service import graph_service


class LabService:
    def generate_dataset(self, size: int = 50, data_type: str = "RANDOM") -> List[int]:
        """
        Generates array of integers based on distribution:
        - RANDOM: Unordered random integers
        - SORTED: Already ascending
        - REVERSED: Descending order (worst-case test for bubble/quick/insertion)
        - NEARLY_SORTED: 90% sorted with few inversions
        """
        size = max(5, min(size, 2000))
        if data_type == "SORTED":
            return list(range(1, size + 1))
        elif data_type == "REVERSED":
            return list(range(size, 0, -1))
        elif data_type == "NEARLY_SORTED":
            arr = list(range(1, size + 1))
            for _ in range(max(1, size // 10)):
                i, j = random.randint(0, size - 1), random.randint(0, size - 1)
                arr[i], arr[j] = arr[j], arr[i]
            return arr
        else:  # RANDOM
            return [random.randint(1, 1000) for _ in range(size)]

    def run_all_sorts(self, arr: List[int]) -> Dict[str, Any]:
        """
        Runs all 7 sorting algorithms on identical copy of input array and measures operations.
        """
        results = []

        # 1. Bubble Sort (limit size if > 800 to avoid long wait)
        if len(arr) <= 1000:
            results.append(bubble_sort(arr))
        else:
            results.append({
                "algorithm": "Bubble Sort",
                "skipped": True,
                "reason": "Skipped for n > 1000 due to O(n²) time complexity"
            })

        # 2. Selection Sort
        if len(arr) <= 1000:
            results.append(selection_sort(arr))
        else:
            results.append({
                "algorithm": "Selection Sort",
                "skipped": True,
                "reason": "Skipped for n > 1000 due to O(n²) time complexity"
            })

        # 3. Insertion Sort
        if len(arr) <= 1000:
            results.append(insertion_sort(arr))
        else:
            results.append({
                "algorithm": "Insertion Sort",
                "skipped": True,
                "reason": "Skipped for n > 1000 due to O(n²) time complexity"
            })

        # 4. Merge Sort
        results.append(merge_sort(arr))

        # 5. Quick Sort
        results.append(quick_sort(arr))

        # 6. Heap Sort
        results.append(heap_sort(arr))

        # 7. Radix Sort
        results.append(radix_sort(arr))

        return {
            "input_size": len(arr),
            "sample_input": arr[:20] if len(arr) > 20 else arr,
            "results": results
        }

    def run_search_lab(self, arr: List[int], target: int) -> Dict[str, Any]:
        """
        Compares Linear Search vs Binary Search on the array.
        """
        # Linear Search on original array
        lin_res = linear_search(arr, target)

        # Binary Search requires sorted array
        sorted_arr = sorted(arr)
        bin_res = binary_search(sorted_arr, target)

        return {
            "target": target,
            "input_size": len(arr),
            "linear_search": lin_res,
            "binary_search": bin_res
        }

    def run_graph_lab(self, start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Runs BFS, DFS, and Dijkstra on the campus road graph.
        """
        return graph_service.compare_navigation_algorithms(start_node, end_node)


lab_service = LabService()
