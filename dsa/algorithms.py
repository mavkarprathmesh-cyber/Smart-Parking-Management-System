"""
DSA Algorithms Module
Implements:
1. Sorting Algorithms: Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort, Heap Sort, Radix Sort
2. Searching Algorithms: Linear Search, Binary Search
3. Greedy Slot Allocation Strategy
4. Recursive Algorithms
Each algorithm tracks execution time, comparisons, swaps/operations, and theoretical time/space complexities.
"""

import time
from typing import List, Dict, Any, Tuple, Callable, Optional


# ==========================================
# 1. SORTING ALGORITHMS
# ==========================================

def bubble_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Bubble Sort: Repeatedly steps through list, compares adjacent elements and swaps them.
    Complexity:
      - Best: O(n) (with early exit)
      - Average: O(n^2)
      - Worst: O(n^2)
      - Space: O(1)
    """
    a = list(arr)
    n = len(a)
    comparisons = 0
    swaps = 0
    start_time = time.perf_counter()

    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            comparisons += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
                swapped = True
        if not swapped:
            break

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Bubble Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": comparisons,
        "swaps": swaps,
        "operations": comparisons + swaps,
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n)",
        "time_complexity_avg": "Θ(n²)",
        "time_complexity_worst": "O(n²)",
        "space_complexity": "O(1)"
    }


def selection_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Selection Sort: Finds minimum element from unsorted part and puts it at beginning.
    Complexity: Best: O(n^2), Average: O(n^2), Worst: O(n^2), Space: O(1)
    """
    a = list(arr)
    n = len(a)
    comparisons = 0
    swaps = 0
    start_time = time.perf_counter()

    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            comparisons += 1
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            swaps += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Selection Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": comparisons,
        "swaps": swaps,
        "operations": comparisons + swaps,
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n²)",
        "time_complexity_avg": "Θ(n²)",
        "time_complexity_worst": "O(n²)",
        "space_complexity": "O(1)"
    }


def insertion_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Insertion Sort: Builds sorted array one item at a time.
    Complexity: Best: O(n), Average: O(n^2), Worst: O(n^2), Space: O(1)
    """
    a = list(arr)
    n = len(a)
    comparisons = 0
    shifts = 0
    start_time = time.perf_counter()

    for i in range(1, n):
        key = a[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if a[j] > key:
                a[j + 1] = a[j]
                shifts += 1
                j -= 1
            else:
                break
        a[j + 1] = key

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Insertion Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": comparisons,
        "swaps": shifts,
        "operations": comparisons + shifts,
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n)",
        "time_complexity_avg": "Θ(n²)",
        "time_complexity_worst": "O(n²)",
        "space_complexity": "O(1)"
    }


def merge_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Merge Sort: Divide and Conquer sorting algorithm.
    Complexity: Best: O(n log n), Average: O(n log n), Worst: O(n log n), Space: O(n)
    """
    a = list(arr)
    n = len(a)
    comparisons = [0]
    moves = [0]
    start_time = time.perf_counter()

    def _merge_sort_rec(lst: List[int]) -> List[int]:
        if len(lst) <= 1:
            return lst
        mid = len(lst) // 2
        left = _merge_sort_rec(lst[:mid])
        right = _merge_sort_rec(lst[mid:])
        return _merge(left, right)

    def _merge(left: List[int], right: List[int]) -> List[int]:
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            comparisons[0] += 1
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
            moves[0] += 1
        while i < len(left):
            merged.append(left[i])
            i += 1
            moves[0] += 1
        while j < len(right):
            merged.append(right[j])
            j += 1
            moves[0] += 1
        return merged

    sorted_res = _merge_sort_rec(a)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "algorithm": "Merge Sort",
        "sorted_array": sorted_res,
        "input_size": n,
        "comparisons": comparisons[0],
        "swaps": moves[0],
        "operations": comparisons[0] + moves[0],
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n log n)",
        "time_complexity_avg": "Θ(n log n)",
        "time_complexity_worst": "O(n log n)",
        "space_complexity": "O(n)"
    }


