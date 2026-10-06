# Smart Parking Management System Using Data Structures and Algorithms (DSA)

An academic mini-project featuring a full-stack **Smart Parking Management System** with **Secure Role-Based Access Control (RBAC)**, **Customer Advance Slot Bookings**, **Live Admin Monitoring**, and a **Pure Python Data Structures & Algorithms Core**.

Built with **FastAPI (Python)**, **SQLite Database**, **Vanilla JavaScript (SPA)**, and **Pure Python DSA Core**.

---

## 🔑 Login & Demo Credentials

When you open the application at `http://127.0.0.1:8000`, the **Authentication Screen (The First Screen)** will appear. You can either register a new customer account or use the built-in fast 1-click viva demo accounts:

| Role | Email Address | Password | Permissions & Dashboard |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@smartpark.com` | `Admin@1234` | Full system control: Live vehicle monitor, block & slot management, global vehicle registry, all bookings, entry/exit checkout, request queues, graph road blockage simulation, audit logs. |
| **Customer User** | `priya@student.edu` | `User@1234` | Customer portal: Find parking by block & date, advance slot reservations, view personal bookings, register personal vehicles, view Dijkstra navigation route to assigned bay, personal parking history. |

---

## 🌟 Data Structures & Algorithms Architecture Mapping

Every single feature in the application is strictly connected to its pure DSA implementation:

| Data Structure / Algorithm | File Location | Parking System Feature & Usage | Time Complexity |
| :--- | :--- | :--- | :--- |
| **Array** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Parking-slot records and direct slot indexing matrix | Access: $\mathcal{O}(1)$ |
| **Singly Linked List** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Dynamic sequential logging of vehicle entries & exits | Append: $\mathcal{O}(1)$ |
| **Doubly Linked List** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Bi-directional navigation waypoint and transaction audit trail | Insert: $\mathcal{O}(1)$ |
| **Circular Linked List** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Cyclic round-robin patrol inspection of parking zones ($A \to B \to C \to D \to A$) | Step: $\mathcal{O}(1)$ |
| **Stack (LIFO)** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Undo operations for recent slot status modifications & ticket checkouts | Push/Pop: $\mathcal{O}(1)$ |
| **FIFO Queue** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Fair first-come first-served queue for normal vehicle parking requests | Enqueue/Dequeue: $\mathcal{O}(1)$ |
| **Circular Queue** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Fixed-capacity buffer for vehicle entry processing at boom barriers | Enqueue/Dequeue: $\mathcal{O}(1)$ |
| **Priority Queue** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Min-Heap priority scheduling: Emergency $>$ Accessibility $>$ VIP $>$ Normal | Push/Pop: $\mathcal{O}(\log n)$ |
| **Deque** | [`dsa/linear.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/linear.py) | Double-ended queue for immediate priority lane overrides | Front/Rear: $\mathcal{O}(1)$ |
| **Binary Tree** | [`dsa/trees.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/trees.py) | Facility structural zone & floor hierarchy | Preorder: $\mathcal{O}(n)$ |
| **Binary Search Tree (BST)** | [`dsa/trees.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/trees.py) | Indexed search for vehicle registrations and slot IDs | Search: $\mathcal{O}(\log n)$ avg |
| **AVL Tree (Self-Balancing)** | [`dsa/trees.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/trees.py) | Balanced indexing using LL, RR, LR, RL rotations | Search: $\mathcal{O}(\log n)$ guaranteed |
| **Min Heap** | [`dsa/trees.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/trees.py) | Nearest & most compatible candidate slot extraction | Extract Min: $\mathcal{O}(\log n)$ |
| **Hash Table** | [`dsa/hash_table.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/hash_table.py) | Instant license plate scan lookup using polynomial rolling hash & chaining | Lookup: $\mathcal{O}(1)$ avg |
| **Weighted Graph** | [`dsa/graph.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/graph.py) | Campus road network, entrance gates, junctions, ramps and slots | Adjacency List: $\mathcal{O}(V + E)$ |
| **Dijkstra's Algorithm** | [`dsa/graph.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/graph.py) | Shortest physical driving route calculation from entry gate to slot | Time: $\mathcal{O}((V + E) \log V)$ |
| **Breadth-First Search (BFS)** | [`dsa/graph.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/graph.py) | Minimum-hop route calculation (fewest turns/junctions) | Time: $\mathcal{O}(V + E)$ |
| **Depth-First Search (DFS)** | [`dsa/graph.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/graph.py) | Zone exploration and road connectivity validation | Time: $\mathcal{O}(V + E)$ |
| **Greedy Algorithm** | [`dsa/algorithms.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/algorithms.py) | Optimal candidate bay selection by composite score | Time: $\mathcal{O}(n)$ |
| **7 Sorting Algorithms** | [`dsa/algorithms.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/algorithms.py) | Bubble, Selection, Insertion, Merge, Quick, Heap, Radix Sort in Lab | Variable $\mathcal{O}(n \log n)$ to $\mathcal{O}(n^2)$ |
| **Binary & Linear Search** | [`dsa/algorithms.py`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/dsa/algorithms.py) | Comparative analysis of sequential vs logarithmic searching | Linear: $\mathcal{O}(n)$, Binary: $\mathcal{O}(\log n)$ |

---

## 🔒 Security & RBAC Enforcement

1. **Password Security**: Passwords are never stored in plaintext. They are hashed using **PBKDF2 with HMAC-SHA256 and 100,000 iterations** using a unique cryptographically random salt per user.
2. **Server-Side Authorization**: Every protected backend endpoint validates session tokens and enforces role restrictions. If a regular user calls an administrative endpoint (`/api/admin/...`, `/api/slots`), the server strictly returns `403 Forbidden`.
3. **Double-Booking & Conflict Prevention**: Advance reservations are validated against existing bookings and real-time slot statuses to guarantee no overlapping reservations.
4. **Data Isolation**: Regular users can only query, view, and cancel their own bookings and vehicles.
5. **Brute-Force Protection & Rate Limiting**: Consecutive failed login attempts trigger temporary account locking.
6. **Audit Logs**: Administrative and critical state modifications are permanently recorded in the `audit_logs` table.

---

## 🚀 Running the Project

```powershell
python run.py
```
*or*
```powershell
python parking_system.py
```

Access the application in your browser:
👉 **`http://127.0.0.1:8000`**

To run automated verification tests:
```powershell
python test_system.py
python verify_api.py
```
