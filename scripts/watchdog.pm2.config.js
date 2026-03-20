# =============================================================================
# System Watchdog - PM2 Configuration
# =============================================================================
# Add this to your ecosystem.config.js or run as standalone
# =============================================================================

module.exports = {
  apps: [
    {
      /**
       * System Watchdog
       * Monitors all processes and restarts failed ones
       * Logs health status every 5 minutes
       */
      name: 'system_watchdog',
      script: './scripts/watchdog.py',
      interpreter: './venv/bin/python',
      cwd: '/opt/ai-employee',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      kill_timeout: 3000,
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: '/opt/ai-employee/AI_Employee_Vault',
        LOG_LEVEL: 'INFO',
        HEALTH_LOG_INTERVAL: '300',        // 5 minutes
        STATUS_CHECK_INTERVAL: '60',       // 1 minute
        MAX_RESTART_ATTEMPTS: '3',
        RESTART_COOLDOWN_SECONDS: '30',
      },
      error_file: '/opt/ai-employee/logs/pm2_watchdog_error.log',
      out_file: '/opt/ai-employee/logs/pm2_watchdog_out.log',
      log_file: '/opt/ai-employee/logs/pm2_watchdog_combined.log',
      time: true,
      merge_logs: true,
    },
  ],
};
