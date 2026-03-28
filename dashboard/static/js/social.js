/**
 * Social Media Page JavaScript
 */

let allPosts = [];
let currentPlatform = 'all';

document.addEventListener('DOMContentLoaded', function() {
    loadSocialPosts();
    setupPlatformTabs();
});

function setupPlatformTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentPlatform = this.dataset.platform;
            filterPosts();
        });
    });
}

async function loadSocialPosts() {
    try {
        const response = await fetch('/api/social/list');
        const result = await response.json();
        
        if (result.success) {
            allPosts = result.data.posts || [];
            renderPosts(allPosts);
        }
    } catch (error) {
        console.error('Error loading social posts:', error);
    }
}

function renderPosts(posts) {
    const container = document.getElementById('posts-grid');
    
    if (posts.length === 0) {
        container.innerHTML = '<div class="loading">No social media posts found</div>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-card ${post.type}" data-platform="${escapeHtml(post.platform)}">
            <div class="post-header">
                <span class="post-platform">${escapeHtml(post.platform)}</span>
                <span class="post-status ${post.status}">${escapeHtml(post.status)}</span>
            </div>
            <div class="post-content">
                ${escapeHtml(post.content || 'No content')}
            </div>
            ${post.scheduled ? `
                <div class="post-footer">
                    <small>Scheduled: ${escapeHtml(post.scheduled)}</small>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function filterPosts() {
    if (currentPlatform === 'all') {
        renderPosts(allPosts);
    } else {
        const filtered = allPosts.filter(p => p.platform === currentPlatform);
        renderPosts(filtered);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
