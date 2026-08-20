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
    const publicPages = ['/login.html', '/register.html', '/privacy.html', '/authenticate.html', '/index.html', '/'];
    const currentPath = window.location.pathname;

    try {
      const res = await API.getCurrentUser();
      if (res.authenticated && res.user) {
        this.currentUser = res.user;
        this.updateUserUI(res.user);
        if (currentPath.endsWith('/login.html') || currentPath === '/') {
          window.location.href = res.user.role === 'admin' ? '/admin.html' : '/dashboard.html';
        }
      } else {
        this.currentUser = null;
        this.updateUserUI(null);
        const isPublic = publicPages.some(page => currentPath.endsWith(page));
        if (!isPublic) {
          window.location.href = '/login.html';
        }
      }
    } catch (e) {
      console.warn('Session check failed:', e);
      this.currentUser = null;
      const isPublic = publicPages.some(page => currentPath.endsWith(page));
      if (!isPublic) {
        window.location.href = '/login.html';
      }
    }
  },

  async logout() {
    try {
      await API.logoutUser();
    } catch (e) {}
    window.location.href = '/login.html';
  },

  updateUserUI(user) {
    const userBadgeEl = document.getElementById('topUserBadge');
    const logoutBtnEl = document.getElementById('topLogoutBtn');

    if (userBadgeEl) {
      if (user) {
        userBadgeEl.textContent = `${user.full_name} (${user.role.toUpperCase()})`;
      } else {
        userBadgeEl.textContent = 'Guest';
      }
    }

    if (logoutBtnEl) {
      if (user) {
        logoutBtnEl.style.display = 'inline-flex';
        logoutBtnEl.style.alignItems = 'center';
        logoutBtnEl.onclick = (e) => {
          e.preventDefault();
          this.logout();
        };
      } else {
        logoutBtnEl.style.display = 'none';
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

window.App = App;

window.escapeHtml = function(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

window.escapeAttr = function(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

