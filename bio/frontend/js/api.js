/* ==========================================================================
   API Service Wrapper — REST Endpoints & Client Session Management
   ========================================================================== */

const API = {
  baseUrl: '/api',

  async request(endpoint, options = {}) {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include', // Always send HTTP-only session cookies
      ...options
    };

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      const data = await response.json().catch(() => ({ success: false, message: 'Invalid response format from server.' }));
      
      if (!response.ok) {
        throw new Error(data.message || `Request failed with status ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`[API Error] ${endpoint}:`, error);
      throw error;
    }
  },

  // Auth Endpoints
  registerUser(userData) {
    return this.request('/register', { method: 'POST', body: userData });
  },

  loginUser(credentials) {
    return this.request('/login', { method: 'POST', body: credentials });
  },

  logoutUser() {
    return this.request('/logout', { method: 'POST' });
  },

  getCurrentUser() {
    return this.request('/me', { method: 'GET' });
  },

  getUserHistory() {
    return this.request('/user/history', { method: 'GET' });
  },

  // Geofence Endpoints
  getGeofenceSettings() {
    return this.request('/location/settings', { method: 'GET' });
  },

  verifyLocation(locationData) {
    return this.request('/location/verify', { method: 'POST', body: locationData });
  },

  // WebAuthn Endpoints
  getWebAuthnRegisterOptions(user_id) {
    return this.request('/webauthn/register/options', { method: 'POST', body: { user_id } });
  },

  verifyWebAuthnRegister(credential, credential_name) {
    return this.request('/webauthn/register/verify', { method: 'POST', body: { credential, credential_name } });
  },

  getWebAuthnLoginOptions(user_id, locationData) {
    return this.request('/webauthn/login/options', { method: 'POST', body: { user_id, ...locationData } });
  },

  verifyWebAuthnLogin(credential, locationData) {
    return this.request('/webauthn/login/verify', { method: 'POST', body: { credential, ...locationData } });
  },

  // Admin Endpoints
  getAdminDashboard() {
    return this.request('/admin/dashboard', { method: 'GET' });
  },

  getAdminUsers(search, status) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    return this.request(`/admin/users?${params.toString()}`, { method: 'GET' });
  },

  updateUserStatus(user_id, status) {
    return this.request(`/admin/users/${user_id}/status`, { method: 'POST', body: { status } });
  },

  deleteUser(user_id) {
    return this.request(`/admin/users/${user_id}`, { method: 'DELETE' });
  },

  saveGeofenceSettings(settings) {
    return this.request('/admin/geofence', { method: 'POST', body: settings });
  },

  getAdminLogs(date_filter, status, search) {
    const params = new URLSearchParams();
    if (date_filter) params.append('date_filter', date_filter);
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    return this.request(`/admin/logs?${params.toString()}`, { method: 'GET' });
  }
};
