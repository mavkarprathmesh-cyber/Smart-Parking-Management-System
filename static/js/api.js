/**
 * API Client Module with Bearer Token Authorization & RBAC
 */

const API = {
  baseUrl: '',

  getToken() {
    return localStorage.getItem('smartpark_token') || sessionStorage.getItem('smartpark_token') || '';
  },

  setToken(token, remember = true) {
    if (remember) {
      localStorage.setItem('smartpark_token', token);
    } else {
      sessionStorage.setItem('smartpark_token', token);
    }
  },

  clearToken() {
    localStorage.removeItem('smartpark_token');
    sessionStorage.removeItem('smartpark_token');
    localStorage.removeItem('smartpark_user');
  },

  getUser() {
    try {
      const u = localStorage.getItem('smartpark_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem('smartpark_user', JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers
        }
      });

      const data = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          this.clearToken();
          if (window.App && typeof window.App.showAuthScreen === 'function') {
            window.App.showAuthScreen();
          }
        }
        throw new Error(data.detail || data.error || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on [${endpoint}]:`, err);
      throw err;
    }
  },

  // ==========================================
  // AUTHENTICATION
  // ==========================================
  login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  register(userData) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  verifyEmail(email, code) {
    return this.request('/api/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ email, code })
    });
  },

  forgotPassword(email) {
    return this.request('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  },

  resetPassword(email, resetCode, newPassword) {
    return this.request('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ email, reset_code: resetCode, new_password: newPassword })
    });
  },

  getProfile() {
    return this.request('/api/auth/me');
  },

  logout() {
    const p = this.request('/api/auth/logout', { method: 'POST' });
    this.clearToken();
    return p;
  },

  // ==========================================
  // USER PORTAL & ADVANCE BOOKINGS
  // ==========================================
  findSlots(zoneId, vehicleType, bookingDate, arrivalTime, durationHours) {
    return this.request(
      `/api/user/find-slots?zone_id=${zoneId}&vehicle_type=${vehicleType}&booking_date=${bookingDate}&arrival_time=${arrivalTime}&duration_hours=${durationHours}`
    );
  },

  bookSlot(bookingData) {
    return this.request('/api/user/book-slot', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
  },

  getUserBookings() {
    return this.request('/api/user/bookings');
  },

  cancelUserBooking(bookingId) {
    return this.request(`/api/user/bookings/${bookingId}/cancel`, { method: 'POST' });
  },

  getUserVehicles() {
    return this.request('/api/user/vehicles');
  },

  addUserVehicle(vehicleData) {
    return this.request('/api/user/vehicles', {
      method: 'POST',
      body: JSON.stringify(vehicleData)
    });
  },

  getUserHistory() {
    return this.request('/api/user/history');
  },

  // ==========================================
  // ADMIN MONITORING & CONTROLS
  // ==========================================
  getLiveMonitor(filters = {}) {
    const q = new URLSearchParams(filters).toString();
    return this.request(`/api/admin/live-monitor?${q}`);
  },

  getBlockSummary() {
    return this.request('/api/admin/block-summary');
  },

  getAdminBookings(status = 'ALL', zoneId = 'ALL') {
    return this.request(`/api/admin/bookings?status=${status}&zone_id=${zoneId}`);
  },

  adminCancelBooking(bookingId) {
    return this.request(`/api/admin/bookings/${bookingId}/cancel`, { method: 'POST' });
  },

  getAuditLogs() {
    return this.request('/api/admin/audit-logs');
  },

  // ==========================================
  // CORE PARKING, DSA & SYSTEM
  // ==========================================
  getDashboard() {
    return this.request('/api/dashboard');
  },

  getSlots(zoneId = 'ALL', status = 'ALL') {
    return this.request(`/api/slots?zone_id=${zoneId}&status=${status}`);
  },

  getSlotById(slotId) {
    return this.request(`/api/slots/${slotId}`);
  },

  addSlot(slotData) {
    return this.request('/api/slots', {
      method: 'POST',
      body: JSON.stringify(slotData)
    });
  },

  updateSlotStatus(slotId, status) {
    return this.request(`/api/slots/${slotId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
  },

  deleteSlot(slotId) {
    return this.request(`/api/slots/${slotId}`, {
      method: 'DELETE'
    });
  },

  getVehicles() {
    return this.request('/api/vehicles');
  },

  registerVehicle(vData) {
    return this.request('/api/vehicles', {
      method: 'POST',
      body: JSON.stringify(vData)
    });
  },

  getRequests() {
    return this.request('/api/requests');
  },

  submitRequest(reqData) {
    return this.request('/api/requests', {
      method: 'POST',
      body: JSON.stringify(reqData)
    });
  },

  allocateRequest(requestId = null) {
    return this.request('/api/requests/allocate', {
      method: 'POST',
      body: JSON.stringify({ request_id: requestId })
    });
  },

  processExit(identifier) {
    return this.request('/api/entry-exit/exit', {
      method: 'POST',
      body: JSON.stringify({ identifier })
    });
  },

  getHistory() {
    return this.request('/api/entry-exit/history');
  },

  search(query) {
    return this.request(`/api/search?q=${encodeURIComponent(query)}`);
  },

  getGraph() {
    return this.request('/api/navigation/graph');
  },

  getRoute(start, destination, algorithm = 'DIJKSTRA') {
    return this.request(`/api/navigation/route?start=${start}&destination=${destination}&algorithm=${algorithm}`);
  },

  compareRoutes(start, destination) {
    return this.request(`/api/navigation/compare?start=${start}&destination=${destination}`);
  },

  toggleLane(u, v, isBlocked) {
    return this.request('/api/navigation/toggle-lane', {
      method: 'POST',
      body: JSON.stringify({ u, v, is_blocked: isBlocked })
    });
  },

  getLabDataset(size = 50, type = 'RANDOM') {
    return this.request(`/api/algorithm-lab/dataset?size=${size}&type=${type}`);
  },

  runSortBenchmark(array) {
    return this.request('/api/algorithm-lab/sort', {
      method: 'POST',
      body: JSON.stringify({ array })
    });
  },

  runSearchBenchmark(array, target) {
    return this.request('/api/algorithm-lab/search', {
      method: 'POST',
      body: JSON.stringify({ array, target })
    });
  },

  getReports() {
    return this.request('/api/reports');
  },

  getDsaDocs() {
    return this.request('/api/dsa-explain');
  },

  undoLastAction() {
    return this.request('/api/undo', { method: 'POST' });
  },

  inspectNextZone() {
    return this.request('/api/zone-inspect');
  },

  resetSeed() {
    return this.request('/api/reset-seed', { method: 'POST' });
  }
};
