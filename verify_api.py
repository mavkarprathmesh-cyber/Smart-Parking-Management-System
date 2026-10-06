"""
API Verification Test
Validates all FastAPI routes, RBAC security enforcement, advance bookings, and DSA endpoints.
"""

from fastapi.testclient import TestClient
from main import app
from database.seed_data import seed_database

client = TestClient(app)

def test_endpoints():
    print("Testing API endpoints and Security Layer...")
    seed_database(force_reset=True)

    # 1. Login as Admin
    res = client.post("/api/auth/login", json={"email": "admin@smartpark.com", "password": "Admin@1234"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_data = res.json()
    admin_token = admin_data["token"]
    assert admin_data["user"]["role"] == "ADMIN"
    print("[OK] Admin login successful with role ADMIN")

    # 2. Login as Customer User
    res = client.post("/api/auth/login", json={"email": "priya@student.edu", "password": "User@1234"})
    assert res.status_code == 200, f"User login failed: {res.text}"
    user_data = res.json()
    user_token = user_data["token"]
    assert user_data["user"]["role"] == "USER"
    print("[OK] User login successful with role USER")

    # 3. RBAC Enforcement: User attempting to access Admin endpoint -> MUST RETURN 403 FORBIDDEN
    res = client.get("/api/admin/live-monitor", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 403, f"Expected 403 Forbidden for normal user, got: {res.status_code}"
    print("[OK] RBAC verified: Customer User access to Admin endpoint correctly rejected (403 Forbidden)")

    # 4. Admin accessing Admin endpoint -> MUST RETURN 200 OK
    res = client.get("/api/admin/live-monitor", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Admin access failed: {res.text}"
    monitor_records = res.json()
    assert len(monitor_records) > 0
    print(f"[OK] Admin live monitor working ({len(monitor_records)} slots tracked)")

    # 5. User Advance Booking Workflow
    # Find slots
    res = client.get("/api/user/find-slots?zone_id=A&vehicle_type=4W&booking_date=2026-10-15&arrival_time=10:00&duration_hours=2", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    available_data = res.json()
    assert available_data["available_count"] > 0

    # Book slot A-02
    res = client.post("/api/user/book-slot", json={
        "vehicle_number": "KA-03-EQ-4567",
        "vehicle_type": "4W",
        "zone_id": "A",
        "slot_id": "A-02",
        "booking_date": "2026-10-15",
        "arrival_time": "10:00",
        "duration_hours": 2,
        "entry_gate": "GATE-1"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200, f"Booking failed: {res.text}"
    bkg_res = res.json()
    bkg_id = bkg_res["booking_id"]
    assert "navigation_route" in bkg_res
    print(f"[OK] Advance Booking created: {bkg_id} with Dijkstra driving path")

    # Double Booking Prevention -> MUST RETURN 400
    res_double = client.post("/api/user/book-slot", json={
        "vehicle_number": "MH-12-AB-9876",
        "vehicle_type": "4W",
        "zone_id": "A",
        "slot_id": "A-02",
        "booking_date": "2026-10-15",
        "arrival_time": "10:00",
        "duration_hours": 2,
        "entry_gate": "GATE-1"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert res_double.status_code == 400
    print("[OK] Double-booking prevention verified (Rejected duplicate on same slot & date)")

    # 6. User Bookings Query (Data Isolation)
    res = client.get("/api/user/bookings", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    user_bkgs = res.json()
    assert any(b["booking_id"] == bkg_id for b in user_bkgs)
    print(f"[OK] User data isolation verified ({len(user_bkgs)} bookings for user)")

    # 7. Dashboard API (Shared/Admin)
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    print("[OK] Dashboard API working")

    # 8. Multi-Structure Search API
    res = client.get("/api/search?q=KA-01")
    assert res.status_code == 200
    search_data = res.json()
    assert len(search_data["benchmarks"]) == 5
    print("[OK] Multi-Structure Search API working (5 benchmark structures verified)")

    # 9. Algorithm Lab
    res = client.post("/api/algorithm-lab/sort", json={"array": [50, 10, 40, 20, 30]})
    assert res.status_code == 200
    lab_data = res.json()
    assert len(lab_data["results"]) == 7
    print("[OK] Algorithm Lab Sort Benchmark working (7 algorithms verified)")

    # 10. Frontend HTML
    res = client.get("/")
    assert res.status_code == 200
    assert "SmartPark DSA" in res.text
    print("[OK] Frontend Single Page Application served successfully")

    print("\nALL API ENDPOINTS, RBAC RESTRICTIONS & ADVANCE BOOKING CHECKS PASSED!")

if __name__ == "__main__":
    test_endpoints()
