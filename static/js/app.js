/**
 * Main Application Controller with Secure RBAC & Dual User/Admin Portals
 */

const App = {
  currentUser: null,
  currentRole: null,
  currentView: 'dashboard',
  refreshInterval: null,

  async init() {
    this.bindAuthEvents();
    this.bindNavigation();
    this.bindForms();
    this.bindGlobalActions();

    // Check existing session token
    const token = API.getToken();
    if (token) {
      try {
        const profile = await API.getProfile();
        if (profile && profile.user) {
          this.setCurrentUser(profile.user);
          return;
        }
      } catch (e) {
        console.warn('Session expired or invalid. Showing login screen.');
      }
    }
    
    // Show login screen by default
    this.showAuthScreen();
  },

  // ==========================================
  // 1. AUTHENTICATION & SESSION MANAGEMENT
  // ==========================================
  showAuthScreen() {
    const overlay = document.getElementById('auth-screen-overlay');
    if (overlay) overlay.style.display = 'flex';
    this.currentUser = null;
    this.currentRole = null;
    API.clearToken();
  },

  hideAuthScreen() {
    const overlay = document.getElementById('auth-screen-overlay');
    if (overlay) overlay.style.display = 'none';
  },

  setCurrentUser(user) {
    this.currentUser = user;
    this.currentRole = user.role === 'ADMIN' ? 'ADMIN' : 'USER';
    API.setUser(user);
    this.hideAuthScreen();

    // Update User Info in Sidebar & Header
    this.renderSidebarProfile();

    // Route to appropriate dashboard
    if (this.currentRole === 'ADMIN') {
      this.switchRoleSidebar('ADMIN');
      this.navigateTo('dashboard');
    } else {
      this.switchRoleSidebar('USER');
      this.navigateTo('user-overview');
    }

    // Initialize Canvas Map & 3D Interactive Map
    ParkingMap.init('parking-canvas', (slot) => this.handleMapSlotClick(slot));
    if (window.Map3D) {
      Map3D.init();
    }
    AlgoLab.init();
  },

  renderSidebarProfile() {
    const nameElem = document.getElementById('sidebar-user-name');
    const roleElem = document.getElementById('sidebar-user-role');
    const avatarElem = document.getElementById('sidebar-user-avatar');
    const headerRoleElem = document.getElementById('header-role-badge');

    if (this.currentUser) {
      if (nameElem) nameElem.innerText = this.currentUser.full_name || 'User';
      if (roleElem) roleElem.innerText = this.currentUser.role || 'USER';
      if (avatarElem) avatarElem.innerText = (this.currentUser.full_name || 'U').charAt(0).toUpperCase();
      if (headerRoleElem) {
        if (this.currentRole === 'ADMIN') {
          headerRoleElem.className = 'role-badge-admin';
          headerRoleElem.innerHTML = '<i class="fas fa-shield-alt"></i> System Administrator';
        } else {
          headerRoleElem.className = 'role-badge-user';
          headerRoleElem.innerHTML = '<i class="fas fa-user"></i> Customer Account';
        }
      }
    }
  },

  switchRoleSidebar(role) {
    document.querySelectorAll('.admin-only-nav').forEach(el => {
      el.style.display = role === 'ADMIN' ? 'block' : 'none';
    });
    document.querySelectorAll('.user-only-nav').forEach(el => {
      el.style.display = role === 'USER' ? 'block' : 'none';
    });
  },

  bindAuthEvents() {
    // Auth Tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const tabTarget = tab.getAttribute('data-tab');

        document.getElementById('auth-tab-login').style.display = tabTarget === 'login' ? 'block' : 'none';
        document.getElementById('auth-tab-register').style.display = tabTarget === 'register' ? 'block' : 'none';
        document.getElementById('auth-tab-forgot').style.display = tabTarget === 'forgot' ? 'block' : 'none';
      });
    });

    // Login Form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const pwd = document.getElementById('login-password').value;
        const remember = document.getElementById('login-remember')?.checked ?? true;

        try {
          const res = await API.login(email, pwd);
          API.setToken(res.token, remember);
          UI.showToast('Login Successful', res.message, 'success');
          this.setCurrentUser(res.user);
        } catch (err) {
          UI.showToast('Login Failed', err.message, 'error');
        }
      });
    }

    // Register Form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const regData = {
          full_name: document.getElementById('reg-name').value.trim(),
          email: document.getElementById('reg-email').value.trim(),
          phone: document.getElementById('reg-phone').value.trim(),
          password: document.getElementById('reg-password').value,
          confirm_password: document.getElementById('reg-confirm-password').value
        };

        try {
          const res = await API.register(regData);
          API.setToken(res.token, true);
          UI.showToast('Registration Successful', `Account created! (Verification Code: ${res.verification_code})`, 'success');
          this.setCurrentUser({
            user_id: res.user_id,
            full_name: res.full_name,
            email: res.email,
            role: res.role,
            is_verified: true
          });
        } catch (err) {
          UI.showToast('Registration Error', err.message, 'error');
        }
      });
    }

    // Forgot Password Form
    const forgotForm = document.getElementById('forgot-password-form');
    if (forgotForm) {
      forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('forgot-email').value.trim();
        try {
          const res = await API.forgotPassword(email);
          UI.showToast('Reset Code Sent', res.message, 'info');
          document.getElementById('reset-password-section').style.display = 'block';
          document.getElementById('reset-email-hidden').value = email;
        } catch (err) {
          UI.showToast('Error', err.message, 'error');
        }
      });
    }

    // Reset Password Form
    const resetForm = document.getElementById('reset-password-form');
    if (resetForm) {
      resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('reset-email-hidden').value.trim();
        const code = document.getElementById('reset-code-input').value.trim();
        const newPwd = document.getElementById('reset-new-password').value;

        try {
          const res = await API.resetPassword(email, code, newPwd);
          UI.showToast('Password Reset', res.message, 'success');
          // Switch back to login
          document.querySelector('.auth-tab[data-tab="login"]').click();
        } catch (err) {
          UI.showToast('Reset Failed', err.message, 'error');
        }
      });
    }
  },

  // Fill Quick Demo Credentials
  fillDemoCredentials(role) {
    if (role === 'ADMIN') {
      document.getElementById('login-email').value = 'admin@smartpark.com';
      document.getElementById('login-password').value = 'Admin@1234';
      UI.showToast('Admin Credentials Loaded', 'Ready to sign in as System Admin', 'info');
    } else {
      document.getElementById('login-email').value = 'priya@student.edu';
      document.getElementById('login-password').value = 'User@1234';
      UI.showToast('User Credentials Loaded', 'Ready to sign in as Customer User', 'info');
    }
  },

  async handleLogout() {
    try {
      await API.logout();
    } catch {}
    UI.showToast('Logged Out', 'You have been securely signed out.', 'info');
    this.showAuthScreen();
  },

  // ==========================================
  // 2. NAVIGATION ROUTER
  // ==========================================
  bindNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.getAttribute('data-view');
        if (view) this.navigateTo(view);
      });
    });

    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        themeBtn.innerHTML = newTheme === 'dark' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
      });
    }
  },

  navigateTo(viewName) {
    // Security check: If regular user tries to navigate to admin views, reject
    const adminViews = ['dashboard', 'live-monitor', 'slots', 'vehicles', 'requests', 'reports', 'audit-logs'];
    if (this.currentRole === 'USER' && adminViews.includes(viewName)) {
      UI.showToast('Access Denied', 'Administrator privileges required for this view.', 'error');
      viewName = 'user-overview';
    }

    this.currentView = viewName;
    if (window.UI && typeof window.UI.closeMobileMenu === 'function') {
      window.UI.closeMobileMenu();
    }

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.getAttribute('data-view') === viewName);
    });

    // Show active page section
    document.querySelectorAll('.page-view').forEach(page => {
      page.style.display = page.id === `view-${viewName}` ? 'block' : 'none';
    });

    // Update Header Context
    this.updateHeaderContext(viewName);

    // Load view data
    switch (viewName) {
      // User Portal
      case 'user-overview':
        this.loadUserOverview();
        break;
      case 'user-find-slots':
        this.loadUserFindSlots();
        break;
      case 'user-my-bookings':
        this.loadUserBookings();
        break;
      case 'user-my-vehicles':
        this.loadUserVehicles();
        break;
      case 'user-history':
        this.loadUserHistory();
        break;

      // Admin Portal
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'live-monitor':
        this.loadLiveMonitor();
        break;
      case 'slots':
        this.loadSlots();
        break;
      case 'vehicles':
        this.loadVehicles();
        break;
      case 'admin-bookings':
        this.loadAdminBookings();
        break;
      case 'requests':
        this.loadRequests();
        break;
      case 'audit-logs':
        this.loadAuditLogs();
        break;

      // Shared Views
      case 'map':
        this.loadMap();
        break;
      case 'park':
        this.loadParkView();
        break;
      case 'entry-exit':
        this.loadEntryExit();
        break;
      case 'navigation':
        this.loadNavigation();
        break;
      case 'search':
        this.loadSearch();
        break;
      case 'algo-lab':
        AlgoLab.init();
        break;
      case 'reports':
        this.loadReports();
        break;
      case 'dsa-guide':
        this.loadDsaGuide();
        break;
    }
  },

  updateHeaderContext(view) {
    const titles = {
      'user-overview': 'Customer Parking Overview',
      'user-find-slots': 'Find Available Parking Bays',
      'user-my-bookings': 'My Advance Bookings & Reservations',
      'user-my-vehicles': 'My Registered Vehicles',
      'user-history': 'My Parking Activity History',
      'dashboard': 'Campus Smart Parking Dashboard (Admin)',
      'live-monitor': 'Real-Time Vehicle & Slot Monitor',
      'slots': 'Parking Bay & Slot Management',
      'vehicles': 'All Registered Vehicles Registry',
      'admin-bookings': 'System-Wide Customer Reservations',
      'park': 'Smart Slot Allocation Engine',
      'requests': 'Request Queues (FIFO & Min-Heap)',
      'entry-exit': 'Active Parked Vehicles & Checkouts',
      'map': 'Interactive 3D Campus Map & Navigation',
      'navigation': 'Campus Navigation & Routing Graph',
      'search': 'Multi-Structure Search Lab',
      'algo-lab': 'Data Structures & Algorithm Benchmark Lab',
      'reports': 'System Reports & Analytical Metrics',
      'audit-logs': 'Security Audit Logs',
      'dsa-guide': 'Academic DSA Mappings & Viva Guide'
    };

    const dsaPills = {
      'user-overview': '<i class="fas fa-layer-group"></i> Array & Hash Table',
      'user-find-slots': '<i class="fas fa-filter"></i> Contiguous Array Scan',
      'user-my-bookings': '<i class="fas fa-receipt"></i> Singly Linked List',
      'dashboard': '<i class="fas fa-chart-pie"></i> Array & Hash Table',
      'live-monitor': '<i class="fas fa-desktop"></i> Hash Table & SLL',
      'map': '<i class="fas fa-cube"></i> Dijkstra 3D Routing & Min-Heap',
      'slots': '<i class="fas fa-th-large"></i> Contiguous Array & BST',
      'vehicles': '<i class="fas fa-car"></i> Hash Table & SLL',
      'park': '<i class="fas fa-microchip"></i> Min-Heap & Greedy Choice',
      'requests': '<i class="fas fa-list-ol"></i> Queue, Priority Queue & Deque',
      'entry-exit': '<i class="fas fa-receipt"></i> Singly & Doubly Linked List',
      'navigation': '<i class="fas fa-route"></i> Weighted Graph, Dijkstra, BFS, DFS',
      'search': '<i class="fas fa-search"></i> Hash vs AVL vs BST vs Binary Search',
      'algo-lab': '<i class="fas fa-flask"></i> 7 Sorting & 2 Search Algorithms',
      'reports': '<i class="fas fa-chart-pie"></i> Merge Sort & Aggregation',
      'audit-logs': '<i class="fas fa-shield-alt"></i> Audit Log Stack',
      'dsa-guide': '<i class="fas fa-graduation-cap"></i> Big-O, Ω & Θ Complexities'
    };

    const pageTitleElem = document.getElementById('page-title');
    const dsaPillElem = document.getElementById('header-dsa-pill');

    if (pageTitleElem) pageTitleElem.innerText = titles[view] || 'Smart Parking System';
    if (dsaPillElem) dsaPillElem.innerHTML = dsaPills[view] || '';
  },

  // ==========================================
  // 3. USER PORTAL LOGIC
  // ==========================================
  async loadUserOverview() {
    try {
      const [bookings, vehicles] = await Promise.all([
        API.getUserBookings(),
        API.getUserVehicles()
      ]);

      const activeBookings = bookings.filter(b => b.status === 'CONFIRMED' || b.status === 'ACTIVE');
      document.getElementById('user-stat-bookings').innerText = activeBookings.length;
      document.getElementById('user-stat-vehicles').innerText = vehicles.length;
      document.getElementById('user-stat-total').innerText = bookings.length;

      // Active Bookings Container
      const container = document.getElementById('user-active-bookings-list');
      if (container) {
        if (activeBookings.length === 0) {
          container.innerHTML = `
            <div style="text-align:center;padding:30px;color:var(--text-muted);">
              <i class="fas fa-calendar-check" style="font-size:32px;margin-bottom:10px;color:#3b82f6;"></i>
              <div>No active advance reservations.</div>
              <button class="btn btn-primary btn-sm" style="margin-top:12px;" onclick="App.navigateTo('user-find-slots')">
                <i class="fas fa-plus"></i> Book a Parking Bay
              </button>
            </div>
          `;
        } else {
          container.innerHTML = activeBookings.map(b => `
            <div class="card" style="border-left:4px solid #10b981;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:15px;">${b.booking_id}</strong>
                <span class="badge badge-free">${b.slot_id} (${b.zone_name})</span>
              </div>
              <div style="font-size:13px;color:var(--text-secondary);margin:8px 0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div>Vehicle: <code>${b.vehicle_number}</code></div>
                <div>Date: <strong>${b.booking_date} at ${b.arrival_time}</strong></div>
                <div>Duration: <strong>${b.duration_hours} hours</strong></div>
                <div>Estimated Fee: <strong>₹${b.total_estimated_fee}</strong></div>
              </div>
              <div style="display:flex;gap:8px;margin-top:10px;">
                <button class="btn btn-primary btn-sm" onclick="App.viewBookingRoute('${b.slot_id}')">
                  <i class="fas fa-map-marked-alt"></i> View Dijkstra Route
                </button>
                <button class="btn btn-secondary btn-sm" onclick="App.cancelUserBookingAction('${b.booking_id}')">
                  <i class="fas fa-times"></i> Cancel Booking
                </button>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load user overview:', err);
    }
  },

  async loadUserFindSlots() {
    // Set default date to today
    const dateInput = document.getElementById('find-slot-date');
    if (dateInput && !dateInput.value) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }
  },

  async executeFindSlots() {
    const zone = document.getElementById('find-slot-zone').value;
    const vType = document.getElementById('find-slot-vtype').value;
    const date = document.getElementById('find-slot-date').value;
    const time = document.getElementById('find-slot-time').value;
    const duration = parseInt(document.getElementById('find-slot-duration').value || 2, 10);

    const container = document.getElementById('find-slots-results-container');
    container.innerHTML = `<div style="text-align:center;padding:30px;"><i class="fas fa-spinner fa-spin"></i> Checking slot availability & double-booking prevention...</div>`;

    try {
      const res = await API.findSlots(zone, vType, date, time, duration);
      const slots = res.slots || [];

      if (slots.length === 0) {
        container.innerHTML = `<div class="card" style="text-align:center;color:var(--text-muted);">No slots exist for selected criteria.</div>`;
        return;
      }

      container.innerHTML = `
        <div style="margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;">
          <div>Available in ${res.zone.name}: <strong style="color:var(--status-free);">${res.available_count} of ${res.total_slots} Slots</strong></div>
          <div style="font-size:12px;color:var(--text-muted);">Rate: ₹${res.zone.hourly_rate}/hr • Estimated Total: ₹${res.zone.hourly_rate * duration}</div>
        </div>
        <div class="slots-grid">
          ${slots.map(s => `
            <div class="slot-box ${s.is_bookable ? 'free' : 'occupied'}">
              <div class="slot-id">${s.slot_id}</div>
              <i class="fas ${s.vehicle_type === '2W' ? 'fa-motorcycle' : 'fa-car-side'} slot-icon"></i>
              <div style="font-size:11px;color:var(--text-muted);">${s.distance_from_gate}m from Gate</div>
              <div style="margin:4px 0;">${UI.getStatusBadge(s.is_bookable ? 'FREE' : s.status)}</div>
              ${s.is_bookable ? `
                <button class="btn btn-primary btn-sm" style="width:100%;margin-top:6px;" onclick="App.openAdvanceBookingModal('${s.slot_id}', '${s.zone_id}', '${s.vehicle_type}', '${date}', '${time}', ${duration})">
                  Book Slot
                </button>
              ` : `
                <div style="font-size:11px;color:var(--text-muted);margin-top:6px;">Unavailable</div>
              `}
            </div>
          `).join('')}
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color:#ef4444;">Search failed: ${err.message}</div>`;
      UI.showToast('Error', err.message, 'error');
    }
  },

  openAdvanceBookingModal(slotId, zoneId, vType, date, time, duration) {
    document.getElementById('bkg-modal-slot-id').innerText = slotId;
    document.getElementById('bkg-slot-id-hidden').value = slotId;
    document.getElementById('bkg-zone-id-hidden').value = zoneId;
    document.getElementById('bkg-vtype-hidden').value = vType;
    document.getElementById('bkg-date-input').value = date;
    document.getElementById('bkg-time-input').value = time;
    document.getElementById('bkg-duration-input').value = duration;

    UI.openModal('advance-booking-modal');
  },

  async handleAdvanceBookingSubmit(e) {
    e.preventDefault();
    const data = {
      slot_id: document.getElementById('bkg-slot-id-hidden').value,
      zone_id: document.getElementById('bkg-zone-id-hidden').value,
      vehicle_type: document.getElementById('bkg-vtype-hidden').value,
      vehicle_number: document.getElementById('bkg-vehicle-plate').value.trim().toUpperCase(),
      booking_date: document.getElementById('bkg-date-input').value,
      arrival_time: document.getElementById('bkg-time-input').value,
      duration_hours: parseInt(document.getElementById('bkg-duration-input').value, 10),
      entry_gate: document.getElementById('bkg-gate-select').value
    };

    try {
      const res = await API.bookSlot(data);
      UI.closeModal('advance-booking-modal');
      UI.showToast('Booking Confirmed!', `Slot ${res.slot_id} reserved. Booking ID: ${res.booking_id}`, 'success');
      
      // Navigate to My Bookings
      App.navigateTo('user-my-bookings');
    } catch (err) {
      UI.showToast('Booking Failed', err.message, 'error');
    }
  },

  async loadUserBookings() {
    const container = document.getElementById('user-bookings-table-tbody');
    if (!container) return;

    try {
      const bookings = await API.getUserBookings();
      if (bookings.length === 0) {
        container.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-muted);">No bookings found.</td></tr>`;
        return;
      }

      container.innerHTML = bookings.map(b => `
        <tr>
          <td><strong>${b.booking_id}</strong></td>
          <td><code>${b.vehicle_number}</code></td>
          <td><span class="badge badge-free">${b.slot_id}</span></td>
          <td>${b.zone_name} (${b.floor})</td>
          <td>${b.booking_date} at ${b.arrival_time}</td>
          <td>${b.duration_hours} hrs</td>
          <td><strong>₹${b.total_estimated_fee}</strong></td>
          <td>
            <div style="display:flex;gap:6px;">
              <button class="btn btn-primary btn-sm" onclick="App.viewBookingRoute('${b.slot_id}')">
                <i class="fas fa-route"></i> Route
              </button>
              ${b.status === 'CONFIRMED' ? `
                <button class="btn btn-secondary btn-sm" onclick="App.cancelUserBookingAction('${b.booking_id}')">
                  <i class="fas fa-times"></i> Cancel
                </button>
              ` : `<span class="badge badge-occupied">${b.status}</span>`}
            </div>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load bookings', 'error');
    }
  },

  cancelUserBookingAction(bookingId) {
    UI.confirm('Cancel Reservation', `Are you sure you want to cancel booking ${bookingId}? The slot will become FREE.`, async () => {
      try {
        const res = await API.cancelUserBooking(bookingId);
        UI.showToast('Cancelled', res.message, 'success');
        App.loadUserBookings();
      } catch (err) {
        UI.showToast('Error', err.message, 'error');
      }
    });
  },

  async viewBookingRoute(slotId) {
    App.navigateTo('map');
    try {
      if (window.Map3D) {
        Map3D.setPredefinedRoute('GATE-1', slotId);
      }
      const route = await API.getRoute('GATE-1', slotId, 'DIJKSTRA');
      ParkingMap.setRoute(route);
      UI.showToast('Route Loaded', `Shortest Dijkstra route to your reserved Bay ${slotId} (${route.total_distance_meters}m)`, 'info');
    } catch (err) {
      console.error(err);
    }
  },

  async loadUserVehicles() {
    const tbody = document.getElementById('user-vehicles-tbody');
    if (!tbody) return;

    try {
      const vehicles = await API.getUserVehicles();
      if (vehicles.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-muted);">No vehicles registered yet. Add one below!</td></tr>`;
        return;
      }

      tbody.innerHTML = vehicles.map(v => `
        <tr>
          <td><strong>${v.vehicle_id}</strong></td>
          <td><code>${v.vehicle_number}</code></td>
          <td><span class="badge badge-free">${v.vehicle_type}</span></td>
          <td>${v.model_name} (${v.color})</td>
          <td>${v.current_parked_slot ? `<span class="badge badge-occupied">Parked in ${v.current_parked_slot}</span>` : '<span class="badge badge-free">Available</span>'}</td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load vehicles', 'error');
    }
  },

  async handleAddUserVehicleSubmit(e) {
    e.preventDefault();
    const vData = {
      vehicle_number: document.getElementById('user-veh-plate').value.trim().toUpperCase(),
      vehicle_type: document.getElementById('user-veh-type').value,
      model_name: document.getElementById('user-veh-model').value.trim(),
      color: document.getElementById('user-veh-color').value.trim()
    };

    try {
      const res = await API.addUserVehicle(vData);
      UI.closeModal('add-user-vehicle-modal');
      UI.showToast('Vehicle Added', res.message, 'success');
      App.loadUserVehicles();
    } catch (err) {
      UI.showToast('Error', err.message, 'error');
    }
  },

  async loadUserHistory() {
    const tbody = document.getElementById('user-history-tbody');
    if (!tbody) return;

    try {
      const history = await API.getUserHistory();
      if (history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted);">No parking history records found.</td></tr>`;
        return;
      }

      tbody.innerHTML = history.map(h => `
        <tr>
          <td><strong>${h.ticket_id}</strong></td>
          <td><code>${h.vehicle_number}</code></td>
          <td><span class="badge badge-free">${h.slot_id}</span></td>
          <td>${h.entry_time}</td>
          <td>${h.exit_time || '<span class="badge badge-occupied">Active</span>'}</td>
          <td>${h.cost_charged > 0 ? `₹${h.cost_charged}` : '—'}</td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load history', 'error');
    }
  },

  // ==========================================
  // 4. ADMIN PORTAL LOGIC & LIVE MONITOR
  // ==========================================
  async loadLiveMonitor() {
    const zone = document.getElementById('monitor-zone-filter')?.value || 'ALL';
    const floor = document.getElementById('monitor-floor-filter')?.value || 'ALL';
    const vType = document.getElementById('monitor-vtype-filter')?.value || 'ALL';
    const status = document.getElementById('monitor-status-filter')?.value || 'ALL';
    const search = document.getElementById('monitor-search-input')?.value || '';

    const tbody = document.getElementById('admin-live-monitor-tbody');
    if (!tbody) return;

    try {
      const records = await API.getLiveMonitor({
        zone_id: zone,
        floor: floor,
        vehicle_type: vType,
        slot_status: status,
        search: search
      });

      if (records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-muted);">No parking records match filter criteria.</td></tr>`;
        return;
      }

      tbody.innerHTML = records.map(r => `
        <tr>
          <td><strong>${r.slot_id}</strong> <span style="font-size:11px;color:var(--text-muted);">(${r.zone_name})</span></td>
          <td>${r.floor}</td>
          <td>${UI.getStatusBadge(r.slot_status)}</td>
          <td>${r.vehicle_number ? `<code>${r.vehicle_number}</code>` : '<span style="color:var(--text-muted);">None</span>'}</td>
          <td>${r.owner_name || '<span style="color:var(--text-muted);">—</span>'}</td>
          <td>${r.ticket_id ? `<span class="badge badge-occupied">${r.ticket_id}</span>` : (r.booking_id ? `<span class="badge badge-reserved">${r.booking_id}</span>` : '—')}</td>
          <td>${r.entry_time || (r.booked_arrival ? `Booked ${r.booked_arrival}` : '—')}</td>
          <td>
            ${r.slot_status === 'OCCUPIED' ? `
              <button class="btn btn-danger btn-sm" onclick="App.handleExitClick('${r.vehicle_number}')">
                <i class="fas fa-sign-out-alt"></i> Checkout
              </button>
            ` : `
              <button class="btn btn-secondary btn-sm" onclick="App.openSlotStatusModal('${r.slot_id}', '${r.slot_status}')">
                <i class="fas fa-edit"></i> Edit
              </button>
            `}
          </td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load live monitor', 'error');
    }
  },

  async loadAdminBookings() {
    const status = document.getElementById('admin-booking-status-filter')?.value || 'ALL';
    const zone = document.getElementById('admin-booking-zone-filter')?.value || 'ALL';
    const tbody = document.getElementById('admin-bookings-tbody');
    if (!tbody) return;

    try {
      const bookings = await API.getAdminBookings(status, zone);
      if (bookings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-muted);">No customer reservations found.</td></tr>`;
        return;
      }

      tbody.innerHTML = bookings.map(b => `
        <tr>
          <td><strong>${b.booking_id}</strong></td>
          <td>${b.user_name} <span style="font-size:11px;color:var(--text-muted);">(${b.user_phone || b.user_email})</span></td>
          <td><code>${b.vehicle_number}</code> (${b.vehicle_type})</td>
          <td><span class="badge badge-free">${b.slot_id}</span></td>
          <td>${b.booking_date} at ${b.arrival_time}</td>
          <td>${b.duration_hours} hrs (₹${b.total_estimated_fee})</td>
          <td>${b.status === 'CONFIRMED' ? '<span class="badge badge-free">Confirmed</span>' : `<span class="badge badge-occupied">${b.status}</span>`}</td>
          <td>
            ${b.status === 'CONFIRMED' ? `
              <button class="btn btn-danger btn-sm" onclick="App.adminCancelBookingAction('${b.booking_id}')">
                <i class="fas fa-times"></i> Cancel
              </button>
            ` : '—'}
          </td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load admin bookings', 'error');
    }
  },

  adminCancelBookingAction(bookingId) {
    UI.confirm('Admin Cancel Booking', `Revoke and cancel reservation ${bookingId}?`, async () => {
      try {
        const res = await API.adminCancelBooking(bookingId);
        UI.showToast('Cancelled', res.message, 'success');
        App.loadAdminBookings();
      } catch (err) {
        UI.showToast('Error', err.message, 'error');
      }
    });
  },

  async loadAuditLogs() {
    const tbody = document.getElementById('audit-logs-tbody');
    if (!tbody) return;

    try {
      const logs = await API.getAuditLogs();
      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-muted);">No audit logs recorded yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = logs.map(l => `
        <tr>
          <td><span class="badge badge-accessibility">${l.action}</span></td>
          <td><strong>${l.user_id}</strong></td>
          <td>${l.target || '—'}</td>
          <td>${l.details || '—'}</td>
          <td style="font-size:11.5px;color:var(--text-muted);">${l.created_at}</td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load audit logs', 'error');
    }
  },

  // ==========================================
  // 5. EXISTING DASHBOARD & SYSTEM LOGIC
  // ==========================================
  async loadDashboard() {
    try {
      const data = await API.getDashboard();

      document.getElementById('kpi-total-slots').innerText = data.total_slots;
      document.getElementById('kpi-free-slots').innerText = data.free_slots;
      document.getElementById('kpi-occupied-slots').innerText = data.occupied_slots;
      document.getElementById('kpi-reserved-slots').innerText = data.reserved_slots;
      document.getElementById('kpi-occupancy-pct').innerText = `${data.occupancy_percentage}%`;
      document.getElementById('kpi-queue-count').innerText = data.priority_queue_count + data.normal_queue_count;

      const queueBadge = document.getElementById('nav-queue-badge');
      if (queueBadge) queueBadge.innerText = data.priority_queue_count + data.normal_queue_count;

      UI.drawDonutChart('occupancy-chart-canvas', [
        { value: data.free_slots, color: '#10b981' },
        { value: data.occupied_slots, color: '#ef4444' },
        { value: data.reserved_slots, color: '#f59e0b' },
        { value: data.blocked_slots, color: '#64748b' }
      ], `${data.occupancy_percentage}%`);

      const zoneContainer = document.getElementById('dashboard-zone-cards');
      if (zoneContainer) {
        zoneContainer.innerHTML = (data.zone_statistics || []).map(z => `
          <div class="card" style="padding:14px; cursor:pointer;" onclick="App.filterSlotsByZone('${z.zone_id}')">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <strong style="font-size:14px;">${z.name}</strong>
              <span class="badge badge-free">${z.allowed_type}</span>
            </div>
            <div style="font-size:12px;color:var(--text-secondary);margin:6px 0;">${z.floor} • ₹${z.hourly_rate}/hr</div>
            <div style="display:flex;gap:12px;font-size:13px;margin-top:8px;">
              <div>Free: <strong style="color:var(--status-free);">${z.free || 0}</strong></div>
              <div>Occupied: <strong style="color:var(--status-occupied);">${z.occupied || 0}</strong></div>
              <div>Total: <strong>${z.total || 0}</strong></div>
            </div>
          </div>
        `).join('');
      }

      const historyTbody = document.getElementById('dashboard-history-tbody');
      if (historyTbody) {
        if (!data.recent_activities || data.recent_activities.length === 0) {
          historyTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No recent activity.</td></tr>`;
        } else {
          historyTbody.innerHTML = data.recent_activities.map(h => `
            <tr>
              <td><strong>${h.ticket_id}</strong></td>
              <td><code>${h.vehicle_number}</code></td>
              <td><span class="badge badge-free">${h.slot_id}</span></td>
              <td>${h.entry_time.split(' ')[1]}</td>
              <td>${h.exit_time ? h.exit_time.split(' ')[1] : '<span class="badge badge-occupied">Active</span>'}</td>
              <td>${h.cost_charged > 0 ? `₹${h.cost_charged}` : '—'}</td>
            </tr>
          `).join('');
        }
      }

      const undoBtn = document.getElementById('undo-btn');
      if (undoBtn) {
        undoBtn.disabled = !data.undo_available;
      }
    } catch (err) {
      console.error('Dashboard load failed:', err);
    }
  },

  filterSlotsByZone(zoneId) {
    document.getElementById('slots-zone-filter').value = zoneId;
    this.navigateTo('slots');
  },

  async loadMap() {
    try {
      const [slots, graph] = await Promise.all([
        API.getSlots('ALL', 'ALL'),
        API.getGraph()
      ]);
      ParkingMap.setData(slots, graph);
      if (window.Map3D) {
        if (!Map3D.isInitialized) {
          Map3D.init();
        } else if (Map3D.map) {
          Map3D.slots = slots;
          Map3D.graphData = graph;
          Map3D.addParkingSlotsLayer();
          Map3D.map.resize();
        }
      }
    } catch (err) {
      UI.showToast('Error', 'Failed to load map data', 'error');
    }
  },

  handleMapSlotClick(slot) {
    if (this.currentRole === 'USER') {
      if (slot.status === 'FREE') {
        App.openAdvanceBookingModal(slot.slot_id, slot.zone_id, slot.vehicle_type, new Date().toISOString().split('T')[0], '10:00', 2);
      } else {
        UI.showToast('Slot Info', `Slot ${slot.slot_id} is currently ${slot.status}`, 'info');
      }
    } else {
      if (slot.status === 'FREE') {
        document.getElementById('park-vehicle-type').value = slot.vehicle_type;
        App.navigateTo('park');
      } else if (slot.status === 'OCCUPIED') {
        UI.confirm('Process Exit', `Process exit and generate checkout for Slot ${slot.slot_id}?`, async () => {
          try {
            const res = await API.processExit(slot.slot_id);
            UI.showToast('Checkout Complete', `Vehicle ${res.vehicle_number} exited. Fee: ₹${res.total_fee}`, 'success');
            App.loadMap();
          } catch (err) {
            UI.showToast('Error', err.message, 'error');
          }
        });
      }
    }
  },

  async loadSlots() {
    const zoneFilter = document.getElementById('slots-zone-filter')?.value || 'ALL';
    const statusFilter = document.getElementById('slots-status-filter')?.value || 'ALL';
    const container = document.getElementById('slots-grid-container');
    if (!container) return;

    try {
      const slots = await API.getSlots(zoneFilter, statusFilter);
      if (slots.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No parking slots match the selected filters.</div>`;
        return;
      }

      container.innerHTML = slots.map(s => `
        <div class="slot-box ${s.status.toLowerCase()}">
          <div class="slot-id">${s.slot_id}</div>
          <i class="fas ${s.vehicle_type === '2W' ? 'fa-motorcycle' : 'fa-car-side'} slot-icon"></i>
          <div style="font-size:11px;color:var(--text-muted);">${s.zone_name || s.zone_id} • ${s.distance_from_gate}m</div>
          <div style="margin-top:4px;">${UI.getStatusBadge(s.status)}</div>
          ${s.vehicle_number ? `<div style="font-size:11px;font-weight:700;color:#38bdf8;margin-top:4px;">${s.vehicle_number}</div>` : ''}
          <div style="margin-top:8px;display:flex;gap:4px;">
            <button class="btn btn-secondary btn-sm" onclick="App.openSlotStatusModal('${s.slot_id}', '${s.status}')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-secondary btn-sm" onclick="App.deleteSlotConfirm('${s.slot_id}')">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load slots', 'error');
    }
  },

  openSlotStatusModal(slotId, currentStatus) {
    document.getElementById('edit-slot-id-hidden').value = slotId;
    document.getElementById('edit-slot-id-label').innerText = slotId;
    document.getElementById('edit-slot-status-select').value = currentStatus;
    UI.openModal('edit-slot-modal');
  },

  deleteSlotConfirm(slotId) {
    UI.confirm('Delete Slot', `Are you sure you want to delete Slot ${slotId}?`, async () => {
      try {
        await API.deleteSlot(slotId);
        UI.showToast('Slot Deleted', `Slot ${slotId} was deleted successfully.`, 'success');
        App.loadSlots();
      } catch (err) {
        UI.showToast('Error', err.message, 'error');
      }
    });
  },

  async loadVehicles() {
    const tbody = document.getElementById('vehicles-table-tbody');
    if (!tbody) return;

    try {
      const vehicles = await API.getVehicles();
      if (vehicles.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:24px;">No registered vehicles found.</td></tr>`;
        return;
      }

      tbody.innerHTML = vehicles.map(v => `
        <tr>
          <td><strong>${v.vehicle_id}</strong></td>
          <td><code>${v.vehicle_number}</code></td>
          <td><span class="badge badge-free">${v.vehicle_type}</span></td>
          <td>${v.owner_name} <span style="font-size:11px;color:var(--text-muted);">(${v.role})</span></td>
          <td>${v.model_name} <span style="font-size:11px;color:var(--text-muted);">(${v.color})</span></td>
          <td>${v.current_parked_slot ? `<span class="badge badge-occupied">${v.current_parked_slot}</span>` : '<span class="badge badge-free">Not Parked</span>'}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="App.quickParkVehicle('${v.vehicle_number}', '${v.vehicle_type}')">
              <i class="fas fa-parking"></i> Park
            </button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load vehicles', 'error');
    }
  },

  quickParkVehicle(plate, type) {
    document.getElementById('park-vehicle-number').value = plate;
    document.getElementById('park-vehicle-type').value = type;
    App.navigateTo('park');
  },

  loadParkView() {},

  async handleSmartAllocationSubmit(e) {
    e.preventDefault();
    const plate = document.getElementById('park-vehicle-number').value.trim().toUpperCase();
    const vType = document.getElementById('park-vehicle-type').value;
    const priority = document.getElementById('park-priority-level').value;
    const gate = document.getElementById('park-entry-gate').value;

    const resultBox = document.getElementById('allocation-result-box');
    resultBox.innerHTML = `<div style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin"></i> Running Greedy Candidate Evaluation & Dijkstra Navigation...</div>`;

    try {
      const reqRes = await API.submitRequest({
        vehicle_number: plate,
        vehicle_type: vType,
        priority_level: priority,
        entry_gate: gate
      });

      const allocRes = await API.allocateRequest(reqRes.request_id);

      resultBox.innerHTML = `
        <div class="card" style="border-left: 4px solid var(--status-free); background: rgba(16, 185, 129, 0.05);">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h3 style="color:var(--status-free);font-size:18px;">
              <i class="fas fa-check-circle"></i> Allocation Successful!
            </h3>
            <span class="badge badge-free">${allocRes.assigned_slot.slot_id}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;font-size:13.5px;">
            <div>Ticket ID: <strong>${allocRes.ticket_id}</strong></div>
            <div>Assigned Zone: <strong>${allocRes.assigned_slot.zone_id}</strong></div>
            <div>Vehicle Number: <code>${allocRes.vehicle_number}</code></div>
            <div>Distance from ${gate}: <strong>${allocRes.assigned_slot.distance_from_gate} meters</strong></div>
          </div>
          <div class="dsa-explain-box">
            <div class="dsa-explain-title"><i class="fas fa-microchip"></i> DSA Allocation Decision</div>
            <div>${allocRes.dsa_decision_trace.reason}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
              Algorithm: ${allocRes.dsa_decision_trace.algorithm} | Priority Level: ${allocRes.priority_level}
            </div>
          </div>
          <div style="margin-top:16px;">
            <button class="btn btn-primary btn-sm" onclick="App.viewAllocationOnMap('${allocRes.assigned_slot.slot_id}', '${gate}')">
              <i class="fas fa-map-marked-alt"></i> View Dijkstra Driving Route on 2D Map
            </button>
          </div>
        </div>
      `;

      UI.showToast('Allocated', `Vehicle ${plate} assigned to Slot ${allocRes.assigned_slot.slot_id}`, 'success');
    } catch (err) {
      resultBox.innerHTML = `
        <div class="card" style="border-left: 4px solid var(--status-occupied); background: rgba(239, 68, 68, 0.05);">
          <h3 style="color:var(--status-occupied);font-size:16px;"><i class="fas fa-times-circle"></i> Allocation Failed</h3>
          <p style="margin-top:8px;font-size:13px;">${err.message}</p>
        </div>
      `;
      UI.showToast('Allocation Error', err.message, 'error');
    }
  },

  async viewAllocationOnMap(slotId, gate) {
    App.navigateTo('map');
    try {
      if (window.Map3D) {
        Map3D.setPredefinedRoute(gate, slotId);
      }
      const route = await API.getRoute(gate, slotId, 'DIJKSTRA');
      ParkingMap.setRoute(route);
      UI.showToast('Navigation Loaded', `Shortest route from ${gate} to ${slotId} (${route.total_distance_meters}m)`, 'info');
    } catch (err) {
      console.error('Failed to route:', err);
    }
  },

  async loadRequests() {
    try {
      const data = await API.getRequests();

      const pqTbody = document.getElementById('priority-queue-tbody');
      if (pqTbody) {
        if (!data.priority_queue || data.priority_queue.length === 0) {
          pqTbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No high-priority requests queued.</td></tr>`;
        } else {
          pqTbody.innerHTML = data.priority_queue.map((req, idx) => `
            <tr>
              <td>#${idx + 1}</td>
              <td><strong>${req.request_id}</strong></td>
              <td><code>${req.vehicle_number}</code></td>
              <td>${UI.getPriorityBadge(req.priority_level)}</td>
              <td>
                <button class="btn btn-primary btn-sm" onclick="App.allocateSpecificRequest('${req.request_id}')">
                  <i class="fas fa-play"></i> Allocate Now
                </button>
              </td>
            </tr>
          `).join('');
        }
      }

      const nqTbody = document.getElementById('normal-queue-tbody');
      if (nqTbody) {
        if (!data.normal_queue || data.normal_queue.length === 0) {
          nqTbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">Normal FIFO queue is empty.</td></tr>`;
        } else {
          nqTbody.innerHTML = data.normal_queue.map((req, idx) => `
            <tr>
              <td>#${idx + 1}</td>
              <td><strong>${req.request_id}</strong></td>
              <td><code>${req.vehicle_number}</code></td>
              <td><span class="badge badge-free">${req.vehicle_type}</span></td>
              <td>
                <button class="btn btn-primary btn-sm" onclick="App.allocateSpecificRequest('${req.request_id}')">
                  <i class="fas fa-play"></i> Allocate
                </button>
              </td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      UI.showToast('Error', 'Failed to load queues', 'error');
    }
  },

  async allocateSpecificRequest(reqId) {
    try {
      const res = await API.allocateRequest(reqId);
      UI.showToast('Allocated', `Assigned Slot ${res.assigned_slot.slot_id} to ${res.vehicle_number}`, 'success');
      App.loadRequests();
    } catch (err) {
      UI.showToast('Error', err.message, 'error');
    }
  },

  async processNextQueueHead() {
    try {
      const res = await API.allocateRequest();
      UI.showToast('Request Processed', `Allocated Slot ${res.assigned_slot.slot_id} to ${res.vehicle_number}`, 'success');
      App.loadRequests();
    } catch (err) {
      UI.showToast('Queue Notice', err.message, 'warning');
    }
  },

  async loadEntryExit() {
    const activeTbody = document.getElementById('active-parked-tbody');
    const historyTbody = document.getElementById('all-history-tbody');

    try {
      const records = await API.getHistory();
      const active = records.filter(r => r.status === 'ACTIVE');
      const completed = records.filter(r => r.status === 'COMPLETED');

      if (activeTbody) {
        if (active.length === 0) {
          activeTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No vehicles currently parked.</td></tr>`;
        } else {
          activeTbody.innerHTML = active.map(r => `
            <tr>
              <td><strong>${r.ticket_id}</strong></td>
              <td><code>${r.vehicle_number}</code></td>
              <td><span class="badge badge-free">${r.slot_id}</span></td>
              <td>${r.zone_name || r.zone_id}</td>
              <td>${r.entry_time}</td>
              <td><span class="badge badge-occupied">Active</span></td>
              <td>
                <button class="btn btn-danger btn-sm" onclick="App.handleExitClick('${r.vehicle_number}')">
                  <i class="fas fa-sign-out-alt"></i> Checkout & Exit
                </button>
              </td>
            </tr>
          `).join('');
        }
      }

      if (historyTbody) {
        if (completed.length === 0) {
          historyTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No completed sessions yet.</td></tr>`;
        } else {
          historyTbody.innerHTML = completed.map(r => `
            <tr>
              <td><strong>${r.ticket_id}</strong></td>
              <td><code>${r.vehicle_number}</code></td>
              <td><span class="badge badge-free">${r.slot_id}</span></td>
              <td>${r.entry_time}</td>
              <td>${r.exit_time}</td>
              <td>${r.duration_minutes} mins</td>
              <td><strong>₹${r.cost_charged}</strong></td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      UI.showToast('Error', 'Failed to load parking history', 'error');
    }
  },

  handleExitClick(identifier) {
    UI.confirm('Vehicle Exit Checkout', `Generate invoice and checkout vehicle ${identifier}?`, async () => {
      try {
        const res = await API.processExit(identifier);
        UI.showToast('Checkout Complete', `Vehicle ${res.vehicle_number} checked out. Duration: ${res.duration_formatted} • Total Fee: ₹${res.total_fee}`, 'success');
        if (App.currentView === 'entry-exit') App.loadEntryExit();
        if (App.currentView === 'live-monitor') App.loadLiveMonitor();
      } catch (err) {
        UI.showToast('Error', err.message, 'error');
      }
    });
  },

  async loadNavigation() {
    try {
      const graph = await API.getGraph();
      const startSelect = document.getElementById('nav-start-select');
      const endSelect = document.getElementById('nav-end-select');

      if (startSelect && endSelect) {
        const optionsHtml = (graph.nodes || []).map(n => `<option value="${n.id}">${n.label} (${n.id})</option>`).join('');
        startSelect.innerHTML = optionsHtml;
        endSelect.innerHTML = optionsHtml;

        startSelect.value = 'GATE-1';
        endSelect.value = 'A-01';
      }

      const lanesList = document.getElementById('lanes-toggle-list');
      if (lanesList) {
        lanesList.innerHTML = (graph.edges || []).map(e => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
            <div>
              <strong>${e.lane_name}</strong>
              <div style="font-size:11px;color:var(--text-muted);">${e.from} <-> ${e.to} (${e.weight}m)</div>
            </div>
            <button class="btn btn-sm ${e.is_blocked ? 'btn-danger' : 'btn-secondary'}" onclick="App.toggleLaneBlock('${e.from}', '${e.to}', ${!e.is_blocked})">
              ${e.is_blocked ? '<i class="fas fa-lock"></i> Blocked' : '<i class="fas fa-lock-open"></i> Open'}
            </button>
          </div>
        `).join('');
      }
    } catch (err) {
      UI.showToast('Error', 'Failed to load navigation graph', 'error');
    }
  },

  async runNavigationCompare() {
    const start = document.getElementById('nav-start-select').value;
    const end = document.getElementById('nav-end-select').value;
    const container = document.getElementById('nav-compare-results');
    if (!container) return;

    container.innerHTML = `<div style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin"></i> Calculating Dijkstra, BFS and DFS paths...</div>`;

    try {
      const res = await API.compareRoutes(start, end);
      const d = res.dijkstra;
      const b = res.bfs;
      const f = res.dfs;

      container.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">
          <!-- Dijkstra -->
          <div class="card" style="border-left:4px solid #38bdf8;">
            <div class="card-title"><i class="fas fa-route"></i> Dijkstra's Algorithm</div>
            <div style="font-size:12px;color:var(--text-secondary);margin:4px 0;">Shortest Weighted Physical Distance</div>
            <div style="margin-top:12px;font-size:13px;display:flex;flex-direction:column;gap:6px;">
              <div>Status: ${d.success ? '<span class="badge badge-free">Optimal Route</span>' : '<span class="badge badge-occupied">No Route</span>'}</div>
              <div>Total Distance: <strong>${d.total_distance_meters || '—'} meters</strong></div>
              <div>Hop Count: <strong>${d.hop_count || '—'}</strong></div>
              <div>Operations (Heap + Edge Relax): <strong>${d.operations_count || 0}</strong></div>
              <div>Path: <code>${d.path ? d.path.join(' ➔ ') : 'None'}</code></div>
              <div>Complexity: <code>${d.complexity || 'O((V+E) log V)'}</code></div>
            </div>
          </div>

          <!-- BFS -->
          <div class="card" style="border-left:4px solid #10b981;">
            <div class="card-title"><i class="fas fa-project-diagram"></i> Breadth-First Search (BFS)</div>
            <div style="font-size:12px;color:var(--text-secondary);margin:4px 0;">Minimum Hop Count (Unweighted)</div>
            <div style="margin-top:12px;font-size:13px;display:flex;flex-direction:column;gap:6px;">
              <div>Status: ${b.success ? '<span class="badge badge-free">Minimum Hops</span>' : '<span class="badge badge-occupied">No Route</span>'}</div>
              <div>Total Distance: <strong>${b.total_distance || '—'} meters</strong></div>
              <div>Hop Count: <strong>${b.hop_count || '—'}</strong></div>
              <div>Operations (Queue Visits): <strong>${b.operations_count || 0}</strong></div>
              <div>Path: <code>${b.path ? b.path.join(' ➔ ') : 'None'}</code></div>
              <div>Complexity: <code>${b.complexity || 'O(V + E)'}</code></div>
            </div>
          </div>

          <!-- DFS -->
          <div class="card" style="border-left:4px solid #f59e0b;">
            <div class="card-title"><i class="fas fa-sitemap"></i> Depth-First Search (DFS)</div>
            <div style="font-size:12px;color:var(--text-secondary);margin:4px 0;">Recursive Path Exploration</div>
            <div style="margin-top:12px;font-size:13px;display:flex;flex-direction:column;gap:6px;">
              <div>Status: ${f.success ? '<span class="badge badge-reserved">Explored Path</span>' : '<span class="badge badge-occupied">No Route</span>'}</div>
              <div>Total Distance: <strong>${f.total_distance || '—'} meters</strong></div>
              <div>Hop Count: <strong>${f.hop_count || '—'}</strong></div>
              <div>Operations (Recursive Calls): <strong>${f.operations_count || 0}</strong></div>
              <div>Path: <code>${f.path ? f.path.join(' ➔ ') : 'None'}</code></div>
              <div>Complexity: <code>${f.complexity || 'O(V + E)'}</code></div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      UI.showToast('Error', err.message, 'error');
    }
  },

  async toggleLaneBlock(u, v, isBlocked) {
    try {
      const res = await API.toggleLane(u, v, isBlocked);
      UI.showToast('Lane Updated', res.message, 'info');
      App.loadNavigation();
      App.loadMap();
    } catch (err) {
      UI.showToast('Error', err.message, 'error');
    }
  },

  loadSearch() {
    const input = document.getElementById('multi-search-input');
    if (input) input.focus();
  },

  async executeMultiSearch() {
    const query = document.getElementById('multi-search-input')?.value.trim();
    const container = document.getElementById('search-benchmarks-container');
    if (!query || !container) return;

    container.innerHTML = `<div style="text-align:center;padding:24px;"><i class="fas fa-spinner fa-spin"></i> Searching across Hash Table, AVL Tree, BST, Binary Search, and Linear Search...</div>`;

    try {
      const res = await API.search(query);
      
      let html = '';
      if (!res.found) {
        html += `
          <div class="card" style="border-left:4px solid var(--status-occupied);margin-bottom:16px;">
            <strong>No Match Found</strong> for query "${query}". Evaluated across all 5 index structures.
          </div>
        `;
      } else {
        const item = res.result_data;
        html += `
          <div class="card" style="border-left:4px solid var(--status-free);margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <h3 style="color:var(--status-free);font-size:16px;"><i class="fas fa-check-circle"></i> Record Located</h3>
              <span class="badge badge-free">${item.type}</span>
            </div>
            <div style="margin-top:10px;font-size:13px;display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:8px;">
              ${Object.entries(item.data).map(([k, v]) => `<div><span style="color:var(--text-muted);">${k}:</span> <strong>${v || '—'}</strong></div>`).join('')}
            </div>
          </div>
        `;
      }

      html += `<div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">`;
      res.benchmarks.forEach(b => {
        html += `
          <div class="card">
            <div class="card-title" style="font-size:14.5px;">${b.structure}</div>
            <div style="margin:12px 0;display:flex;flex-direction:column;gap:6px;font-size:13px;">
              <div>Execution Time: <strong style="color:#38bdf8;">${b.time_microseconds} µs</strong></div>
              <div>Comparisons: <strong>${b.comparisons}</strong></div>
              <div>Best: <code>${b.theoretical_best}</code> | Avg: <code>${b.theoretical_average}</code> | Worst: <code>${b.theoretical_worst}</code></div>
              <div style="font-size:11.5px;color:var(--text-muted);margin-top:4px;">${b.diagnostic}</div>
            </div>
          </div>
        `;
      });
      html += `</div>`;

      container.innerHTML = html;
    } catch (err) {
      UI.showToast('Error', err.message, 'error');
    }
  },

  async loadReports() {
    try {
      const data = await API.getReports();
      const s = data.summary;

      document.getElementById('report-total-tickets').innerText = s.total_tickets;
      document.getElementById('report-completed-tickets').innerText = s.completed_tickets;
      document.getElementById('report-avg-duration').innerText = `${s.avg_duration_minutes}m`;
      document.getElementById('report-total-revenue').innerText = `₹${s.total_revenue}`;

      const hours = (data.hourly_traffic || []).map(h => `${h.hour}:00`);
      const counts = (data.hourly_traffic || []).map(h => h.count);
      UI.drawBarChart('hourly-traffic-chart', hours.length ? hours : ['09:00', '10:00', '11:00'], counts.length ? counts : [4, 8, 3], '#60a5fa');

      const zTbody = document.getElementById('report-zone-tbody');
      if (zTbody) {
        zTbody.innerHTML = (data.zone_occupancy || []).map(z => `
          <tr>
            <td><strong>${z.name}</strong></td>
            <td>${z.capacity}</td>
            <td>${z.occupied || 0}</td>
            <td><strong>${z.capacity > 0 ? Math.round(((z.occupied || 0) / z.capacity) * 100) : 0}%</strong></td>
          </tr>
        `).join('');
      }
    } catch (err) {
      UI.showToast('Error', 'Failed to load reports', 'error');
    }
  },

  async loadDsaGuide() {
    const container = document.getElementById('dsa-guide-container');
    if (!container) return;

    try {
      const data = await API.getDsaDocs();
      container.innerHTML = (data.structures || []).map(s => `
        <div class="card" style="margin-bottom:16px;border-left:4px solid #8b5cf6;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h3 style="font-size:16px;color:#c4b5fd;">
              <i class="fas fa-cube"></i> ${s.name}
            </h3>
            <span class="badge badge-accessibility">${s.module}</span>
          </div>
          <p style="margin:8px 0;font-size:13px;color:var(--text-secondary);">${s.description}</p>
          <div style="background:rgba(0,0,0,0.2);padding:10px 14px;border-radius:var(--radius-sm);margin:10px 0;font-size:12.5px;">
            <strong>Time Complexity:</strong> ${s.time_complexity || `Access: ${s.time_access} | Search: ${s.time_search} | Insert: ${s.time_insert} | Delete: ${s.time_delete}`} • <strong>Space:</strong> ${s.space_complexity || s.space}
          </div>
          <div style="font-size:12.5px;color:#93c5fd;">
            <strong>Why Used in Smart Parking:</strong> ${s.why_used}
          </div>
        </div>
      `).join('');
    } catch (err) {
      UI.showToast('Error', 'Failed to load DSA documentation', 'error');
    }
  },

  // ==========================================
  // 6. GLOBAL FORMS & ACTIONS
  // ==========================================
  bindForms() {
    // Add Slot Form
    const addSlotForm = document.getElementById('add-slot-form');
    if (addSlotForm) {
      addSlotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const slotData = {
          slot_id: document.getElementById('slot-id-input').value,
          zone_id: document.getElementById('slot-zone-input').value,
          vehicle_type: document.getElementById('slot-vtype-input').value,
          distance_from_gate: parseFloat(document.getElementById('slot-dist-input').value),
          priority: document.getElementById('slot-priority-input').value,
          pos_x: parseFloat(document.getElementById('slot-posx-input').value || 100),
          pos_y: parseFloat(document.getElementById('slot-posy-input').value || 100)
        };
        try {
          await API.addSlot(slotData);
          UI.closeModal('add-slot-modal');
          UI.showToast('Slot Added', `Slot ${slotData.slot_id} created.`, 'success');
          App.loadSlots();
        } catch (err) {
          UI.showToast('Error', err.message, 'error');
        }
      });
    }

    // Edit Slot Status Form
    const editSlotForm = document.getElementById('edit-slot-form');
    if (editSlotForm) {
      editSlotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const slotId = document.getElementById('edit-slot-id-hidden').value;
        const newStatus = document.getElementById('edit-slot-status-select').value;
        try {
          await API.updateSlotStatus(slotId, newStatus);
          UI.closeModal('edit-slot-modal');
          UI.showToast('Status Updated', `Slot ${slotId} is now ${newStatus}`, 'success');
          if (App.currentView === 'slots') App.loadSlots();
          if (App.currentView === 'live-monitor') App.loadLiveMonitor();
        } catch (err) {
          UI.showToast('Error', err.message, 'error');
        }
      });
    }

    // Register Vehicle Form (Admin)
    const regVehForm = document.getElementById('register-vehicle-form');
    if (regVehForm) {
      regVehForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const vData = {
          vehicle_number: document.getElementById('reg-plate-input').value,
          vehicle_type: document.getElementById('reg-vtype-input').value,
          owner_name: document.getElementById('reg-owner-input').value,
          model_name: document.getElementById('reg-model-input').value,
          color: document.getElementById('reg-color-input').value
        };
        try {
          const res = await API.registerVehicle(vData);
          UI.closeModal('register-vehicle-modal');
          UI.showToast('Vehicle Registered', `Vehicle ${vData.vehicle_number} registered (${res.vehicle_id})`, 'success');
          App.loadVehicles();
        } catch (err) {
          UI.showToast('Error', err.message, 'error');
        }
      });
    }

    // User Add Vehicle Form
    const userAddVehForm = document.getElementById('add-user-vehicle-form');
    if (userAddVehForm) {
      userAddVehForm.addEventListener('submit', (e) => this.handleAddUserVehicleSubmit(e));
    }

    // Advance Booking Form
    const advBkgForm = document.getElementById('advance-booking-form');
    if (advBkgForm) {
      advBkgForm.addEventListener('submit', (e) => this.handleAdvanceBookingSubmit(e));
    }

    // Smart Park Allocation Form
    const parkForm = document.getElementById('smart-park-form');
    if (parkForm) {
      parkForm.addEventListener('submit', (e) => this.handleSmartAllocationSubmit(e));
    }
  },

  bindGlobalActions() {
    // Undo button
    const undoBtn = document.getElementById('undo-btn');
    if (undoBtn) {
      undoBtn.addEventListener('click', async () => {
        try {
          const res = await API.undoLastAction();
          UI.showToast('Action Undone', res.message, 'success');
          App.loadDashboard();
          App.loadSlots();
        } catch (err) {
          UI.showToast('Undo Notice', err.message, 'warning');
        }
      });
    }

    // Patrol Zone button
    const patrolBtn = document.getElementById('patrol-zone-btn');
    if (patrolBtn) {
      patrolBtn.addEventListener('click', async () => {
        try {
          const res = await API.inspectNextZone();
          UI.showToast('CLL Zone Patrol', `Inspected ${res.zone_name} (${res.floor}) • Free: ${res.live_counts.free}/${res.live_counts.total}`, 'info');
        } catch (err) {
          UI.showToast('Error', err.message, 'error');
        }
      });
    }

    // Reset Database Seed
    const resetBtn = document.getElementById('reset-seed-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        UI.confirm('Reset Seed Data', 'Reset database to default college mini-project seed state?', async () => {
          try {
            await API.resetSeed();
            UI.showToast('Reset Complete', 'System restored to pristine seed dataset.', 'success');
            if (App.currentRole === 'ADMIN') {
              App.loadDashboard();
              App.loadSlots();
              App.loadVehicles();
            } else {
              App.loadUserOverview();
            }
          } catch (err) {
            UI.showToast('Error', err.message, 'error');
          }
        });
      });
    }
  },

  // ==========================================
  // MOBILE APP & SERVER CONFIGURATION
  // ==========================================
  setServerPreset(preset) {
    const inp = document.getElementById('server-url-input');
    if (!inp) return;
    if (preset === 'emulator') {
      inp.value = 'http://10.0.2.2:8000';
    } else if (preset === 'localhost') {
      inp.value = 'http://localhost:8000';
    } else if (preset === 'sameorigin') {
      inp.value = '';
    }
  },

  async testServerConnection() {
    const inp = document.getElementById('server-url-input');
    const resBox = document.getElementById('server-ping-result');
    const target = inp ? inp.value.trim() : '';
    if (resBox) {
      resBox.style.display = 'block';
      resBox.style.background = '#eff6ff';
      resBox.style.color = '#1d4ed8';
      resBox.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting to ' + (target || 'same origin') + '...';
    }
    const res = await API.pingServer(target);
    if (resBox) {
      if (res.success) {
        resBox.style.background = '#ecfdf5';
        resBox.style.color = '#065f46';
        resBox.innerHTML = '<i class="fas fa-check-circle"></i> ' + res.message;
      } else {
        resBox.style.background = '#fef2f2';
        resBox.style.color = '#991b1b';
        resBox.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + res.message;
      }
    }
  },

  saveServerConfig() {
    const inp = document.getElementById('server-url-input');
    const url = inp ? inp.value.trim() : '';
    API.setBaseUrl(url);
    UI.closeModal('server-config-modal');
    UI.showToast('Server Updated', `Backend API URL saved: ${url || 'Same origin (default)'}`, 'success');
    if (App.currentRole === 'ADMIN') {
      App.loadDashboard();
    } else if (App.currentRole === 'USER') {
      App.loadUserOverview();
    }
  },

  setupNativeMobileFeatures() {
    // Android Back Button handler via Capacitor
    if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
      window.Capacitor.Plugins.App.addListener('backButton', ({ canGoBack }) => {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('open')) {
          UI.closeMobileMenu();
          return;
        }
        const activeModals = document.querySelectorAll('.modal-backdrop.active');
        if (activeModals.length > 0) {
          activeModals[activeModals.length - 1].classList.remove('active');
          return;
        }
        if (window.history.length > 1) {
          window.history.back();
        } else {
          window.Capacitor.Plugins.App.exitApp();
        }
      });
    }
  }
};

// Global startup
window.App = App;
document.addEventListener('DOMContentLoaded', () => {
  App.init();
  App.setupNativeMobileFeatures();
});