def quick_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Quick Sort: Divide and Conquer with pivot partitioning.
    Complexity: Best: O(n log n), Average: O(n log n), Worst: O(n^2), Space: O(log n)
    """
    a = list(arr)
    n = len(a)
    comparisons = [0]
    swaps = [0]
    start_time = time.perf_counter()

    def _quick_sort_rec(low: int, high: int):
        if low < high:
            pi = _partition(low, high)
            _quick_sort_rec(low, pi - 1)
            _quick_sort_rec(pi + 1, high)

    def _partition(low: int, high: int) -> int:
        pivot = a[high]
        i = low - 1
        for j in range(low, high):
            comparisons[0] += 1
            if a[j] < pivot:
                i += 1
                a[i], a[j] = a[j], a[i]
                swaps[0] += 1
        a[i + 1], a[high] = a[high], a[i + 1]
        swaps[0] += 1
        return i + 1

    _quick_sort_rec(0, n - 1)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "algorithm": "Quick Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": comparisons[0],
        "swaps": swaps[0],
        "operations": comparisons[0] + swaps[0],
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n log n)",
        "time_complexity_avg": "Θ(n log n)",
        "time_complexity_worst": "O(n²)",
        "space_complexity": "O(log n)"
    }


def heap_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Heap Sort: Comparison-based sorting using a Binary Max-Heap.
    Complexity: Best: O(n log n), Average: O(n log n), Worst: O(n log n), Space: O(1)
    """
    a = list(arr)
    n = len(a)
    comparisons = [0]
    swaps = [0]
    start_time = time.perf_counter()

    def _heapify(n_size: int, i: int):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2

        if l < n_size:
            comparisons[0] += 1
            if a[l] > a[largest]:
                largest = l

        if r < n_size:
            comparisons[0] += 1
            if a[r] > a[largest]:
                largest = r

        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            swaps[0] += 1
            _heapify(n_size, largest)

    for i in range(n // 2 - 1, -1, -1):
        _heapify(n, i)

    for i in range(n - 1, 0, -1):
        a[i], a[0] = a[0], a[i]
        swaps[0] += 1
        _heapify(i, 0)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Heap Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": comparisons[0],
        "swaps": swaps[0],
        "operations": comparisons[0] + swaps[0],
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(n log n)",
        "time_complexity_avg": "Θ(n log n)",
        "time_complexity_worst": "O(n log n)",
        "space_complexity": "O(1)"
    }


