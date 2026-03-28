/**
 * Accounting Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    loadAccounting();
});

async function loadAccounting() {
    try {
        const response = await fetch('/api/accounting/summary');
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // Update counts
            document.getElementById('invoice-count').textContent = (data.invoices || []).length;
            document.getElementById('transaction-count').textContent = (data.transactions || []).length;
            document.getElementById('report-count').textContent = (data.reports || []).length;
            
            // Render invoices
            renderInvoices(data.invoices || []);
            
            // Render transactions
            renderTransactions(data.transactions || []);
            
            // Render reports
            renderReports(data.reports || []);
        }
    } catch (error) {
        console.error('Error loading accounting data:', error);
    }
}

function renderInvoices(invoices) {
    const container = document.getElementById('invoices-list');
    
    if (invoices.length === 0) {
        container.innerHTML = '<div class="loading">No invoices found</div>';
        return;
    }
    
    container.innerHTML = invoices.map(invoice => `
        <div class="invoice-item">
            <div class="invoice-header">
                <strong>${escapeHtml(invoice.title || 'Invoice')}</strong>
                ${invoice.amount ? `<span class="invoice-amount">${escapeHtml(invoice.amount)}</span>` : ''}
            </div>
            ${invoice.customer ? `<div class="invoice-customer">${escapeHtml(invoice.customer)}</div>` : ''}
            ${invoice.status ? `<div class="invoice-status">${escapeHtml(invoice.status)}</div>` : ''}
        </div>
    `).join('');
}

function renderTransactions(transactions) {
    const container = document.getElementById('transactions-list');
    
    if (transactions.length === 0) {
        container.innerHTML = '<div class="loading">No transactions found</div>';
        return;
    }
    
    container.innerHTML = transactions.map(tx => `
        <div class="transaction-item">
            <span class="transaction-description">${escapeHtml(tx.description)}</span>
            <span class="transaction-amount">${escapeHtml(tx.amount)}</span>
        </div>
    `).join('');
}

function renderReports(reports) {
    const container = document.getElementById('reports-list');
    
    if (reports.length === 0) {
        container.innerHTML = '<div class="loading">No reports found</div>';
        return;
    }
    
    container.innerHTML = reports.map(report => `
        <div class="report-item">
            <i class="fas fa-file-alt"></i>
            <span>${escapeHtml(report.title)}</span>
        </div>
    `).join('');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
