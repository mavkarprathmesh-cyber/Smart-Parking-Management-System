"""
Parking Service Module
Orchestrates high-level business logic and maps every operation to its pure DSA data structure:
- Queue & PriorityQueue for parking requests
- MinHeap & Greedy for candidate selection
- SinglyLinkedList & DoublyLinkedList for history
- CircularLinkedList for cyclic zone inspection
- CircularQueue for entry buffer
- Stack for action undo
- Dijkstra graph for route planning
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from database.db import get_db_connection
from dsa.linear import (
    Queue,
    PriorityQueue,
    Deque,
    Stack,
    SinglyLinkedList,
    DoublyLinkedList,
    CircularLinkedList,
    CircularQueue
)
from dsa.trees import MinHeap, BinaryTree
from dsa.algorithms import greedy_slot_allocation
from dsa.graph import ParkingGraph


class ParkingService:
    def __init__(self):
        # In-memory DSA state structures
        self.normal_queue = Queue()
        self.priority_queue = PriorityQueue()
        self.priority_deque = Deque()
        self.undo_stack = Stack(max_capacity=50)
        self.history_sll = SinglyLinkedList()
        self.audit_dll = DoublyLinkedList()
        self.zone_cll = CircularLinkedList()
        self.entry_buffer_cq = CircularQueue(capacity=10)
        self.facility_tree = BinaryTree(root_key="Campus Parking Facility")
        
        # Initialize graph and populate zones in CLL
        self._init_zone_cll()
        self._sync_active_queues_from_db()
        self._sync_history_from_db()

    def _init_zone_cll(self):
        """Initializes Circular Linked List for cyclic zone traversal."""
        from database.db import init_db
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_zones ORDER BY zone_id ASC")
        zones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        self.zone_cll = CircularLinkedList()
        for z in zones:
            self.zone_cll.append(z)

    def _sync_active_queues_from_db(self):
        """Loads any pending queued requests from database into Queue / PriorityQueue."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_requests WHERE status = 'QUEUED' ORDER BY requested_at ASC")
        requests = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for req in requests:
            p_level = req.get("priority_level", "NORMAL")
            if p_level == "NORMAL":
                self.normal_queue.enqueue(req)
            else:
                rank_map = {"EMERGENCY": 1, "ACCESSIBILITY": 2, "RESERVED": 3}
                rank = rank_map.get(p_level, 4)
                self.priority_queue.enqueue(req, rank)

    def _sync_history_from_db(self):
        """Loads recent completed & active tickets into SLL and DLL."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entry_exit_history ORDER BY id DESC LIMIT 50")
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for rec in reversed(records):
            self.history_sll.append(rec)
            self.audit_dll.append(rec)

    # ==========================================
    # 1. DASHBOARD KPI & OVERVIEW
    # ==========================================
    def get_dashboard_data(self) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Slot counts
        cursor.execute("SELECT status, COUNT(*) as cnt FROM parking_slots GROUP BY status")
        status_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        total_slots = sum(status_counts.values())
        free_slots = status_counts.get("FREE", 0)
        occupied_slots = status_counts.get("OCCUPIED", 0)
        reserved_slots = status_counts.get("RESERVED", 0)
        blocked_slots = status_counts.get("BLOCKED", 0)

        occupancy_pct = round((occupied_slots / total_slots * 100), 1) if total_slots > 0 else 0.0

        # Zone-wise stats
        cursor.execute("""
        SELECT z.zone_id, z.name, z.floor, z.allowed_type, z.hourly_rate,
               COUNT(s.id) as total,
               SUM(CASE WHEN s.status = 'FREE' THEN 1 ELSE 0 END) as free,
               SUM(CASE WHEN s.status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN s.status = 'RESERVED' THEN 1 ELSE 0 END) as reserved
        FROM parking_zones z
        LEFT JOIN parking_slots s ON z.zone_id = s.zone_id
        GROUP BY z.zone_id
        """)
        zone_stats = [dict(row) for row in cursor.fetchall()]

        # Recent activities from SLL/DB
        cursor.execute("SELECT * FROM entry_exit_history ORDER BY id DESC LIMIT 8")
        recent_activities = [dict(row) for row in cursor.fetchall()]

        # Active parked vehicles
        cursor.execute("SELECT * FROM entry_exit_history WHERE status = 'ACTIVE' ORDER BY entry_time DESC")
        active_parked = [dict(row) for row in cursor.fetchall()]

        # System Undo Stack size
        undo_available = not self.undo_stack.is_empty()
        last_action = self.undo_stack.peek()

        conn.close()

        return {
            "total_slots": total_slots,
            "free_slots": free_slots,
            "occupied_slots": occupied_slots,
            "reserved_slots": reserved_slots,
            "blocked_slots": blocked_slots,
            "occupancy_percentage": occupancy_pct,
            "normal_queue_count": self.normal_queue.size(),
            "priority_queue_count": self.priority_queue.size(),
            "total_active_parked": len(active_parked),
            "zone_statistics": zone_stats,
            "recent_activities": recent_activities,
            "undo_available": undo_available,
            "last_action": last_action
        }

    # ==========================================
    # 2. PARKING SLOTS MANAGEMENT
    # ==========================================
    def get_all_slots(self, zone_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT s.*, v.vehicle_number, v.model_name, u.full_name as owner_name, z.name as zone_name, z.hourly_rate
        FROM parking_slots s
        LEFT JOIN vehicles v ON s.assigned_vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        LEFT JOIN parking_zones z ON s.zone_id = z.zone_id
        WHERE 1=1
        """
        params = []
        if zone_id and zone_id != "ALL":
            query += " AND s.zone_id = ?"
            params.append(zone_id)
        if status and status != "ALL":
            query += " AND s.status = ?"
            params.append(status)

        query += " ORDER BY s.zone_id, s.slot_id ASC"
        cursor.execute(query, params)
        slots = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return slots

    def get_slot_by_id(self, slot_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT s.*, v.vehicle_number, v.model_name, u.full_name as owner_name, z.name as zone_name, z.hourly_rate
        FROM parking_slots s
        LEFT JOIN vehicles v ON s.assigned_vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        LEFT JOIN parking_zones z ON s.zone_id = z.zone_id
        WHERE s.slot_id = ?
        """, (slot_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
        slot_id = slot_data.get("slot_id", "").strip().upper()
        zone_id = slot_data.get("zone_id", "").strip().upper()
        v_type = slot_data.get("vehicle_type", "4W")
        dist = float(slot_data.get("distance_from_gate", 30.0))
        priority = slot_data.get("priority", "NORMAL")
        pos_x = float(slot_data.get("pos_x", 100))
        pos_y = float(slot_data.get("pos_y", 100))

        if not slot_id or not zone_id:
            return {"success": False, "error": "Slot ID and Zone ID are required"}

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO parking_slots (slot_id, zone_id, vehicle_type, status, distance_from_gate, priority, pos_x, pos_y, is_demo)
            VALUES (?, ?, ?, 'FREE', ?, ?, ?, ?, 0)
            """, (slot_id, zone_id, v_type, dist, priority, pos_x, pos_y))
            conn.commit()

            # Record in undo stack
            self.undo_stack.push({
                "action": "ADD_SLOT",
                "slot_id": slot_id,
                "details": f"Added slot {slot_id} in Zone {zone_id}"
            })

            return {"success": True, "message": f"Slot {slot_id} successfully created."}
        except sqlite3.IntegrityError as e:
            return {"success": False, "error": f"Slot with ID '{slot_id}' already exists."}
        finally:
            conn.close()

    def update_slot_status(self, slot_id: str, new_status: str) -> Dict[str, Any]:
        slot_id = slot_id.strip().upper()
        if new_status not in ["FREE", "OCCUPIED", "RESERVED", "BLOCKED"]:
            return {"success": False, "error": f"Invalid status '{new_status}'"}

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_slots WHERE slot_id = ?", (slot_id,))
        slot = cursor.fetchone()
        if not slot:
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' not found"}

        old_status = slot["status"]
        cursor.execute("UPDATE parking_slots SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE slot_id = ?", (new_status, slot_id))
        conn.commit()
        conn.close()

        # Push to undo stack
        self.undo_stack.push({
            "action": "UPDATE_SLOT_STATUS",
            "slot_id": slot_id,
            "old_status": old_status,
            "new_status": new_status,
            "details": f"Changed slot {slot_id} from {old_status} to {new_status}"
        })

        return {"success": True, "message": f"Slot {slot_id} status updated to {new_status}"}

    def delete_slot(self, slot_id: str) -> Dict[str, Any]:
        slot_id = slot_id.strip().upper()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_slots WHERE slot_id = ?", (slot_id,))
        slot = cursor.fetchone()
        if not slot:
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' does not exist"}

        if slot["status"] == "OCCUPIED":
            conn.close()
            return {"success": False, "error": "Cannot delete an OCCUPIED slot. Please exit vehicle first."}

        cursor.execute("DELETE FROM parking_slots WHERE slot_id = ?", (slot_id,))
        conn.commit()
        conn.close()

        self.undo_stack.push({
            "action": "DELETE_SLOT",
            "slot_id": slot_id,
            "details": f"Deleted slot {slot_id}"
        })

        return {"success": True, "message": f"Slot {slot_id} deleted successfully."}

    # ==========================================
    # 3. VEHICLE MANAGEMENT
    # ==========================================
    def register_vehicle(self, v_data: Dict[str, Any]) -> Dict[str, Any]:
        v_num = v_data.get("vehicle_number", "").strip().upper()
        v_type = v_data.get("vehicle_type", "4W")
        user_name = v_data.get("owner_name", "Visitor").strip()
        model = v_data.get("model_name", "Standard").strip()
        color = v_data.get("color", "Black").strip()

        if not v_num:
            return {"success": False, "error": "Vehicle registration number is required."}

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate vehicle number
        cursor.execute("SELECT * FROM vehicles WHERE UPPER(vehicle_number) = ?", (v_num,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": f"Vehicle with number '{v_num}' is already registered."}

        # Generate User and Vehicle IDs
        cursor.execute("SELECT COUNT(*) FROM users")
        u_count = cursor.fetchone()[0] + 1
        user_id = f"U-{100 + u_count}"

        cursor.execute("SELECT COUNT(*) FROM vehicles")
        v_count = cursor.fetchone()[0] + 1
        v_id = f"V-{100 + v_count}"

        try:
            cursor.execute("""
            INSERT INTO users (user_id, full_name, role, is_demo)
            VALUES (?, ?, 'USER', 0)
            """, (user_id, user_name))

            cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_number, user_id, vehicle_type, model_name, color, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (v_id, v_num, user_id, v_type, model, color))

            conn.commit()
            return {
                "success": True,
                "message": f"Vehicle '{v_num}' successfully registered.",
                "vehicle_id": v_id,
                "user_id": user_id
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT v.*, u.full_name as owner_name, u.role, u.email,
               s.slot_id as current_parked_slot, s.status as slot_status
        FROM vehicles v
        JOIN users u ON v.user_id = u.user_id
        LEFT JOIN parking_slots s ON s.assigned_vehicle_id = v.vehicle_id
        ORDER BY v.id DESC
        """)
        vehicles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return vehicles

    # ==========================================
    # 4. SMART SLOT ALLOCATION ENGINE (DSA WORKFLOW)
    # ==========================================
    def submit_parking_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submits a parking request:
        1. Validates vehicle existence (auto-registers if new).
        2. Validates vehicle is not already parked.
        3. Enqueues request into Queue (Normal) or PriorityQueue (Min-Heap for Emergency/VIP).
        4. Batch adds to CircularQueue entry buffer.
        """
        v_num = request_data.get("vehicle_number", "").strip().upper()
        v_type = request_data.get("vehicle_type", "4W")
        priority_level = request_data.get("priority_level", "NORMAL").upper()
        gate = request_data.get("entry_gate", "GATE-1")

        if not v_num:
            return {"success": False, "error": "Vehicle number is required."}

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if already parked
        cursor.execute("""
        SELECT * FROM entry_exit_history
        WHERE UPPER(vehicle_number) = ? AND status = 'ACTIVE'
        """, (v_num,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": f"Vehicle '{v_num}' is ALREADY currently parked inside the facility."}

        # Check or auto-create vehicle
        cursor.execute("SELECT * FROM vehicles WHERE UPPER(vehicle_number) = ?", (v_num,))
        v_row = cursor.fetchone()
        if not v_row:
            rand_id = random_generator()
            user_id = f"U-{rand_id}"
            v_id = f"V-{rand_id}"
            cursor.execute("INSERT INTO users (user_id, full_name, role) VALUES (?, ?, 'VISITOR')", (user_id, f"Guest Driver ({v_num})"))
            cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_number, user_id, vehicle_type, model_name, color)
            VALUES (?, ?, ?, ?, 'Car/Bike', 'Unknown')
            """, (v_id, v_num, user_id, v_type))
            conn.commit()
            vehicle_id = v_id
        else:
            vehicle_id = v_row["vehicle_id"]
            v_type = v_row["vehicle_type"]

        # Generate request ID
        req_id_int = int(datetime.now().timestamp() * 1000) % 1000000
        req_id = f"REQ-{req_id_int}"
        queue_type = "PRIORITY" if priority_level != "NORMAL" else "FIFO"

        cursor.execute("""
        INSERT INTO parking_requests (request_id, vehicle_id, vehicle_number, vehicle_type, priority_level, status, queue_type)
        VALUES (?, ?, ?, ?, ?, 'QUEUED', ?)
        """, (req_id, vehicle_id, v_num, v_type, priority_level, queue_type))
        conn.commit()
        db_id = cursor.lastrowid
        conn.close()

        req_obj = {
            "id": db_id,
            "request_id": req_id,
            "vehicle_id": vehicle_id,
            "vehicle_number": v_num,
            "vehicle_type": v_type,
            "priority_level": priority_level,
            "queue_type": queue_type,
            "entry_gate": gate,
            "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Add to Entry Buffer (Circular Queue)
        self.entry_buffer_cq.enqueue(req_obj)

        # Enqueue into appropriate DSA queue
        if priority_level == "NORMAL":
            self.normal_queue.enqueue(req_obj)
            dsa_structure_used = "FIFO Queue"
        else:
            rank_map = {"EMERGENCY": 1, "ACCESSIBILITY": 2, "RESERVED": 3}
            rank = rank_map.get(priority_level, 4)
            self.priority_queue.enqueue(req_obj, rank)
            dsa_structure_used = f"Min-Heap Priority Queue (Rank {rank})"

        return {
            "success": True,
            "message": f"Request {req_id} placed in {queue_type} queue.",
            "request_id": req_id,
            "vehicle_number": v_num,
            "queue_position": self.priority_queue.size() if priority_level != "NORMAL" else self.normal_queue.size(),
            "dsa_structure_used": dsa_structure_used,
            "request_data": req_obj
        }

    def allocate_next_request(self, target_req_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes Smart Allocation for the next queued vehicle or a specific request:
        1. Dequeues request (Priority Queue receives strict precedence over Normal Queue).
        2. Evaluates compatible free slots using Greedy Allocation + Min Heap scoring.
        3. Assigns best slot and computes Dijkstra shortest path from Gate to Slot.
        4. Creates active parking ticket in DB and updates history SLL/DLL.
        """
        # Determine which request to process
        req_to_process = None

        if target_req_id:
            # Lookup specific request from DB
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_requests WHERE request_id = ? AND status = 'QUEUED'", (target_req_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                req_to_process = dict(row)
                if req_to_process.get("priority_level") == "NORMAL":
                    self.normal_queue.remove_by_id(req_to_process["id"])
                else:
                    self.priority_queue.remove_by_id(req_to_process["id"])
        else:
            # Priority Queue has strict precedence
            if not self.priority_queue.is_empty():
                req_to_process = self.priority_queue.dequeue()
            elif not self.normal_queue.is_empty():
                req_to_process = self.normal_queue.dequeue()

        if not req_to_process:
            return {"success": False, "error": "No pending parking requests in queue."}

        v_type = req_to_process.get("vehicle_type", "4W")
        priority_lvl = req_to_process.get("priority_level", "NORMAL")
        v_num = req_to_process.get("vehicle_number")
        v_id = req_to_process.get("vehicle_id")
        req_id = req_to_process.get("request_id")
        gate = req_to_process.get("entry_gate", "GATE-1")

        # Fetch all currently FREE slots from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_slots WHERE status = 'FREE'")
        free_slots = [dict(row) for row in cursor.fetchall()]

        if not free_slots:
            conn.close()
            # Restore request back to queue
            if priority_lvl == "NORMAL":
                self.normal_queue.enqueue(req_to_process)
            else:
                self.priority_queue.enqueue(req_to_process, 1)
            return {
                "success": False,
                "error": "PARKING FULL: No FREE slots currently available in any zone.",
                "request_id": req_id
            }

        # Run Min-Heap candidate scoring & Greedy algorithm
        min_heap = MinHeap()
        for slot in free_slots:
            if slot["vehicle_type"] != v_type:
                continue
            if priority_lvl == "NORMAL" and slot["priority"] in ["EMERGENCY", "RESERVED"]:
                continue

            dist = float(slot["distance_from_gate"])
            bonus = 0.0
            if priority_lvl == "EMERGENCY":
                bonus = 50.0
            elif priority_lvl == "ACCESSIBILITY" and slot["zone_id"] in ["A", "D"]:
                bonus = 30.0
            elif priority_lvl == "RESERVED":
                bonus = 20.0

            score = max(0.0, dist - bonus)
            min_heap.push(score, slot)

        if min_heap.is_empty():
            conn.close()
            if priority_lvl == "NORMAL":
                self.normal_queue.enqueue(req_to_process)
            else:
                self.priority_queue.enqueue(req_to_process, 1)
            return {
                "success": False,
                "error": f"No compatible slots available for vehicle type {v_type} with priority {priority_lvl}."
            }

        # Extract optimal slot from Min-Heap
        best_slot = min_heap.pop()
        ranked_candidates = min_heap.get_ranked_candidates()

        slot_id = best_slot["slot_id"]
        zone_id = best_slot["zone_id"]

        # Calculate driving navigation route via Dijkstra
        from .graph_service import graph_service
        nav_route = graph_service.get_shortest_route(gate, slot_id)

        # Update Database: Mark slot OCCUPIED and assign vehicle
        cursor.execute("""
        UPDATE parking_slots
        SET status = 'OCCUPIED', assigned_vehicle_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE slot_id = ?
        """, (v_id, slot_id))

        # Update Request status to ALLOCATED
        cursor.execute("""
        UPDATE parking_requests
        SET status = 'ALLOCATED', allocated_slot_id = ?, allocated_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
        """, (slot_id, req_id))

        # Generate Parking Ticket
        tkt_num = int(datetime.now().timestamp()) % 100000
        ticket_id = f"TKT-{tkt_num}"
        entry_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO entry_exit_history (ticket_id, vehicle_id, vehicle_number, vehicle_type, slot_id, zone_id, entry_time, status, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 0)
        """, (ticket_id, v_id, v_num, v_type, slot_id, zone_id, entry_time_str))

        ticket_db_id = cursor.lastrowid
        conn.commit()
        conn.close()

        ticket_obj = {
            "id": ticket_db_id,
            "ticket_id": ticket_id,
            "vehicle_id": v_id,
            "vehicle_number": v_num,
            "vehicle_type": v_type,
            "slot_id": slot_id,
            "zone_id": zone_id,
            "entry_time": entry_time_str,
            "status": "ACTIVE"
        }

        # Update SLL and DLL
        self.history_sll.prepend(ticket_obj)
        self.audit_dll.append(ticket_obj)

        # Push action to Undo Stack
        self.undo_stack.push({
            "action": "ALLOCATE_PARKING",
            "ticket_id": ticket_id,
            "slot_id": slot_id,
            "vehicle_number": v_num,
            "details": f"Allocated slot {slot_id} to vehicle {v_num} (Ticket: {ticket_id})"
        })

        return {
            "success": True,
            "message": f"Vehicle {v_num} successfully allocated to Slot {slot_id} ({zone_id}).",
            "ticket_id": ticket_id,
            "assigned_slot": best_slot,
            "vehicle_number": v_num,
            "priority_level": priority_lvl,
            "navigation_route": nav_route,
            "dsa_decision_trace": {
                "algorithm": "Greedy Choice via Min-Heap Ranking",
                "min_heap_candidates_count": min_heap.size() + 1,
                "calculated_cost_score": best_slot["distance_from_gate"],
                "reason": f"Closest compatible slot to {gate} in Zone {zone_id} ({best_slot['distance_from_gate']}m)"
            }
        }

    # ==========================================
    # 5. ENTRY & EXIT PROCESSING
    # ==========================================
    def process_vehicle_exit(self, identifier: str) -> Dict[str, Any]:
        """
        Handles Vehicle Exit:
        1. Looks up ACTIVE ticket by vehicle_number or slot_id.
        2. Calculates parking duration and hourly parking fee.
        3. Frees the parking slot (status -> 'FREE', assigned_vehicle -> NULL).
        4. Updates ticket status -> 'COMPLETED'.
        5. Logs to SLL, DLL, and Stack.
        """
        clean_id = identifier.strip().upper()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find active ticket
        cursor.execute("""
        SELECT t.*, z.hourly_rate
        FROM entry_exit_history t
        JOIN parking_zones z ON t.zone_id = z.zone_id
        WHERE t.status = 'ACTIVE' AND (UPPER(t.vehicle_number) = ? OR UPPER(t.slot_id) = ? OR t.ticket_id = ?)
        """, (clean_id, clean_id, clean_id))
        ticket = cursor.fetchone()

        if not ticket:
            conn.close()
            return {"success": False, "error": f"No active parked vehicle found for '{clean_id}'"}

        ticket_id = ticket["ticket_id"]
        slot_id = ticket["slot_id"]
        v_num = ticket["vehicle_number"]
        entry_time_str = ticket["entry_time"]
        hourly_rate = float(ticket["hourly_rate"])

        # Calculate duration
        exit_time = datetime.now()
        try:
            entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            entry_time = exit_time

        duration_seconds = max(60, int((exit_time - entry_time).total_seconds()))
        duration_minutes = int(duration_seconds / 60)
        hours_billed = max(1.0, round(duration_minutes / 60.0, 2))
        total_cost = round(hours_billed * hourly_rate, 2)
        exit_time_str = exit_time.strftime("%Y-%m-%d %H:%M:%S")

        # Update History Ticket
        cursor.execute("""
        UPDATE entry_exit_history
        SET exit_time = ?, duration_minutes = ?, cost_charged = ?, status = 'COMPLETED'
        WHERE ticket_id = ?
        """, (exit_time_str, duration_minutes, total_cost, ticket_id))

        # Free the slot
        cursor.execute("""
        UPDATE parking_slots
        SET status = 'FREE', assigned_vehicle_id = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE slot_id = ?
        """, (slot_id,))

        conn.commit()
        conn.close()

        # Log to undo stack
        self.undo_stack.push({
            "action": "PROCESS_EXIT",
            "ticket_id": ticket_id,
            "slot_id": slot_id,
            "vehicle_number": v_num,
            "details": f"Processed exit for {v_num} from {slot_id} (Fee: ₹{total_cost})"
        })

        return {
            "success": True,
            "message": f"Vehicle {v_num} successfully checked out.",
            "ticket_id": ticket_id,
            "slot_id": slot_id,
            "vehicle_number": v_num,
            "entry_time": entry_time_str,
            "exit_time": exit_time_str,
            "duration_minutes": duration_minutes,
            "duration_formatted": f"{duration_minutes // 60}h {duration_minutes % 60}m",
            "hourly_rate": hourly_rate,
            "total_fee": total_cost
        }

    # ==========================================
    # 6. UNDO RECENT ACTION (STACK IMPLEMENTATION)
    # ==========================================
    def undo_last_action(self) -> Dict[str, Any]:
        """
        Pops the most recent action from the LIFO Stack and reverses the database change.
        """
        if self.undo_stack.is_empty():
            return {"success": False, "error": "Undo stack is empty. No recent actions to reverse."}

        action_data = self.undo_stack.pop()
        action_type = action_data.get("action")
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            if action_type == "UPDATE_SLOT_STATUS":
                slot_id = action_data["slot_id"]
                old_status = action_data["old_status"]
                cursor.execute("UPDATE parking_slots SET status = ? WHERE slot_id = ?", (old_status, slot_id))
                conn.commit()
                return {"success": True, "message": f"Reverted Slot {slot_id} status back to {old_status}.", "action": action_data}

            elif action_type == "ALLOCATE_PARKING":
                slot_id = action_data["slot_id"]
                ticket_id = action_data["ticket_id"]
                # Revert slot to FREE and cancel ticket
                cursor.execute("UPDATE parking_slots SET status = 'FREE', assigned_vehicle_id = NULL WHERE slot_id = ?", (slot_id,))
                cursor.execute("DELETE FROM entry_exit_history WHERE ticket_id = ?", (ticket_id,))
                conn.commit()
                return {"success": True, "message": f"Cancelled allocation for Ticket {ticket_id}. Slot {slot_id} is now FREE.", "action": action_data}

            elif action_type == "PROCESS_EXIT":
                slot_id = action_data["slot_id"]
                ticket_id = action_data["ticket_id"]
                v_num = action_data["vehicle_number"]
                # Re-occupy slot
                cursor.execute("SELECT vehicle_id FROM vehicles WHERE vehicle_number = ?", (v_num,))
                v_row = cursor.fetchone()
                v_id = v_row["vehicle_id"] if v_row else None

                cursor.execute("UPDATE parking_slots SET status = 'OCCUPIED', assigned_vehicle_id = ? WHERE slot_id = ?", (v_id, slot_id))
                cursor.execute("UPDATE entry_exit_history SET status = 'ACTIVE', exit_time = NULL WHERE ticket_id = ?", (ticket_id,))
                conn.commit()
                return {"success": True, "message": f"Re-opened active session for {v_num} in Slot {slot_id}.", "action": action_data}

            else:
                return {"success": True, "message": f"Popped action: {action_data.get('details')}", "action": action_data}
        finally:
            conn.close()

    # ==========================================
    # 7. CYCLIC ZONE INSPECTION (CIRCULAR LINKED LIST)
    # ==========================================
    def inspect_next_zone(self) -> Dict[str, Any]:
        """Advances Circular Linked List pointer to inspect the next parking zone in round-robin."""
        zone = self.zone_cll.next_zone()
        if not zone:
            return {"success": False, "error": "No zones found in CLL"}

        # Fetch live stats for this zone
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'FREE' THEN 1 ELSE 0 END) as free,
               SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied,
               SUM(CASE WHEN status = 'RESERVED' THEN 1 ELSE 0 END) as reserved
        FROM parking_slots WHERE zone_id = ?
        """, (zone["zone_id"],))
        stats = cursor.fetchone()
        conn.close()

        return {
            "success": True,
            "dsa_structure": "Circular Linked List (CLL)",
            "zone_id": zone["zone_id"],
            "zone_name": zone["name"],
            "floor": zone["floor"],
            "allowed_type": zone["allowed_type"],
            "hourly_rate": zone["hourly_rate"],
            "live_counts": {
                "total": stats["total"],
                "free": stats["free"] or 0,
                "occupied": stats["occupied"] or 0,
                "reserved": stats["reserved"] or 0
            }
        }

    def get_pending_requests(self) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parking_requests WHERE status = 'QUEUED' ORDER BY requested_at ASC")
        all_queued = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Separate into priority and normal
        priority_list = [r for r in all_queued if r["priority_level"] != "NORMAL"]
        # Rank priority list by level
        rank_weights = {"EMERGENCY": 1, "ACCESSIBILITY": 2, "RESERVED": 3}
        priority_list.sort(key=lambda x: rank_weights.get(x["priority_level"], 4))
        normal_list = [r for r in all_queued if r["priority_level"] == "NORMAL"]

        return {
            "priority_queue": priority_list,
            "normal_queue": normal_list,
            "entry_buffer_size": self.entry_buffer_cq.size(),
            "total_pending": len(all_queued)
        }

    # ==========================================
    # 8. USER SCOPED ACCESS METHODS
    # ==========================================
    def get_user_vehicles(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches vehicles belonging strictly to a specific user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT v.*, s.slot_id as current_parked_slot, s.status as slot_status, s.zone_id as parked_zone
        FROM vehicles v
        LEFT JOIN parking_slots s ON s.assigned_vehicle_id = v.vehicle_id
        WHERE v.user_id = ?
        ORDER BY v.id DESC
        """, (user_id,))
        vehicles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return vehicles

    def register_user_vehicle(self, user_id: str, v_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a vehicle for an authenticated user."""
        v_num = v_data.get("vehicle_number", "").strip().upper()
        v_type = v_data.get("vehicle_type", "4W")
        model = v_data.get("model_name", "Standard").strip()
        color = v_data.get("color", "Black").strip()

        if not v_num:
            return {"success": False, "error": "Vehicle number is required."}

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate plate
        cursor.execute("SELECT * FROM vehicles WHERE UPPER(vehicle_number) = ?", (v_num,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": f"Vehicle '{v_num}' is already registered in the system."}

        v_id = f"V-{random_generator()}"

        try:
            cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_number, user_id, vehicle_type, model_name, color, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (v_id, v_num, user_id, v_type, model, color))
            conn.commit()
            return {
                "success": True,
                "message": f"Vehicle '{v_num}' successfully added to your account.",
                "vehicle_id": v_id,
                "vehicle_number": v_num
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches entry/exit logs strictly for vehicles owned by user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT h.*, z.name as zone_name
        FROM entry_exit_history h
        JOIN vehicles v ON h.vehicle_id = v.vehicle_id
        LEFT JOIN parking_zones z ON h.zone_id = z.zone_id
        WHERE v.user_id = ?
        ORDER BY h.id DESC
        """, (user_id,))
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    # ==========================================
    # 9. ADMIN LIVE PARKING MONITOR & BLOCK-WISE STATUS
    # ==========================================
    def get_admin_live_monitor(
        self,
        zone_id: Optional[str] = None,
        floor: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        slot_status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Admin query showing exact parked vehicle status:
        Vehicle Number -> Slot -> Zone -> Floor -> Entry Time -> Booking ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT s.slot_id, s.zone_id, s.vehicle_type as slot_vtype, s.status as slot_status,
               s.distance_from_gate, s.priority,
               z.name as zone_name, z.floor, z.hourly_rate,
               v.vehicle_id, v.vehicle_number, v.vehicle_type as vehicle_type, v.model_name, v.color,
               u.user_id, u.full_name as owner_name, u.email as owner_email, u.phone as owner_phone,
               h.ticket_id, h.entry_time,
               b.booking_id, b.arrival_time as booked_arrival, b.duration_hours as booked_duration
        FROM parking_slots s
        JOIN parking_zones z ON s.zone_id = z.zone_id
        LEFT JOIN vehicles v ON s.assigned_vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        LEFT JOIN entry_exit_history h ON (h.slot_id = s.slot_id AND h.status = 'ACTIVE')
        LEFT JOIN bookings b ON (b.slot_id = s.slot_id AND b.status IN ('ACTIVE', 'CONFIRMED'))
        WHERE 1=1
        """
        params = []
        if zone_id and zone_id != "ALL":
            query += " AND s.zone_id = ?"
            params.append(zone_id)
        if floor and floor != "ALL":
            query += " AND z.floor = ?"
            params.append(floor)
        if vehicle_type and vehicle_type != "ALL":
            query += " AND s.vehicle_type = ?"
            params.append(vehicle_type)
        if slot_status and slot_status != "ALL":
            query += " AND s.status = ?"
            params.append(slot_status)
        if search_query:
            query += " AND (UPPER(v.vehicle_number) LIKE ? OR UPPER(s.slot_id) LIKE ? OR UPPER(u.full_name) LIKE ?)"
            clean_q = f"%{search_query.strip().upper()}%"
            params.extend([clean_q, clean_q, clean_q])

        query += " ORDER BY s.zone_id, s.slot_id ASC"
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    def get_block_wise_summary(self) -> List[Dict[str, Any]]:
        """Returns visual block-wise (Zone A/B/C/D) aggregation for Admin Dashboard."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT z.zone_id, z.name, z.floor, z.allowed_type, z.hourly_rate,
               COUNT(s.id) as total_slots,
               SUM(CASE WHEN s.status = 'FREE' THEN 1 ELSE 0 END) as free_slots,
               SUM(CASE WHEN s.status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied_slots,
               SUM(CASE WHEN s.status = 'RESERVED' THEN 1 ELSE 0 END) as reserved_slots,
               SUM(CASE WHEN s.status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_slots
        FROM parking_zones z
        LEFT JOIN parking_slots s ON z.zone_id = s.zone_id
        GROUP BY z.zone_id
        ORDER BY z.zone_id ASC
        """)
        blocks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return blocks


def random_generator():
    import random
    return random.randint(1000, 9999)


parking_service = ParkingService()
