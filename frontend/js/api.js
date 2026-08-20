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

  resetPassword(data) {
    return this.request('/reset-password', { method: 'POST', body: data });
  },

  sendOtp(data) {
    return this.request('/send-otp', { method: 'POST', body: data });
  },

  verifyOtpReset(data) {
    return this.request('/verify-otp-reset', { method: 'POST', body: data });
  },

  logoutUser() {
    return this.request('/logout', { method: 'POST' });
  },

  getCurrentUser() {
    return this.request('/me', { method: 'GET' });
  },

  updateOwnProfile(profileData) {
    return this.request('/me', { method: 'PUT', body: profileData });
  },

  changeOwnPassword(current_password, new_password) {
    return this.request('/me/change-password', { method: 'POST', body: { current_password, new_password } });
  },

  getUserHistory() {
    return this.request('/user/history', { method: 'GET' });
  },

  checkAttendance(user_id) {
    return this.request(`/attendance/check/${encodeURIComponent(user_id)}`, { method: 'GET' });
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

  getAdminUsers(search, status, role, sort_by) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status && status !== 'all') params.append('status', status);
    if (role && role !== 'all') params.append('role', role);
    if (sort_by) params.append('sort_by', sort_by);
    return this.request(`/admin/users?${params.toString()}`, { method: 'GET' });
  },

  getAdminUserDetails(user_id) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}`, { method: 'GET' });
  },

  adminCreateUser(userData) {
    return this.request('/admin/users', { method: 'POST', body: userData });
  },

  updateUserStatus(user_id, status) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}/status`, { method: 'POST', body: { status } });
  },

  updateUserDetails(user_id, userData) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}`, { method: 'PUT', body: userData });
  },

  adminResetUserPassword(user_id, new_password) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}/reset-password`, { method: 'POST', body: { new_password } });
  },

  deleteUser(user_id) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}`, { method: 'DELETE' });
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
  },

  processAbsentees(target_date) {
    return this.request('/admin/process-absent', { method: 'POST', body: { target_date } });
  },

  // Late Slip & Unblock Endpoints
  getLatestLateSlip() {
    return this.request('/late-slip/latest', { method: 'GET' });
  },

  submitLateSlipReason(data) {
    return this.request('/late-slip/submit', { method: 'POST', body: data });
  },

  adminUnblockLateUser(user_id) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}/unblock-late`, { method: 'POST' });
  },

  adminGetLateRequests() {
    return this.request('/admin/late-requests', { method: 'GET' });
  },

  // Credential Management Endpoints
  getUserCredentials() {
    return this.request('/webauthn/credentials', { method: 'GET' });
  },

  deleteUserCredential(credential_id) {
    return this.request(`/webauthn/credentials/${encodeURIComponent(credential_id)}`, { method: 'DELETE' });
  },

  getAdminUserCredentials(user_id) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}/credentials`, { method: 'GET' });
  },

  adminDeleteUserCredential(user_id, credential_id) {
    return this.request(`/admin/users/${encodeURIComponent(user_id)}/credentials/${encodeURIComponent(credential_id)}`, { method: 'DELETE' });
  }
};
