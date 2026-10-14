/**
 * Interactive 3D Parking Map & Live Road Navigation Module
 * Features:
 * - Real Geocoding (Indian addresses, cities, stations, landmarks, campus bays/gates)
 * - Road-Based Driving Directions (OSRM / Mapbox Directions)
 * - Identifies and displays Fastest and Shortest Available Routes
 * - User can switch between Fastest and Shortest routes
 * - Animated Blinking / Pulsing Route highlight along real road geometry
 * - Moving 3D-Style Car Animation following road tangent bearing
 * - Smooth pitch (tilt), rotation, zoom, camera follow-car mode
 * - Location Lock/Unlock, Start & Destination Markers, Route Confirmation & Reset
 * - Traffic awareness status & non-blocking graceful fallbacks
 */

const Map3D = {
  map: null,
  isInitialized: false,
  mapConfig: null,
  slots: [],
  graphData: null,

  // Default Geo Anchor (Pune / Campus region)
  campusCenter: [73.8567, 18.5204],

  // Selection & Lock State
  startLocation: null, // { id, label, display_name, lng, lat, type }
  destLocation: null,  // { id, label, display_name, lng, lat, type }
  isStartLocked: false,
  isDestLocked: false,

  // Markers
  startMarker: null,
  destMarker: null,
  slotMarkers: [],
  carMarker: null,

  // Calculated Road Routes
  routes: [],
  activeRouteIndex: 0,
  trafficInfo: { has_live_traffic: false, message: '' },

  // Animations State
  routeRequestId: 0,
  carAnimation: {
    progress: 0.0,       // 0.0 to 1.0
    speed: 0.0006,       // animation step per frame
    isPlaying: true,
    reqId: null,
    followCamera: false,
    cumDistances: [],
    totalDistance: 0
  },
  pulseAnimation: {
    reqId: null,
    phase: 0
  },

  // Active View Mode ('3d' or '2d')
  currentViewMode: '3d',
  searchDebounceTimer: null,

  /**
   * Convert Campus Canvas (x, y) coordinates to Geographic [Longitude, Latitude]
   */
  campusToGeo(x, y) {
    const scale = 0.000008;
    const centerX = 430.0;
    const centerY = 330.0;
    const lng = this.campusCenter[0] + (x - centerX) * scale;
    const lat = this.campusCenter[1] + (centerY - y) * scale;
    return [parseFloat(lng.toFixed(7)), parseFloat(lat.toFixed(7))];
  },

  /**
   * Initialize 3D Map container and components
   */
  async init() {
    const container = document.getElementById('map3d-canvas-container');
    if (!container || this.isInitialized) return;

    try {
      // 1. Fetch Map Config from Server
      try {
        const cfg = await API.getMapConfig();
        this.mapConfig = cfg;
        if (cfg.campus_center && cfg.campus_center.lng && cfg.campus_center.lat) {
          this.campusCenter = [cfg.campus_center.lng, cfg.campus_center.lat];
        }
      } catch (e) {
        console.warn('Using default map config:', e);
        this.mapConfig = { has_mapbox: false, default_pitch: 58, default_bearing: -18, default_zoom: 13.5 };
      }

      // 2. Fetch Slots & Navigation Graph Data
      const [slotsData, graphData] = await Promise.all([
        API.getSlots('ALL', 'ALL').catch(() => []),
        API.getGraph().catch(() => ({ nodes: [], edges: [] }))
      ]);
      this.slots = slotsData;
      this.graphData = graphData;

      // 3. Initialize WebGL Map (MapLibre GL or Mapbox GL)
      const GL = window.maplibregl || window.mapboxgl;
      if (!GL) {
        console.error('WebGL Mapping engine not loaded.');
        container.innerHTML = `
          <div style="padding:40px; text-align:center; color:var(--text-muted);">
            <i class="fas fa-exclamation-triangle" style="font-size:36px; color:#f59e0b; margin-bottom:12px;"></i>
            <h3>3D WebGL Library Loading...</h3>
            <p style="margin-top:8px;">Please check internet connection to load map tiles.</p>
          </div>
        `;
        return;
      }

      if (this.mapConfig.has_mapbox && window.mapboxgl && this.mapConfig.mapbox_token) {
        window.mapboxgl.accessToken = this.mapConfig.mapbox_token;
      }

      const mapStyle = this.buildVectorMapStyle();

      this.map = new GL.Map({
        container: 'map3d-canvas-container',
        style: mapStyle,
        center: this.campusCenter,
        zoom: this.mapConfig.default_zoom || 13.5,
        pitch: this.mapConfig.default_pitch || 55,
        bearing: this.mapConfig.default_bearing || -15,
        maxPitch: 85,
        attributionControl: false
      });

      // Navigation Controls: Zoom, Pitch, Compass
      this.map.addControl(new GL.NavigationControl({
        visualizePitch: true,
        showCompass: true,
        showZoom: true
      }), 'top-right');

      this.map.on('load', () => {
        this.onMapReady();
      });

      this.setupUIListeners();
      this.isInitialized = true;

    } catch (err) {
      console.error('Failed to initialize 3D Map:', err);
    }
  },

  /**
   * Vector Style with OpenStreetMap tiles & 3D atmosphere
   */
  buildVectorMapStyle() {
    return {
      version: 8,
      name: 'SmartPark Live 3D Navigation',
      glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png'
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors'
        }
      },
      layers: [
        {
          id: 'osm-base',
          type: 'raster',
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19,
          paint: {
            'raster-opacity': 0.9,
            'raster-saturation': -0.1
          }
        }
      ]
    };
  },

  /**
   * Called once Map WebGL context is ready
   */
  onMapReady() {
    this.add3DBuildings();
    this.initRoadRouteLayers();
    this.addParkingSlotsLayer();

    // Direct Map Click
    this.map.on('click', (e) => this.handleMapClick(e));
    this.map.resize();
  },

  /**
   * Adds 3D extruded campus buildings
   */
  add3DBuildings() {
    const makeRect = (x1, y1, x2, y2) => {
      const c1 = this.campusToGeo(x1, y1);
      const c2 = this.campusToGeo(x2, y1);
      const c3 = this.campusToGeo(x2, y2);
      const c4 = this.campusToGeo(x1, y2);
      return [c1, c2, c3, c4, c1];
    };

    const buildingsGeoJson = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: { id: 'ZONE-A', name: 'Zone A - Ground Floor (4W)', height: 9, min_height: 0, color: '#10b981' },
          geometry: { type: 'Polygon', coordinates: [makeRect(75, 110, 365, 270)] }
        },
        {
          type: 'Feature',
          properties: { id: 'ZONE-B', name: 'Zone B - First Floor (4W Multi-Deck)', height: 18, min_height: 0, color: '#0284c7' },
          geometry: { type: 'Polygon', coordinates: [makeRect(475, 110, 765, 270)] }
        },
        {
          type: 'Feature',
          properties: { id: 'ZONE-C', name: 'Zone C - Two-Wheeler Bay (2W)', height: 6, min_height: 0, color: '#9333ea' },
          geometry: { type: 'Polygon', coordinates: [makeRect(75, 330, 365, 490)] }
        },
        {
          type: 'Feature',
          properties: { id: 'ZONE-D', name: 'Zone D - Priority & Emergency Wing', height: 12, min_height: 0, color: '#f59e0b' },
          geometry: { type: 'Polygon', coordinates: [makeRect(475, 330, 765, 490)] }
        },
        {
          type: 'Feature',
          properties: { id: 'GATE-1', name: 'Main Entry Gate 1 (West)', height: 5, min_height: 0, color: '#059669' },
          geometry: { type: 'Polygon', coordinates: [makeRect(25, 140, 55, 180)] }
        },
        {
          type: 'Feature',
          properties: { id: 'GATE-2', name: 'East Entry Gate 2 (East)', height: 5, min_height: 0, color: '#059669' },
          geometry: { type: 'Polygon', coordinates: [makeRect(805, 380, 835, 420)] }
        }
      ]
    };

    if (this.map.getSource('campus-3d-buildings')) {
      this.map.getSource('campus-3d-buildings').setData(buildingsGeoJson);
      return;
    }

    this.map.addSource('campus-3d-buildings', {
      type: 'geojson',
      data: buildingsGeoJson
    });

    this.map.addLayer({
      id: 'campus-buildings-extrusion',
      type: 'fill-extrusion',
      source: 'campus-3d-buildings',
      paint: {
        'fill-extrusion-color': ['get', 'color'],
        'fill-extrusion-height': ['get', 'height'],
        'fill-extrusion-base': ['get', 'min_height'],
        'fill-extrusion-opacity': 0.85
      }
    });

    this.map.addLayer({
      id: 'campus-buildings-labels',
      type: 'symbol',
      source: 'campus-3d-buildings',
      layout: {
        'text-field': ['get', 'name'],
        'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
        'text-size': 11,
        'text-anchor': 'center'
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': 'rgba(15, 23, 42, 0.9)',
        'text-halo-width': 2
      }
    });
  },

  /**
   * Initializes Live Road Route GeoJSON sources & layers (Active + Alternative)
   */
  initRoadRouteLayers() {
    const emptyGeoJson = { type: 'FeatureCollection', features: [] };

    // 1. Alternative Route Source & Layer
    if (!this.map.getSource('alt-route-source')) {
      this.map.addSource('alt-route-source', { type: 'geojson', data: emptyGeoJson });

      this.map.addLayer({
        id: 'alt-route-line',
        type: 'line',
        source: 'alt-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#64748b',
          'line-width': 5,
          'line-opacity': 0.65,
          'line-dasharray': [3, 2]
        }
      });
    }

    // 2. Selected / Primary Route Source & Layers
    if (!this.map.getSource('active-route-source')) {
      this.map.addSource('active-route-source', { type: 'geojson', data: emptyGeoJson });

      // Solid outer dark border for crisp road contrast
      this.map.addLayer({
        id: 'active-route-casing',
        type: 'line',
        source: 'active-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#0f172a',
          'line-width': 9,
          'line-opacity': 0.85
        }
      });

      // Animated Glowing Aura (pulsing opacity)
      this.map.addLayer({
        id: 'active-route-glow',
        type: 'line',
        source: 'active-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#38bdf8',
          'line-width': 14,
          'line-opacity': 0.6,
          'line-blur': 4
        }
      });

      // Highway Core Line
      this.map.addLayer({
        id: 'active-route-core',
        type: 'line',
        source: 'active-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#0284c7',
          'line-width': 5.5,
          'line-opacity': 0.95
        }
      });

      // Pulsing neon dash flow overlay
      this.map.addLayer({
        id: 'active-route-pulse',
        type: 'line',
        source: 'active-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#67e8f9',
          'line-width': 3,
          'line-dasharray': [1, 3]
        }
      });
    }

    // Start pulsing animation loop
    this.startRoutePulseAnimation();
  },

  /**
   * Continuous subtle pulsing / blinking animation along the selected road route
   */
  startRoutePulseAnimation() {
    if (this.pulseAnimation.reqId) {
      cancelAnimationFrame(this.pulseAnimation.reqId);
      this.pulseAnimation.reqId = null;
    }

    const animatePulse = (timestamp) => {
      if (this.map && this.map.getLayer('active-route-glow') && this.routes.length > 0) {
        // Smooth sine wave between 0.35 and 0.85 opacity
        const opacity = 0.55 + 0.3 * Math.sin(timestamp / 380);
        this.map.setPaintProperty('active-route-glow', 'line-opacity', opacity);

        // Subtle dash animation
        const offset = (timestamp / 200) % 4;
        this.map.setPaintProperty('active-route-pulse', 'line-dasharray', [1, 3 + offset * 0.2]);
      }
      this.pulseAnimation.reqId = requestAnimationFrame(animatePulse);
    };

    this.pulseAnimation.reqId = requestAnimationFrame(animatePulse);
  },

  /**
   * Adds 3D parking slots/bays on the map
   */
  addParkingSlotsLayer() {
    this.slotMarkers.forEach(m => m.remove());
    this.slotMarkers = [];

    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    (this.slots || []).forEach(slot => {
      const geo = this.campusToGeo(slot.pos_x || 100, slot.pos_y || 100);

      const el = document.createElement('div');
      el.className = `map3d-slot-marker status-${slot.status.toLowerCase()}`;
      el.setAttribute('data-slot-id', slot.slot_id);
      el.setAttribute('title', `Bay ${slot.slot_id} [${slot.status}]`);

      let iconClass = slot.vehicle_type === '2W' ? 'fa-motorcycle' : 'fa-car';
      el.innerHTML = `
        <div class="slot-marker-bubble">
          <i class="fas ${iconClass}"></i>
          <span class="slot-marker-id">${slot.slot_id}</span>
        </div>
      `;

      el.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleSlotMarkerClick(slot, geo);
      });

      const marker = new GL.Marker({ element: el, anchor: 'bottom' })
        .setLngLat(geo)
        .addTo(this.map);

      this.slotMarkers.push(marker);
    });
  },

  /**
   * Direct map click popup
   */
  handleMapClick(e) {
    const lngLat = e.lngLat;
    const clickedGeo = [parseFloat(lngLat.lng.toFixed(6)), parseFloat(lngLat.lat.toFixed(6))];

    const entity = {
      id: `MAP-POINT`,
      label: `Map Point (${clickedGeo[1].toFixed(4)}°N, ${clickedGeo[0].toFixed(4)}°E)`,
      display_name: `Selected Coordinates: ${clickedGeo[1]}, ${clickedGeo[0]}`,
      lng: clickedGeo[0],
      lat: clickedGeo[1],
      type: 'COORDINATES'
    };

    this.showLocationActionPopup(entity, clickedGeo);
  },

  /**
   * Action popup when user clicks a point on the map
   */
  showLocationActionPopup(entity, geo) {
    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    const popupContent = document.createElement('div');
    popupContent.className = 'map3d-action-popup';
    popupContent.innerHTML = `
      <div style="font-weight:700;font-size:13px;color:var(--text-primary);margin-bottom:3px;">
        <i class="fas fa-map-marker-alt" style="color:#2563eb;"></i> ${entity.label}
      </div>
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:10px;">
        ${entity.display_name}
      </div>
      <div style="display:flex;gap:6px;">
        <button id="popup-set-start" class="btn btn-primary btn-sm" style="flex:1;font-size:11px;padding:6px;">
          <i class="fas fa-play"></i> Set Start
        </button>
        <button id="popup-set-dest" class="btn btn-secondary btn-sm" style="flex:1;font-size:11px;padding:6px;">
          <i class="fas fa-flag-checkered"></i> Set Destination
        </button>
      </div>
    `;

    const popup = new GL.Popup({ offset: 15, closeButton: true })
      .setLngLat(geo)
      .setDOMContent(popupContent)
      .addTo(this.map);

    popupContent.querySelector('#popup-set-start').addEventListener('click', () => {
      this.setStartLocation(entity);
      popup.remove();
    });

    popupContent.querySelector('#popup-set-dest').addEventListener('click', () => {
      this.setDestLocation(entity);
      popup.remove();
    });
  },

  /**
   * Slot marker click popup
   */
  handleSlotMarkerClick(slot, geo) {
    const entity = {
      id: slot.slot_id,
      label: `Bay ${slot.slot_id}`,
      display_name: `SmartPark Bay ${slot.slot_id} (${slot.zone_id} • ${slot.vehicle_type})`,
      lng: geo[0],
      lat: geo[1],
      type: 'PARKING_SLOT',
      status: slot.status
    };

    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    const popupContent = document.createElement('div');
    popupContent.className = 'map3d-slot-popup';
    popupContent.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <strong style="font-size:13.5px;">Bay ${slot.slot_id}</strong>
        <span class="badge badge-${slot.status.toLowerCase()}">${slot.status}</span>
      </div>
      <div style="font-size:11px;color:var(--text-secondary);margin-bottom:8px;">
        Zone ${slot.zone_id} • Type: ${slot.vehicle_type} • ₹${slot.hourly_rate || 20}/hr
      </div>
      <div style="display:flex;gap:6px;margin-bottom:6px;">
        <button id="slot-popup-start" class="btn btn-secondary btn-sm" style="flex:1;font-size:11px;">
          <i class="fas fa-play"></i> Start
        </button>
        <button id="slot-popup-dest" class="btn btn-primary btn-sm" style="flex:1;font-size:11px;">
          <i class="fas fa-flag-checkered"></i> Destination
        </button>
      </div>
    `;

    const popup = new GL.Popup({ offset: 25, closeButton: true })
      .setLngLat(geo)
      .setDOMContent(popupContent)
      .addTo(this.map);

    popupContent.querySelector('#slot-popup-start').addEventListener('click', () => {
      this.setStartLocation(entity);
      popup.remove();
    });

    popupContent.querySelector('#slot-popup-dest').addEventListener('click', () => {
      this.setDestLocation(entity);
      popup.remove();
    });
  },

  /**
   * Set Starting Location (From)
   */
  setStartLocation(entity) {
    if (this.isStartLocked) {
      UI.showToast('Location Locked', 'Starting Location is locked. Click "Unlock" to modify it.', 'warning');
      return;
    }

    this.startLocation = entity;
    const input = document.getElementById('map3d-start-input');
    if (input) {
      input.value = entity.label || entity.display_name;
    }

    this.renderStartMarker();
    this.checkAndCalculateLiveRoute();
  },

  /**
   * Set Destination Location (To)
   */
  setDestLocation(entity) {
    if (this.isDestLocked) {
      UI.showToast('Location Locked', 'Destination is locked. Click "Unlock" to modify it.', 'warning');
      return;
    }

    this.destLocation = entity;
    const input = document.getElementById('map3d-dest-input');
    if (input) {
      input.value = entity.label || entity.display_name;
    }

    this.renderDestMarker();
    this.checkAndCalculateLiveRoute();
  },

  /**
   * Lock / Unlock Starting Location
   */
  toggleLockStart() {
    if (!this.startLocation) {
      UI.showToast('Notice', 'Please select a starting location before locking.', 'warning');
      return;
    }

    this.isStartLocked = !this.isStartLocked;
    const btn = document.getElementById('map3d-lock-start-btn');
    const badge = document.getElementById('start-lock-status');
    const input = document.getElementById('map3d-start-input');

    if (this.isStartLocked) {
      if (btn) btn.innerHTML = '<i class="fas fa-unlock"></i> Unlock';
      if (btn) btn.className = 'btn btn-secondary';
      if (badge) badge.innerHTML = '<i class="fas fa-lock"></i> Locked';
      if (badge) badge.className = 'badge badge-locked';
      if (input) input.disabled = true;
      UI.showToast('Locked', 'Starting location locked.', 'info');
    } else {
      if (btn) btn.innerHTML = '<i class="fas fa-lock"></i> Lock';
      if (btn) btn.className = 'btn btn-outline-success';
      if (badge) badge.innerHTML = '<i class="fas fa-lock-open"></i> Unlocked';
      if (badge) badge.className = 'badge badge-unlocked';
      if (input) input.disabled = false;
      UI.showToast('Unlocked', 'Starting location unlocked for changes.', 'info');
    }
  },

  /**
   * Lock / Unlock Destination
   */
  toggleLockDest() {
    if (!this.destLocation) {
      UI.showToast('Notice', 'Please select a destination before locking.', 'warning');
      return;
    }

    this.isDestLocked = !this.isDestLocked;
    const btn = document.getElementById('map3d-lock-dest-btn');
    const badge = document.getElementById('dest-lock-status');
    const input = document.getElementById('map3d-dest-input');

    if (this.isDestLocked) {
      if (btn) btn.innerHTML = '<i class="fas fa-unlock"></i> Unlock';
      if (btn) btn.className = 'btn btn-secondary';
      if (badge) badge.innerHTML = '<i class="fas fa-lock"></i> Locked';
      if (badge) badge.className = 'badge badge-locked';
      if (input) input.disabled = true;
      UI.showToast('Locked', 'Destination locked.', 'info');
    } else {
      if (btn) btn.innerHTML = '<i class="fas fa-lock"></i> Lock';
      if (btn) btn.className = 'btn btn-outline-danger';
      if (badge) badge.innerHTML = '<i class="fas fa-lock-open"></i> Unlocked';
      if (badge) badge.className = 'badge badge-unlocked';
      if (input) input.disabled = false;
      UI.showToast('Unlocked', 'Destination unlocked for changes.', 'info');
    }
  },

  /**
   * Clear Starting Location
   */
  clearStartLocation() {
    if (this.isStartLocked) this.toggleLockStart();
    this.startLocation = null;
    const input = document.getElementById('map3d-start-input');
    if (input) input.value = '';
    if (this.startMarker) {
      this.startMarker.remove();
      this.startMarker = null;
    }
    this.clearAllRoutes();
  },

  /**
   * Clear Destination
   */
  clearDestLocation() {
    if (this.isDestLocked) this.toggleLockDest();
    this.destLocation = null;
    const input = document.getElementById('map3d-dest-input');
    if (input) input.value = '';
    if (this.destMarker) {
      this.destMarker.remove();
      this.destMarker = null;
    }
    this.clearAllRoutes();
  },

  /**
   * Render Start Beacon Marker
   */
  renderStartMarker() {
    if (this.startMarker) {
      this.startMarker.remove();
      this.startMarker = null;
    }
    if (!this.startLocation || !this.map) return;

    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    const el = document.createElement('div');
    el.className = 'map3d-point-marker marker-start';
    el.innerHTML = `
      <div class="marker-pulse-ring start-ring"></div>
      <div class="marker-pin start-pin"><i class="fas fa-play"></i></div>
      <div class="marker-label">START: ${this.startLocation.label}</div>
    `;

    this.startMarker = new GL.Marker({ element: el, anchor: 'bottom' })
      .setLngLat([this.startLocation.lng, this.startLocation.lat])
      .addTo(this.map);

    this.map.flyTo({
      center: [this.startLocation.lng, this.startLocation.lat],
      zoom: Math.max(this.map.getZoom(), 14),
      duration: 1000
    });
  },

  /**
   * Render Destination Beacon Marker
   */
  renderDestMarker() {
    if (this.destMarker) {
      this.destMarker.remove();
      this.destMarker = null;
    }
    if (!this.destLocation || !this.map) return;

    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    const el = document.createElement('div');
    el.className = 'map3d-point-marker marker-dest';
    el.innerHTML = `
      <div class="marker-pulse-ring dest-ring"></div>
      <div class="marker-pin dest-pin"><i class="fas fa-flag-checkered"></i></div>
      <div class="marker-label">DESTINATION: ${this.destLocation.label}</div>
    `;

    this.destMarker = new GL.Marker({ element: el, anchor: 'bottom' })
      .setLngLat([this.destLocation.lng, this.destLocation.lat])
      .addTo(this.map);

    this.map.flyTo({
      center: [this.destLocation.lng, this.destLocation.lat],
      zoom: Math.max(this.map.getZoom(), 14),
      duration: 1000
    });
  },

  /**
   * Core Road-Based Routing Trigger
   * Calculates actual road routes using OSRM / Mapbox Directions,
   * identifies Fastest and Shortest routes, and starts moving car animation.
   */
  async checkAndCalculateLiveRoute() {
    if (!this.startLocation || !this.destLocation) {
      this.clearAllRoutes();
      return;
    }

    // Coordinates Validation
    if (
      typeof this.startLocation.lng !== 'number' || isNaN(this.startLocation.lng) ||
      typeof this.destLocation.lng !== 'number' || isNaN(this.destLocation.lng)
    ) {
      UI.showToast('Location Unresolved', 'Please select a valid location from the search dropdown suggestions.', 'warning');
      return;
    }

    const currentReq = ++this.routeRequestId;
    this.stopCarAnimation();

    const routeCard = document.getElementById('map3d-route-card');
    const confirmBtn = document.getElementById('map3d-confirm-btn');

    if (routeCard) {
      routeCard.style.display = 'block';
      routeCard.innerHTML = `
        <div style="text-align:center;padding:16px;color:var(--text-muted);">
          <i class="fas fa-spinner fa-spin"></i> Calculating actual road driving routes (Fastest & Shortest)...
        </div>
      `;
    }

    try {
      const res = await API.getRoadRoute(
        this.startLocation.lng,
        this.startLocation.lat,
        this.destLocation.lng,
        this.destLocation.lat,
        true
      );

      // Discard stale responses if user picked another location while request was in-flight
      if (currentReq !== this.routeRequestId) return;

      if (!res.success || !res.routes || res.routes.length === 0) {
        throw new Error(res.error || 'No road driving route found between selected points.');
      }

      this.routes = res.routes;
      this.trafficInfo = {
        has_live_traffic: res.has_live_traffic,
        message: res.traffic_status_message
      };

      // By default select Fastest route (or 0)
      let fastestIdx = this.routes.findIndex(r => r.is_fastest);
      if (fastestIdx === -1) fastestIdx = 0;
      this.activeRouteIndex = fastestIdx;

      this.renderRoutesOnMap();
      this.renderRouteInfoCard();

      if (confirmBtn) confirmBtn.disabled = false;

    } catch (err) {
      if (currentReq !== this.routeRequestId) return;
      console.warn('Live road routing error:', err);
      this.clearAllRoutes();

      if (routeCard) {
        routeCard.style.display = 'block';
        routeCard.innerHTML = `
          <div class="card" style="border-left:4px solid #ef4444;background:rgba(239, 68, 68, 0.05);margin-top:10px;">
            <div style="font-weight:700;color:#ef4444;font-size:13.5px;">
              <i class="fas fa-exclamation-circle"></i> Road Routing Unavailable
            </div>
            <div style="font-size:12.5px;color:var(--text-secondary);margin-top:4px;">
              ${err.message || 'Could not calculate road route between selected coordinates.'}
            </div>
          </div>
        `;
      }
      if (confirmBtn) confirmBtn.disabled = true;
    }
  },

  /**
   * Renders the Active Route and any Alternative Routes on the 3D Map
   */
  renderRoutesOnMap() {
    if (!this.map || this.routes.length === 0) return;

    const activeRoute = this.routes[this.activeRouteIndex];
    if (!activeRoute) return;

    // 1. Draw Active Route
    const activeGeoJson = {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        properties: { id: activeRoute.id, name: activeRoute.route_name },
        geometry: activeRoute.geometry
      }]
    };
    if (this.map.getSource('active-route-source')) {
      this.map.getSource('active-route-source').setData(activeGeoJson);
    }

    // 2. Draw Alternative Routes (if present)
    const altFeatures = [];
    this.routes.forEach((r, idx) => {
      if (idx !== this.activeRouteIndex) {
        altFeatures.push({
          type: 'Feature',
          properties: { id: r.id, index: idx },
          geometry: r.geometry
        });
      }
    });

    const altGeoJson = { type: 'FeatureCollection', features: altFeatures };
    if (this.map.getSource('alt-route-source')) {
      this.map.getSource('alt-route-source').setData(altGeoJson);
    }

    // 3. Auto Fit Bounds to show complete road route
    const coords = activeRoute.geometry.coordinates || [];
    const GL = window.maplibregl || window.mapboxgl;
    if (GL && coords.length > 0) {
      const bounds = coords.reduce(
        (b, pt) => b.extend(pt),
        new GL.LngLatBounds(coords[0], coords[0])
      );
      this.map.fitBounds(bounds, {
        padding: { top: 90, bottom: 80, left: 80, right: 80 },
        pitch: 55,
        bearing: -15,
        duration: 1200
      });
    }

    // 4. Initialize and start the moving car animation along the selected road route
    this.initMovingCarAnimation(coords);
  },

  /**
   * Switch between Fastest Route and Shortest Route
   */
  selectRoute(index) {
    if (index < 0 || index >= this.routes.length || index === this.activeRouteIndex) return;

    this.activeRouteIndex = index;
    this.renderRoutesOnMap();
    this.renderRouteInfoCard();
    UI.showToast('Route Switched', `Now following: ${this.routes[index].route_type} (${this.routes[index].distance_km} km)`, 'info');
  },

  /**
   * Initializes and executes the moving 3D-styled car animation along the road geometry
   */
  initMovingCarAnimation(coordinates) {
    this.stopCarAnimation();

    if (!coordinates || coordinates.length < 2) return;

    // Precalculate segment distances and cumulative totals
    const cumDists = [0];
    let total = 0;
    for (let i = 0; i < coordinates.length - 1; i++) {
      const p1 = coordinates[i];
      const p2 = coordinates[i + 1];
      const d = this.calculateGeoDistanceMeters(p1[1], p1[0], p2[1], p2[0]);
      total += d;
      cumDists.push(total);
    }

    this.carAnimation.cumDistances = cumDists;
    this.carAnimation.totalDistance = total;
    this.carAnimation.progress = 0.0;
    this.carAnimation.isPlaying = true;

    // Create or position car marker
    const GL = window.maplibregl || window.mapboxgl;
    if (!GL) return;

    if (!this.carMarker) {
      const carEl = document.createElement('div');
      carEl.className = 'map3d-moving-car-wrapper';
      carEl.innerHTML = `
        <div class="moving-car-body">
          <div class="car-headlights"></div>
          <div class="car-windshield"></div>
          <div class="car-roof"></div>
          <div class="car-taillights"></div>
        </div>
      `;

      this.carMarker = new GL.Marker({
        element: carEl,
        anchor: 'center',
        rotationAlignment: 'map',
        pitchAlignment: 'map'
      }).setLngLat(coordinates[0]).addTo(this.map);
    } else {
      this.carMarker.setLngLat(coordinates[0]);
    }

    // Start requestAnimationFrame loop
    const animateCar = () => {
      if (!this.carAnimation.isPlaying || !this.map || !this.carMarker) return;

      // Adjust speed so route traversal preview takes ~25-35 seconds
      const step = 1.0 / (30.0 * 60.0); // 30 seconds at 60fps
      this.carAnimation.progress += step;

      if (this.carAnimation.progress >= 1.0) {
        this.carAnimation.progress = 1.0;
        this.updateCarPosition(coordinates, 1.0);
        this.carAnimation.isPlaying = false;
        return;
      }

      this.updateCarPosition(coordinates, this.carAnimation.progress);

      this.carAnimation.reqId = requestAnimationFrame(animateCar);
    };

    this.carAnimation.reqId = requestAnimationFrame(animateCar);
  },

  /**
   * Updates car position and bearing along the road tangent
   */
  updateCarPosition(coordinates, t) {
    if (!this.carMarker || coordinates.length < 2) return;

    const targetDist = t * this.carAnimation.totalDistance;
    const cum = this.carAnimation.cumDistances;

    // Find segment
    let segIdx = 0;
    for (let i = 0; i < cum.length - 1; i++) {
      if (targetDist >= cum[i] && targetDist <= cum[i + 1]) {
        segIdx = i;
        break;
      }
    }

    const p1 = coordinates[segIdx];
    const p2 = coordinates[segIdx + 1] || coordinates[segIdx];
    const segLen = cum[segIdx + 1] - cum[segIdx];
    const frac = segLen > 0 ? (targetDist - cum[segIdx]) / segLen : 0;

    const curLng = p1[0] + frac * (p2[0] - p1[0]);
    const curLat = p1[1] + frac * (p2[1] - p1[1]);

    // Calculate road tangent bearing
    const bearing = this.calculateBearing(p1[0], p1[1], p2[0], p2[1]);

    this.carMarker.setLngLat([curLng, curLat]);
    this.carMarker.setRotation(bearing);

    // Optional: Follow camera
    if (this.carAnimation.followCamera && this.map) {
      this.map.easeTo({ center: [curLng, curLat], duration: 100 });
    }
  },

  /**
   * Calculates geographic distance in meters between two lat/lng coordinates (Haversine)
   */
  calculateGeoDistanceMeters(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  },

  /**
   * Calculates bearing in degrees from North (road tangent heading)
   */
  calculateBearing(lng1, lat1, lng2, lat2) {
    const rad = Math.PI / 180;
    const phi1 = lat1 * rad;
    const phi2 = lat2 * rad;
    const deltaLambda = (lng2 - lng1) * rad;

    const y = Math.sin(deltaLambda) * Math.cos(phi2);
    const x = Math.cos(phi1) * Math.sin(phi2) -
              Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);

    const theta = Math.atan2(y, x);
    return (theta * 180 / Math.PI + 360) % 360;
  },

  /**
   * Stops moving car animation
   */
  stopCarAnimation() {
    if (this.carAnimation.reqId) {
      cancelAnimationFrame(this.carAnimation.reqId);
      this.carAnimation.reqId = null;
    }
    this.carAnimation.isPlaying = false;
  },

  /**
   * Replays moving car animation along current route
   */
  replayCarAnimation() {
    const activeRoute = this.routes[this.activeRouteIndex];
    if (activeRoute && activeRoute.geometry) {
      this.initMovingCarAnimation(activeRoute.geometry.coordinates);
    }
  },

  /**
   * Toggle camera following car
   */
  toggleFollowCar() {
    this.carAnimation.followCamera = !this.carAnimation.followCamera;
    const btn = document.getElementById('btn-follow-car');
    if (btn) {
      if (this.carAnimation.followCamera) {
        btn.className = 'camera-btn active';
        UI.showToast('Follow Car', 'Camera following moving car preview.', 'info');
      } else {
        btn.className = 'camera-btn';
        UI.showToast('Follow Car', 'Camera follow disabled.', 'info');
      }
    }
  },

  /**
   * Renders Route Information Card with Fastest vs Shortest selection pills
   */
  renderRouteInfoCard() {
    const routeCard = document.getElementById('map3d-route-card');
    if (!routeCard || this.routes.length === 0) return;

    const activeRoute = this.routes[this.activeRouteIndex];
    if (!activeRoute) return;

    // Route Selection Pills (Fastest vs Shortest / Alternatives)
    const pillsHtml = this.routes.map((r, idx) => {
      const isActive = idx === this.activeRouteIndex;
      let badgeIcon = 'fa-road';
      let badgeColor = '#64748b';
      if (r.is_fastest && r.is_shortest) {
        badgeIcon = 'fa-bolt';
        badgeColor = '#10b981';
      } else if (r.is_fastest) {
        badgeIcon = 'fa-bolt';
        badgeColor = '#0284c7';
      } else if (r.is_shortest) {
        badgeIcon = 'fa-ruler';
        badgeColor = '#8b5cf6';
      }

      return `
        <button type="button" class="route-select-pill ${isActive ? 'active' : ''}" onclick="Map3D.selectRoute(${idx})">
          <div style="display:flex;align-items:center;gap:6px;">
            <i class="fas ${badgeIcon}" style="color:${badgeColor};"></i>
            <span style="font-weight:700;">${r.route_type}</span>
          </div>
          <div style="font-size:11px;margin-top:2px;">
            <strong>${r.duration_text}</strong> • ${r.distance_km} km
          </div>
        </button>
      `;
    }).join('');

    // Step-by-step turns (first 6 steps)
    const stepsHtml = (activeRoute.steps || []).slice(0, 6).map((st, i) => `
      <div class="route-step-item">
        <div class="step-num">${i + 1}</div>
        <div style="flex:1;">
          <div style="font-weight:600;font-size:12px;">${st.instruction}</div>
          <div style="font-size:11px;color:var(--text-muted);">${st.street_name || 'Highway'} (${st.distance_meters}m)</div>
        </div>
      </div>
    `).join('');

    routeCard.innerHTML = `
      <div class="route-summary-panel">
        <!-- Multiple Route Options Switcher -->
        <div class="route-options-switcher">
          ${pillsHtml}
        </div>

        <!-- Metrics Row -->
        <div class="route-metrics-row" style="margin-top:10px;">
          <div class="route-metric">
            <div class="metric-val"><i class="fas fa-road" style="color:#0284c7;"></i> ${activeRoute.distance_km} km</div>
            <div class="metric-label">Total Distance</div>
          </div>
          <div class="route-metric">
            <div class="metric-val"><i class="fas fa-clock" style="color:#10b981;"></i> ${activeRoute.duration_text}</div>
            <div class="metric-label">Estimated Driving Time</div>
          </div>
          <div class="route-metric">
            <div class="metric-val"><i class="fas fa-route" style="color:#f59e0b;"></i> ${activeRoute.route_type}</div>
            <div class="metric-label">Selected Route Classification</div>
          </div>
        </div>

        <!-- Traffic & Traversal Preview Notice -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:11.5px;color:var(--text-muted);">
          <span><i class="fas fa-info-circle"></i> ${this.trafficInfo.message}</span>
          <div style="display:flex;gap:6px;">
            <button type="button" class="btn btn-secondary btn-sm" onclick="Map3D.replayCarAnimation()" style="padding:2px 8px;font-size:11px;">
              <i class="fas fa-redo"></i> Replay Preview
            </button>
            <button type="button" id="btn-follow-car" class="btn btn-secondary btn-sm" onclick="Map3D.toggleFollowCar()" style="padding:2px 8px;font-size:11px;">
              <i class="fas fa-video"></i> Follow Car
            </button>
          </div>
        </div>

        <!-- Traversal notice badge -->
        <div style="margin: 6px 0; font-size:10.5px; color:#64748b; font-style:italic;">
          * Route Traversal Preview: Simulated motion along calculated road path.
        </div>

        <!-- Step-by-Step Directions -->
        <div style="margin: 8px 0 4px; font-size:11.5px; font-weight:700; color:var(--text-secondary);">
          <i class="fas fa-directions"></i> Turn-by-Turn Driving Guidance:
        </div>
        <div class="route-steps-container">
          ${stepsHtml || '<div style="font-size:11.5px;color:var(--text-muted);">Direct road segment.</div>'}
        </div>
      </div>
    `;
    routeCard.style.display = 'block';
  },

  /**
   * Confirms route and proceeds with existing booking/parking workflow
   */
  confirmRoute() {
    if (!this.destLocation) {
      UI.showToast('Select Destination', 'Please select a destination point first.', 'warning');
      return;
    }

    const slotId = this.destLocation.id;
    const destLabel = this.destLocation.label || this.destLocation.display_name;

    // Check if destination is a campus parking bay
    const slotObj = this.slots.find(s => s.slot_id === slotId);

    if (slotObj && slotObj.status === 'FREE') {
      const role = API.getUser() ? API.getUser().role : 'USER';
      if (role === 'USER') {
        UI.showToast('Route Confirmed', `Route confirmed! Proceeding to advance reservation for Bay ${slotId}.`, 'success');
        if (window.App && typeof window.App.openAdvanceBookingModal === 'function') {
          const today = new Date().toISOString().split('T')[0];
          window.App.openAdvanceBookingModal(slotObj.slot_id, slotObj.zone_id, slotObj.vehicle_type, today, '10:00', 2);
        }
      } else {
        UI.showToast('Route Confirmed', `Route confirmed to Bay ${slotId}.`, 'success');
        if (window.App && typeof window.App.navigateTo === 'function') {
          window.App.navigateTo('park');
        }
      }
    } else {
      UI.showToast('Route Confirmed', `Navigation confirmed to ${destLabel}. Shortest/fastest road path locked.`, 'success');
    }
  },

  /**
   * Resets Route, cleans markers, stops moving car, and restores camera
   */
  resetRoute() {
    this.clearStartLocation();
    this.clearDestLocation();
    this.clearAllRoutes();

    if (this.map) {
      this.map.flyTo({
        center: this.campusCenter,
        zoom: this.mapConfig.default_zoom || 13.5,
        pitch: this.mapConfig.default_pitch || 55,
        bearing: this.mapConfig.default_bearing || -15,
        duration: 1200
      });
    }

    UI.showToast('Route Reset', 'Locations and navigation route cleared.', 'info');
  },

  /**
   * Clears route line layers and stops animations
   */
  clearAllRoutes() {
    this.routes = [];
    this.activeRouteIndex = 0;
    this.stopCarAnimation();

    if (this.carMarker) {
      this.carMarker.remove();
      this.carMarker = null;
    }

    const empty = { type: 'FeatureCollection', features: [] };
    if (this.map) {
      if (this.map.getSource('active-route-source')) this.map.getSource('active-route-source').setData(empty);
      if (this.map.getSource('alt-route-source')) this.map.getSource('alt-route-source').setData(empty);
    }

    const routeCard = document.getElementById('map3d-route-card');
    if (routeCard) {
      routeCard.style.display = 'none';
      routeCard.innerHTML = '';
    }

    const confirmBtn = document.getElementById('map3d-confirm-btn');
    if (confirmBtn) confirmBtn.disabled = true;
  },

  /**
   * Requests user's real GPS location only when explicitly chosen
   */
  useCurrentLocation() {
    if (!navigator.geolocation) {
      UI.showToast('Not Supported', 'Geolocation is not supported by your browser.', 'error');
      return;
    }

    UI.showToast('Locating', 'Requesting GPS location from browser...', 'info');

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const userLng = parseFloat(pos.coords.longitude.toFixed(6));
        const userLat = parseFloat(pos.coords.latitude.toFixed(6));

        const gpsEntity = {
          id: 'GPS-LOCATION',
          label: `My Location (${userLat.toFixed(4)}, ${userLng.toFixed(4)})`,
          display_name: `Current GPS Coordinates: ${userLat}, ${userLng}`,
          type: 'GPS',
          lng: userLng,
          lat: userLat
        };

        this.setStartLocation(gpsEntity);
        this.toggleLockStart();
        UI.showToast('GPS Located', 'Starting point set to your current GPS position.', 'success');
      },
      (err) => {
        console.warn('Geolocation denied or failed:', err);
        UI.showToast('GPS Denied', 'Location permission denied. Please choose a location or type in search.', 'warning');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  },

  /**
   * Unified Location Search: Searches Campus Features + Real Geocoded Addresses
   */
  async searchUnified(query) {
    if (!query || query.trim().length < 2) return [];
    const q = query.trim().toLowerCase();
    const results = [];

    // 1. Check Campus Parking Bays & Gates
    (this.graphData.nodes || []).filter(n => n.type === 'GATE').forEach(g => {
      if (g.id.toLowerCase().includes(q) || g.label.toLowerCase().includes(q)) {
        const geo = this.campusToGeo(g.x, g.y);
        results.push({
          id: g.id,
          label: g.label,
          display_name: `${g.label} (Campus Entrance)`,
          type: 'GATE',
          lng: geo[0],
          lat: geo[1]
        });
      }
    });

    (this.slots || []).forEach(s => {
      if (s.slot_id.toLowerCase().includes(q) || `bay ${s.slot_id}`.toLowerCase().includes(q)) {
        const geo = this.campusToGeo(s.pos_x || 100, s.pos_y || 100);
        results.push({
          id: s.slot_id,
          label: `Bay ${s.slot_id}`,
          display_name: `SmartPark Bay ${s.slot_id} (Zone ${s.zone_id} • Status: ${s.status})`,
          type: 'PARKING_SLOT',
          status: s.status,
          lng: geo[0],
          lat: geo[1]
        });
      }
    });

    // 2. Real Geocoding (Indian cities, railway stations, hospitals, landmarks, streets)
    try {
      const geoResults = await API.geocode(query);
      if (Array.isArray(geoResults)) {
        geoResults.forEach(item => {
          results.push({
            id: item.id || `GEO-${item.lng}-${item.lat}`,
            label: item.label,
            display_name: item.display_name,
            type: item.type || 'LOCATION',
            lng: item.lng,
            lat: item.lat
          });
        });
      }
    } catch (e) {
      console.warn('Geocoding search failed:', e);
    }

    return results.slice(0, 8);
  },

  /**
   * Setup UI input search and dropdown listeners
   */
  setupUIListeners() {
    const startInput = document.getElementById('map3d-start-input');
    const startDropdown = document.getElementById('map3d-start-suggestions');
    const destInput = document.getElementById('map3d-dest-input');
    const destDropdown = document.getElementById('map3d-dest-suggestions');

    // Starting location search
    if (startInput && startDropdown) {
      startInput.addEventListener('input', (e) => {
        clearTimeout(this.searchDebounceTimer);
        const val = e.target.value;
        this.searchDebounceTimer = setTimeout(async () => {
          if (!val || val.trim().length < 2) {
            startDropdown.style.display = 'none';
            return;
          }
          startDropdown.innerHTML = '<div class="suggestion-item no-match"><i class="fas fa-spinner fa-spin"></i> Searching locations...</div>';
          startDropdown.style.display = 'block';

          const matches = await this.searchUnified(val);
          this.renderSuggestions(matches, startDropdown, (sel) => {
            this.setStartLocation(sel);
            startDropdown.style.display = 'none';
          });
        }, 250);
      });

      startInput.addEventListener('focus', () => {
        if (startInput.value.trim().length >= 2) startDropdown.style.display = 'block';
      });
    }

    // Destination search
    if (destInput && destDropdown) {
      destInput.addEventListener('input', (e) => {
        clearTimeout(this.searchDebounceTimer);
        const val = e.target.value;
        this.searchDebounceTimer = setTimeout(async () => {
          if (!val || val.trim().length < 2) {
            destDropdown.style.display = 'none';
            return;
          }
          destDropdown.innerHTML = '<div class="suggestion-item no-match"><i class="fas fa-spinner fa-spin"></i> Searching locations...</div>';
          destDropdown.style.display = 'block';

          const matches = await this.searchUnified(val);
          this.renderSuggestions(matches, destDropdown, (sel) => {
            this.setDestLocation(sel);
            destDropdown.style.display = 'none';
          });
        }, 250);
      });

      destInput.addEventListener('focus', () => {
        if (destInput.value.trim().length >= 2) destDropdown.style.display = 'block';
      });
    }

    // Outside click dismiss
    document.addEventListener('click', (e) => {
      if (startDropdown && !e.target.closest('#map3d-start-input-group')) startDropdown.style.display = 'none';
      if (destDropdown && !e.target.closest('#map3d-dest-input-group')) destDropdown.style.display = 'none';
    });
  },

  /**
   * Renders the suggestion items into the dropdown
   */
  renderSuggestions(items, dropdownEl, onSelect) {
    if (!items || items.length === 0) {
      dropdownEl.innerHTML = '<div class="suggestion-item no-match"><i class="fas fa-info-circle"></i> No locations found. Try another city, address or bay.</div>';
      dropdownEl.style.display = 'block';
      return;
    }

    dropdownEl.innerHTML = items.map((item, idx) => {
      let icon = 'fa-map-pin';
      let badge = item.type;
      if (item.type === 'GATE') icon = 'fa-door-open';
      else if (item.type === 'PARKING_SLOT') icon = 'fa-parking';
      else if (item.type.includes('STATION')) icon = 'fa-train';
      else if (item.type.includes('CITY') || item.type.includes('TOWN')) icon = 'fa-city';
      else if (item.type.includes('HOSPITAL')) icon = 'fa-hospital';

      return `
        <div class="suggestion-item" data-idx="${idx}">
          <div style="display:flex;align-items:center;gap:8px;max-width:85%;">
            <i class="fas ${icon}" style="color:var(--accent-primary);flex-shrink:0;"></i>
            <div style="overflow:hidden;">
              <div style="font-weight:600;font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${item.label}</div>
              <div style="font-size:11px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${item.display_name}</div>
            </div>
          </div>
          <span class="badge badge-secondary" style="font-size:10px;">${badge}</span>
        </div>
      `;
    }).join('');

    dropdownEl.style.display = 'block';

    dropdownEl.querySelectorAll('.suggestion-item:not(.no-match)').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-idx'));
        onSelect(items[idx]);
      });
    });
  },

  /**
   * Quick chip selection
   */
  selectQuickChip(type, id) {
    let entity = null;
    if (id === 'GATE-1') {
      const geo = this.campusToGeo(40, 160);
      entity = { id: 'GATE-1', label: 'Main Entry Gate 1 (West)', display_name: 'Main Gate 1 (West Entrance)', lng: geo[0], lat: geo[1], type: 'GATE' };
    } else if (id === 'GATE-2') {
      const geo = this.campusToGeo(820, 400);
      entity = { id: 'GATE-2', label: 'East Entry Gate 2 (East)', display_name: 'East Gate 2 (East Entrance)', lng: geo[0], lat: geo[1], type: 'GATE' };
    } else if (id === 'ZONE-A') {
      const geo = this.campusToGeo(200, 160);
      entity = { id: 'ZONE-A', label: 'Zone A (4W Ground)', display_name: 'Zone A Parking Structure', lng: geo[0], lat: geo[1], type: 'ZONE' };
    } else if (id === 'ZONE-B') {
      const geo = this.campusToGeo(620, 160);
      entity = { id: 'ZONE-B', label: 'Zone B (Floor 1)', display_name: 'Zone B Multi-Deck Garage', lng: geo[0], lat: geo[1], type: 'ZONE' };
    } else if (id === 'ZONE-C') {
      const geo = this.campusToGeo(200, 420);
      entity = { id: 'ZONE-C', label: 'Zone C (2W)', display_name: 'Zone C Two-Wheeler Bay', lng: geo[0], lat: geo[1], type: 'ZONE' };
    } else if (id === 'ZONE-D') {
      const geo = this.campusToGeo(620, 420);
      entity = { id: 'ZONE-D', label: 'Zone D (Priority)', display_name: 'Zone D Priority & Emergency Wing', lng: geo[0], lat: geo[1], type: 'ZONE' };
    }

    if (!entity) return;

    if (!this.startLocation || !this.isStartLocked) {
      this.setStartLocation(entity);
    } else {
      this.setDestLocation(entity);
    }
  },

  /**
   * Set 3D Camera view preset
   */
  setCameraPreset(preset) {
    if (!this.map) return;

    if (preset === '3d') {
      this.map.flyTo({ pitch: 60, bearing: -20, duration: 800 });
    } else if (preset === 'top') {
      this.map.flyTo({ pitch: 0, bearing: 0, duration: 800 });
    } else if (preset === 'north') {
      this.map.flyTo({ bearing: 0, duration: 600 });
    } else if (preset === 'reset') {
      this.map.flyTo({
        center: this.campusCenter,
        zoom: this.mapConfig.default_zoom || 13.5,
        pitch: this.mapConfig.default_pitch || 55,
        bearing: this.mapConfig.default_bearing || -15,
        duration: 1000
      });
    }
  },

  /**
   * Switch between 3D Interactive Map and 2D Blueprint Canvas
   */
  switchViewMode(mode) {
    this.currentViewMode = mode;

    const wrapper3d = document.getElementById('map-3d-view-wrapper');
    const wrapper2d = document.getElementById('map-2d-view-wrapper');
    const btn3d = document.getElementById('btn-mode-3d');
    const btn2d = document.getElementById('btn-mode-2d');

    if (mode === '3d') {
      if (wrapper3d) wrapper3d.style.display = 'block';
      if (wrapper2d) wrapper2d.style.display = 'none';
      if (btn3d) btn3d.className = 'btn btn-sm btn-primary active';
      if (btn2d) btn2d.className = 'btn btn-sm btn-secondary';

      if (!this.isInitialized) {
        this.init();
      } else if (this.map) {
        setTimeout(() => this.map.resize(), 100);
      }
    } else {
      if (wrapper3d) wrapper3d.style.display = 'none';
      if (wrapper2d) wrapper2d.style.display = 'block';
      if (btn3d) btn3d.className = 'btn btn-sm btn-secondary';
      if (btn2d) btn2d.className = 'btn btn-sm btn-primary active';

      if (window.ParkingMap) {
        ParkingMap.resize();
        ParkingMap.render();
      }
    }
  },

  /**
   * Pre-load predefined route (e.g. from My Bookings or Instant Allocation)
   */
  async setPredefinedRoute(startId, destId) {
    if (!this.isInitialized) {
      await this.init();
    }
    this.switchViewMode('3d');

    const startNode = (this.graphData.nodes || []).find(n => n.id === startId) || { id: startId, label: startId, x: 40, y: 160 };
    const destNode = (this.graphData.nodes || []).find(n => n.id === destId) || { id: destId, label: `Bay ${destId}`, x: 200, y: 160 };

    const startGeo = this.campusToGeo(startNode.x, startNode.y);
    const destGeo = this.campusToGeo(destNode.x, destNode.y);

    this.startLocation = {
      id: startNode.id,
      label: startNode.label,
      display_name: startNode.label,
      lng: startGeo[0],
      lat: startGeo[1],
      type: 'GATE'
    };
    this.destLocation = {
      id: destNode.id,
      label: destNode.label,
      display_name: destNode.label,
      lng: destGeo[0],
      lat: destGeo[1],
      type: 'SLOT'
    };

    const sIn = document.getElementById('map3d-start-input');
    const dIn = document.getElementById('map3d-dest-input');
    if (sIn) sIn.value = this.startLocation.label;
    if (dIn) dIn.value = this.destLocation.label;

    this.isStartLocked = true;
    this.isDestLocked = true;

    const btnStart = document.getElementById('map3d-lock-start-btn');
    const btnDest = document.getElementById('map3d-lock-dest-btn');
    if (btnStart) btnStart.innerHTML = '<i class="fas fa-unlock"></i> Unlock';
    if (btnDest) btnDest.innerHTML = '<i class="fas fa-unlock"></i> Unlock';

    this.renderStartMarker();
    this.renderDestMarker();
    this.checkAndCalculateLiveRoute();
  }
};
