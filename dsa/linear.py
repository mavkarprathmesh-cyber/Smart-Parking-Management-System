"""
DSA Linear Data Structures Module
Implements:
1. Singly Linked List (for Parking/Vehicle History)
2. Doubly Linked List (for Bi-directional Navigation & History)
3. Circular Linked List (for Cyclic Parking Zone Traversal)
4. Stack (for Undo/Redo and Recent Actions)
5. Queue (FIFO for Normal Parking Requests)
6. Circular Queue (for Vehicle-Entry Batch Processing with fixed buffer)
7. Priority Queue (Min-Heap based for Emergency/Accessibility/Reserved requests)
8. Deque (Double-Ended Queue for flexible priority insertions)
"""

from typing import Any, Optional, List, Dict
import time


# ==========================================
# 1. SINGLY LINKED LIST (Parking History)
# ==========================================
class SLLNode:
    def __init__(self, data: Any):
        self.data = data
        self.next: Optional['SLLNode'] = None


class SinglyLinkedList:
    """
    Singly Linked List used for maintaining sequential vehicle entry/exit history.
    Time Complexity:
      - Append: O(1) with tail pointer
      - Prepend: O(1)
      - Search/Traversal: O(n)
      - Delete by value: O(n)
    """
    def __init__(self):
        self.head: Optional[SLLNode] = None
        self.tail: Optional[SLLNode] = None
        self._size: int = 0

    def append(self, data: Any) -> None:
        new_node = SLLNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def prepend(self, data: Any) -> None:
        new_node = SLLNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
        self._size += 1

    def to_list(self) -> List[Any]:
        items = []
        curr = self.head
        while curr:
            items.append(curr.data)
            curr = curr.next
        return items

    def search(self, key_func) -> Optional[Any]:
        curr = self.head
        while curr:
            if key_func(curr.data):
                return curr.data
            curr = curr.next
        return None

    def size(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0


# ==========================================
# 2. DOUBLY LINKED LIST (History & Navigation)
# ==========================================
class DLLNode:
    def __init__(self, data: Any):
        self.data = data
        self.prev: Optional['DLLNode'] = None
        self.next: Optional['DLLNode'] = None


class DoublyLinkedList:
    """
    Doubly Linked List for bi-directional audit trail and navigation steps.
    Time Complexity:
      - Append / Prepend: O(1)
      - Forward / Backward Traversal: O(n)
      - Delete specific node: O(1) if node reference is known, O(n) otherwise
    """
    def __init__(self):
        self.head: Optional[DLLNode] = None
        self.tail: Optional[DLLNode] = None
        self._size: int = 0

    def append(self, data: Any) -> DLLNode:
        new_node = DLLNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self._size += 1
        return new_node

    def prepend(self, data: Any) -> DLLNode:
        new_node = DLLNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self._size += 1
        return new_node

    def to_list_forward(self) -> List[Any]:
        items = []
        curr = self.head
        while curr:
            items.append(curr.data)
            curr = curr.next
        return items

    def to_list_backward(self) -> List[Any]:
        items = []
        curr = self.tail
        while curr:
            items.append(curr.data)
            curr = curr.prev
        return items

    def size(self) -> int:
        return self._size


# ==========================================
# 3. CIRCULAR LINKED LIST (Cyclic Zone Traversal)
# ==========================================
class CLLNode:
    def __init__(self, data: Any):
        self.data = data
        self.next: Optional['CLLNode'] = None


class CircularLinkedList:
    """
    Circular Linked List for cyclic inspection of parking zones (Zone A -> Zone B -> Zone C -> Zone D -> Zone A).
    Time Complexity:
      - Append: O(n) or O(1) with tail
      - Traversal: O(n)
      - Round-Robin step: O(1)
    """
    def __init__(self):
        self.head: Optional[CLLNode] = None
        self.current_inspection_ptr: Optional[CLLNode] = None
        self._size: int = 0

    def append(self, data: Any) -> None:
        new_node = CLLNode(data)
        if not self.head:
            self.head = new_node
            new_node.next = self.head
            self.current_inspection_ptr = self.head
        else:
            curr = self.head
            while curr.next != self.head:
                assert curr.next is not None
                curr = curr.next
            curr.next = new_node
            new_node.next = self.head
        self._size += 1

    def next_zone(self) -> Optional[Any]:
        """Advance to the next zone in round-robin fashion."""
        if not self.current_inspection_ptr:
            return None
        val = self.current_inspection_ptr.data
        self.current_inspection_ptr = self.current_inspection_ptr.next
        return val

    def to_list(self) -> List[Any]:
        if not self.head:
            return []
        items = []
        curr = self.head
        while True:
            items.append(curr.data)
            curr = curr.next
            if curr == self.head:
                break
        return items

    def size(self) -> int:
        return self._size


# ==========================================
# 4. STACK (Undo & Recent Actions)
# ==========================================
class Stack:
    """
    LIFO Stack for tracking system transactions, slot state reversals, and undo actions.
    Time Complexity:
      - Push: O(1)
      - Pop: O(1)
      - Peek: O(1)
    """
    def __init__(self, max_capacity: int = 100):
        self._items: List[Dict[str, Any]] = []
        self.max_capacity = max_capacity

    def push(self, action: Dict[str, Any]) -> None:
        if "timestamp" not in action:
            action["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._items.append(action)
        if len(self._items) > self.max_capacity:
            self._items.pop(0)

    def pop(self) -> Optional[Dict[str, Any]]:
        if not self.is_empty():
            return self._items.pop()
        return None

    def peek(self) -> Optional[Dict[str, Any]]:
        if not self.is_empty():
            return self._items[-1]
        return None

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all items with most recent first."""
        return list(reversed(self._items))


# ==========================================
# 5. FIFO QUEUE (Normal Parking Requests)
# ==========================================
class Queue:
    """
    FIFO Queue for normal vehicle parking requests.
    Time Complexity:
      - Enqueue: O(1)
      - Dequeue: O(1)
      - Peek: O(1)
    """
    def __init__(self):
        self._items: List[Any] = []

    def enqueue(self, item: Any) -> None:
        self._items.append(item)

    def dequeue(self) -> Optional[Any]:
        if not self.is_empty():
            return self._items.pop(0)
        return None

    def peek(self) -> Optional[Any]:
        if not self.is_empty():
            return self._items[0]
        return None

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> List[Any]:
        return list(self._items)

    def remove_by_id(self, req_id: int) -> Optional[Any]:
        for i, item in enumerate(self._items):
            if isinstance(item, dict) and item.get("id") == req_id:
                return self._items.pop(i)
        return None


# ==========================================
# 6. CIRCULAR QUEUE (Vehicle-Entry Batch Processing)
# ==========================================
class CircularQueue:
    """
    Fixed-capacity Circular Queue for vehicle entry processing buffer at gate.
    Avoids memory reallocation and demonstrates classic ring buffer.
    Time Complexity:
      - Enqueue: O(1)
      - Dequeue: O(1)
      - IsFull / IsEmpty: O(1)
    """
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.queue: List[Optional[Any]] = [None] * capacity
        self.front: int = -1
        self.rear: int = -1
        self._count: int = 0

    def is_full(self) -> bool:
        return (self.rear + 1) % self.capacity == self.front

    def is_empty(self) -> bool:
        return self.front == -1

    def enqueue(self, data: Any) -> bool:
        if self.is_full():
            return False  # Queue overflow
        if self.front == -1:
            self.front = 0
            self.rear = 0
        else:
            self.rear = (self.rear + 1) % self.capacity
        self.queue[self.rear] = data
        self._count += 1
        return True

    def dequeue(self) -> Optional[Any]:
        if self.is_empty():
            return None  # Queue underflow
        data = self.queue[self.front]
        self.queue[self.front] = None
        self._count -= 1
        if self.front == self.rear:
            self.front = -1
            self.rear = -1
        else:
            self.front = (self.front + 1) % self.capacity
        return data

    def peek(self) -> Optional[Any]:
        if self.is_empty():
            return None
        return self.queue[self.front]

    def size(self) -> int:
        return self._count

    def to_list(self) -> List[Any]:
        if self.is_empty():
            return []
        items = []
        idx = self.front
        while True:
            items.append(self.queue[idx])
            if idx == self.rear:
                break
            idx = (idx + 1) % self.capacity
        return items


# ==========================================
# 7. PRIORITY QUEUE (Priority/Emergency/Reserved)
# ==========================================
class PriorityQueue:
    """
    Min-Heap based Priority Queue for handling parking requests by priority level:
      Level 1: Emergency (Ambulance / Fire / Police) - Highest Priority
      Level 2: Accessibility / Disabled
      Level 3: VIP / Reserved
      Level 4: Normal
    Time Complexity:
      - Enqueue (Push): O(log n)
      - Dequeue (Pop Min): O(log n)
      - Peek: O(1)
    """
    def __init__(self):
        # Heap elements: tuple of (priority_int, arrival_timestamp, data_dict)
        self._heap: List[tuple] = []
        self._counter: int = 0  # tie-breaker

    def enqueue(self, item: Any, priority_rank: int) -> None:
        """Lower priority_rank number = higher priority."""
        self._counter += 1
        entry = (priority_rank, self._counter, item)
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def dequeue(self) -> Optional[Any]:
        if not self._heap:
            return None
        self._swap(0, len(self._heap) - 1)
        min_entry = self._heap.pop()
        if self._heap:
            self._sift_down(0)
        return min_entry[2]

    def peek(self) -> Optional[Any]:
        if not self._heap:
            return None
        return self._heap[0][2]

    def _sift_up(self, idx: int) -> None:
        parent = (idx - 1) // 2
        while idx > 0 and self._heap[idx] < self._heap[parent]:
            self._swap(idx, parent)
            idx = parent
            parent = (idx - 1) // 2

    def _sift_down(self, idx: int) -> None:
        n = len(self._heap)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            if left < n and self._heap[left] < self._heap[smallest]:
                smallest = left
            if right < n and self._heap[right] < self._heap[smallest]:
                smallest = right
            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def to_sorted_list(self) -> List[Any]:
        # Return a copy sorted by priority without destroying the heap
        sorted_copy = sorted(self._heap, key=lambda x: (x[0], x[1]))
        return [entry[2] for entry in sorted_copy]

    def remove_by_id(self, req_id: int) -> Optional[Any]:
        for i, entry in enumerate(self._heap):
            item = entry[2]
            if isinstance(item, dict) and item.get("id") == req_id:
                removed_item = item
                # Replace with last element and restore heap property
                last_entry = self._heap.pop()
                if i < len(self._heap):
                    self._heap[i] = last_entry
                    self._sift_down(i)
                    self._sift_up(i)
                return removed_item
        return None


# ==========================================
# 8. DEQUE (Double-Ended Queue)
# ==========================================
class Deque:
    """
    Double-Ended Queue allowing insertion/removal at both Front and Rear.
    Used for immediate lane priority overrides and queue re-ordering.
    Time Complexity:
      - Append Front/Rear: O(1)
      - Pop Front/Rear: O(1)
    """
    def __init__(self):
        self._items: List[Any] = []

    def append_rear(self, item: Any) -> None:
        self._items.append(item)

    def append_front(self, item: Any) -> None:
        self._items.insert(0, item)

    def pop_front(self) -> Optional[Any]:
        if not self.is_empty():
            return self._items.pop(0)
        return None

    def pop_rear(self) -> Optional[Any]:
        if not self.is_empty():
            return self._items.pop()
        return None

    def peek_front(self) -> Optional[Any]:
        return self._items[0] if not self.is_empty() else None

    def peek_rear(self) -> Optional[Any]:
        return self._items[-1] if not self.is_empty() else None

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> List[Any]:
        return list(self._items)
