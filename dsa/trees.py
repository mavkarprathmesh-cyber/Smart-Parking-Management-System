"""
DSA Trees and Heaps Module
Implements:
1. Binary Tree (for parking zone/floor hierarchy)
2. Binary Search Tree - BST (for vehicle and slot search indexing)
3. AVL Tree (Self-balancing BST with LL, RR, LR, RL rotations for guaranteed O(log n) lookups)
4. Min Heap (for candidate slot selection by minimum distance/cost)
"""

from typing import Any, Optional, List, Dict, Tuple


# ==========================================
# 1. GENERAL BINARY TREE (Zone Hierarchy)
# ==========================================
class TreeNode:
    def __init__(self, key: str, value: Any = None):
        self.key = key
        self.value = value
        self.left: Optional['TreeNode'] = None
        self.right: Optional['TreeNode'] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }


class BinaryTree:
    """
    General Binary Tree representation for structural hierarchical modeling
    (e.g., Facility -> North Wing / South Wing -> Ground Floor / First Floor -> Zones).
    """
    def __init__(self, root_key: str = "Facility", root_val: Any = None):
        self.root = TreeNode(root_key, root_val)

    def preorder(self, node: Optional[TreeNode] = None, result: Optional[List] = None) -> List[str]:
        if result is None:
            result = []
        if node is None and self.root:
            node = self.root
        if node:
            result.append(node.key)
            if node.left:
                self.preorder(node.left, result)
            if node.right:
                self.preorder(node.right, result)
        return result

    def get_hierarchy(self) -> Dict[str, Any]:
        return self.root.to_dict() if self.root else {}


# ==========================================
# 2. BINARY SEARCH TREE (BST)
# ==========================================
class BSTNode:
    def __init__(self, key: str, data: Any):
        self.key = str(key).upper().strip()
        self.data = data
        self.left: Optional['BSTNode'] = None
        self.right: Optional['BSTNode'] = None


class BinarySearchTree:
    """
    Binary Search Tree for indexing and searching vehicles / slots by alphanumeric key.
    Time Complexity:
      - Search: Average O(log n), Worst O(n) (unbalanced)
      - Insert: Average O(log n), Worst O(n)
      - Inorder Traversal (Sorted order): O(n)
    """
    def __init__(self):
        self.root: Optional[BSTNode] = None
        self.size: int = 0

    def insert(self, key: str, data: Any) -> None:
        normalized_key = str(key).upper().strip()
        self.root = self._insert_rec(self.root, normalized_key, data)

    def _insert_rec(self, node: Optional[BSTNode], key: str, data: Any) -> BSTNode:
        if node is None:
            self.size += 1
            return BSTNode(key, data)
        if key < node.key:
            node.left = self._insert_rec(node.left, key, data)
        elif key > node.key:
            node.right = self._insert_rec(node.right, key, data)
        else:
            # Update data on duplicate key
            node.data = data
        return node

    def search(self, key: str) -> Tuple[Optional[Any], int]:
        """Returns (data, comparison_count)"""
        normalized_key = str(key).upper().strip()
        return self._search_rec(self.root, normalized_key, 0)

    def _search_rec(self, node: Optional[BSTNode], key: str, comparisons: int) -> Tuple[Optional[Any], int]:
        if node is None:
            return None, comparisons
        comparisons += 1
        if key == node.key:
            return node.data, comparisons
        elif key < node.key:
            return self._search_rec(node.left, key, comparisons)
        else:
            return self._search_rec(node.right, key, comparisons)

    def inorder(self) -> List[Dict[str, Any]]:
        result = []
        self._inorder_rec(self.root, result)
        return result

    def _inorder_rec(self, node: Optional[BSTNode], result: List[Dict[str, Any]]) -> None:
        if node:
            self._inorder_rec(node.left, result)
            result.append({"key": node.key, "data": node.data})
            self._inorder_rec(node.right, result)

    def get_height(self) -> int:
        return self._height_rec(self.root)

    def _height_rec(self, node: Optional[BSTNode]) -> int:
        if not node:
            return 0
        return 1 + max(self._height_rec(node.left), self._height_rec(node.right))


# ==========================================
# 3. AVL TREE (Self-Balancing BST)
# ==========================================
class AVLNode:
    def __init__(self, key: str, data: Any):
        self.key = str(key).upper().strip()
        self.data = data
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height: int = 1


