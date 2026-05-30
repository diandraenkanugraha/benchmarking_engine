"""
data_structures.py
==================
Manual from-scratch implementations of:
  - ArrayDS         : Dynamic array with linear & binary search
  - HashTableDS     : Open-addressing hash table with linear probing
  - BinarySearchTreeDS : Standard BST with full 3-case deletion
  - AVLTreeDS       : Self-balancing AVL tree with all 4 rotations

All classes expose: insert(data), search(data) -> bool, delete(data)
BST and AVL also expose: get_nodes_edges() -> tuple[list, list]

Author  : Generated for UAS Struktur Data
Python  : 3.10+
"""

from __future__ import annotations
from typing import Optional, Any


# ══════════════════════════════════════════════════════════════════
#  1.  ARRAY  (linear & binary search, insert, delete)
# ══════════════════════════════════════════════════════════════════

class ArrayDS:
    """
    A dynamic array built on a plain Python list that exposes only the
    primitives we implement ourselves (no dict / set / bisect).

    Attributes
    ----------
    _data : list[int]
        Internal storage.
    """

    def __init__(self) -> None:
        """Initialise an empty array."""
        self._data: list[int] = []
        self._is_sorted: bool = True

    # ── public API ──────────────────────────────────────────────

    def insert(self, value: int) -> None:
        """
        Append *value* to the end of the array.

        Time complexity: O(1) amortised.

        Parameters
        ----------
        value : int
            The integer to append.
        """
        self._data.append(value)
        self._is_sorted = False

    def search(self, value: int) -> bool:
        """
        Linear search – O(n).

        Parameters
        ----------
        value : int
            Value to look for.

        Returns
        -------
        bool
            True if found, False otherwise.
        """
        return self._linear_search(value)

    def binary_search(self, value: int) -> bool:
        """
        Binary search – O(log n) after a one‑time lazy sort.

        The first call after any insert/delete triggers a sort of the
        internal array, then caches the sorted state via ``_is_sorted``.

        Parameters
        ----------
        value : int
            Value to look for.

        Returns
        -------
        bool
            True if found, False otherwise.
        """
        if not self._is_sorted:
            self._data = self._merge_sort(self._data)
            self._is_sorted = True
        return self._binary_search(self._data, value, 0, len(self._data) - 1)

    def delete(self, value: int) -> bool:
        """
        Find the first occurrence of *value* and remove it by shifting
        subsequent elements left – O(n).

        Parameters
        ----------
        value : int
            Value to remove.

        Returns
        -------
        bool
            True if an element was removed, False if not found.
        """
        idx = -1
        for i in range(len(self._data)):
            if self._data[i] == value:
                idx = i
                break
        if idx == -1:
            return False
        # manual shift-left (no list.pop to demonstrate the algorithm)
        for i in range(idx, len(self._data) - 1):
            self._data[i] = self._data[i + 1]
        self._data.pop()          # shrink by one slot
        self._is_sorted = False
        return True

    def get_data(self) -> list[int]:
        """Return a shallow copy of the internal array."""
        return self._data[:]

    def size(self) -> int:
        """Return the number of elements currently stored."""
        return len(self._data)

    # ── private helpers ─────────────────────────────────────────

    def _linear_search(self, value: int) -> bool:
        """Iterate through every element – O(n)."""
        for item in self._data:
            if item == value:
                return True
        return False

    def _binary_search(
        self,
        arr: list[int],
        value: int,
        low: int,
        high: int,
    ) -> bool:
        """Recursive binary search on a sorted list – O(log n)."""
        if low > high:
            return False
        mid = (low + high) // 2
        if arr[mid] == value:
            return True
        if arr[mid] < value:
            return self._binary_search(arr, value, mid + 1, high)
        return self._binary_search(arr, value, low, mid - 1)

    def _merge_sort(self, arr: list[int]) -> list[int]:
        """Pure merge-sort (no sorted() built-in) – O(n log n)."""
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left  = self._merge_sort(arr[:mid])
        right = self._merge_sort(arr[mid:])
        return self._merge(left, right)

    def _merge(self, left: list[int], right: list[int]) -> list[int]:
        """Merge two sorted sub-lists."""
        result: list[int] = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        while i < len(left):
            result.append(left[i]); i += 1
        while j < len(right):
            result.append(right[j]); j += 1
        return result


