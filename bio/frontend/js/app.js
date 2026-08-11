/* ==========================================================================
   Global Application Logic & UI Handlers
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

const App = {
  currentUser: null,

  async init() {
    this.registerServiceWorker();
    this.setupActiveNavigation();
    await this.checkSession();
  },

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js')
        .then(reg => console.log('[PWA] Service Worker registered:', reg.scope))
        .catch(err => console.warn('[PWA] Service Worker registration failed:', err));
    }
  },

  async checkSession() {
    try {
      const res = await API.getCurrentUser();
      if (res.authenticated && res.user) {
        this.currentUser = res.user;
        this.updateUserUI(res.user);
      } else {
        this.currentUser = null;
        this.updateUserUI(null);
      }
    } catch (e) {
      console.warn('Session check failed:', e);
      this.currentUser = null;
    }
  },

  updateUserUI(user) {
    const userBadgeEl = document.getElementById('topUserBadge');
    if (userBadgeEl) {
      if (user) {
        userBadgeEl.textContent = `${user.full_name} (${user.role.toUpperCase()})`;
      } else {
        userBadgeEl.textContent = 'Guest';
      }
    }
  },

  setupActiveNavigation() {
    const path = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item, .desktop-nav a');
    
    navItems.forEach(item => {
      const href = item.getAttribute('href');
      if (href && path.endsWith(href)) {
        item.classList.add('active');
      }
    });
  },

  showAlert(message, type = 'danger', containerId = 'alertContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert-banner alert-${type}`;
    alert.innerHTML = `
      <span>${message}</span>
    `;

    container.innerHTML = '';
    container.appendChild(alert);

    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 6000);
  },

  clearAlert(containerId = 'alertContainer') {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = '';
  }
};
