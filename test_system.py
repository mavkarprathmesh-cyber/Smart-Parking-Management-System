"""
Comprehensive Test Suite for Smart Parking System
Tests all pure DSA data structures, database persistence, authentication, RBAC, advance bookings, and API workflows.
"""

import unittest
import sqlite3
import os
import time

# Import DSA Structures
from dsa.linear import (
    SinglyLinkedList,
    DoublyLinkedList,
    CircularLinkedList,
    Stack,
    Queue,
    CircularQueue,
    PriorityQueue,
    Deque
)
from dsa.trees import BinarySearchTree, AVLTree, MinHeap
from dsa.hash_table import HashTable
from dsa.graph import ParkingGraph
from dsa.algorithms import (
    bubble_sort,
    selection_sort,
    insertion_sort,
    merge_sort,
    quick_sort,
    heap_sort,
    radix_sort,
    linear_search,
    binary_search,
    greedy_slot_allocation
)
from database.db import init_db, get_db_connection
from database.seed_data import seed_database
from services.parking_service import ParkingService
from services.search_service import SearchService
from services.graph_service import GraphService
from services.lab_service import LabService
from services.auth_service import AuthService
from services.booking_service import BookingService
from services.security import hash_password, verify_password, validate_password_strength


class TestDSADataStructures(unittest.TestCase):

    def test_singly_linked_list(self):
        sll = SinglyLinkedList()
        self.assertTrue(sll.is_empty())
        sll.append({"id": 1, "car": "KA-01"})
        sll.append({"id": 2, "car": "KA-02"})
        sll.prepend({"id": 0, "car": "KA-00"})
        self.assertEqual(sll.size(), 3)
        items = sll.to_list()
        self.assertEqual(items[0]["car"], "KA-00")
        self.assertEqual(items[-1]["car"], "KA-02")

    def test_doubly_linked_list(self):
        dll = DoublyLinkedList()
        dll.append("A")
        dll.append("B")
        dll.append("C")
        self.assertEqual(dll.to_list_forward(), ["A", "B", "C"])
        self.assertEqual(dll.to_list_backward(), ["C", "B", "A"])

    def test_circular_linked_list(self):
        cll = CircularLinkedList()
        cll.append("Zone A")
        cll.append("Zone B")
        cll.append("Zone C")
        self.assertEqual(cll.size(), 3)
        self.assertEqual(cll.next_zone(), "Zone A")
        self.assertEqual(cll.next_zone(), "Zone B")
        self.assertEqual(cll.next_zone(), "Zone C")
        self.assertEqual(cll.next_zone(), "Zone A")

    def test_stack_undo(self):
        st = Stack()
        st.push({"action": "PARK", "slot": "A-01"})
        st.push({"action": "PARK", "slot": "A-02"})
        self.assertEqual(st.size(), 2)
        popped = st.pop()
        self.assertEqual(popped["slot"], "A-02")
        self.assertEqual(st.peek()["slot"], "A-01")

    def test_fifo_queue(self):
        q = Queue()
        q.enqueue("REQ-1")
        q.enqueue("REQ-2")
        self.assertEqual(q.dequeue(), "REQ-1")
        self.assertEqual(q.dequeue(), "REQ-2")
        self.assertTrue(q.is_empty())

    def test_circular_queue(self):
        cq = CircularQueue(capacity=3)
        self.assertTrue(cq.enqueue("A"))
        self.assertTrue(cq.enqueue("B"))
        self.assertTrue(cq.enqueue("C"))
        self.assertFalse(cq.enqueue("D"))
        self.assertEqual(cq.dequeue(), "A")
        self.assertTrue(cq.enqueue("D"))
        self.assertEqual(cq.dequeue(), "B")

    def test_priority_queue(self):
        pq = PriorityQueue()
        pq.enqueue("Normal Car", 4)
        pq.enqueue("Ambulance", 1)
        pq.enqueue("VIP Car", 3)
        pq.enqueue("Disabled Driver", 2)
        self.assertEqual(pq.dequeue(), "Ambulance")
        self.assertEqual(pq.dequeue(), "Disabled Driver")
        self.assertEqual(pq.dequeue(), "VIP Car")
        self.assertEqual(pq.dequeue(), "Normal Car")

    def test_deque(self):
        dq = Deque()
        dq.append_rear("B")
        dq.append_front("A")
        dq.append_rear("C")
        self.assertEqual(dq.to_list(), ["A", "B", "C"])
        self.assertEqual(dq.pop_front(), "A")
        self.assertEqual(dq.pop_rear(), "C")

    def test_bst_and_avl(self):
        bst = BinarySearchTree()
        avl = AVLTree()
        keys = ["KA-05-AA", "KA-01-BB", "KA-09-CC", "KA-03-DD", "KA-07-EE"]
        for k in keys:
            bst.insert(k, f"Data-{k}")
            avl.insert(k, f"Data-{k}")

        data_bst, comps_bst = bst.search("KA-03-DD")
        data_avl, comps_avl = avl.search("KA-03-DD")
        self.assertEqual(data_bst, "Data-KA-03-DD")
        self.assertEqual(data_avl, "Data-KA-03-DD")
        self.assertTrue(comps_avl > 0)

    def test_min_heap(self):
        heap = MinHeap()
        heap.push(45.0, "Slot-Far")
        heap.push(12.0, "Slot-Near")
        heap.push(28.0, "Slot-Mid")
        self.assertEqual(heap.pop(), "Slot-Near")
        self.assertEqual(heap.pop(), "Slot-Mid")
        self.assertEqual(heap.pop(), "Slot-Far")

    def test_hash_table(self):
        ht = HashTable(initial_capacity=11)
        ht.insert("KA-01-1234", {"owner": "Alice", "slot": "A-01"})
        ht.insert("KA-02-5678", {"owner": "Bob", "slot": "B-02"})
        val, comps, bucket = ht.search("KA-01-1234")
        self.assertIsNotNone(val)
        self.assertEqual(val["owner"], "Alice")

    def test_graph_and_dijkstra(self):
        g = ParkingGraph()
        g.add_node("GATE", "Main Gate", "GATE", 0, 0)
        g.add_node("J1", "Junction 1", "JUNCTION", 10, 0)
        g.add_node("SLOT-A", "Slot A", "SLOT", 20, 0)
        g.add_node("SLOT-B", "Slot B", "SLOT", 10, 30)

        g.add_edge("GATE", "J1", 10.0)
        g.add_edge("J1", "SLOT-A", 10.0)
        g.add_edge("J1", "SLOT-B", 30.0)

        res = g.dijkstra_shortest_path("GATE", "SLOT-A")
        self.assertTrue(res["success"])
        self.assertEqual(res["path"], ["GATE", "J1", "SLOT-A"])
        self.assertEqual(res["total_distance_meters"], 20.0)

    def test_sorting_algorithms(self):
        sample = [64, 34, 25, 12, 22, 11, 90]
        expected = sorted(sample)

        for sort_fn in [bubble_sort, selection_sort, insertion_sort, merge_sort, quick_sort, heap_sort, radix_sort]:
            res = sort_fn(sample)
            self.assertEqual(res["sorted_array"], expected, f"Failed for {res.get('algorithm')}")

    def test_search_algorithms(self):
        arr = [10, 20, 30, 40, 50, 60]
        lin_res = linear_search(arr, 40)
        self.assertTrue(lin_res["found"])
        self.assertEqual(lin_res["index"], 3)

        bin_res = binary_search(arr, 40)
        self.assertTrue(bin_res["found"])
        self.assertEqual(bin_res["index"], 3)