# ══════════════════════════════════════════════════════════════════
#  2.  HASH TABLE  (open addressing – linear probing)
# ══════════════════════════════════════════════════════════════════

# Tombstone sentinel for the hash table's open-addressing delete.
# Using a plain object() instead of a class with a self-referential
# class attribute prevents copy.deepcopy from entering an infinite
# recursion when it traverses the _table list and encounters this object.
_DELETED = object()   # singleton tombstone – identity check: `slot is _DELETED`


class HashTableDS:
    """
    Hash table implemented with **open addressing + linear probing**.

    Collisions are resolved by scanning forward (+1 each step) until an
    empty slot is found.  Deletion uses a tombstone sentinel so that
    subsequent probes are not broken.

    Parameters
    ----------
    capacity : int
        Initial number of buckets (default 64).  The table is resized
        (doubled) automatically when the load factor exceeds 0.7.

    Attributes
    ----------
    _capacity : int
    _size     : int   – number of live entries
    _table    : list  – internal bucket array
    """

    _LOAD_FACTOR_THRESHOLD: float = 0.7

    def __init__(self, capacity: int = 64) -> None:
        """Initialise an empty hash table with *capacity* buckets."""
        self._capacity: int       = capacity
        self._size:     int       = 0
        self._table:    list[Any] = [None] * self._capacity

    # ── public API ──────────────────────────────────────────────

    def insert(self, value: int) -> None:
        """
        Insert *value* into the table.  Duplicates are silently ignored.
        Triggers a resize when load factor > 0.7.

        Time complexity: O(1) amortised.

        Parameters
        ----------
        value : int
        """
        if self._load_factor() > self._LOAD_FACTOR_THRESHOLD:
            self._resize()

        idx = self._probe_for_insert(value)
        if idx is None:
            return  # value already present
        self._table[idx] = value
        self._size += 1

    def search(self, value: int) -> bool:
        """
        Look up *value* in the table.

        Time complexity: O(1) average, O(n) worst-case.

        Parameters
        ----------
        value : int

        Returns
        -------
        bool
        """
        idx = self._hash(value)
        for _ in range(self._capacity):
            slot = self._table[idx]
            if slot is None:
                return False                     # definitely absent
            if slot is not _DELETED and slot == value:
                return True
            idx = (idx + 1) % self._capacity
        return False

    def delete(self, value: int) -> bool:
        """
        Remove *value* from the table, replacing its slot with a
        tombstone so linear-probe chains remain intact.

        Time complexity: O(1) average.

        Parameters
        ----------
        value : int

        Returns
        -------
        bool
            True if removed, False if not found.
        """
        idx = self._hash(value)
        for _ in range(self._capacity):
            slot = self._table[idx]
            if slot is None:
                return False
            if slot is not _DELETED and slot == value:
                self._table[idx] = _DELETED
                self._size -= 1
                return True
            idx = (idx + 1) % self._capacity
        return False

    def get_all_values(self) -> list[int]:
        """Return a sorted list of all live values (for display)."""
        out: list[int] = []
        for slot in self._table:
            if slot is not None and slot is not _DELETED:
                out.append(slot)
        # manual insertion sort (no sorted())
        for i in range(1, len(out)):
            key = out[i]; j = i - 1
            while j >= 0 and out[j] > key:
                out[j + 1] = out[j]; j -= 1
            out[j + 1] = key
        return out

    def capacity(self) -> int:
        """Return the current bucket count."""
        return self._capacity

    def size(self) -> int:
        """Return the number of live entries."""
        return self._size

    def get_bucket_state(self, max_buckets: int = 50) -> list[int]:
        """
        Return bucket occupancy for visualisation.

        Parameters
        ----------
        max_buckets : int
            Maximum number of buckets to report (default 50).

        Returns
        -------
        list[int]
            Each element is ``0`` (empty), ``1`` (filled), or ``2`` (tombstone).
        """
        n = min(self._capacity, max_buckets)
        result: list[int] = []
        for i in range(n):
            slot = self._table[i]
            if slot is None:
                result.append(0)
            elif slot is _DELETED:
                result.append(2)
            else:
                result.append(1)
        return result

    # ── private helpers ─────────────────────────────────────────

    def _hash(self, value: int) -> int:
        """Primary hash: value mod capacity."""
        return abs(value) % self._capacity

    def _load_factor(self) -> float:
        return self._size / self._capacity

    def _probe_for_insert(self, value: int) -> Optional[int]:
        """
        Find the best slot for insertion.

        Returns the index of the first tombstone or empty slot found
        while probing, unless *value* is already present (returns None).
        """
        idx        = self._hash(value)
        first_tomb: Optional[int] = None

        for _ in range(self._capacity):
            slot = self._table[idx]
            if slot is None:
                return first_tomb if first_tomb is not None else idx
            if slot is _DELETED:
                if first_tomb is None:
                    first_tomb = idx
            elif slot == value:
                return None   # duplicate – caller will skip
            idx = (idx + 1) % self._capacity

        return first_tomb  # table is full of tombstones

    def _resize(self) -> None:
        """Double the capacity and rehash all live entries."""
        old_table      = self._table
        self._capacity = self._capacity * 2
        self._table    = [None] * self._capacity
        self._size     = 0
        for slot in old_table:
            if slot is not None and slot is not _DELETED:
                self.insert(slot)


