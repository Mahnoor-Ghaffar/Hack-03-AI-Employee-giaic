/**
 * Email Page JavaScript
 */

let allEmails = [];
let currentEmail = null;

document.addEventListener('DOMContentLoaded', function() {
    loadEmails();
});

async function loadEmails() {
    try {
        const response = await fetch('/api/email/list');
        const result = await response.json();
        
        if (result.success) {
            allEmails = result.data.emails || [];
            renderEmails(allEmails);
        }
    } catch (error) {
        console.error('Error loading emails:', error);
    }
}

function renderEmails(emails) {
    const container = document.getElementById('email-list');
    
    if (emails.length === 0) {
        container.innerHTML = '<div class="loading">No emails to triage</div>';
        return;
    }
    
    container.innerHTML = emails.map(email => `
        <div class="email-card" onclick="viewEmail('${escapeHtml(email.filename)}')" style="cursor: pointer;">
            <div class="email-card-header">
                <div>
                    <h4>${escapeHtml(email.subject || 'No Subject')}</h4>
                    <span class="text-muted">From: ${escapeHtml(email.from || 'Unknown')}</span>
                </div>
                <span class="priority-badge ${email.priority}">${email.priority}</span>
            </div>
            <div class="email-card-body">
                ${email.summary ? `<p>${escapeHtml(email.summary)}</p>` : ''}
                ${email.draft_preview ? `
                    <div class="draft-preview">
                        <strong>Draft Reply:</strong>
                        <p>${escapeHtml(email.draft_preview)}</p>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function viewEmail(filename) {
    try {
        const email = allEmails.find(e => e.filename === filename);
        if (!email) return;
        
        currentEmail = email;
        
        document.getElementById('modal-email-title').textContent = email.subject || 'Email Details';
        document.getElementById('modal-email-content').innerHTML = `
            <div class="email-detail">
                <div class="email-meta">
                    <p><strong>From:</strong> ${escapeHtml(email.from || 'Unknown')}</p>
                    <p><strong>Priority:</strong> ${escapeHtml(email.priority)}</p>
                    <p><strong>Status:</strong> ${escapeHtml(email.status)}</p>
                </div>
                
                ${email.summary ? `
                    <div class="mt-2">
                        <strong>Summary:</strong>
                        <p>${escapeHtml(email.summary)}</p>
                    </div>
                ` : ''}
                
                ${email.draft_preview ? `
                    <div class="mt-2">
                        <strong>Draft Reply:</strong>
                        <div class="draft-content">${escapeHtml(email.draft_preview)}</div>
                    </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('email-modal').classList.add('active');
    } catch (error) {
        console.error('Error viewing email:', error);
    }
}

function closeEmailModal() {
    document.getElementById('email-modal').classList.remove('active');
    currentEmail = null;
}

function forwardEmail() {
    alert('Forward functionality - To be implemented with MCP email integration');
}

function archiveEmail() {
    alert('Archive functionality - To be implemented');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
