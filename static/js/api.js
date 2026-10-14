/**
 * API Client Module with Bearer Token Authorization & RBAC
 */

const API = {
  getBaseUrl() {
    const saved = localStorage.getItem('smartpark_api_url');
    if (saved && saved.trim()) return saved.trim().replace(/\/+$/, '');
    
    // Auto-detect native Capacitor or local wrapper environment
    const isCapacitor = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
    const isLocalScheme = window.location.protocol === 'file:' || window.location.protocol === 'capacitor:';
    
    if (isCapacitor || isLocalScheme) {
      return 'http://10.0.2.2:8000';
    }
    return '';
  },

  setBaseUrl(url) {
    if (!url || !url.trim()) {
      localStorage.removeItem('smartpark_api_url');
    } else {
      localStorage.setItem('smartpark_api_url', url.trim().replace(/\/+$/, ''));
    }
  },

  async pingServer(targetUrl) {
    const base = (targetUrl !== undefined ? targetUrl : this.getBaseUrl()).trim().replace(/\/+$/, '');
    const url = `${base}/api/dashboard`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);
    try {
      const resp = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);
      if (resp.ok) {
        return { success: true, message: `Connected successfully (HTTP ${resp.status})` };
      }
      return { success: false, message: `Server replied with HTTP ${resp.status}` };
    } catch (err) {
      clearTimeout(timer);
      return { success: false, message: `Connection failed: ${err.name === 'AbortError' ? 'Connection timed out (4s)' : err.message}` };
    }
  },

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

    const base = this.getBaseUrl();
    try {
      const response = await fetch(`${base}${endpoint}`, {
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
      if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
        const currentBase = base || 'current origin';
        if (window.UI && typeof window.UI.showToast === 'function') {
          window.UI.showToast(`Cannot reach backend at ${currentBase}. Tap server settings to configure.`, 'error');
        }
      }
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

  getMapConfig() {
    return this.request('/api/config/map');
  },

  getGraph() {
    return this.request('/api/navigation/graph');
  },

  geocode(query) {
    return this.request(`/api/navigation/geocode?q=${encodeURIComponent(query)}`);
  },

  getRoadRoute(startLng, startLat, destLng, destLat, alternatives = true) {
    return this.request(
      `/api/navigation/road-route?start_lng=${startLng}&start_lat=${startLat}&dest_lng=${destLng}&dest_lat=${destLat}&alternatives=${alternatives}`
    );
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
