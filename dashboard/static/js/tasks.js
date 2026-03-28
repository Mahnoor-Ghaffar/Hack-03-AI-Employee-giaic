/**
 * Tasks Page JavaScript
 */

let allTasks = [];
let currentTask = null;

document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
});

async function loadTasks() {
    try {
        const response = await fetch('/api/tasks/list');
        const result = await response.json();
        
        if (result.success) {
            allTasks = result.data.tasks || [];
            renderTasks(allTasks);
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function renderTasks(tasks) {
    const tbody = document.getElementById('tasks-table-body');
    
    if (tasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No tasks found</td></tr>';
        return;
    }
    
    tbody.innerHTML = tasks.map(task => `
        <tr>
            <td>${escapeHtml(task.name)}</td>
            <td><span class="task-type">${escapeHtml(task.type)}</span></td>
            <td><span class="priority-badge ${task.priority}">${task.priority}</span></td>
            <td>${escapeHtml(task.status)}</td>
            <td class="text-muted" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
                ${escapeHtml(task.body_preview)}
            </td>
            <td>
                <button class="btn btn-small btn-primary" onclick="viewTask('${escapeHtml(task.name)}')">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
}

function filterTasks() {
    const typeFilter = document.getElementById('filter-type').value;
    const priorityFilter = document.getElementById('filter-priority').value;
    const searchTerm = document.getElementById('search-tasks').value.toLowerCase();
    
    let filtered = allTasks;
    
    if (typeFilter !== 'all') {
        filtered = filtered.filter(t => t.type === typeFilter);
    }
    
    if (priorityFilter !== 'all') {
        filtered = filtered.filter(t => t.priority === priorityFilter);
    }
    
    if (searchTerm) {
        filtered = filtered.filter(t => 
            t.name.toLowerCase().includes(searchTerm) ||
            t.body_preview.toLowerCase().includes(searchTerm)
        );
    }
    
    renderTasks(filtered);
}

async function viewTask(taskName) {
    try {
        const response = await fetch(`/api/tasks/${encodeURIComponent(taskName)}`);
        const result = await response.json();
        
        if (result.success) {
            currentTask = result.data;
            
            document.getElementById('modal-task-title').textContent = taskName;
            document.getElementById('modal-task-content').innerHTML = `
                <div class="task-detail">
                    <h4>Metadata</h4>
                    <table class="meta-table">
                        ${Object.entries(currentTask.metadata || {}).map(([key, value]) => `
                            <tr>
                                <td><strong>${escapeHtml(key)}:</strong></td>
                                <td>${escapeHtml(value)}</td>
                            </tr>
                        `).join('')}
                    </table>
                    
                    <h4 class="mt-2">Content</h4>
                    <div class="task-body">${escapeHtml(currentTask.body)}</div>
                </div>
            `;
            
            document.getElementById('task-modal').classList.add('active');
        }
    } catch (error) {
        console.error('Error loading task:', error);
        alert('Error loading task details');
    }
}

function closeModal() {
    document.getElementById('task-modal').classList.remove('active');
    currentTask = null;
}

async function completeTask() {
    if (!currentTask) return;
    
    const summary = prompt('Enter completion summary (optional):', 'Task completed via dashboard');
    if (summary === null) return;
    
    try {
        const response = await fetch(`/api/tasks/${encodeURIComponent(currentTask.file_name)}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Task marked as complete!');
            closeModal();
            loadTasks();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error completing task:', error);
        alert('Error completing task');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
