/**
 * AI Employee Dashboard - Main JavaScript
 * Platinum Tier
 */

// Configuration
const API_BASE = '';
const REFRESH_INTERVAL = 30000; // 30 seconds
let refreshTimer = null;

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Employee Dashboard initialized');
    updateDateTime();
    loadDashboardData();
    startAutoRefresh();
});

// =============================================================================
// Dashboard Data Loading
// =============================================================================

async function loadDashboardData() {
    await Promise.all([
        loadVaultStatus(),
        loadPendingTasks(),
        loadPendingApprovals(),
        loadEmailTriage(),
        loadHealthStatus(),
        loadUrgentSignals()
    ]);
    updateLastSync();
}

async function loadVaultStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/vault/status`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // Update stat cards
            document.getElementById('stat-needs-action').textContent = data.needs_action || 0;
            document.getElementById('stat-pending-approval').textContent = data.pending_approval || 0;
            document.getElementById('stat-email').textContent = data.inbox || 0;
            document.getElementById('stat-done').textContent = data.done || 0;
            document.getElementById('stat-signals').textContent = data.signals || 0;
            document.getElementById('stat-updates').textContent = data.updates || 0;
            
            // Update badges
            document.getElementById('tasks-badge').textContent = data.needs_action || 0;
            document.getElementById('approvals-badge').textContent = data.pending_approval || 0;
            
            // Update system status
            const statusDot = document.getElementById('system-status');
            const statusText = document.getElementById('status-text');
            
            if (data.dashboard_status === 'online') {
                statusDot.className = 'status-dot';
                statusText.textContent = 'Online';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Offline';
            }
            
            if (data.last_updated) {
                document.getElementById('last-sync').textContent = formatDateTime(data.last_updated);
            }
        }
    } catch (error) {
        console.error('Error loading vault status:', error);
    }
}

async function loadPendingTasks() {
    try {
        const response = await fetch(`${API_BASE}/api/tasks/list`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('pending-tasks-list');
            const tasks = result.data.tasks || [];
            
            if (tasks.length === 0) {
                container.innerHTML = '<div class="loading">No pending tasks</div>';
                return;
            }
            
            container.innerHTML = tasks.slice(0, 5).map(task => `
                <div class="task-item">
                    <div class="task-item-header">
                        <span class="task-name">${escapeHtml(task.name)}</span>
                        <span class="priority-badge ${task.priority}">${task.priority}</span>
                    </div>
                    <div class="task-preview">${escapeHtml(task.body_preview)}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

async function loadPendingApprovals() {
    try {
        const response = await fetch(`${API_BASE}/api/approvals/list`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('pending-approvals-list');
            const approvals = result.data.approvals || [];
            
            if (approvals.length === 0) {
                container.innerHTML = '<div class="loading">No pending approvals</div>';
                return;
            }
            
            container.innerHTML = approvals.slice(0, 5).map(approval => `
                <div class="approval-item">
                    <div class="approval-item-header">
                        <span class="approval-name">${escapeHtml(approval.filename)}</span>
                        <span class="approval-type">${escapeHtml(approval.type)}</span>
                    </div>
                    <div class="approval-preview">${escapeHtml(approval.summary || 'No summary')}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading approvals:', error);
    }
}

async function loadEmailTriage() {
    try {
        const response = await fetch(`${API_BASE}/api/email/list`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('email-triage-list');
            const emails = result.data.emails || [];
            
            if (emails.length === 0) {
                container.innerHTML = '<div class="loading">No emails to triage</div>';
                return;
            }
            
            container.innerHTML = emails.slice(0, 5).map(email => `
                <div class="email-item">
                    <div class="email-item-header">
                        <span class="email-subject">${escapeHtml(email.subject || 'No Subject')}</span>
                        <span class="priority-badge ${email.priority}">${email.priority}</span>
                    </div>
                    <div class="email-preview">From: ${escapeHtml(email.from || 'Unknown')}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading emails:', error);
    }
}

async function loadHealthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/health/status`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('health-status');
            const data = result.data;
            
            const statusClass = data.errors > 5 ? 'critical' : (data.errors > 0 ? 'warning' : 'good');
            
            container.innerHTML = `
                <div class="health-item">
                    <span class="health-label">Status</span>
                    <span class="health-value ${statusClass}">${data.status || 'unknown'}</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Uptime</span>
                    <span class="health-value">${(data.uptime_hours || 0).toFixed(1)}h</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Checks</span>
                    <span class="health-value">${data.checks_performed || 0}</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Errors</span>
                    <span class="health-value ${data.errors > 0 ? 'warning' : 'good'}">${data.errors || 0}</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading health status:', error);
    }
}

async function loadUrgentSignals() {
    try {
        const response = await fetch(`${API_BASE}/api/signals/list`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('urgent-signals-list');
            const signals = result.data.signals || [];
            
            if (signals.length === 0) {
                container.innerHTML = '<div class="loading">No urgent signals</div>';
                return;
            }
            
            container.innerHTML = signals.map(signal => `
                <div class="signal-item">
                    <div class="task-item-header">
                        <span class="task-name">
                            <i class="fas fa-exclamation-triangle text-${signal.severity}"></i>
                            ${escapeHtml(signal.filename)}
                        </span>
                        <span class="text-muted">${formatDateTime(signal.timestamp)}</span>
                    </div>
                    <div class="task-preview">${escapeHtml(signal.message)}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading signals:', error);
    }
}

// =============================================================================
// Utility Functions
// =============================================================================

function refreshDashboard() {
    const btn = document.querySelector('.btn-refresh');
    if (btn) {
        btn.querySelector('i').classList.add('fa-spin');
    }
    
    loadDashboardData().then(() => {
        if (btn) {
            setTimeout(() => {
                btn.querySelector('i').classList.remove('fa-spin');
            }, 500);
        }
    });
}

function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(loadDashboardData, REFRESH_INTERVAL);
}

function updateDateTime() {
    const element = document.getElementById('current-datetime');
    if (element) {
        const now = new Date();
        element.textContent = now.toLocaleString();
    }
    setTimeout(updateDateTime, 1000);
}

function updateLastSync() {
    const element = document.getElementById('last-sync');
    if (element) {
        element.textContent = new Date().toLocaleTimeString();
    }
}

function formatDateTime(isoString) {
    if (!isoString) return '--';
    const date = new Date(isoString);
    return date.toLocaleString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
