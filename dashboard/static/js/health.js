/**
 * Health Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    loadHealthStatus();
    loadLogs();
});

async function loadHealthStatus() {
    try {
        const response = await fetch('/api/health/status');
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // Update overall status
            const overallStatus = document.getElementById('overall-status');
            const statusIcon = overallStatus.querySelector('.status-indicator-large i');
            const statusTitle = overallStatus.querySelector('h3');
            const statusDesc = overallStatus.querySelector('p');
            
            if (data.status === 'healthy') {
                statusIcon.className = 'fas fa-check-circle';
                statusIcon.style.color = 'var(--success-color)';
                statusTitle.textContent = 'System Healthy';
                statusDesc.textContent = 'All systems operational';
            } else if (data.status === 'degraded') {
                statusIcon.className = 'fas fa-exclamation-triangle';
                statusIcon.style.color = 'var(--warning-color)';
                statusTitle.textContent = 'System Degraded';
                statusDesc.textContent = 'Some issues detected';
            } else {
                statusIcon.className = 'fas fa-question-circle';
                statusIcon.style.color = 'var(--text-muted)';
                statusTitle.textContent = 'Status Unknown';
                statusDesc.textContent = 'Unable to determine status';
            }
            
            // Update resource usage
            updateResource('cpu', data.cpu || 0);
            updateResource('memory', data.memory || 0);
            updateResource('disk', data.disk || 0);
            
            // Update uptime
            document.getElementById('uptime').textContent = (data.uptime_hours || 0).toFixed(1);
            
            // Update statistics
            document.getElementById('checks-performed').textContent = data.checks_performed || 0;
            document.getElementById('processes-restarted').textContent = data.processes_restarted || 0;
            document.getElementById('alerts-sent').textContent = data.alerts_sent || 0;
            document.getElementById('errors').textContent = data.errors || 0;
        }
    } catch (error) {
        console.error('Error loading health status:', error);
    }
}

function updateResource(type, value) {
    const valueEl = document.getElementById(`${type}-usage`);
    const barEl = document.getElementById(`${type}-bar`);
    
    if (valueEl && barEl) {
        valueEl.textContent = `${value.toFixed(1)}%`;
        barEl.style.width = `${Math.min(value, 100)}%`;
        
        // Update color based on value
        if (value < 70) {
            barEl.style.background = 'var(--success-color)';
        } else if (value < 90) {
            barEl.style.background = 'var(--warning-color)';
        } else {
            barEl.style.background = 'var(--danger-color)';
        }
    }
}

async function loadLogs() {
    try {
        const response = await fetch('/api/health/logs');
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('logs-container');
            const logs = result.data.logs || [];
            
            if (logs.length === 0) {
                container.innerHTML = '<div class="loading">No logs available</div>';
                return;
            }
            
            container.innerHTML = logs.map(log => {
                let levelClass = 'log-level-info';
                if (log.content.includes('ERROR')) levelClass = 'log-level-error';
                else if (log.content.includes('WARN')) levelClass = 'log-level-warning';
                
                return `
                    <div class="log-entry">
                        <span class="log-time">[${log.source}]</span>
                        <span class="${levelClass}">${escapeHtml(log.content)}</span>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
