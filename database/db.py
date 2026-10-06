"""
Database Management Module
Handles SQLite connection, schema initializations, transactions, and migration logic.
Data is persisted in local 'parking_system.db' file.
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "parking_system.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initializes all database tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table with Authentication & Verification fields
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT,
        salt TEXT,
        role TEXT DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN', 'STAFF', 'FACULTY', 'STUDENT', 'GUEST', 'EMERGENCY')),
        is_verified INTEGER DEFAULT 1,
        verification_code TEXT,
        reset_token TEXT,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP,
        is_demo INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Schema Migration check for existing users table
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    if "password_hash" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "salt" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN salt TEXT")
    if "is_verified" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1")
    if "verification_code" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")
    if "reset_token" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    if "failed_login_attempts" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
    if "locked_until" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP")

    # User Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)

    # Vehicles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id TEXT UNIQUE NOT NULL,
        vehicle_number TEXT UNIQUE NOT NULL,
        user_id TEXT NOT NULL,
        vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('2W', '4W')),
        model_name TEXT,
        color TEXT,
        is_demo INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)

    # Parking Zones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_zones (
        zone_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        floor TEXT NOT NULL,
        allowed_type TEXT NOT NULL,
        total_capacity INTEGER NOT NULL,
        hourly_rate REAL DEFAULT 20.0,
        description TEXT
    )
    """)

    # Parking Slots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id TEXT UNIQUE NOT NULL,
        zone_id TEXT NOT NULL,
        vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('2W', '4W')),
        status TEXT NOT NULL CHECK(status IN ('FREE', 'OCCUPIED', 'RESERVED', 'BLOCKED')),
        distance_from_gate REAL NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('NORMAL', 'ACCESSIBILITY', 'RESERVED', 'EMERGENCY')),
        assigned_vehicle_id TEXT,
        pos_x REAL DEFAULT 0,
        pos_y REAL DEFAULT 0,
        is_demo INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (zone_id) REFERENCES parking_zones(zone_id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL
    )
    """)

    # Advance Bookings / Reservations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT UNIQUE NOT NULL,
        user_id TEXT NOT NULL,
        vehicle_number TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        zone_id TEXT NOT NULL,
        slot_id TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        duration_hours INTEGER DEFAULT 2,
        total_estimated_fee REAL DEFAULT 0.0,
        status TEXT NOT NULL CHECK(status IN ('CONFIRMED', 'ACTIVE', 'COMPLETED', 'CANCELLED')) DEFAULT 'CONFIRMED',
        is_demo INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (zone_id) REFERENCES parking_zones(zone_id) ON DELETE CASCADE,
        FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id) ON DELETE CASCADE
    )
    """)

    # Parking Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE NOT NULL,
        vehicle_id TEXT NOT NULL,
        vehicle_number TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        priority_level TEXT NOT NULL CHECK(priority_level IN ('NORMAL', 'RESERVED', 'ACCESSIBILITY', 'EMERGENCY')),
        status TEXT NOT NULL CHECK(status IN ('QUEUED', 'ALLOCATED', 'CANCELLED', 'REJECTED')),
        queue_type TEXT NOT NULL CHECK(queue_type IN ('FIFO', 'PRIORITY', 'DEQUE')),
        allocated_slot_id TEXT,
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        allocated_at TIMESTAMP,
        is_demo INTEGER DEFAULT 0,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
        FOREIGN KEY (allocated_slot_id) REFERENCES parking_slots(slot_id) ON DELETE SET NULL
    )
    """)

    # Entry Exit History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entry_exit_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        vehicle_id TEXT NOT NULL,
        vehicle_number TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        slot_id TEXT NOT NULL,
        zone_id TEXT NOT NULL,
        entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_time TIMESTAMP,
        duration_minutes INTEGER DEFAULT 0,
        cost_charged REAL DEFAULT 0.0,
        status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'COMPLETED')),
        is_demo INTEGER DEFAULT 0,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
        FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
    )
    """)

    # Graph Nodes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS graph_nodes (
        node_id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        node_type TEXT NOT NULL,
        x REAL DEFAULT 0,
        y REAL DEFAULT 0
    )
    """)

    # Graph Edges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS graph_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        u TEXT NOT NULL,
        v TEXT NOT NULL,
        weight REAL NOT NULL,
        bidirectional INTEGER DEFAULT 1,
        is_blocked INTEGER DEFAULT 0,
        lane_name TEXT,
        FOREIGN KEY (u) REFERENCES graph_nodes(node_id),
        FOREIGN KEY (v) REFERENCES graph_nodes(node_id)
    )
    """)

    # Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action TEXT NOT NULL,
        target TEXT,
        ip_address TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # System Logs / Undo Stack Persistence
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Indexes for fast querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_status ON parking_slots(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_zone ON parking_slots(zone_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_num ON vehicles(vehicle_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_status ON entry_exit_history(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token)")

    conn.commit()
    conn.close()
