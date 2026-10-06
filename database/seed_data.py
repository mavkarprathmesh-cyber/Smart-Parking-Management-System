"""
Seed Data Generator Module
Populates the SQLite database with realistic initial academic demo data:
Admin & User accounts with PBKDF2 hashed passwords, Vehicles, Zones,
Slots (with 2D map coordinates), Bookings, Graph Nodes, Edges, and Tickets.
All demo data is marked with `is_demo = 1` for clear separation.
"""

import sqlite3
from datetime import datetime, timedelta
import random
from .db import get_db_connection, init_db
from services.security import hash_password


def seed_database(force_reset: bool = False):
    """Populates database with realistic parking system records."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if slots already exist and not forcing reset
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] > 0 and not force_reset:
        conn.close()
        return

    if force_reset:
        # Clear existing tables
        tables = [
            "audit_logs", "user_sessions", "bookings", "system_logs",
            "entry_exit_history", "parking_requests", "parking_slots",
            "parking_zones", "vehicles", "users", "graph_edges", "graph_nodes"
        ]
        for t in tables:
            cursor.execute(f"DELETE FROM {t}")
        conn.commit()

    # Default Passwords
    admin_pwd_hash, admin_salt = hash_password("Admin@1234")
    user_pwd_hash, user_salt = hash_password("User@1234")

    # ==========================================
    # 1. USERS & ADMIN ACCOUNTS
    # ==========================================
    users_data = [
        ("ADM-001", "Chief Parking Administrator", "admin@smartpark.com", "+91-9999900001", admin_pwd_hash, admin_salt, "ADMIN", 1, 1),
        ("U-101", "Dr. Rajesh Sharma", "rajesh.sharma@campus.edu", "+91-9876543210", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-102", "Priya Patel", "priya@student.edu", "+91-9876543211", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-103", "Amit Verma", "amit.verma@campus.edu", "+91-9876543212", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-104", "Campus Emergency Team", "emergency@campus.edu", "+91-9876543213", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-105", "Sunita Nair", "sunita.nair@guest.org", "+91-9876543214", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-106", "Rohan Mehta", "rohan.mehta@student.edu", "+91-9876543215", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-107", "Vikram Singh", "vikram.singh@campus.edu", "+91-9876543216", user_pwd_hash, user_salt, "USER", 1, 1),
        ("U-108", "Ananya Roy", "ananya.roy@student.edu", "+91-9876543217", user_pwd_hash, user_salt, "USER", 1, 1)
    ]
    cursor.executemany("""
    INSERT INTO users (user_id, full_name, email, phone, password_hash, salt, role, is_verified, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # ==========================================
    # 2. PARKING ZONES
    # ==========================================
    zones_data = [
        ("A", "Zone A - Ground Floor (4W Premium)", "Ground Floor", "4W", 8, 20.0, "Standard 4-wheeler parking close to Main Gate 1"),
        ("B", "Zone B - First Floor (4W Economy)", "First Floor", "4W", 8, 15.0, "Multi-level ramp accessible 4-wheeler bays"),
        ("C", "Zone C - Two-Wheeler Bay (2W)", "Ground Floor", "2W", 8, 10.0, "Dedicated bays for motorbikes, scooters and bicycles"),
        ("D", "Zone D - Priority & Emergency", "Ground Floor", "4W", 6, 25.0, "Accessibility, emergency and reserved corporate slots")
    ]
    cursor.executemany("""
    INSERT INTO parking_zones (zone_id, name, floor, allowed_type, total_capacity, hourly_rate, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, zones_data)

    # ==========================================
    # 3. VEHICLES
    # ==========================================
    vehicles_data = [
        ("V-101", "KA-01-MG-2024", "U-101", "4W", "Honda City", "White", 1),
        ("V-102", "KA-03-EQ-4567", "U-102", "2W", "Yamaha FZ", "Matte Black", 1),
        ("V-103", "MH-12-AB-9876", "U-103", "4W", "Hyundai Creta", "Silver", 1),
        ("V-104", "KA-05-EM-108", "U-104", "4W", "Force Ambulance", "Red/White", 1),
        ("V-105", "DL-01-ZZ-5544", "U-105", "4W", "Toyota Innova", "Grey", 1),
        ("V-106", "KA-04-BK-1122", "U-106", "2W", "Royal Enfield Classic", "Navy Blue", 1),
        ("V-107", "KA-02-CD-3344", "U-107", "4W", "Tata Nexon EV", "Teal Blue", 1),
        ("V-108", "KA-01-SC-8899", "U-108", "2W", "Honda Activa 6G", "Red", 1)
    ]
    cursor.executemany("""
    INSERT INTO vehicles (vehicle_id, vehicle_number, user_id, vehicle_type, model_name, color, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, vehicles_data)

    # ==========================================
    # 4. PARKING SLOTS
    # ==========================================
    slots_data = [
        # Zone A (4W Ground)
        ("A-01", "A", "4W", "OCCUPIED", 15.0, "NORMAL", "V-101", 120, 160, 1),
        ("A-02", "A", "4W", "FREE", 20.0, "NORMAL", None, 180, 160, 1),
        ("A-03", "A", "4W", "FREE", 25.0, "NORMAL", None, 240, 160, 1),
        ("A-04", "A", "4W", "OCCUPIED", 30.0, "NORMAL", "V-103", 300, 160, 1),
        ("A-05", "A", "4W", "FREE", 32.0, "NORMAL", None, 120, 240, 1),
        ("A-06", "A", "4W", "FREE", 36.0, "NORMAL", None, 180, 240, 1),
        ("A-07", "A", "4W", "FREE", 40.0, "NORMAL", None, 240, 240, 1),
        ("A-08", "A", "4W", "RESERVED", 45.0, "RESERVED", None, 300, 240, 1),

        # Zone B (4W First Floor)
        ("B-01", "B", "4W", "OCCUPIED", 65.0, "NORMAL", "V-107", 520, 160, 1),
        ("B-02", "B", "4W", "FREE", 70.0, "NORMAL", None, 580, 160, 1),
        ("B-03", "B", "4W", "FREE", 75.0, "NORMAL", None, 640, 160, 1),
        ("B-04", "B", "4W", "FREE", 80.0, "NORMAL", None, 700, 160, 1),
        ("B-05", "B", "4W", "FREE", 82.0, "NORMAL", None, 520, 240, 1),
        ("B-06", "B", "4W", "FREE", 86.0, "NORMAL", None, 580, 240, 1),
        ("B-07", "B", "4W", "FREE", 90.0, "NORMAL", None, 640, 240, 1),
        ("B-08", "B", "4W", "FREE", 95.0, "NORMAL", None, 700, 240, 1),

        # Zone C (2W Ground)
        ("C-01", "C", "2W", "OCCUPIED", 20.0, "NORMAL", "V-102", 120, 390, 1),
        ("C-02", "C", "2W", "FREE", 24.0, "NORMAL", None, 180, 390, 1),
        ("C-03", "C", "2W", "OCCUPIED", 28.0, "NORMAL", "V-106", 240, 390, 1),
        ("C-04", "C", "2W", "FREE", 32.0, "NORMAL", None, 300, 390, 1),
        ("C-05", "C", "2W", "FREE", 35.0, "NORMAL", None, 120, 470, 1),
        ("C-06", "C", "2W", "FREE", 38.0, "NORMAL", None, 180, 470, 1),
        ("C-07", "C", "2W", "FREE", 42.0, "NORMAL", None, 240, 470, 1),
        ("C-08", "C", "2W", "FREE", 46.0, "NORMAL", None, 300, 470, 1),

        # Zone D (Priority / Emergency)
        ("D-01", "D", "4W", "OCCUPIED", 10.0, "EMERGENCY", "V-104", 520, 390, 1),
        ("D-02", "D", "4W", "FREE", 14.0, "ACCESSIBILITY", None, 600, 390, 1),
        ("D-03", "D", "4W", "FREE", 18.0, "ACCESSIBILITY", None, 680, 390, 1),
        ("D-04", "D", "4W", "FREE", 22.0, "RESERVED", None, 520, 470, 1),
        ("D-05", "D", "4W", "FREE", 26.0, "RESERVED", None, 600, 470, 1),
        ("D-06", "D", "4W", "FREE", 30.0, "NORMAL", None, 680, 470, 1)
    ]
    cursor.executemany("""
    INSERT INTO parking_slots (slot_id, zone_id, vehicle_type, status, distance_from_gate, priority, assigned_vehicle_id, pos_x, pos_y, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, slots_data)

    # ==========================================
    # 5. INITIAL ADVANCE BOOKINGS
    # ==========================================
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    bookings_data = [
        ("BKG-10101", "U-102", "KA-03-EQ-4567", "2W", "C", "C-01", today_str, "09:00", 3, 30.0, "ACTIVE", 1),
        ("BKG-10102", "U-101", "KA-01-MG-2024", "4W", "A", "A-01", today_str, "08:30", 4, 80.0, "ACTIVE", 1),
        ("BKG-10103", "U-102", "KA-03-EQ-4567", "2W", "C", "C-04", tomorrow_str, "10:00", 2, 20.0, "CONFIRMED", 1)
    ]
    cursor.executemany("""
    INSERT INTO bookings (booking_id, user_id, vehicle_number, vehicle_type, zone_id, slot_id, booking_date, arrival_time, duration_hours, total_estimated_fee, status, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, bookings_data)

    # ==========================================
    # 6. GRAPH NODES & EDGES
    # ==========================================
    graph_nodes = [
        ("GATE-1", "Main Entry Gate 1 (West)", "GATE", 40, 160),
        ("GATE-2", "East Entry Gate 2 (East)", "GATE", 820, 400),
        ("EXIT-1", "Main Exit Gate (South)", "GATE", 410, 560),
        ("J1", "Junction 1 (West Central)", "JUNCTION", 200, 290),
        ("J2", "Junction 2 (Central Spine)", "JUNCTION", 410, 290),
        ("J3", "Junction 3 (East Central)", "JUNCTION", 620, 290),
        ("RAMP-1", "First Floor Access Ramp", "JUNCTION", 410, 100),
        ("ZONE-A", "Zone A Entry Way", "ZONE", 200, 160),
        ("ZONE-B", "Zone B Entry Way", "ZONE", 620, 160),
        ("ZONE-C", "Zone C Entry Way", "ZONE", 200, 420),
        ("ZONE-D", "Zone D Priority Entry", "ZONE", 620, 420),
        ("A-01", "Bay A-01", "SLOT", 120, 160),
        ("A-04", "Bay A-04", "SLOT", 300, 160),
        ("B-01", "Bay B-01", "SLOT", 520, 160),
        ("C-01", "Bay C-01", "SLOT", 120, 390),
        ("C-03", "Bay C-03", "SLOT", 240, 390),
        ("D-01", "Bay D-01 (Ambulance)", "SLOT", 520, 390),
        ("D-02", "Bay D-02 (Accessible)", "SLOT", 600, 390)
    ]
    cursor.executemany("""
    INSERT INTO graph_nodes (node_id, label, node_type, x, y)
    VALUES (?, ?, ?, ?, ?)
    """, graph_nodes)

    graph_edges = [
        ("GATE-1", "ZONE-A", 12.0, 1, 0, "West Gate Lane"),
        ("GATE-1", "J1", 18.0, 1, 0, "West Outer Boulevard"),
        ("ZONE-A", "A-01", 5.0, 1, 0, "Zone A Aisle 1"),
        ("ZONE-A", "A-04", 8.0, 1, 0, "Zone A Aisle 2"),
        ("ZONE-A", "J1", 10.0, 1, 0, "Zone A Connecting Lane"),
        ("J1", "J2", 15.0, 1, 0, "Central Spine West"),
        ("J1", "ZONE-C", 12.0, 1, 0, "Zone C Approach"),
        ("ZONE-C", "C-01", 6.0, 1, 0, "Zone C Aisle 1"),
        ("ZONE-C", "C-03", 9.0, 1, 0, "Zone C Aisle 2"),
        ("J2", "RAMP-1", 14.0, 1, 0, "Floor 1 Incline Ramp"),
        ("RAMP-1", "ZONE-B", 16.0, 1, 0, "Floor 1 Overpass"),
        ("ZONE-B", "B-01", 6.0, 1, 0, "Zone B Aisle 1"),
        ("J2", "J3", 15.0, 1, 0, "Central Spine East"),
        ("J2", "EXIT-1", 20.0, 1, 0, "Main Exit Corridor"),
        ("GATE-2", "J3", 14.0, 1, 0, "East Gate Lane"),
        ("GATE-2", "ZONE-D", 10.0, 1, 0, "Express Priority Lane"),
        ("J3", "ZONE-D", 11.0, 1, 0, "Zone D Access Lane"),
        ("ZONE-D", "D-01", 4.0, 1, 0, "Emergency Express Bay"),
        ("ZONE-D", "D-02", 6.0, 1, 0, "Accessibility Bay"),
        ("ZONE-D", "EXIT-1", 18.0, 1, 0, "Zone D Exit Lane"),
        ("ZONE-C", "EXIT-1", 16.0, 1, 0, "Zone C Exit Lane")
    ]
    cursor.executemany("""
    INSERT INTO graph_edges (u, v, weight, bidirectional, is_blocked, lane_name)
    VALUES (?, ?, ?, ?, ?, ?)
    """, graph_edges)

    # ==========================================
    # 7. PARKING TICKETS & HISTORY
    # ==========================================
    two_hours_ago = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    one_hour_ago = (now - timedelta(hours=1, minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    thirty_mins_ago = (now - timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S")
    ten_mins_ago = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    active_tickets = [
        ("TKT-1001", "V-101", "KA-01-MG-2024", "4W", "A-01", "A", two_hours_ago, None, 0, 0.0, "ACTIVE", 1),
        ("TKT-1002", "V-103", "MH-12-AB-9876", "4W", "A-04", "A", one_hour_ago, None, 0, 0.0, "ACTIVE", 1),
        ("TKT-1003", "V-107", "KA-02-CD-3344", "4W", "B-01", "B", thirty_mins_ago, None, 0, 0.0, "ACTIVE", 1),
        ("TKT-1004", "V-102", "KA-03-EQ-4567", "2W", "C-01", "C", two_hours_ago, None, 0, 0.0, "ACTIVE", 1),
        ("TKT-1005", "V-106", "KA-04-BK-1122", "2W", "C-03", "C", thirty_mins_ago, None, 0, 0.0, "ACTIVE", 1),
        ("TKT-1006", "V-104", "KA-05-EM-108", "4W", "D-01", "D", ten_mins_ago, None, 0, 0.0, "ACTIVE", 1)
    ]
    cursor.executemany("""
    INSERT INTO entry_exit_history (ticket_id, vehicle_id, vehicle_number, vehicle_type, slot_id, zone_id, entry_time, exit_time, duration_minutes, cost_charged, status, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, active_tickets)

    # Completed Historical Tickets
    hist_entries = [
        ("TKT-0995", "V-105", "DL-01-ZZ-5544", "4W", "A-02", "A", (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(hours=4, minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), 110, 40.0, "COMPLETED", 1),
        ("TKT-0996", "V-108", "KA-01-SC-8899", "2W", "C-02", "C", (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), 90, 20.0, "COMPLETED", 1),
        ("TKT-0997", "V-101", "KA-01-MG-2024", "4W", "B-02", "B", (now - timedelta(days=1, hours=4)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S"), 120, 30.0, "COMPLETED", 1),
        ("TKT-0998", "V-103", "MH-12-AB-9876", "4W", "D-03", "D", (now - timedelta(days=1, hours=6)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=1, hours=5)).strftime("%Y-%m-%d %H:%M:%S"), 60, 25.0, "COMPLETED", 1)
    ]
    cursor.executemany("""
    INSERT INTO entry_exit_history (ticket_id, vehicle_id, vehicle_number, vehicle_type, slot_id, zone_id, entry_time, exit_time, duration_minutes, cost_charged, status, is_demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, hist_entries)

    # Initial Logs
    cursor.execute("""
    INSERT INTO system_logs (action_type, description, metadata_json)
    VALUES ('SYSTEM_INIT', 'Smart Parking Management System with Secure RBAC and Advance Bookings initialized.', '{"version":"2.5.0","admin":"admin@smartpark.com"}')
    """)

    conn.commit()
    conn.close()
    print("Database successfully seeded with secure admin/user credentials and bookings.")


if __name__ == "__main__":
    seed_database(force_reset=True)
