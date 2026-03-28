/**
 * Settings Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
});

function loadSettings() {
    // Load saved settings from localStorage
    const refreshInterval = localStorage.getItem('refreshInterval') || '30';
    const theme = localStorage.getItem('theme') || 'light';
    const notificationsEnabled = localStorage.getItem('notificationsEnabled') !== 'false';
    
    document.getElementById('refresh-interval').value = refreshInterval;
    document.getElementById('theme').value = theme;
    document.getElementById('notifications-enabled').checked = notificationsEnabled;
    
    // Apply theme
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    // Update last sync time
    document.getElementById('last-sync-time').textContent = new Date().toLocaleString();
}

function updateSettings() {
    const refreshInterval = document.getElementById('refresh-interval').value;
    localStorage.setItem('refreshInterval', refreshInterval);
    
    // Show save notification
    showNotification('Settings saved successfully');
}

function toggleTheme() {
    const theme = document.getElementById('theme').value;
    localStorage.setItem('theme', theme);
    
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    
    showNotification('Theme changed to ' + theme);
}

function syncVault() {
    showNotification('Vault sync initiated...');
    
    // Simulate sync - in production this would call an API
    setTimeout(() => {
        showNotification('Vault synced successfully');
    }, 2000);
}

function clearCache() {
    if (confirm('Are you sure you want to clear the dashboard cache?')) {
        localStorage.clear();
        showNotification('Cache cleared. Page will reload...');
        setTimeout(() => {
            location.reload();
        }, 1500);
    }
}

function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success-color);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
