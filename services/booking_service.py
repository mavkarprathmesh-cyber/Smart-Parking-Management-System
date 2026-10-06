"""
Advance Slot Booking & Reservation Service Module
Handles:
1. Slot availability checking by location, zone, date, arrival time, and vehicle type.
2. Advance slot booking with double-booking prevention.
3. User booking history retrieval (Strict User Data Isolation).
4. Booking cancellation and slot state restoration.
5. Dijkstra shortest path route generation for booked slot navigation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sqlite3
import random

from database.db import get_db_connection
from .graph_service import graph_service
from .security import record_audit_log


class BookingService:

    def find_available_slots(
        self,
        zone_id: str,
        vehicle_type: str,
        booking_date: str,
        arrival_time: str,
        duration_hours: int = 2
    ) -> Dict[str, Any]:
        """
        Finds all compatible free slots in the requested zone and vehicle type.
        Checks both current slot status and conflicting advance bookings.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch zone details
        cursor.execute("SELECT * FROM parking_zones WHERE zone_id = ?", (zone_id,))
        zone = cursor.fetchone()
        if not zone:
            conn.close()
            return {"success": False, "error": f"Zone '{zone_id}' not found."}

        zone_dict = dict(zone)

        # Query slots matching vehicle_type and zone
        cursor.execute("""
        SELECT s.*, z.name as zone_name, z.floor, z.hourly_rate
        FROM parking_slots s
        JOIN parking_zones z ON s.zone_id = z.zone_id
        WHERE s.zone_id = ? AND s.vehicle_type = ?
        ORDER BY s.distance_from_gate ASC
        """, (zone_id, vehicle_type))
        slots = [dict(row) for row in cursor.fetchall()]

        # Query bookings on that date for this zone that are active/confirmed
        cursor.execute("""
        SELECT slot_id, arrival_time, duration_hours
        FROM bookings
        WHERE zone_id = ? AND booking_date = ? AND status IN ('CONFIRMED', 'ACTIVE')
        """, (zone_id, booking_date))
        existing_bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        booked_slot_ids = {b["slot_id"] for b in existing_bookings}

        results = []
        for s in slots:
            is_currently_free = s["status"] == "FREE"
            is_booked_future = s["slot_id"] in booked_slot_ids
            
            is_bookable = is_currently_free and not is_booked_future

            results.append({
                "slot_id": s["slot_id"],
                "zone_id": s["zone_id"],
                "zone_name": s["zone_name"],
                "floor": s["floor"],
                "vehicle_type": s["vehicle_type"],
                "status": s["status"],
                "is_bookable": is_bookable,
                "distance_from_gate": s["distance_from_gate"],
                "priority": s["priority"],
                "hourly_rate": s["hourly_rate"],
                "estimated_fee": round(float(s["hourly_rate"]) * duration_hours, 2)
            })

        return {
            "success": True,
            "zone": zone_dict,
            "booking_date": booking_date,
            "arrival_time": arrival_time,
            "duration_hours": duration_hours,
            "vehicle_type": vehicle_type,
            "total_slots": len(results),
            "available_count": sum(1 for s in results if s["is_bookable"]),
            "slots": results
        }

    def create_advance_booking(
        self,
        user_id: str,
        vehicle_number: str,
        vehicle_type: str,
        zone_id: str,
        slot_id: str,
        booking_date: str,
        arrival_time: str,
        duration_hours: int = 2,
        entry_gate: str = "GATE-1"
    ) -> Dict[str, Any]:
        """
        Reserves slot for user:
        1. Validates slot compatibility and availability.
        2. Prevents double-booking or booking occupied slots.
        3. Updates slot status -> 'RESERVED'.
        4. Calculates Dijkstra route from Entry Gate to Slot.
        5. Generates booking record.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check slot
        cursor.execute("""
        SELECT s.*, z.hourly_rate, z.name as zone_name
        FROM parking_slots s
        JOIN parking_zones z ON s.zone_id = z.zone_id
        WHERE s.slot_id = ?
        """, (slot_id,))
        slot = cursor.fetchone()

        if not slot:
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' does not exist."}

        slot_dict = dict(slot)

        # Validate vehicle type compatibility
        if slot_dict["vehicle_type"] != vehicle_type:
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' is for {slot_dict['vehicle_type']}, but vehicle is {vehicle_type}."}

        # Check current slot status
        if slot_dict["status"] in ["OCCUPIED", "BLOCKED"]:
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' is currently {slot_dict['status']} and cannot be booked."}

        # Check conflicting existing booking
        cursor.execute("""
        SELECT * FROM bookings
        WHERE slot_id = ? AND booking_date = ? AND status IN ('CONFIRMED', 'ACTIVE')
        """, (slot_id, booking_date))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": f"Slot '{slot_id}' is already booked for date {booking_date}."}

        # Generate unique Booking ID
        booking_id = f"BKG-{random.randint(10000, 99999)}"
        hourly_rate = float(slot_dict["hourly_rate"])
        total_fee = round(hourly_rate * duration_hours, 2)

        try:
            # Insert booking
            cursor.execute("""
            INSERT INTO bookings (booking_id, user_id, vehicle_number, vehicle_type, zone_id, slot_id, booking_date, arrival_time, duration_hours, total_estimated_fee, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED')
            """, (booking_id, user_id, vehicle_number.upper(), vehicle_type, zone_id, slot_id, booking_date, arrival_time, duration_hours, total_fee))

            # Update Slot status to RESERVED
            cursor.execute("""
            UPDATE parking_slots
            SET status = 'RESERVED', updated_at = CURRENT_TIMESTAMP
            WHERE slot_id = ?
            """, (slot_id,))

            conn.commit()
            
            # Log audit
            record_audit_log(user_id, "CREATE_BOOKING", target=booking_id, details=f"Booked slot {slot_id} on {booking_date}")

            # Compute navigation path via Dijkstra
            nav_route = graph_service.get_shortest_route(entry_gate, slot_id)

            return {
                "success": True,
                "message": f"Slot {slot_id} successfully booked! Booking ID: {booking_id}",
                "booking_id": booking_id,
                "slot_id": slot_id,
                "zone_id": zone_id,
                "zone_name": slot_dict["zone_name"],
                "vehicle_number": vehicle_number.upper(),
                "booking_date": booking_date,
                "arrival_time": arrival_time,
                "duration_hours": duration_hours,
                "total_estimated_fee": total_fee,
                "navigation_route": nav_route
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_user_bookings(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches bookings belonging strictly to the requested user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT b.*, z.name as zone_name, z.floor, s.distance_from_gate, s.status as current_slot_status
        FROM bookings b
        JOIN parking_zones z ON b.zone_id = z.zone_id
        JOIN parking_slots s ON b.slot_id = s.slot_id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
        """, (user_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def cancel_booking(self, user_id: str, booking_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """Cancels booking and frees slot."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if is_admin:
            cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        else:
            cursor.execute("SELECT * FROM bookings WHERE booking_id = ? AND user_id = ?", (booking_id, user_id))
        
        booking = cursor.fetchone()
        if not booking:
            conn.close()
            return {"success": False, "error": "Booking not found or unauthorized."}

        booking_dict = dict(booking)
        if booking_dict["status"] in ["CANCELLED", "COMPLETED"]:
            conn.close()
            return {"success": False, "error": f"Booking is already {booking_dict['status']}."}

        slot_id = booking_dict["slot_id"]

        try:
            cursor.execute("UPDATE bookings SET status = 'CANCELLED' WHERE booking_id = ?", (booking_id,))
            cursor.execute("UPDATE parking_slots SET status = 'FREE' WHERE slot_id = ?", (slot_id,))
            conn.commit()

            record_audit_log(user_id, "CANCEL_BOOKING", target=booking_id, details=f"Cancelled booking for slot {slot_id}")

            return {
                "success": True,
                "message": f"Booking {booking_id} has been cancelled. Slot {slot_id} is now FREE."
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_all_bookings(self, status: Optional[str] = None, zone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Admin endpoint: Fetches all bookings with optional filters."""
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT b.*, u.full_name as user_name, u.email as user_email, u.phone as user_phone,
               z.name as zone_name, z.floor, s.status as current_slot_status
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN parking_zones z ON b.zone_id = z.zone_id
        JOIN parking_slots s ON b.slot_id = s.slot_id
        WHERE 1=1
        """
        params = []
        if status and status != "ALL":
            query += " AND b.status = ?"
            params.append(status)
        if zone_id and zone_id != "ALL":
            query += " AND b.zone_id = ?"
            params.append(zone_id)

        query += " ORDER BY b.id DESC"
        cursor.execute(query, params)
        bookings = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return bookings


booking_service = BookingService()