class TestAuthAndBookings(unittest.TestCase):

    def setUp(self):
        init_db()
        seed_database(force_reset=True)

    def test_password_hashing(self):
        pwd = "SecurePassword@123"
        h, salt = hash_password(pwd)
        self.assertTrue(verify_password(pwd, h, salt))
        self.assertFalse(verify_password("WrongPassword", h, salt))

    def test_admin_and_user_login(self):
        auth = AuthService()
        # Admin Login
        admin_res = auth.login_user({"email": "admin@smartpark.com", "password": "Admin@1234"})
        self.assertTrue(admin_res["success"])
        self.assertEqual(admin_res["user"]["role"], "ADMIN")

        # User Login
        user_res = auth.login_user({"email": "priya@student.edu", "password": "User@1234"})
        self.assertTrue(user_res["success"])
        self.assertEqual(user_res["user"]["role"], "USER")

        # Bad Password
        bad_res = auth.login_user({"email": "admin@smartpark.com", "password": "WrongPassword"})
        self.assertFalse(bad_res["success"])

    def test_advance_booking_and_double_booking_prevention(self):
        bs = BookingService()
        ps = ParkingService()

        # 1. Book Slot A-03 for tomorrow
        res1 = bs.create_advance_booking(
            user_id="U-102",
            vehicle_number="KA-03-EQ-4567",
            vehicle_type="4W",
            zone_id="A",
            slot_id="A-03",
            booking_date="2026-10-01",
            arrival_time="11:00",
            duration_hours=3
        )
        self.assertTrue(res1["success"])
        bkg_id = res1["booking_id"]

        # Slot in DB should now be RESERVED
        slot = ps.get_slot_by_id("A-03")
        self.assertEqual(slot["status"], "RESERVED")

        # 2. Attempt double booking on same slot & date -> MUST FAIL
        res2 = bs.create_advance_booking(
            user_id="U-101",
            vehicle_number="KA-01-MG-2024",
            vehicle_type="4W",
            zone_id="A",
            slot_id="A-03",
            booking_date="2026-10-01",
            arrival_time="11:00",
            duration_hours=2
        )
        self.assertFalse(res2["success"])
        self.assertIn("already", res2["error"].lower())

        # 3. User cancels booking
        cancel_res = bs.cancel_booking(user_id="U-102", booking_id=bkg_id)
        self.assertTrue(cancel_res["success"])

        # Slot should now be FREE again
        slot_freed = ps.get_slot_by_id("A-03")
        self.assertEqual(slot_freed["status"], "FREE")


if __name__ == "__main__":
    unittest.main()
