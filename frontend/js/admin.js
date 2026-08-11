/* ==========================================================================
   Admin Dashboard & Location Settings Controller
   ========================================================================== */

const AdminController = {
  leafletMap: null,
  centerMarker: null,
  radiusCircle: null,

  /**
   * Initializes Admin Location Settings Page & Interactive Map.
   */
  async initLocationPage() {
    try {
      const res = await API.getGeofenceSettings();
      if (!res.success) return;
      const settings = res.settings;

      document.getElementById('location_name').value = settings.location_name;
      document.getElementById('latitude').value = settings.latitude;
      document.getElementById('longitude').value = settings.longitude;
      document.getElementById('radius_meters').value = settings.radius_meters;
      document.getElementById('max_gps_accuracy').value = settings.max_gps_accuracy_meters;
      document.getElementById('is_demo_mode').checked = settings.is_demo_mode;

      this.renderMap(settings.latitude, settings.longitude, settings.radius_meters);
    } catch (e) {
      App.showAlert(`Failed to load geofence settings: ${e.message}`, 'danger');
    }
  },

  renderMap(lat, lon, radius) {
    if (typeof L === 'undefined') {
      console.warn('Leaflet JS map library is loading or unsupplied.');
      return;
    }

    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;

    if (!this.leafletMap) {
      this.leafletMap = L.map('map').setView([lat, lon], 16);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(this.leafletMap);

      // Add click listener to select new center on map
      this.leafletMap.on('click', (e) => {
        const clickLat = e.latlng.lat.toFixed(6);
        const clickLon = e.latlng.lng.toFixed(6);
        document.getElementById('latitude').value = clickLat;
        document.getElementById('longitude').value = clickLon;
        this.updateMapShapes(clickLat, clickLon, document.getElementById('radius_meters').value);
      });
    } else {
      this.leafletMap.setView([lat, lon], 16);
    }

    this.updateMapShapes(lat, lon, radius);
  },

  updateMapShapes(lat, lon, radius) {
    if (!this.leafletMap) return;

    const numericLat = parseFloat(lat);
    const numericLon = parseFloat(lon);
    const numericRadius = parseFloat(radius) || 100;

    if (this.centerMarker) this.leafletMap.removeLayer(this.centerMarker);
    if (this.radiusCircle) this.leafletMap.removeLayer(this.radiusCircle);

    this.centerMarker = L.marker([numericLat, numericLon], { draggable: true }).addTo(this.leafletMap);
    this.centerMarker.bindPopup('<b>Authorized Location Center</b>').openPopup();

    this.centerMarker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      document.getElementById('latitude').value = pos.lat.toFixed(6);
      document.getElementById('longitude').value = pos.lng.toFixed(6);
      this.updateMapShapes(pos.lat, pos.lng, document.getElementById('radius_meters').value);
    });

    this.radiusCircle = L.circle([numericLat, numericLon], {
      color: '#3b82f6',
      fillColor: '#3b82f6',
      fillOpacity: 0.2,
      radius: numericRadius
    }).addTo(this.leafletMap);

    this.leafletMap.fitBounds(this.radiusCircle.getBounds());
  },

  async saveLocationSettings(event) {
    if (event) event.preventDefault();

    const location_name = document.getElementById('location_name').value;
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const radius_meters = document.getElementById('radius_meters').value;
    const max_gps_accuracy_meters = document.getElementById('max_gps_accuracy').value;
    const is_demo_mode = document.getElementById('is_demo_mode').checked;

    try {
      const res = await API.saveGeofenceSettings({
        location_name,
        latitude,
        longitude,
        radius_meters,
        max_gps_accuracy_meters,
        is_demo_mode
      });

      if (res.success) {
        App.showAlert('Geofence settings updated successfully!', 'success');
        this.updateMapShapes(latitude, longitude, radius_meters);
      }
    } catch (e) {
      App.showAlert(e.message, 'danger');
    }
  },

  async useCurrentAdminLocation() {
    try {
      App.showAlert('Retrieving current GPS location...', 'info');
      const pos = await GeoService.getCurrentPosition();
      document.getElementById('latitude').value = pos.latitude.toFixed(6);
      document.getElementById('longitude').value = pos.longitude.toFixed(6);
      this.updateMapShapes(pos.latitude, pos.longitude, document.getElementById('radius_meters').value);
      App.showAlert(`Captured location: ${pos.latitude.toFixed(5)}, ${pos.longitude.toFixed(5)} (Accuracy: ${pos.accuracy.toFixed(1)}m)`, 'success');
    } catch (e) {
      App.showAlert(e.message, 'danger');
    }
  }
};
