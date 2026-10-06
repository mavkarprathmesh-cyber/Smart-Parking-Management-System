/**
 * Interactive Parking Floorplan & Route Animator Module
 * Renders 2D Canvas Map of Zones, Gates, Slots, and Animated Dijkstra Driving Routes.
 */

const ParkingMap = {
  canvas: null,
  ctx: null,
  slots: [],
  graphData: null,
  activeRoute: null,
  animationProgress: 0,
  animationTimer: null,
  hoveredSlot: null,
  onSlotClickCallback: null,

  init(canvasId, onSlotClick) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.onSlotClickCallback = onSlotClick;

    // Handle high DPI displays
    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Mouse events
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.canvas.addEventListener('mouseleave', () => {
      this.hoveredSlot = null;
      this.render();
    });
  },

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width || 900;
    this.canvas.height = 540;
    this.render();
  },

  setData(slots, graphData) {
    this.slots = slots || [];
    this.graphData = graphData || null;
    this.render();
  },

  setRoute(routeData) {
    this.activeRoute = routeData;
    this.animationProgress = 0;
    if (this.animationTimer) clearInterval(this.animationTimer);

    if (routeData && routeData.path_coordinates && routeData.path_coordinates.length > 1) {
      this.animationTimer = setInterval(() => {
        this.animationProgress += 0.02;
        if (this.animationProgress >= 1.0) {
          this.animationProgress = 1.0;
          clearInterval(this.animationTimer);
        }
        this.render();
      }, 20);
    } else {
      this.render();
    }
  },

  clearRoute() {
    this.activeRoute = null;
    if (this.animationTimer) clearInterval(this.animationTimer);
    this.render();
  },

  render() {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Scale factors from virtual coordinate space (900x540)
    const scaleX = w / 900;
    const scaleY = h / 540;

    ctx.clearRect(0, 0, w, h);

    // 1. Background Grid & Asphalt Roads
    this.drawCampusLayout(ctx, scaleX, scaleY);

    // 2. Graph Roads / Connecting Lanes
    if (this.graphData && this.graphData.edges) {
      this.drawLanes(ctx, scaleX, scaleY);
    }

    // 3. Active Navigation Route (Dijkstra)
    if (this.activeRoute && this.activeRoute.path_coordinates) {
      this.drawAnimatedRoute(ctx, scaleX, scaleY);
    }

    // 4. Gates & Junction Markers
    this.drawGatesAndJunctions(ctx, scaleX, scaleY);

    // 5. Parking Slots
    this.drawSlots(ctx, scaleX, scaleY);

    // 6. Tooltip for hovered slot
    if (this.hoveredSlot) {
      this.drawSlotTooltip(ctx, scaleX, scaleY, this.hoveredSlot);
    }
  },

  drawCampusLayout(ctx, sx, sy) {
    // Zone backgrounds
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1.5;

    // Zone A (Top-Left)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(80 * sx, 110 * sy, 290 * sx, 180 * sy);
    ctx.strokeRect(80 * sx, 110 * sy, 290 * sx, 180 * sy);

    // Zone B (Top-Right - First Floor)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(480 * sx, 110 * sy, 290 * sx, 180 * sy);
    ctx.strokeRect(480 * sx, 110 * sy, 290 * sx, 180 * sy);

    // Zone C (Bottom-Left - 2W)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(80 * sx, 330 * sy, 290 * sx, 180 * sy);
    ctx.strokeRect(80 * sx, 330 * sy, 290 * sx, 180 * sy);

    // Zone D (Bottom-Right - Priority)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(480 * sx, 330 * sy, 290 * sx, 180 * sy);
    ctx.strokeRect(480 * sx, 330 * sy, 290 * sx, 180 * sy);

    // Zone Header Labels
    ctx.font = 'bold 12px Outfit, sans-serif';
    ctx.fillStyle = '#475569';

    ctx.fillText('ZONE A • GROUND FLOOR (4W)', 90 * sx, 130 * sy);
    ctx.fillText('ZONE B • FIRST FLOOR (4W)', 490 * sx, 130 * sy);
    ctx.fillText('ZONE C • TWO-WHEELERS (2W)', 90 * sx, 350 * sy);
    ctx.fillText('ZONE D • PRIORITY / EMERGENCY', 490 * sx, 350 * sy);
  },

  drawLanes(ctx, sx, sy) {
    if (!this.graphData) return;
    const nodeMap = {};
    (this.graphData.nodes || []).forEach(n => nodeMap[n.id] = n);

    (this.graphData.edges || []).forEach(edge => {
      const uNode = nodeMap[edge.from];
      const vNode = nodeMap[edge.to];
      if (!uNode || !vNode) return;

      ctx.beginPath();
      ctx.moveTo(uNode.x * sx, uNode.y * sy);
      ctx.lineTo(vNode.x * sx, vNode.y * sy);

      if (edge.is_blocked) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 3;
        ctx.setLineDash([4, 4]);
      } else {
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([]);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    });
  },

  drawGatesAndJunctions(ctx, sx, sy) {
    if (!this.graphData) return;

    (this.graphData.nodes || []).forEach(node => {
      if (node.type === 'GATE') {
        ctx.fillStyle = node.id.includes('EXIT') ? '#ef4444' : '#10b981';
        ctx.beginPath();
        ctx.arc(node.x * sx, node.y * sy, 10, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#0f172a';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, node.x * sx, (node.y - 14) * sy);
      }
    });
  },

  drawAnimatedRoute(ctx, sx, sy) {
    const coords = this.activeRoute.path_coordinates;
    if (!coords || coords.length < 2) return;

    // Draw full glowing path line
    ctx.beginPath();
    ctx.moveTo(coords[0].x * sx, coords[0].y * sy);
    for (let i = 1; i < coords.length; i++) {
      ctx.lineTo(coords[i].x * sx, coords[i].y * sy);
    }
    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 5;
    ctx.shadowColor = 'rgba(37, 99, 235, 0.4)';
    ctx.shadowBlur = 10;
    ctx.stroke();
    ctx.shadowBlur = 0; // reset

    // Calculate moving car position
    const totalSegments = coords.length - 1;
    const currentProgressTotal = this.animationProgress * totalSegments;
    const segIdx = Math.min(Math.floor(currentProgressTotal), totalSegments - 1);
    const segFrac = currentProgressTotal - segIdx;

    const p1 = coords[segIdx];
    const p2 = coords[segIdx + 1];
    const curX = (p1.x + (p2.x - p1.x) * segFrac) * sx;
    const curY = (p1.y + (p2.y - p1.y) * segFrac) * sy;

    // Vehicle Pulse Marker
    ctx.beginPath();
    ctx.arc(curX, curY, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.shadowColor = 'rgba(245, 158, 11, 0.5)';
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.shadowBlur = 0;
  },

  drawSlots(ctx, sx, sy) {
    this.slots.forEach(slot => {
      const x = (slot.pos_x || 100) * sx;
      const y = (slot.pos_y || 100) * sy;
      const slotW = 50 * sx;
      const slotH = 40 * sy;

      // Determine color
      let fillColor = '#ecfdf5';
      let strokeColor = '#10b981';
      if (slot.status === 'OCCUPIED') {
        fillColor = '#fef2f2';
        strokeColor = '#ef4444';
      } else if (slot.status === 'RESERVED') {
        fillColor = '#fffbeb';
        strokeColor = '#f59e0b';
      } else if (slot.status === 'BLOCKED') {
        fillColor = '#f1f5f9';
        strokeColor = '#94a3b8';
      }

      // Slot Box
      ctx.fillStyle = fillColor;
      ctx.beginPath();
      ctx.roundRect(x - slotW / 2, y - slotH / 2, slotW, slotH, 6);
      ctx.fill();

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Slot ID Text (Dark Slate for crisp contrast)
      ctx.fillStyle = '#0f172a';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(slot.slot_id, x, y - 4 * sy);

      // Icon / vehicle type indicator
      ctx.font = '9px Inter, sans-serif';
      ctx.fillStyle = strokeColor;
      ctx.fillText(slot.vehicle_type || '4W', x, y + 10 * sy);
    });
  },

  drawSlotTooltip(ctx, sx, sy, slot) {
    const x = (slot.pos_x || 100) * sx;
    const y = (slot.pos_y || 100) * sy - 35 * sy;

    const text = `${slot.slot_id} [${slot.status}] • ${slot.distance_from_gate}m`;
    ctx.font = '12px Inter, sans-serif';
    const textWidth = ctx.measureText(text).width + 20;

    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(x - textWidth / 2, y - 12, textWidth, 24, 4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#f8fafc';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
  },

  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const sx = this.canvas.width / 900;
    const sy = this.canvas.height / 540;

    let found = null;
    for (const slot of this.slots) {
      const x = (slot.pos_x || 100) * sx;
      const y = (slot.pos_y || 100) * sy;
      const slotW = 50 * sx;
      const slotH = 40 * sy;

      if (mouseX >= x - slotW / 2 && mouseX <= x + slotW / 2 &&
          mouseY >= y - slotH / 2 && mouseY <= y + slotH / 2) {
        found = slot;
        break;
      }
    }

    if (this.hoveredSlot !== found) {
      this.hoveredSlot = found;
      this.canvas.style.cursor = found ? 'pointer' : 'default';
      this.render();
    }
  },

  handleClick(e) {
    if (this.hoveredSlot && this.onSlotClickCallback) {
      this.onSlotClickCallback(this.hoveredSlot);
    }
  }
};
