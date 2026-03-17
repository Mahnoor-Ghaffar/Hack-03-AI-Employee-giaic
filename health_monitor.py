"""
Platinum Tier Health Monitor
Monitors all processes and auto-recovers failures

This monitor runs on both Cloud and Local machines:
- Cloud: Monitors Cloud Orchestrator, watchers, Odoo Docker
- Local: Monitors Local Orchestrator, WhatsApp watcher, Git sync

Features:
- Process health checks
- Auto-restart failed processes via PM2
- Docker container monitoring
- Disk space and memory alerts
- Human notification on critical failures

Usage:
    python health_monitor.py
"""

import psutil
import subprocess
import time
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from log_manager import setup_logging

# Setup logging
logger = setup_logging(
    log_file="logs/health_monitor.log",
    logger_name="health_monitor"
)


# Process definitions for Cloud agent
CLOUD_PROCESSES = {
    'cloud_agent': 'orchestrator_cloud.py',
    'gmail_watcher': 'gmail_watcher.py',
    'facebook_watcher': 'facebook_watcher.py',
    'twitter_watcher': 'twitter_watcher.py',
    'git_sync': 'git_sync.py',
}

# Process definitions for Local agent
LOCAL_PROCESSES = {
    'local_agent': 'orchestrator_local.py',
    'whatsapp_watcher': 'whatsapp_watcher.py',
    'filesystem_watcher': 'filesystem_watcher.py',
    'git_sync': 'git_sync.py',
}

# Docker containers for Odoo
ODOO_CONTAINERS = ['odoo_prod', 'odoo_db_prod', 'odoo_backup']


