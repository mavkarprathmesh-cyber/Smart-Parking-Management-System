/**
 * UI Components & Visualizations Module
 * Handles Toasts, Modals, Canvas Charts, and Badges.
 */

const UI = {
  // ==========================================
  // 1. TOAST NOTIFICATIONS
  // ==========================================
  showToast(title, message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-triangle';
    if (type === 'warning') icon = 'fa-bell';

    toast.innerHTML = `
      <i class="fas ${icon} toast-icon"></i>
      <div class="toast-content" style="flex: 1;">
        <div class="toast-title">${title}</div>
        <div class="toast-desc">${message}</div>
      </div>
      <button style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:14px;" onclick="this.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // ==========================================
  // 2. MODAL MANAGER
  // ==========================================
  toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('active');
  },

  closeMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
  },

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      if (modalId === 'server-config-modal') {
        const inp = document.getElementById('server-url-input');
        if (inp && window.API && typeof window.API.getBaseUrl === 'function') {
          inp.value = window.API.getBaseUrl();
        }
        const res = document.getElementById('server-ping-result');
        if (res) res.style.display = 'none';
      }
      modal.classList.add('active');
    }
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  },

  closeAllModals() {
    document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('active'));
  },

  confirm(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    if (!modal) {
      if (window.confirm(`${title}\n${message}`)) {
        onConfirm();
      }
      return;
    }

    document.getElementById('confirm-modal-title').innerText = title;
    document.getElementById('confirm-modal-msg').innerText = message;
    
    const btn = document.getElementById('confirm-modal-btn');
    btn.onclick = () => {
      UI.closeModal('confirm-modal');
      onConfirm();
    };

    UI.openModal('confirm-modal');
  },

  // ==========================================
  // 3. BADGES & FORMATTING
  // ==========================================
  getStatusBadge(status) {
    const s = String(status).toUpperCase();
    if (s === 'FREE') return `<span class="badge badge-free"><span class="badge-dot"></span> Free</span>`;
    if (s === 'OCCUPIED') return `<span class="badge badge-occupied"><span class="badge-dot"></span> Occupied</span>`;
    if (s === 'RESERVED') return `<span class="badge badge-reserved"><span class="badge-dot"></span> Reserved</span>`;
    if (s === 'BLOCKED') return `<span class="badge badge-blocked"><span class="badge-dot"></span> Blocked</span>`;
    return `<span class="badge">${s}</span>`;
  },

  getPriorityBadge(priority) {
    const p = String(priority).toUpperCase();
    if (p === 'EMERGENCY') return `<span class="badge badge-emergency"><i class="fas fa-ambulance"></i> Emergency</span>`;
    if (p === 'ACCESSIBILITY') return `<span class="badge badge-accessibility"><i class="fas fa-wheelchair"></i> Accessible</span>`;
    if (p === 'RESERVED') return `<span class="badge badge-reserved"><i class="fas fa-crown"></i> Reserved</span>`;
    return `<span class="badge badge-free"><i class="fas fa-car"></i> Normal</span>`;
  },

  // ==========================================
  // 4. PURE HTML5 CANVAS CHARTS
  // ==========================================
  drawDonutChart(canvasId, slices, centerText = '') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 15;
    const innerRadius = radius * 0.65;

    const total = slices.reduce((sum, s) => sum + s.value, 0);
    if (total === 0) return;

    let startAngle = -Math.PI / 2;

    slices.forEach(slice => {
      const sliceAngle = (slice.value / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.arc(centerX, centerY, innerRadius, startAngle + sliceAngle, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = slice.color;
      ctx.fill();

      startAngle += sliceAngle;
    });

    // Center text
    if (centerText) {
      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 20px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(centerText, centerX, centerY);
    }
  },

  drawBarChart(canvasId, labels, values, color = '#3b82f6') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (!values.length) return;

    const paddingBottom = 25;
    const paddingTop = 20;
    const chartHeight = height - paddingBottom - paddingTop;
    const maxVal = Math.max(...values, 5);
    const barWidth = Math.min(32, (width / values.length) - 10);

    values.forEach((val, i) => {
      const barHeight = (val / maxVal) * chartHeight;
      const x = (i * (width / values.length)) + ((width / values.length) - barWidth) / 2;
      const y = height - paddingBottom - barHeight;

      // Draw Bar
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barHeight, [4, 4, 0, 0]);
      ctx.fill();

      // Value label on top
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(val, x + barWidth / 2, y - 5);

      // X-axis label
      ctx.fillStyle = '#64748b';
      ctx.fillText(labels[i] || '', x + barWidth / 2, height - 8);
    });
  }
};
