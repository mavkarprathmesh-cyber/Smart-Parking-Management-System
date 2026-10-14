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

---

## 📱 Android Mobile Application

The Smart Parking Management System is packaged as a native Android application using **Capacitor**, preserving the entire UI, interactive 3D navigation, viva demo accounts, and pure Python DSA backend connectivity.

### 📦 APK Location
* **Debug APK**: [`android/app/build/outputs/apk/debug/app-debug.apk`](file:///c:/Users/Lenovo/Downloads/SUMIT'S%20DOCUMENT/DSA%20PROJECT/android/app/build/outputs/apk/debug/app-debug.apk) (~4.2 MB)
* **Package ID**: `com.smartparking.management`
* **App Name**: `Smart Parking Management System`
* **Min SDK**: 24 (Android 7.0+) | **Target SDK**: 36 (Android 16+)

### 📲 Transfer & Install on Android Phone
1. Transfer `app-debug.apk` to your phone via USB cable, Google Drive, WhatsApp, or local file sharing.
2. On your Android phone, open the APK file in **Files** / **Downloads**.
3. If prompted, toggle **Allow installation from unknown sources / this source**.
4. Tap **Install** and open **Smart Parking Management System**.

### 🌐 Backend & Server Configuration
When the app launches on an Android phone:
1. Tap the **Network / Server icon** in the top-right corner of the Login screen or Top Header.
2. Set your server endpoint:
   * **Wi-Fi / Local Network**: Enter `http://<YOUR_LAPTOP_IP>:8000` (e.g., `http://192.168.1.105:8000`). Make sure your laptop and phone are on the same Wi-Fi network and start the server with `python -m uvicorn main:app --host 0.0.0.0 --port 8000`.
   * **Android Emulator**: Tap **Emulator (10.0.2.2)** preset (`http://10.0.2.2:8000`).
   * **Cloud / Production**: Enter your deployed Vercel/Render API URL (e.g. `https://your-app.vercel.app`).
3. Tap **Ping Test** to verify connection, then tap **Save & Connect**.

### 🔨 Rebuilding the Android APK
To rebuild the Android APK after making frontend or native changes:
```powershell
# 1. Sync web assets into Android native project
npx.cmd cap sync android

# 2. Build the Debug APK using Gradle
cd android
.\gradlew.bat assembleDebug
```
*Generated APK output*: `android/app/build/outputs/apk/debug/app-debug.apk`

### 🔑 Debug APK vs Signed Release APK
* **Debug APK (`app-debug.apk`)**: Automatically signed with Android's default debug keystore. Perfect for viva testing, direct installation via USB/sideloading, and development without needing a personal signing certificate.
* **Release APK / AAB**: Requires generating a private keystore (`keytool`), configuring `signingConfigs` in `build.gradle`, running `gradlew assembleRelease`, and alignment/zipalign for Google Play Store publication.