class HealthMonitor:
    """
    Platinum Tier Health Monitor
    
    Monitors processes and Docker containers, auto-recovers failures.
    """

    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        agent_type: str = "cloud",
        check_interval: int = 60
    ):
        """
        Initialize Health Monitor.
        
        Args:
            vault_path: Path to AI Employee vault
            agent_type: 'cloud' or 'local'
            check_interval: Check interval in seconds
        """
        self.vault_path = Path(vault_path)
        self.agent_type = agent_type
        self.check_interval = check_interval
        
        # Select processes based on agent type
        self.processes = CLOUD_PROCESSES if agent_type == "cloud" else LOCAL_PROCESSES
        
        # Directories
        self.logs_dir = self.vault_path / "Logs"
        self.signals_dir = self.vault_path / "Signals"
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.signals_dir / "urgent").mkdir(parents=True, exist_ok=True)
        
        # Restart tracking
        self.restart_count = {}
        self.max_restarts_before_alert = 3
        
        # Statistics
        self.stats = {
            'checks_performed': 0,
            'processes_restarted': 0,
            'containers_restarted': 0,
            'alerts_sent': 0,
            'start_time': datetime.now().isoformat(),
            'errors': 0
        }
        
        logger.info(f"Health Monitor initialized for {agent_type} agent")

    def check_process(self, name: str, script: str) -> bool:
        """
        Check if process is running.
        
        Args:
            name: Process name
            script: Script filename to look for
        
        Returns:
            True if process is running
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if script in cmdline and 'python' in cmdline.lower():
                        logger.debug(f"Process {name} is running (PID: {proc.info['pid']})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.warning(f"Process {name} not running")
            return False
            
        except Exception as e:
            logger.error(f"Error checking process {name}: {e}")
            return False

    def restart_process(self, name: str, script: str) -> bool:
        """
        Restart a failed process via PM2.
        
        Args:
            name: Process name
            script: Script filename
        
        Returns:
            True if restart successful
        """
        try:
            logger.warning(f"Restarting {name}...")
            
            # Try PM2 restart
            result = subprocess.run(
                ['pm2', 'restart', name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully restarted {name} via PM2")
                self.restart_count[name] = self.restart_count.get(name, 0) + 1
                self.stats['processes_restarted'] += 1
                
                # Check if restart count exceeds threshold
                if self.restart_count[name] > self.max_restarts_before_alert:
                    logger.error(f"{name} restarted {self.restart_count[name]} times. Alerting human.")
                    self.alert_human(f"Process {name} keeps failing (restarted {self.restart_count[name]} times)")
                
                return True
            else:
                logger.error(f"PM2 restart failed for {name}: {result.stderr}")
                
                # Fallback: Try to start with subprocess
                logger.info(f"Attempting to start {name} with subprocess...")
                proc = subprocess.Popen(
                    ['python', script],
                    cwd=str(Path(__file__).parent),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if proc.poll() is None:
                    logger.info(f"Started {name} with subprocess (PID: {proc.pid})")
                    return True
                else:
                    logger.error(f"Failed to start {name} with subprocess")
                    return False
                    
        except FileNotFoundError:
            logger.warning("PM2 not found, trying subprocess...")
            
            # Fallback: Start with subprocess
            try:
                proc = subprocess.Popen(
                    ['python', script],
                    cwd=str(Path(__file__).parent),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if proc.poll() is None:
                    logger.info(f"Started {name} with subprocess (PID: {proc.pid})")
                    return True
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error restarting {name}: {e}")
            self.stats['errors'] += 1
            return False

    def check_docker_containers(self) -> List[str]:
        """
        Check if Docker containers are running.
        
        Returns:
            List of failed container names
        """
        failed = []
        
        try:
            for container in ODOO_CONTAINERS:
                result = subprocess.run(
                    ['docker', 'inspect', '--format={{.State.Running}}', container],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0 or result.stdout.strip() != 'true':
                    logger.warning(f"Docker container {container} not running")
                    failed.append(container)
                else:
                    logger.debug(f"Docker container {container} is running")
            
        except FileNotFoundError:
            logger.debug("Docker not installed or not in PATH")
        except Exception as e:
            logger.error(f"Error checking Docker containers: {e}")
        
        return failed

    def restart_docker(self, container: str) -> bool:
        """
        Restart a failed Docker container.
        
        Args:
            container: Container name
        
        Returns:
            True if restart successful
        """
        try:
            logger.warning(f"Restarting Docker container {container}...")
            
            result = subprocess.run(
                ['docker-compose', 'restart', container],
                cwd=str(Path(__file__).parent / 'docker'),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully restarted {container}")
                self.stats['containers_restarted'] += 1
                return True
            else:
                logger.error(f"Failed to restart {container}: {result.stderr}")
                
                # Fallback: docker restart
                result = subprocess.run(
                    ['docker', 'restart', container],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully restarted {container} with docker restart")
                    return True
                else:
                    logger.error(f"docker restart also failed for {container}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error restarting Docker {container}: {e}")
            self.stats['errors'] += 1
            return False

    def check_disk_space(self) -> bool:
        """
        Check available disk space.
        
        Returns:
            True if disk space OK
        """
        try:
            usage = psutil.disk_usage(str(self.vault_path))
            
            if usage.percent > 90:
                logger.error(f"Disk space critical: {usage.percent}% used")
                self.alert_human(f"Disk space critical: {usage.percent}% used")
                return False
            elif usage.percent > 80:
                logger.warning(f"Disk space warning: {usage.percent}% used")
            
            logger.debug(f"Disk space: {usage.percent}% used")
            return True
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False

    def check_memory(self) -> bool:
        """
        Check available memory.
        
        Returns:
            True if memory OK
        """
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 95:
                logger.error(f"Memory critical: {memory.percent}% used")
                self.alert_human(f"Memory critical: {memory.percent}% used")
                return False
            elif memory.percent > 85:
                logger.warning(f"Memory warning: {memory.percent}% used")
            
            logger.debug(f"Memory: {memory.percent}% used")
            return True
            
        except Exception as e:
            logger.error(f"Error checking memory: {e}")
            return False

    def check_cpu(self) -> bool:
        """
        Check CPU usage.
        
        Returns:
            True if CPU OK
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 90:
                logger.warning(f"CPU usage high: {cpu_percent}%")
            
            logger.debug(f"CPU: {cpu_percent}%")
            return True
            
        except Exception as e:
            logger.error(f"Error checking CPU: {e}")
            return False

    def alert_human(self, message: str, severity: str = "high"):
        """
        Send alert to human via vault file and console.
        
        Args:
            message: Alert message
            severity: Severity level (low, medium, high, critical)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = self.signals_dir / "urgent" / f"ALERT_{timestamp}.md"
            
            alert_content = f"""---
type: system_alert
severity: {severity}
timestamp: {datetime.now().isoformat()}
agent_type: {self.agent_type}
---

# System Alert

**Severity:** {severity.upper()}
**Agent:** {self.agent_type}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Message

{message}

