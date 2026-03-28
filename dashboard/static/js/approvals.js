/**
 * Approvals Page JavaScript
 */

let allApprovals = [];
let currentApproval = null;

document.addEventListener('DOMContentLoaded', function() {
    loadApprovals();
});

async function loadApprovals() {
    try {
        const response = await fetch('/api/approvals/list');
        const result = await response.json();
        
        if (result.success) {
            allApprovals = result.data.approvals || [];
            renderApprovals(allApprovals);
            updateStats(allApprovals);
        }
    } catch (error) {
        console.error('Error loading approvals:', error);
    }
}

function renderApprovals(approvals) {
    const container = document.getElementById('approvals-list');
    
    if (approvals.length === 0) {
        container.innerHTML = '<div class="loading">No pending approvals</div>';
        return;
    }
    
    container.innerHTML = approvals.map(approval => `
        <div class="approval-card">
            <div class="approval-card-header">
                <div>
                    <h4>${escapeHtml(approval.filename)}</h4>
                    <span class="text-muted">${escapeHtml(approval.type)}</span>
                </div>
                <div class="approval-card-actions">
                    <button class="btn btn-small btn-primary" onclick="viewApproval('${escapeHtml(approval.filename)}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
            </div>
            <div class="approval-preview">${escapeHtml(approval.summary || 'No summary')}</div>
        </div>
    `).join('');
}

function updateStats(approvals) {
    document.getElementById('total-approvals').textContent = approvals.length;
    
    const emailCount = approvals.filter(a => a.type === 'email_send_approval').length;
    const socialCount = approvals.filter(a => a.type === 'linkedin_post_approval').length;
    const paymentCount = approvals.filter(a => a.type === 'payment_approval').length;
    
    document.getElementById('email-approvals').textContent = emailCount;
    document.getElementById('social-approvals').textContent = socialCount;
    document.getElementById('payment-approvals').textContent = paymentCount;
}

async function viewApproval(filename) {
    try {
        // Find the approval in the list
        const approval = allApprovals.find(a => a.filename === filename);
        if (!approval) return;
        
        currentApproval = approval;
        
        document.getElementById('modal-approval-title').textContent = filename;
        document.getElementById('modal-approval-content').innerHTML = `
            <div class="approval-detail">
                <p><strong>Type:</strong> ${escapeHtml(approval.type)}</p>
                <p><strong>Status:</strong> ${escapeHtml(approval.status)}</p>
                <p><strong>Summary:</strong> ${escapeHtml(approval.summary || 'N/A')}</p>
                ${approval.subject ? `<p><strong>Subject:</strong> ${escapeHtml(approval.subject)}</p>` : ''}
                ${approval.recipient ? `<p><strong>Recipient:</strong> ${escapeHtml(approval.recipient)}</p>` : ''}
                ${approval.content_preview ? `
                    <div class="mt-2">
                        <strong>Content Preview:</strong>
                        <pre class="content-preview">${escapeHtml(approval.content_preview)}</pre>
                    </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('approval-modal').classList.add('active');
    } catch (error) {
        console.error('Error viewing approval:', error);
    }
}

function closeApprovalModal() {
    document.getElementById('approval-modal').classList.remove('active');
    currentApproval = null;
}

async function approveAction() {
    if (!currentApproval) return;
    
    if (!confirm('Are you sure you want to approve this action?')) return;
    
    try {
        const response = await fetch(`/api/approvals/${encodeURIComponent(currentApproval.filename)}/approve`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Approval granted!');
            closeApprovalModal();
            loadApprovals();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error approving:', error);
        alert('Error approving action');
    }
}

async function rejectApproval() {
    if (!currentApproval) return;
    
    const reason = prompt('Enter rejection reason (optional):');
    if (reason === null) return;
    
    try {
        const response = await fetch(`/api/approvals/${encodeURIComponent(currentApproval.filename)}/reject`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Approval rejected');
            closeApprovalModal();
            loadApprovals();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error rejecting:', error);
        alert('Error rejecting approval');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