class AVLTree:
    """
    Self-Balancing Binary Search Tree (Adelson-Velsky and Landis).
    Guarantees strict O(log n) search, insertion, and deletion via 4 rotation types:
      - Left-Left (Right Rotation)
      - Right-Right (Left Rotation)
      - Left-Right (Left-Right Double Rotation)
      - Right-Left (Right-Left Double Rotation)
    """
    def __init__(self):
        self.root: Optional[AVLNode] = None
        self.size: int = 0
        self.rotations_count: int = 0

    def height(self, node: Optional[AVLNode]) -> int:
        if not node:
            return 0
        return node.height

    def get_balance(self, node: Optional[AVLNode]) -> int:
        if not node:
            return 0
        return self.height(node.left) - self.height(node.right)

    def right_rotate(self, y: AVLNode) -> AVLNode:
        x = y.left
        assert x is not None
        t2 = x.right

        # Perform rotation
        x.right = y
        y.left = t2

        # Update heights
        y.height = 1 + max(self.height(y.left), self.height(y.right))
        x.height = 1 + max(self.height(x.left), self.height(x.right))
        self.rotations_count += 1
        return x

    def left_rotate(self, x: AVLNode) -> AVLNode:
        y = x.right
        assert y is not None
        t2 = y.left

        # Perform rotation
        y.left = x
        x.right = t2

        # Update heights
        x.height = 1 + max(self.height(x.left), self.height(x.right))
        y.height = 1 + max(self.height(y.left), self.height(y.right))
        self.rotations_count += 1
        return y

    def insert(self, key: str, data: Any) -> None:
        normalized_key = str(key).upper().strip()
        self.root = self._insert_rec(self.root, normalized_key, data)

    def _insert_rec(self, node: Optional[AVLNode], key: str, data: Any) -> AVLNode:
        # Standard BST insertion
        if not node:
            self.size += 1
            return AVLNode(key, data)

        if key < node.key:
            node.left = self._insert_rec(node.left, key, data)
        elif key > node.key:
            node.right = self._insert_rec(node.right, key, data)
        else:
            node.data = data
            return node

        # Update height
        node.height = 1 + max(self.height(node.left), self.height(node.right))

        # Check balance factor
        balance = self.get_balance(node)

        # 4 Balance cases:
        # Case 1: Left-Left
        if balance > 1 and node.left and key < node.left.key:
            return self.right_rotate(node)

        # Case 2: Right-Right
        if balance < -1 and node.right and key > node.right.key:
            return self.left_rotate(node)

        # Case 3: Left-Right
        if balance > 1 and node.left and key > node.left.key:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)

        # Case 4: Right-Left
        if balance < -1 and node.right and key < node.right.key:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)

        return node

    def search(self, key: str) -> Tuple[Optional[Any], int]:
        """Returns (data, comparisons_count)"""
        normalized_key = str(key).upper().strip()
        return self._search_rec(self.root, normalized_key, 0)

    def _search_rec(self, node: Optional[AVLNode], key: str, comparisons: int) -> Tuple[Optional[Any], int]:
        if not node:
            return None, comparisons
        comparisons += 1
        if key == node.key:
            return node.data, comparisons
        elif key < node.key:
            return self._search_rec(node.left, key, comparisons)
        else:
            return self._search_rec(node.right, key, comparisons)

    def to_tree_json(self, node: Optional[AVLNode] = None) -> Optional[Dict[str, Any]]:
        if node is None and self.root:
            node = self.root
        if not node:
            return None
        return {
            "key": node.key,
            "height": node.height,
            "balance": self.get_balance(node),
            "left": self.to_tree_json(node.left) if node.left else None,
            "right": self.to_tree_json(node.right) if node.right else None
        }


# ==========================================
# 4. MIN HEAP (Nearest/Optimal Candidate Selection)
# ==========================================
class MinHeap:
    """
    Min Heap for smart parking slot selection.
    Elements are stored as tuples: (score, tiebreaker_counter, slot_data)
    Score is calculated from:
      composite_score = distance_from_gate + priority_offset - compatibility_bonus
    Time Complexity:
      - Insert: O(log n)
      - Extract Min: O(log n)
      - Peek Min: O(1)
      - Heapify list: O(n)
    """
    def __init__(self):
        self._heap: List[Tuple[float, int, Any]] = []
        self._counter: int = 0

    def push(self, score: float, slot: Any) -> None:
        self._counter += 1
        self._heap.append((score, self._counter, slot))
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> Optional[Any]:
        if not self._heap:
            return None
        self._swap(0, len(self._heap) - 1)
        min_item = self._heap.pop()
        if self._heap:
            self._sift_down(0)
        return min_item[2]

    def peek(self) -> Optional[Any]:
        return self._heap[0][2] if self._heap else None

    def size(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

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

    def get_ranked_candidates(self) -> List[Dict[str, Any]]:
        """Returns all candidates ranked by min score without destroying the heap."""
        sorted_elements = sorted(self._heap, key=lambda x: (x[0], x[1]))
        return [{"score": elem[0], "slot": elem[2]} for elem in sorted_elements]