**Action Required:** Please check the {self.agent_type} agent immediately.
"""
            
            alert_file.write_text(alert_content)
            self.stats['alerts_sent'] += 1
            
            # Also print to console
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(severity.lower(), '🟠')
            
            print(f"\n{severity_emoji} ALERT: {message}")
            
            logger.warning(f"Alert sent: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            self.stats['errors'] += 1

    def write_health_status(self):
        """Write current health status to logs"""
        try:
            health_file = self.logs_dir / "health_status.md"
            
            uptime_seconds = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            # Get system stats
            disk_usage = psutil.disk_usage(str(self.vault_path))
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            health_content = f"""---
last_check: {datetime.now().isoformat()}
status: {'healthy' if self.stats['errors'] < 3 else 'degraded'}
uptime_hours: {uptime_hours:.2f}
agent_type: {self.agent_type}
---

# Health Status - {self.agent_type.capitalize()} Agent

## System Resources
| Resource | Usage | Status |
|----------|-------|--------|
| CPU | {cpu_percent:.1f}% | {'✅' if cpu_percent < 80 else '⚠️'} |
| Memory | {memory.percent:.1f}% | {'✅' if memory.percent < 85 else '⚠️'} |
| Disk | {disk_usage.percent:.1f}% | {'✅' if disk_usage.percent < 80 else '⚠️'} |

## Statistics
- Checks Performed: {self.stats['checks_performed']}
- Processes Restarted: {self.stats['processes_restarted']}
- Containers Restarted: {self.stats['containers_restarted']}
- Alerts Sent: {self.stats['alerts_sent']}
- Errors: {self.stats['errors']}

## Status
{'✅ All systems operational.' if self.stats['errors'] < 3 else '⚠️ Elevated error rate. Check logs.'}

## Process Restarts
"""
            
            if self.restart_count:
                for proc_name, count in self.restart_count.items():
                    health_content += f"- {proc_name}: {count} restarts\n"
            else:
                health_content += "- No restarts\n"
            
            health_file.write_text(health_content)
            logger.debug("Health status written")
            
        except Exception as e:
            logger.error(f"Failed to write health status: {e}")
            self.stats['errors'] += 1

    def run(self):
        """Main monitoring loop"""
        logger.info(f"Health Monitor started for {self.agent_type} agent")
        logger.info(f"Monitoring {len(self.processes)} processes")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        # Send startup notification
        self.alert_human(
            f"Health Monitor started for {self.agent_type} agent",
            severity="low"
        )
        
        while True:
            try:
                self.stats['checks_performed'] += 1
                logger.info(f"=== Health Check {self.stats['checks_performed']} ===")
                
                # Check processes
                for name, script in self.processes.items():
                    if not self.check_process(name, script):
                        logger.warning(f"Process {name} not running, attempting restart...")
                        self.restart_process(name, script)
                
                # Check Docker containers (Cloud only)
                if self.agent_type == "cloud":
                    failed_containers = self.check_docker_containers()
                    for container in failed_containers:
                        logger.warning(f"Docker container {container} not running, restarting...")
                        self.restart_docker(container)
                
                # Check resources
                self.check_disk_space()
                self.check_memory()
                self.check_cpu()
                
                # Write health status
                self.write_health_status()
                
                logger.info(f"Health check {self.stats['checks_performed']} complete")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info(f"Health Monitor shutting down (user interrupt)")
                self.alert_human(
                    f"Health Monitor shutting down for {self.agent_type} agent",
                    severity="high"
                )
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                self.stats['errors'] += 1
                time.sleep(30)


def main():
    """Entry point for Health Monitor"""
    print("=" * 60)
    print("PLATINUM TIER - HEALTH MONITOR")
    print("=" * 60)
    print()
    
    # Determine agent type from environment
    agent_type = os.getenv('PLATINUM_AGENT', 'cloud')
    
    print(f"Agent Type: {agent_type}")
    print(f"Monitoring: {len(CLOUD_PROCESSES if agent_type == 'cloud' else LOCAL_PROCESSES)} processes")
    print()
    
    if agent_type == 'cloud':
        print("Monitoring Cloud processes:")
        for name in CLOUD_PROCESSES:
            print(f"  - {name}")
        print(f"\nMonitoring Docker containers:")
        for container in ODOO_CONTAINERS:
            print(f"  - {container}")
    else:
        print("Monitoring Local processes:")
        for name in LOCAL_PROCESSES:
            print(f"  - {name}")
    
    print()
    print("=" * 60)
    print()
    
    monitor = HealthMonitor(
        vault_path="AI_Employee_Vault",
        agent_type=agent_type,
        check_interval=60
    )
    
    monitor.run()


if __name__ == "__main__":
    main()
