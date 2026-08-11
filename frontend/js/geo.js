/* ==========================================================================
   Geolocation & Haversine Distance Helper Module
   ========================================================================== */

const GeoService = {
  EARTH_RADIUS_METERS: 6371000.0,

  /**
   * Requests browser GPS location with high accuracy.
   * Returns Promise resolving to { latitude, longitude, accuracy, timestamp }
   */
  getCurrentPosition(options = {}) {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported by your browser or device."));
        return;
      }

      const defaultOptions = {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 0,
        ...options
      };

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
              msg = "Location permission denied. Please allow location access in your browser settings.";
              break;
            case error.POSITION_UNAVAILABLE:
              msg = "Location information is currently unavailable. Ensure GPS is enabled.";
              break;
            case error.TIMEOUT:
              msg = "Location request timed out. Please try again in an open sky area.";
              break;
          }
          reject(new Error(msg));
        },
        defaultOptions
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