def radix_sort(arr: List[int]) -> Dict[str, Any]:
    """
    Radix Sort: Non-comparative integer sorting algorithm.
    Complexity: Best/Avg/Worst: O(d * (n + b)) where d is digits and b is base (10). Space: O(n + b)
    """
    a = [abs(x) for x in arr]  # handles non-negative integers
    n = len(a)
    if n == 0:
        return {"algorithm": "Radix Sort", "sorted_array": [], "execution_time_ms": 0}

    start_time = time.perf_counter()
    operations = 0
    max_val = max(a)
    exp = 1

    while max_val // exp > 0:
        output = [0] * n
        count = [0] * 10

        for i in range(n):
            index = (a[i] // exp) % 10
            count[index] += 1
            operations += 1

        for i in range(1, 10):
            count[i] += count[i - 1]
            operations += 1

        for i in range(n - 1, -1, -1):
            index = (a[i] // exp) % 10
            output[count[index] - 1] = a[i]
            count[index] -= 1
            operations += 1

        for i in range(n):
            a[i] = output[i]
            operations += 1

        exp *= 10

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Radix Sort",
        "sorted_array": a,
        "input_size": n,
        "comparisons": 0,
        "swaps": operations,
        "operations": operations,
        "execution_time_ms": round(elapsed_ms, 4),
        "time_complexity_best": "Ω(d·(n+k))",
        "time_complexity_avg": "Θ(d·(n+k))",
        "time_complexity_worst": "O(d·(n+k))",
        "space_complexity": "O(n+k)"
    }


# ==========================================
# 2. SEARCHING ALGORITHMS
# ==========================================

def linear_search(arr: List[Any], target: Any, key_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Linear Search: Sequentially checks each element.
    Complexity: Best: O(1), Average: O(n), Worst: O(n), Space: O(1)
    """
    start_time = time.perf_counter()
    comparisons = 0
    found_index = -1
    found_item = None

    for idx, item in enumerate(arr):
        comparisons += 1
        val = key_fn(item) if key_fn else item
        if str(val).upper().strip() == str(target).upper().strip():
            found_index = idx
            found_item = item
            break

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Linear Search",
        "found": found_index != -1,
        "index": found_index,
        "item": found_item,
        "comparisons": comparisons,
        "execution_time_ms": round(elapsed_ms, 5),
        "time_complexity_best": "Ω(1)",
        "time_complexity_avg": "Θ(n)",
        "time_complexity_worst": "O(n)",
        "space_complexity": "O(1)"
    }


def binary_search(sorted_arr: List[Any], target: Any, key_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Binary Search: Searches sorted array by repeatedly dividing search interval in half.
    Complexity: Best: O(1), Average: O(log n), Worst: O(log n), Space: O(1)
    """
    start_time = time.perf_counter()
    comparisons = 0
    low = 0
    high = len(sorted_arr) - 1
    found_index = -1
    found_item = None
    target_str = str(target).upper().strip()

    while low <= high:
        comparisons += 1
        mid = (low + high) // 2
        mid_val = key_fn(sorted_arr[mid]) if key_fn else sorted_arr[mid]
        mid_str = str(mid_val).upper().strip()

        if mid_str == target_str:
            found_index = mid
            found_item = sorted_arr[mid]
            break
        elif mid_str < target_str:
            low = mid + 1
        else:
            high = mid - 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return {
        "algorithm": "Binary Search",
        "found": found_index != -1,
        "index": found_index,
        "item": found_item,
        "comparisons": comparisons,
        "execution_time_ms": round(elapsed_ms, 5),
        "time_complexity_best": "Ω(1)",
        "time_complexity_avg": "Θ(log n)",
        "time_complexity_worst": "O(log n)",
        "space_complexity": "O(1)"
    }


# ==========================================
# 3. GREEDY ALLOCATION ALGORITHM
# ==========================================

def greedy_slot_allocation(
    available_slots: List[Dict[str, Any]],
    vehicle_type: str,
    priority_level: str,
    requested_gate: str = "GATE-1"
) -> Dict[str, Any]:
    """
    Greedy Smart Allocation:
    1. Filter compatible slots (Vehicle type matching: 2W vs 4W, and Status == 'FREE').
    2. Respect Reserved / Emergency slot restrictions:
       - Normal requests cannot take Emergency/Reserved slots unless allowed.
       - Accessibility requests prefer Ground Floor / Zone D near gates.
    3. Score each candidate slot using greedy objective function:
       score = distance_from_gate - priority_bonus + zone_floor_penalty
    4. Select minimum score slot (Greedy choice property).
    Complexity: O(n) filtering + O(n) min finding, or O(n log k) with Min-Heap
    """
    if not available_slots:
        return {
            "success": False,
            "error": "Parking is completely full. No slots available.",
            "candidates_evaluated": 0
        }

    compatible_candidates = []
    evaluated_count = 0

    for slot in available_slots:
        evaluated_count += 1
        if slot.get("status") != "FREE":
            continue

        slot_vtype = slot.get("vehicle_type", "4W")
        # Exact vehicle type match (2W fits 2W slot, 4W fits 4W slot)
        if slot_vtype != vehicle_type:
            continue

        slot_priority = slot.get("priority", "NORMAL")
        # If normal request, skip VIP/EMERGENCY reserved slots if flag set
        if priority_level == "NORMAL" and slot_priority in ["EMERGENCY", "RESERVED"]:
            continue

        dist = float(slot.get("distance_from_gate", 50.0))
        
        # Priority modifiers
        priority_bonus = 0.0
        if priority_level == "EMERGENCY":
            priority_bonus = 50.0
        elif priority_level == "ACCESSIBILITY":
            # Prefer ground floor / Zone A or D
            if slot.get("zone_id") in ["A", "D"]:
                priority_bonus = 30.0
        elif priority_level == "RESERVED":
            priority_bonus = 20.0

        # Calculate greedy score (lower is better)
        score = max(0.0, dist - priority_bonus)

        compatible_candidates.append({
            "slot": slot,
            "distance": dist,
            "calculated_score": round(score, 2),
            "zone": slot.get("zone_id"),
            "slot_id": slot.get("slot_id")
        })

    if not compatible_candidates:
        return {
            "success": False,
            "error": f"No compatible FREE slots found for vehicle type '{vehicle_type}' and priority '{priority_level}'.",
            "candidates_evaluated": evaluated_count
        }

    # Greedy Choice: Select candidate with minimum score
    best_candidate = min(compatible_candidates, key=lambda c: c["calculated_score"])

    return {
        "success": True,
        "selected_slot": best_candidate["slot"],
        "reason": f"Greedy optimal choice: Minimum weighted distance ({best_candidate['distance']}m) in Zone {best_candidate['zone']}",
        "score": best_candidate["calculated_score"],
        "candidates_evaluated": evaluated_count,
        "compatible_count": len(compatible_candidates),
        "all_ranked_candidates": sorted(compatible_candidates, key=lambda c: c["calculated_score"])
    }
