"""
Main Application Server (FastAPI)
Smart Parking Management System with Secure RBAC, Advance Bookings & Pure DSA Core
Provides REST API endpoints and serves modern responsive frontend single-page application.
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database.db import init_db
from database.seed_data import seed_database
from services.parking_service import parking_service
from services.search_service import search_service
from services.graph_service import graph_service
from services.lab_service import lab_service
from services.auth_service import auth_service
from services.booking_service import booking_service
from services.security import verify_session_token, record_audit_log
from dsa.complexity import get_all_dsa_explanations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB is created and seeded
    init_db()
    seed_database(force_reset=False)
    graph_service.load_graph_from_db()
    search_service.rebuild_search_indices()
    yield


app = FastAPI(
    title="Smart Parking Management System (DSA Project)",
    description="Academic Mini-Project with Secure RBAC and Pure Data Structures & Algorithms",
    version="2.5.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# AUTH & RBAC DEPENDENCIES
# ==========================================
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency: Validates session token for any authenticated user."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required. Please login.")
    user = verify_session_token(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token. Please login again.")
    return user


def get_current_admin(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency: Strictly enforces ADMIN role authorization on backend."""
    user = get_current_user(authorization)
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Administrator privileges required for this action."
        )
    return user


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class UserRegisterSchema(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = ""
    password: str
    confirm_password: str


class UserLoginSchema(BaseModel):
    email: str
    password: str


class VerifyEmailSchema(BaseModel):
    email: str
    code: str


class ForgotPasswordSchema(BaseModel):
    email: str


class ResetPasswordSchema(BaseModel):
    email: str
    reset_code: str
    new_password: str


class AdvanceBookingSchema(BaseModel):
    vehicle_number: str
    vehicle_type: str = "4W"
    zone_id: str
    slot_id: str
    booking_date: str
    arrival_time: str
    duration_hours: int = 2
    entry_gate: str = "GATE-1"


class SlotCreateSchema(BaseModel):
    slot_id: str
    zone_id: str
    vehicle_type: str = "4W"
    distance_from_gate: float = 25.0
    priority: str = "NORMAL"
    pos_x: float = 100.0
    pos_y: float = 100.0


class SlotStatusUpdateSchema(BaseModel):
    status: str


class VehicleRegisterSchema(BaseModel):
    vehicle_number: str
    vehicle_type: str = "4W"
    owner_name: str = "Visitor"
    model_name: str = "Standard Model"
    color: str = "Black"


class UserVehicleRegisterSchema(BaseModel):
    vehicle_number: str
    vehicle_type: str = "4W"
    model_name: str = "Standard Model"
    color: str = "Black"


class ParkingRequestSchema(BaseModel):
    vehicle_number: str
    vehicle_type: str = "4W"
    priority_level: str = "NORMAL"
    entry_gate: str = "GATE-1"


class AllocateRequestSchema(BaseModel):
    request_id: Optional[str] = None


class ExitProcessSchema(BaseModel):
    identifier: str


class BlockLaneSchema(BaseModel):
    u: str
    v: str
    is_blocked: bool


class LabSortSchema(BaseModel):
    array: List[int]


class LabSearchSchema(BaseModel):
    array: List[int]
    target: int


# ==========================================
# 1. AUTHENTICATION API ENDPOINTS
# ==========================================

@app.post("/api/auth/register")
def register(data: UserRegisterSchema):
    res = auth_service.register_user(data.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/login")
def login(data: UserLoginSchema, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    res = auth_service.login_user(data.model_dump(), ip_address=client_ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/verify-email")
def verify_email(data: VerifyEmailSchema):
    res = auth_service.verify_email_code(data.email, data.code)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/forgot-password")
def forgot_password(data: ForgotPasswordSchema):
    res = auth_service.request_password_reset(data.email)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/reset-password")
def reset_password(data: ResetPasswordSchema):
    res = auth_service.reset_password(data.email, data.reset_code, data.new_password)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        auth_service.logout_user(authorization)
    return {"success": True, "message": "Logged out successfully."}


@app.get("/api/auth/me")
def get_current_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "success": True,
        "user": user
    }


# ==========================================
# 2. USER DASHBOARD & BOOKINGS API
# ==========================================

@app.get("/api/user/find-slots")
def find_available_slots(
    zone_id: str = Query("A"),
    vehicle_type: str = Query("4W"),
    booking_date: str = Query(...),
    arrival_time: str = Query("10:00"),
    duration_hours: int = Query(2),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Allows authenticated user to search for bookable slots."""
    return booking_service.find_available_slots(zone_id, vehicle_type, booking_date, arrival_time, duration_hours)


@app.post("/api/user/book-slot")
def book_slot_advance(
    data: AdvanceBookingSchema,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Reserves slot in advance for the user and generates Dijkstra driving directions."""
    res = booking_service.create_advance_booking(
        user_id=user["user_id"],
        vehicle_number=data.vehicle_number,
        vehicle_type=data.vehicle_type,
        zone_id=data.zone_id,
        slot_id=data.slot_id,
        booking_date=data.booking_date,
        arrival_time=data.arrival_time,
        duration_hours=data.duration_hours,
        entry_gate=data.entry_gate
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.get("/api/user/bookings")
def get_user_bookings(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns ONLY the authenticated user's own bookings."""
    return booking_service.get_user_bookings(user["user_id"])


@app.post("/api/user/bookings/{booking_id}/cancel")
def cancel_user_booking(
    booking_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Allows user to cancel their own booking."""
    res = booking_service.cancel_booking(user["user_id"], booking_id, is_admin=False)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.get("/api/user/vehicles")
def get_user_vehicles(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns vehicles belonging strictly to the user."""
    return parking_service.get_user_vehicles(user["user_id"])


@app.post("/api/user/vehicles")
def register_user_vehicle(
    data: UserVehicleRegisterSchema,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Registers vehicle under the authenticated user's account."""
    res = parking_service.register_user_vehicle(user["user_id"], data.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.get("/api/user/history")
def get_user_history(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns only the authenticated user's parking history."""
    return parking_service.get_user_history(user["user_id"])


# ==========================================
# 3. ADMIN DASHBOARD & LIVE MONITORING API
# ==========================================

@app.get("/api/admin/live-monitor")
def get_admin_live_monitor(
    zone_id: Optional[str] = Query("ALL"),
    floor: Optional[str] = Query("ALL"),
    vehicle_type: Optional[str] = Query("ALL"),
    slot_status: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin live monitoring: which vehicle is parked -> where -> status -> booking."""
    return parking_service.get_admin_live_monitor(zone_id, floor, vehicle_type, slot_status, search)


@app.get("/api/admin/block-summary")
def get_admin_block_summary(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Admin block-wise (Zone A/B/C/D) status summary."""
    return parking_service.get_block_wise_summary()


@app.get("/api/admin/bookings")
def get_admin_all_bookings(
    status: Optional[str] = Query("ALL"),
    zone_id: Optional[str] = Query("ALL"),
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin view of all customer bookings."""
    return booking_service.get_all_bookings(status, zone_id)


@app.post("/api/admin/bookings/{booking_id}/cancel")
def admin_cancel_booking(
    booking_id: str,
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Admin can cancel any reservation."""
    res = booking_service.cancel_booking(admin["user_id"], booking_id, is_admin=True)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.get("/api/admin/audit-logs")
def get_admin_audit_logs(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Returns security audit logs."""
    from database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return logs


# ==========================================
# 4. DASHBOARD & SLOTS API (ALL EXISTING DSA ROUTES)
# ==========================================

@app.get("/api/dashboard")
def get_dashboard():
    return parking_service.get_dashboard_data()


@app.get("/api/slots")
def get_slots(zone_id: Optional[str] = None, status: Optional[str] = None):
    return parking_service.get_all_slots(zone_id, status)


@app.get("/api/slots/{slot_id}")
def get_slot(slot_id: str):
    slot = parking_service.get_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


@app.post("/api/slots")
def add_slot(data: SlotCreateSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    res = parking_service.add_slot(data.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.put("/api/slots/{slot_id}/status")
def update_slot_status(slot_id: str, data: SlotStatusUpdateSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    res = parking_service.update_slot_status(slot_id, data.status)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.delete("/api/slots/{slot_id}")
def delete_slot(slot_id: str, admin: Dict[str, Any] = Depends(get_current_admin)):
    res = parking_service.delete_slot(slot_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


# 5. Vehicles (All Vehicles - Admin)
@app.get("/api/vehicles")
def get_vehicles(admin: Dict[str, Any] = Depends(get_current_admin)):
    return parking_service.get_all_vehicles()


@app.post("/api/vehicles")
def register_vehicle(data: VehicleRegisterSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    res = parking_service.register_vehicle(data.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


# 6. Smart Slot Allocation & Requests
@app.get("/api/requests")
def get_pending_requests():
    return parking_service.get_pending_requests()


@app.post("/api/requests")
def submit_parking_request(data: ParkingRequestSchema):
    res = parking_service.submit_parking_request(data.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/requests/allocate")
def allocate_parking(data: AllocateRequestSchema):
    res = parking_service.allocate_next_request(data.request_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


# 7. Entry & Exit
@app.post("/api/entry-exit/exit")
def process_vehicle_exit(data: ExitProcessSchema):
    res = parking_service.process_vehicle_exit(data.identifier)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


@app.get("/api/entry-exit/history")
def get_parking_history():
    from database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT h.*, z.name as zone_name
    FROM entry_exit_history h
    LEFT JOIN parking_zones z ON h.zone_id = z.zone_id
    ORDER BY h.id DESC
    """)
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


# 8. Multi-Structure Search
@app.get("/api/search")
def search_system(q: str = Query(..., min_length=1)):
    return search_service.multi_search_compare(q)


# 9. Navigation & Graph Routing
@app.get("/api/navigation/graph")
def get_navigation_graph():
    return graph_service.get_all_graph_elements()


@app.get("/api/navigation/route")
def get_navigation_route(
    start: str = Query("GATE-1"),
    destination: str = Query("A-01"),
    algorithm: str = Query("DIJKSTRA")
):
    res = graph_service.get_shortest_route(start, destination, algorithm)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.get("/api/navigation/compare")
def compare_navigation_routes(
    start: str = Query("GATE-1"),
    destination: str = Query("A-01")
):
    return graph_service.compare_navigation_algorithms(start, destination)


@app.post("/api/navigation/toggle-lane")
def toggle_lane(data: BlockLaneSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    return graph_service.toggle_edge_blocked(data.u, data.v, data.is_blocked)


# 10. Algorithm Lab
@app.get("/api/algorithm-lab/dataset")
def get_lab_dataset(size: int = 50, type: str = "RANDOM"):
    arr = lab_service.generate_dataset(size, type)
    return {"size": len(arr), "type": type, "array": arr}


@app.post("/api/algorithm-lab/sort")
def run_sort_benchmark(data: LabSortSchema):
    if not data.array:
        raise HTTPException(status_code=400, detail="Array cannot be empty")
    return lab_service.run_all_sorts(data.array)


@app.post("/api/algorithm-lab/search")
def run_search_benchmark(data: LabSearchSchema):
    return lab_service.run_search_lab(data.array, data.target)


# 11. Reports & Analytics
@app.get("/api/reports")
def get_system_reports():
    from database.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) as total_tickets,
           SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_tickets,
           SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_tickets,
           AVG(CASE WHEN status = 'COMPLETED' THEN duration_minutes ELSE NULL END) as avg_duration,
           SUM(cost_charged) as total_revenue
    FROM entry_exit_history
    """)
    summary = dict(cursor.fetchone())

    cursor.execute("""
    SELECT strftime('%H', entry_time) as hour, COUNT(*) as count
    FROM entry_exit_history
    GROUP BY hour
    ORDER BY hour ASC
    """)
    hourly_traffic = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
    SELECT vehicle_type, COUNT(*) as count
    FROM vehicles
    GROUP BY vehicle_type
    """)
    vtype_stats = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
    SELECT z.zone_id, z.name, COUNT(s.id) as capacity,
           SUM(CASE WHEN s.status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied
    FROM parking_zones z
    LEFT JOIN parking_slots s ON z.zone_id = s.zone_id
    GROUP BY z.zone_id
    """)
    zone_occupancy = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "summary": {
            "total_tickets": summary["total_tickets"] or 0,
            "completed_tickets": summary["completed_tickets"] or 0,
            "active_tickets": summary["active_tickets"] or 0,
            "avg_duration_minutes": round(summary["avg_duration"] or 0, 1),
            "total_revenue": round(summary["total_revenue"] or 0.0, 2)
        },
        "hourly_traffic": hourly_traffic,
        "vehicle_type_breakdown": vtype_stats,
        "zone_occupancy": zone_occupancy
    }


# 12. DSA Documentation & Viva Guide
@app.get("/api/dsa-explain")
def get_dsa_documentation():
    return {
        "title": "Smart Parking System - Academic DSA Mappings",
        "structures": get_all_dsa_explanations()
    }


# 13. Undo Action (Stack)
@app.post("/api/undo")
def undo_action(admin: Dict[str, Any] = Depends(get_current_admin)):
    res = parking_service.undo_last_action()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    search_service.rebuild_search_indices()
    return res


# 14. Cyclic Zone Inspection (Circular Linked List)
@app.get("/api/zone-inspect")
def inspect_next_zone():
    return parking_service.inspect_next_zone()


# 15. Re-seed Database
@app.post("/api/reset-seed")
def reset_database(admin: Dict[str, Any] = Depends(get_current_admin)):
    seed_database(force_reset=True)
    graph_service.load_graph_from_db()
    search_service.rebuild_search_indices()
    parking_service._init_zone_cll()
    parking_service._sync_active_queues_from_db()
    parking_service._sync_history_from_db()
    return {"success": True, "message": "Database and in-memory DSA structures reset to clean initial seed dataset."}


# ==========================================
# STATIC FILES & SPA SERVING
# ==========================================
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    file_path = os.path.join(STATIC_DIR, full_path)
    if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(status_code=200, content={"message": "Smart Parking System API Running"})
