/**
 * AI Employee - PM2 Ecosystem Configuration
 *
 * Production-ready configuration for 24/7 operation
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 restart ecosystem.config.js
 *   pm2 stop ecosystem.config.js
 *   pm2 monit
 *
 * Features:
 * - Auto-restart on crash
 * - Max memory restart limits
 * - Log rotation
 * - Environment-specific variables
 * - Graceful shutdown
 */

// Get current directory for paths
const path = require('path');
const CURRENT_DIR = process.cwd();
const LOG_DIR = path.join(CURRENT_DIR, 'logs');
const VAULT_DIR = path.join(CURRENT_DIR, 'AI_Employee_Vault');

module.exports = {
  apps: [
    {
      /**
       * Main Orchestrator
       * Coordinates all watchers and skills
       */
      name: 'orchestrator',
      script: './orchestrator.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      kill_timeout: 3000,
      wait_ready: true,
      listen_timeout: 10000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        LOG_FILE: path.join(LOG_DIR, 'ai_employee.log'),
        DEBUG_MODE: 'false',
        MAX_WATCHER_THREADS: '10',
        MAX_MEMORY_MB: '2048',
        TASK_QUEUE_SIZE: '100',
        HEALTH_CHECK_INTERVAL: '60',
        ERROR_NOTIFICATION_ENABLED: 'true',
        ERROR_NOTIFICATION_EMAIL: 'admin@example.com',
      },
      error_file: path.join(LOG_DIR, 'pm2_orchestrator_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_orchestrator_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_orchestrator_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Gold Tier Orchestrator
       * Enhanced orchestrator with social media and Odoo integration
       */
      name: 'orchestrator_gold',
      script: './orchestrator_gold.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '768M',
      kill_timeout: 3000,
      wait_ready: true,
      listen_timeout: 10000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        LOG_FILE: path.join(LOG_DIR, 'ai_employee.log'),
        DEBUG_MODE: 'false',
        ODOO_URL: 'http://localhost:8069',
        ODOO_DB: 'odoo_db',
        ODOO_USERNAME: 'admin',
        MCP_EMAIL_ENABLED: 'true',
        MCP_LINKEDIN_ENABLED: 'true',
        MCP_FACEBOOK_ENABLED: 'true',
        MCP_TWITTER_ENABLED: 'true',
        MCP_ODOO_ENABLED: 'true',
      },
      error_file: path.join(LOG_DIR, 'pm2_orchestrator_gold_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_orchestrator_gold_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_orchestrator_gold_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Gmail Watcher
       * Monitors Gmail for new emails
       */
      name: 'gmail_watcher',
      script: './gmail_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        GMAIL_CHECK_INTERVAL: '120',
        GMAIL_SENDER_EMAIL: 'your-email@gmail.com',
      },
      error_file: path.join(LOG_DIR, 'pm2_gmail_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_gmail_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_gmail_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * LinkedIn Watcher
       * Monitors LinkedIn for notifications and messages
       * Runs continuously with infinite loop
       */
      name: 'linkedin_watcher',
      script: './linkedin_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        LINKEDIN_CHECK_INTERVAL: '300',
      },
      error_file: path.join(LOG_DIR, 'pm2_linkedin_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_linkedin_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_linkedin_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * LinkedIn Poster
       * Auto-posts LinkedIn content with approval workflow
       */
      name: 'linkedin_poster',
      script: './linkedin_poster.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        LINKEDIN_POST_SCHEDULE: '0 9 * * 1-5',
      },
      error_file: path.join(LOG_DIR, 'pm2_linkedin_poster_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_linkedin_poster_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_linkedin_poster_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Facebook Watcher
       * Monitors Facebook Pages and Instagram
       */
      name: 'facebook_watcher',
      script: './facebook_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        FACEBOOK_CHECK_INTERVAL: '600',
      },
      error_file: path.join(LOG_DIR, 'pm2_facebook_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_facebook_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_facebook_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Twitter Watcher
       * Monitors Twitter/X mentions and hashtags
       */
      name: 'twitter_watcher',
      script: './twitter_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        TWITTER_CHECK_INTERVAL: '300',
      },
      error_file: path.join(LOG_DIR, 'pm2_twitter_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_twitter_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_twitter_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * WhatsApp Watcher
       * Monitors WhatsApp messages
       * Runs continuously with infinite loop (browser-based)
       */
      name: 'whatsapp_watcher',
      script: './whatsapp_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        WHATSAPP_CHECK_INTERVAL: '300',
        WHATSAPP_SESSION_PATH: path.join(CURRENT_DIR, 'whatsapp_session'),
        DISPLAY: ':0',  // Required for browser GUI
      },
      error_file: path.join(LOG_DIR, 'pm2_whatsapp_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_whatsapp_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_whatsapp_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Filesystem Watcher
       * Monitors file system for changes
       */
      name: 'filesystem_watcher',
      script: './filesystem_watcher.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        FILESYSTEM_CHECK_INTERVAL: '60',
      },
      error_file: path.join(LOG_DIR, 'pm2_filesystem_watcher_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_filesystem_watcher_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_filesystem_watcher_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Health Monitor
       * Monitors system health and restarts failed processes
       */
      name: 'health_monitor',
      script: './health_monitor.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        HEALTH_CHECK_INTERVAL: '60',
      },
      error_file: path.join(LOG_DIR, 'pm2_health_monitor_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_health_monitor_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_health_monitor_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * Git Sync
       * Syncs vault with remote Git repository
       * Gracefully handles missing remote (local-only mode)
       */
      name: 'git_sync',
      script: './git_sync.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        VAULT_SYNC_INTERVAL: '300',
      },
      error_file: path.join(LOG_DIR, 'pm2_git_sync_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_git_sync_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_git_sync_combined.log'),
      time: true,
      merge_logs: true,
    },
    {
      /**
       * MCP Executor
       * Executes MCP server actions
       * Runs continuously monitoring Pending_Approval folder
       */
      name: 'mcp_executor',
      script: './mcp_executor.py',
      interpreter: './venv/bin/python',
      cwd: CURRENT_DIR,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: VAULT_DIR,
        LOG_LEVEL: 'INFO',
        MCP_TIMEOUT: '120',
      },
      error_file: path.join(LOG_DIR, 'pm2_mcp_executor_error.log'),
      out_file: path.join(LOG_DIR, 'pm2_mcp_executor_out.log'),
      log_file: path.join(LOG_DIR, 'pm2_mcp_executor_combined.log'),
      time: true,
      merge_logs: true,
    },
  ],
};