# ══════════════════════════════════════════════════════════════════
#  3.  BINARY SEARCH TREE
# ══════════════════════════════════════════════════════════════════

class _BSTNode:
    """A single node in a Binary Search Tree."""

    __slots__ = ("value", "left", "right")

    def __init__(self, value: int) -> None:
        self.value: int                 = value
        self.left:  Optional[_BSTNode] = None
        self.right: Optional[_BSTNode] = None


class BinarySearchTreeDS:
    """
    Standard Binary Search Tree (unbalanced).

    Supports insert, search, and delete (all three deletion cases:
    leaf, one-child, two-children / in-order successor).

    Attributes
    ----------
    _root : _BSTNode | None
        Root of the tree.
    _size : int
        Number of nodes currently stored.
    """

    def __init__(self) -> None:
        """Initialise an empty BST."""
        self._root: Optional[_BSTNode] = None
        self._size: int                = 0

    # ── public API ──────────────────────────────────────────────

    def insert(self, value: int) -> None:
        """
        Insert *value*. Duplicates are silently ignored.

        Time complexity: O(h) where h = tree height.

        Parameters
        ----------
        value : int
        """
        self._root  = self._insert_rec(self._root, value)

    def search(self, value: int) -> bool:
        """
        Return True if *value* is present in the tree.

        Time complexity: O(h).

        Parameters
        ----------
        value : int
        """
        return self._search_rec(self._root, value)

    def delete(self, value: int) -> bool:
        """
        Remove *value* from the tree, handling all three cases:

        1. Leaf node            → detach directly.
        2. One child            → replace node with its child.
        3. Two children         → replace with in-order successor
                                   (smallest value in right subtree),
                                   then delete that successor.

        Time complexity: O(h).

        Parameters
        ----------
        value : int

        Returns
        -------
        bool
            True if *value* was found and removed.
        """
        if not self.search(value):
            return False
        self._root = self._delete_rec(self._root, value)
        self._size -= 1
        return True

    def get_nodes_edges(self) -> tuple[list[dict], list[dict]]:
        """
        Traverse the tree and return node + edge descriptors suitable
        for ``streamlit-agraph``.

        Returns
        -------
        nodes : list[dict]
            Each dict has keys ``id`` (str) and ``label`` (str).
        edges : list[dict]
            Each dict has keys ``source`` (str) and ``target`` (str).
        """
        nodes: list[dict] = []
        edges: list[dict] = []
        self._collect(self._root, nodes, edges)
        return nodes, edges

    def size(self) -> int:
        """Return the number of nodes in the tree."""
        return self._size

    def get_height(self) -> int:
        """
        Return the height of the tree (0 if empty).

        Time complexity: O(n).

        Returns
        -------
        int
            Height of the root node, or 0 if the tree is empty.
        """
        return self._get_height_rec(self._root)

    # ── private helpers (existing) ───────────────────────────────

    def _get_height_rec(
        self,
        node: Optional[_BSTNode],
    ) -> int:
        if node is None:
            return 0
        return 1 + max(
            self._get_height_rec(node.left),
            self._get_height_rec(node.right),
        )

    def inorder(self) -> list[int]:
        """Return a sorted list of all values (in-order traversal)."""
        result: list[int] = []
        self._inorder_rec(self._root, result)
        return result

    # ── private helpers ─────────────────────────────────────────

    def _insert_rec(
        self,
        node: Optional[_BSTNode],
        value: int,
    ) -> _BSTNode:
        if node is None:
            self._size += 1
            return _BSTNode(value)
        if value < node.value:
            node.left  = self._insert_rec(node.left,  value)
        elif value > node.value:
            node.right = self._insert_rec(node.right, value)
        # equal → duplicate, do nothing
        return node

    def _search_rec(
        self,
        node: Optional[_BSTNode],
        value: int,
    ) -> bool:
        if node is None:
            return False
        if value == node.value:
            return True
        if value < node.value:
            return self._search_rec(node.left,  value)
        return self._search_rec(node.right, value)

    def _delete_rec(
        self,
        node: Optional[_BSTNode],
        value: int,
    ) -> Optional[_BSTNode]:
        if node is None:
            return None

        if value < node.value:
            node.left  = self._delete_rec(node.left,  value)
        elif value > node.value:
            node.right = self._delete_rec(node.right, value)
        else:
            # ── Case 1 & 2: leaf or single child ──────────────
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left

            # ── Case 3: two children ──────────────────────────
            # Find in-order successor (min of right subtree)
            successor       = self._min_node(node.right)
            node.value      = successor.value
            # Delete the successor from the right subtree
            node.right      = self._delete_rec(node.right, successor.value)

        return node

    @staticmethod
    def _min_node(node: _BSTNode) -> _BSTNode:
        """Walk left until the leftmost (smallest) node is reached."""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _collect(
        self,
        node: Optional[_BSTNode],
        nodes: list[dict],
        edges:  list[dict],
    ) -> None:
        """Pre-order traversal collecting agraph-compatible dicts."""
        if node is None:
            return
        nodes.append({"id": str(node.value), "label": str(node.value)})
        if node.left is not None:
            edges.append({"source": str(node.value), "target": str(node.left.value)})
        if node.right is not None:
            edges.append({"source": str(node.value), "target": str(node.right.value)})
        self._collect(node.left,  nodes, edges)
        self._collect(node.right, nodes, edges)

    def _inorder_rec(
        self,
        node: Optional[_BSTNode],
        result: list[int],
    ) -> None:
        if node is None:
            return
        self._inorder_rec(node.left,  result)
        result.append(node.value)
        self._inorder_rec(node.right, result)


