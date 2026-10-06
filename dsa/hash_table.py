"""
DSA Hash Table Module
Implements:
Custom Hash Table with Separate Chaining (Collision Resolution via Linked Buckets),
Dynamic Rehashing, Load Factor Analysis, and lookup step counting for search comparison.
"""

from typing import Any, Optional, List, Dict, Tuple


class HashNode:
    def __init__(self, key: str, value: Any):
        self.key: str = str(key).upper().strip()
        self.value: Any = value
        self.next: Optional['HashNode'] = None


class HashTable:
    """
    Custom Chaining Hash Table for O(1) average lookup of vehicles and slots.
    Time Complexity:
      - Insert: Average O(1), Worst O(n)
      - Search: Average O(1), Worst O(n)
      - Delete: Average O(1), Worst O(n)
    Space Complexity: O(n + m) where m is bucket count
    """
    def __init__(self, initial_capacity: int = 31, max_load_factor: float = 0.75):
        self.capacity: int = initial_capacity
        self.max_load_factor: float = max_load_factor
        self.buckets: List[Optional[HashNode]] = [None] * self.capacity
        self.size: int = 0
        self.collisions_count: int = 0

    def _hash_function(self, key: str) -> int:
        """
        Polynomial rolling hash function:
        hash = (s[0]*p^(k-1) + s[1]*p^(k-2) + ... + s[k-1]) % capacity
        """
        p = 31
        hash_val = 0
        for char in str(key):
            hash_val = (hash_val * p + ord(char)) % self.capacity
        return hash_val

    def insert(self, key: str, value: Any) -> None:
        normalized_key = str(key).upper().strip()
        index = self._hash_function(normalized_key)
        head = self.buckets[index]

        # Check if key already exists in the chain
        curr = head
        while curr:
            if curr.key == normalized_key:
                curr.value = value
                return
            curr = curr.next

        # Key not found, prepend new node to chain
        new_node = HashNode(normalized_key, value)
        if head is not None:
            self.collisions_count += 1
        new_node.next = head
        self.buckets[index] = new_node
        self.size += 1

        # Check load factor for dynamic rehashing
        if (self.size / self.capacity) > self.max_load_factor:
            self._rehash()

    def search(self, key: str) -> Tuple[Optional[Any], int, int]:
        """
        Returns (value, comparisons_count, bucket_index)
        """
        normalized_key = str(key).upper().strip()
        index = self._hash_function(normalized_key)
        head = self.buckets[index]
        comparisons = 0

        curr = head
        while curr:
            comparisons += 1
            if curr.key == normalized_key:
                return curr.value, comparisons, index
            curr = curr.next

        return None, comparisons, index

    def delete(self, key: str) -> bool:
        normalized_key = str(key).upper().strip()
        index = self._hash_function(normalized_key)
        head = self.buckets[index]
        prev = None
        curr = head

        while curr:
            if curr.key == normalized_key:
                if prev:
                    prev.next = curr.next
                else:
                    self.buckets[index] = curr.next
                self.size -= 1
                return True
            prev = curr
            curr = curr.next

        return False

    def _rehash(self) -> None:
        """Double capacity to next prime-like odd number and re-index all nodes."""
        old_buckets = self.buckets
        self.capacity = self.capacity * 2 + 1
        self.buckets = [None] * self.capacity
        self.size = 0
        self.collisions_count = 0

        for head in old_buckets:
            curr = head
            while curr:
                self.insert(curr.key, curr.value)
                curr = curr.next

    def get_stats(self) -> Dict[str, Any]:
        bucket_lengths = []
        occupied_buckets = 0
        for head in self.buckets:
            length = 0
            curr = head
            while curr:
                length += 1
                curr = curr.next
            if length > 0:
                occupied_buckets += 1
            bucket_lengths.append(length)

        return {
            "capacity": self.capacity,
            "total_items": self.size,
            "occupied_buckets": occupied_buckets,
            "load_factor": round(self.size / self.capacity, 3) if self.capacity > 0 else 0,
            "collisions_count": self.collisions_count,
            "max_chain_length": max(bucket_lengths) if bucket_lengths else 0
        }

    def to_list(self) -> List[Dict[str, Any]]:
        items = []
        for i, head in enumerate(self.buckets):
            curr = head
            while curr:
                items.append({"key": curr.key, "value": curr.value, "bucket": i})
                curr = curr.next
        return items
