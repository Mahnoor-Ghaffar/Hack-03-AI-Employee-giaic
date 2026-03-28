/**
 * Briefings Page JavaScript
 */

let allBriefings = [];

document.addEventListener('DOMContentLoaded', function() {
    loadBriefings();
});

async function loadBriefings() {
    try {
        const response = await fetch('/api/briefings/list');
        const result = await response.json();
        
        if (result.success) {
            allBriefings = result.data.briefings || [];
            renderBriefings(allBriefings);
        }
    } catch (error) {
        console.error('Error loading briefings:', error);
    }
}

function renderBriefings(briefings) {
    const container = document.getElementById('briefings-list');
    
    if (briefings.length === 0) {
        container.innerHTML = '<div class="loading">No CEO briefings found</div>';
        return;
    }
    
    container.innerHTML = briefings.map(briefing => `
        <div class="briefing-card" onclick="viewBriefing('${escapeHtml(briefing.filename)}')" style="cursor: pointer;">
            <div class="briefing-header">
                <h3><i class="fas fa-file-alt"></i> ${escapeHtml(briefing.title)}</h3>
                <span class="briefing-date">${formatDateTime(briefing.created)}</span>
            </div>
            ${briefing.period ? `
                <div class="briefing-period">
                    <strong>Period:</strong> ${escapeHtml(briefing.period)}
                </div>
            ` : ''}
        </div>
    `).join('');
}

async function viewBriefing(filename) {
    try {
        const response = await fetch(`/api/briefings/${encodeURIComponent(filename)}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            document.getElementById('modal-briefing-title').textContent = data.filename;
            document.getElementById('modal-briefing-content').innerHTML = `
                <div class="briefing-content">
                    <pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(data.content)}</pre>
                </div>
            `;
            
            document.getElementById('briefing-modal').classList.add('active');
        }
    } catch (error) {
        console.error('Error loading briefing:', error);
    }
}

function closeBriefingModal() {
    document.getElementById('briefing-modal').classList.remove('active');
}

function downloadBriefing() {
    alert('Download functionality - To be implemented');
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