# ══════════════════════════════════════════════════════════════════
#  4.  AVL TREE  (self-balancing BST)
# ══════════════════════════════════════════════════════════════════

class _AVLNode:
    """A single node in an AVL Tree."""

    __slots__ = ("value", "left", "right", "height")

    def __init__(self, value: int) -> None:
        self.value:  int                 = value
        self.left:   Optional[_AVLNode]  = None
        self.right:  Optional[_AVLNode]  = None
        self.height: int                 = 1   # leaf height = 1


class AVLTreeDS:
    """
    AVL Tree – a height-balanced Binary Search Tree.

    After every insert or delete the balance factor of every ancestor
    is checked and one of four rotations is applied when |bf| > 1:

    * Left Rotation          (LL-heavy right subtree)
    * Right Rotation         (RR-heavy left subtree)
    * Left-Right Rotation    (LR case)
    * Right-Left Rotation    (RL case)

    This guarantees O(log n) for all three operations.

    Attributes
    ----------
    _root : _AVLNode | None
    _size : int
    """

    def __init__(self) -> None:
        """Initialise an empty AVL tree."""
        self._root: Optional[_AVLNode] = None
        self._size: int                = 0

    # ── public API ──────────────────────────────────────────────

    def insert(self, value: int) -> None:
        """
        Insert *value* and rebalance as needed.

        Time complexity: O(log n).

        Parameters
        ----------
        value : int
        """
        before      = self._size
        self._root  = self._insert_rec(self._root, value)
        # _size is incremented inside _insert_rec on actual insertion

    def search(self, value: int) -> bool:
        """
        Return True if *value* exists in the tree.

        Time complexity: O(log n).

        Parameters
        ----------
        value : int
        """
        return self._search_rec(self._root, value)

    def delete(self, value: int) -> bool:
        """
        Remove *value* and rebalance as needed.

        Time complexity: O(log n).

        Parameters
        ----------
        value : int

        Returns
        -------
        bool
            True if *value* was removed.
        """
        if not self.search(value):
            return False
        self._root  = self._delete_rec(self._root, value)
        self._size -= 1
        return True

    def get_nodes_edges(self) -> tuple[list[dict], list[dict]]:
        """
        Return agraph-compatible node and edge descriptors.

        Returns
        -------
        nodes : list[dict]
            Each dict has keys ``id``, ``label``, ``title`` (balance factor).
        edges : list[dict]
            Each dict has keys ``source`` and ``target``.
        """
        nodes: list[dict] = []
        edges: list[dict] = []
        self._collect(self._root, nodes, edges)
        return nodes, edges

    def size(self) -> int:
        """Return the number of nodes."""
        return self._size

    def get_height(self) -> int:
        """Return the height of the AVL tree."""
        return self._height(self._root)

    def inorder(self) -> list[int]:
        """Return a sorted list of all values."""
        result: list[int] = []
        self._inorder_rec(self._root, result)
        return result

    # ── private: core insert / delete ───────────────────────────

    def _search_rec(
        self,
        node: Optional[_AVLNode],
        value: int,
    ) -> bool:
        """Recursive BST search – O(log n) on a balanced tree."""
        if node is None:
            return False
        if value == node.value:
            return True
        if value < node.value:
            return self._search_rec(node.left,  value)
        return self._search_rec(node.right, value)

    def _insert_rec(
        self,
        node: Optional[_AVLNode],
        value: int,
    ) -> _AVLNode:
        # ── 1. standard BST insert ──────────────────────────────
        if node is None:
            self._size += 1
            return _AVLNode(value)

        if value < node.value:
            node.left  = self._insert_rec(node.left,  value)
        elif value > node.value:
            node.right = self._insert_rec(node.right, value)
        else:
            return node  # duplicate – ignore

        # ── 2. update height ────────────────────────────────────
        self._update_height(node)

        # ── 3. rebalance ────────────────────────────────────────
        return self._rebalance(node, value)

    def _delete_rec(
        self,
        node: Optional[_AVLNode],
        value: int,
    ) -> Optional[_AVLNode]:
        # ── 1. standard BST delete ──────────────────────────────
        if node is None:
            return None

        if value < node.value:
            node.left  = self._delete_rec(node.left,  value)
        elif value > node.value:
            node.right = self._delete_rec(node.right, value)
        else:
            # Node to delete found
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            # Two children: replace with in-order successor
            successor  = self._min_node(node.right)
            node.value = successor.value
            node.right = self._delete_rec(node.right, successor.value)

        # ── 2. update height ────────────────────────────────────
        self._update_height(node)

        # ── 3. rebalance (deletion variant – no value hint) ─────
        return self._rebalance_delete(node)

    # ── private: rotations ──────────────────────────────────────

    def _rotate_right(self, z: _AVLNode) -> _AVLNode:
        """
        Right rotation around *z*.

              z                  y
             / \\               / \\
            y   T4    →       x   z
           / \\                   / \\
          x   T3               T3  T4
        """
        y        = z.left
        T3       = y.right    # type: ignore[union-attr]

        y.right  = z          # type: ignore[union-attr]
        z.left   = T3

        self._update_height(z)
        self._update_height(y)  # type: ignore[arg-type]
        return y               # type: ignore[return-value]

    def _rotate_left(self, z: _AVLNode) -> _AVLNode:
        """
        Left rotation around *z*.

          z                    y
         / \\                  / \\
        T1   y      →        z   x
            / \\            / \\
           T2   x          T1  T2
        """
        y        = z.right
        T2       = y.left     # type: ignore[union-attr]

        y.left   = z          # type: ignore[union-attr]
        z.right  = T2

        self._update_height(z)
        self._update_height(y)  # type: ignore[arg-type]
        return y               # type: ignore[return-value]

    # ── private: balance helpers ────────────────────────────────

    @staticmethod
    def _height(node: Optional[_AVLNode]) -> int:
        """Return stored height, treating None as 0."""
        return node.height if node is not None else 0

    def _update_height(self, node: _AVLNode) -> None:
        """Recompute height from children's heights."""
        node.height = 1 + max(
            self._height(node.left),
            self._height(node.right),
        )

    def _balance_factor(self, node: Optional[_AVLNode]) -> int:
        """
        Balance factor = height(left) - height(right).

        *  > 1  → left-heavy  (right rotation needed)
        * < -1  → right-heavy (left rotation needed)
        """
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _rebalance(self, node: _AVLNode, inserted_value: int) -> _AVLNode:
        """
        Rebalance after an **insertion** using the inserted value to
        choose the exact rotation case.

        Four cases
        ----------
        LL  bf > 1  and value < node.left.value   → right rotate
        RR  bf < -1 and value > node.right.value  → left rotate
        LR  bf > 1  and value > node.left.value   → left-right rotate
        RL  bf < -1 and value < node.right.value  → right-left rotate
        """
        bf = self._balance_factor(node)

        # ── LL ──────────────────────────────────────────────────
        if bf > 1 and node.left is not None and inserted_value < node.left.value:
            return self._rotate_right(node)

        # ── RR ──────────────────────────────────────────────────
        if bf < -1 and node.right is not None and inserted_value > node.right.value:
            return self._rotate_left(node)

        # ── LR ──────────────────────────────────────────────────
        if bf > 1 and node.left is not None and inserted_value > node.left.value:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # ── RL ──────────────────────────────────────────────────
        if bf < -1 and node.right is not None and inserted_value < node.right.value:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node  # already balanced

    def _rebalance_delete(self, node: _AVLNode) -> _AVLNode:
        """
        Rebalance after a **deletion** using balance factors only
        (no inserted value available).

        The four rotation cases are determined solely by the balance
        factors of the current node and its taller child.
        """
        bf = self._balance_factor(node)

        # ── Left-heavy ──────────────────────────────────────────
        if bf > 1:
            left_bf = self._balance_factor(node.left)
            if left_bf >= 0:
                # LL
                return self._rotate_right(node)
            else:
                # LR
                node.left = self._rotate_left(node.left)   # type: ignore[arg-type]
                return self._rotate_right(node)

        # ── Right-heavy ─────────────────────────────────────────
        if bf < -1:
            right_bf = self._balance_factor(node.right)
            if right_bf <= 0:
                # RR
                return self._rotate_left(node)
            else:
                # RL
                node.right = self._rotate_right(node.right)  # type: ignore[arg-type]
                return self._rotate_left(node)

        return node  # already balanced

    # ── private: traversal helpers ──────────────────────────────

    @staticmethod
    def _min_node(node: _AVLNode) -> _AVLNode:
        """Return the leftmost (smallest) node in a subtree."""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _collect(
        self,
        node: Optional[_AVLNode],
        nodes: list[dict],
        edges:  list[dict],
    ) -> None:
        """Pre-order traversal producing agraph-compatible dicts."""
        if node is None:
            return
        bf    = self._balance_factor(node)
        label = str(node.value)
        nodes.append({
            "id":    label,
            "label": label,
            "title": f"bf={bf}, h={node.height}",
        })
        if node.left is not None:
            edges.append({"source": label, "target": str(node.left.value)})
        if node.right is not None:
            edges.append({"source": label, "target": str(node.right.value)})
        self._collect(node.left,  nodes, edges)
        self._collect(node.right, nodes, edges)

    def _inorder_rec(
        self,
        node: Optional[_AVLNode],
        result: list[int],
    ) -> None:
        if node is None:
            return
        self._inorder_rec(node.left,  result)
        result.append(node.value)
        self._inorder_rec(node.right, result)


