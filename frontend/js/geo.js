/* ==========================================================================
   Geolocation & Haversine Distance Helper Module — Fast GPS Resolution
   ========================================================================== */

const GeoService = {
  EARTH_RADIUS_METERS: 6371000.0,
  _lastKnownPosition: null,

  /**
   * Requests browser GPS location with fast fallback.
   * Returns Promise resolving to { latitude, longitude, accuracy, timestamp }
   */
  async getCurrentPosition(options = {}) {
    if (!navigator.geolocation) {
      throw new Error("Geolocation is not supported by your browser or device.");
    }

    // Try fast high-accuracy first with recent cache allowed (10s)
    try {
      const pos = await this._fetchPosition({
        enableHighAccuracy: true,
        timeout: 6000,
        maximumAge: 10000,
        ...options
      });
      this._lastKnownPosition = pos;
      return pos;
    } catch (err) {
      // If timed out or high-accuracy slow, fallback to standard fast fix (30s cache)
      if (err.message && (err.message.includes('timed out') || err.message.includes('unavailable'))) {
        try {
          const fallbackPos = await this._fetchPosition({
            enableHighAccuracy: false,
            timeout: 5000,
            maximumAge: 30000
          });
          this._lastKnownPosition = fallbackPos;
          return fallbackPos;
        } catch (fallbackErr) {
          throw err;
        }
      }
      throw err;
    }
  },

  _fetchPosition(opts) {
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp
          });
        },
        (error) => {
          let msg = "Unable to retrieve location.";
          switch (error.code) {
            case error.PERMISSION_DENIED:
              msg = "Location permission denied. Please allow location access in your mobile browser.";
              break;
            case error.POSITION_UNAVAILABLE:
              msg = "GPS position unavailable. Please ensure Location/GPS is turned ON in your phone settings.";
              break;
            case error.TIMEOUT:
              msg = "Location request timed out. Retrying with network location...";
              break;
          }
          reject(new Error(msg));
        },
        opts
      );
    });
  },

  /**
   * Calculates Haversine distance in meters between two lat/lon points.
   */
  calculateHaversineDistance(lat1, lon1, lat2, lon2) {
    const toRad = (val) => (val * Math.PI) / 180.0;
    
    const phi1 = toRad(lat1);
    const phi2 = toRad(lat2);
    const deltaPhi = toRad(lat2 - lat1);
    const deltaLambda = toRad(lon2 - lon1);

    let a =
      Math.sin(deltaPhi / 2.0) * Math.sin(deltaPhi / 2.0) +
      Math.cos(phi1) * Math.cos(phi2) *
      Math.sin(deltaLambda / 2.0) * Math.sin(deltaLambda / 2.0);

    a = Math.min(1.0, Math.max(0.0, a));
    const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
    const distance = this.EARTH_RADIUS_METERS * c;
    
    return Math.round(distance * 100) / 100;
  }
};