# ══════════════════════════════════════════════════════════════════
#  Quick self-test  (python data_structures.py)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random

    # ── Array ────────────────────────────────────────────────────
    arr = ArrayDS()
    for v in [5, 3, 8, 1, 9, 2]:
        arr.insert(v)
    assert arr.search(8)  is True,  "linear search failed"
    assert arr.search(99) is False, "linear search false positive"
    assert arr.binary_search(3)  is True,  "binary search failed"
    assert arr.binary_search(99) is False, "binary search false positive"
    arr.delete(3)
    assert arr.search(3) is False, "delete failed"
    print("ArrayDS       ✓")

    # ── Hash Table ───────────────────────────────────────────────
    ht = HashTableDS(capacity=8)
    for v in [10, 20, 30, 18, 26]:
        ht.insert(v)
    assert ht.search(20) is True,  "hash search failed"
    assert ht.search(99) is False, "hash search false positive"
    ht.delete(20)
    assert ht.search(20) is False, "hash delete failed"
    # trigger resize
    for v in range(100):
        ht.insert(v)
    assert ht.search(77) is True,  "hash search after resize failed"
    print("HashTableDS   ✓")

    # ── BST ──────────────────────────────────────────────────────
    bst = BinarySearchTreeDS()
    for v in [50, 30, 70, 20, 40, 60, 80]:
        bst.insert(v)
    assert bst.search(40) is True,  "BST search failed"
    assert bst.search(99) is False, "BST search false positive"
    bst.delete(30)   # two-child deletion
    assert bst.search(30) is False, "BST delete (2-child) failed"
    bst.delete(80)   # leaf deletion
    assert bst.search(80) is False, "BST delete (leaf) failed"
    bst.delete(70)   # one-child deletion
    assert bst.search(70) is False, "BST delete (1-child) failed"
    print("BinarySearchTreeDS ✓")

    # ── AVL ──────────────────────────────────────────────────────
    avl = AVLTreeDS()
    values = [10, 20, 30, 40, 50, 25]
    for v in values:
        avl.insert(v)
    # Verify in-order gives sorted sequence
    io = avl.inorder()
    assert io == sorted(values), f"AVL in-order wrong: {io}"
    # Verify height stays O(log n)
    assert avl._root is not None
    assert avl._root.height <= 4, f"AVL unbalanced: height={avl._root.height}"
    avl.delete(40)
    assert avl.search(40) is False, "AVL delete failed"
    # Random stress test – use a unique set so delete/search ranges don't overlap
    rng   = random.Random(42)
    uniq  = list(range(1, 501))          # 500 unique values
    rng.shuffle(uniq)
    insert_vals = uniq[:300]
    delete_vals = uniq[:100]             # first 100 of inserted set
    keep_vals   = uniq[100:200]          # next 100 must still be present

    avl2 = AVLTreeDS()
    for v in insert_vals:
        avl2.insert(v)
    for v in delete_vals:
        avl2.delete(v)
    for v in keep_vals:
        assert avl2.search(v) is True, f"AVL stress-search failed for {v}"
    for v in delete_vals:
        assert avl2.search(v) is False, f"AVL ghost value after delete: {v}"
    print("AVLTreeDS     ✓")

    print("\nAll tests passed ✓")
