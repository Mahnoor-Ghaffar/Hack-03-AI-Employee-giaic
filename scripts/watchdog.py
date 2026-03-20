#!/usr/bin/env python3
# =============================================================================
# System Watchdog
# =============================================================================
# Monitors orchestrator and watcher processes
# Restarts stopped processes automatically
# Logs status every 5 minutes to /vault/logs/system_health.md
# =============================================================================

import os
import sys
import json
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# =============================================================================
# Configuration
# =============================================================================

# Base paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
VAULT_ROOT = PROJECT_ROOT / "AI_Employee_Vault"
LOGS_DIR = PROJECT_ROOT / "logs"

# Health log location
HEALTH_LOG = VAULT_ROOT / "Logs" / "system_health.md"

# PM2 process names to monitor
CRITICAL_PROCESSES = [
    "orchestrator",
    "orchestrator_gold",
]

WATCHER_PROCESSES = [
    "gmail_watcher",
    "linkedin_watcher",
    "linkedin_poster",
    "facebook_watcher",
    "twitter_watcher",
    "whatsapp_watcher",
    "filesystem_watcher",
]

SUPPORT_PROCESSES = [
    "health_monitor",
    "git_sync",
    "mcp_executor",
]

ALL_PROCESSES = CRITICAL_PROCESSES + WATCHER_PROCESSES + SUPPORT_PROCESSES

# Restart settings
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN_SECONDS = 30

# Status check settings
STATUS_CHECK_INTERVAL = 60  # 1 minute
HEALTH_LOG_INTERVAL = 300   # 5 minutes


# =============================================================================
# Data Structures
# =============================================================================

class ProcessStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERRORED = "errored"
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass
class ProcessInfo:
    """Information about a monitored process"""
    name: str
    status: str
    pid: Optional[int]
    uptime: Optional[str]
    memory: Optional[str]
    cpu: Optional[str]
    restart_count: int = 0
    last_restart: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    timestamp: str
    overall_status: str
    total_processes: int
    running_processes: int
    stopped_processes: int
    errored_processes: int
    processes: List[ProcessInfo]
    restart_events: List[Dict]
    system_info: Dict


# =============================================================================
# Process Monitor
# =============================================================================

class ProcessMonitor:
    """Monitors and manages PM2 processes"""
    
    def __init__(self):
        self.restart_attempts: Dict[str, int] = {}
        self.last_restart: Dict[str, float] = {}
    
    def check_pm2_installed(self) -> bool:
        """Check if PM2 is installed"""
        try:
            result = subprocess.run(
                ["pm2", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_process_list(self) -> List[ProcessInfo]:
        """Get status of all PM2 processes"""
        processes = []
        
        try:
            # Get PM2 process list in JSON format
            result = subprocess.run(
                ["pm2", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error getting PM2 list: {result.stderr}")
                return self._create_offline_processes()
            
            pm2_data = json.loads(result.stdout)
            
            # Build status for monitored processes
            pm2_status = {p.get("name"): p for p in pm2_data}
            
            for proc_name in ALL_PROCESSES:
                if proc_name in pm2_status:
                    p = pm2_status[proc_name]
                    proc_info = ProcessInfo(
                        name=proc_name,
                        status=p.get("pm2_env", {}).get("status", "unknown"),
                        pid=p.get("pid"),
                        uptime=p.get("pm2_env", {}).get("pm_uptime", "N/A"),
                        memory=p.get("monit", {}).get("memory", 0),
                        cpu=p.get("monit", {}).get("cpu", 0),
                    )
                else:
                    proc_info = ProcessInfo(
                        name=proc_name,
                        status="offline",
                        pid=None,
                        uptime=None,
                        memory=None,
                        cpu=None,
                    )
                processes.append(proc_info)
            
        except subprocess.TimeoutExpired:
            print("Timeout getting PM2 process list")
            return self._create_offline_processes()
        except json.JSONDecodeError as e:
            print(f"Error parsing PM2 JSON: {e}")
            return self._create_offline_processes()
        except Exception as e:
            print(f"Error checking processes: {e}")
            return self._create_offline_processes()
        
        return processes
    
    def _create_offline_processes(self) -> List[ProcessInfo]:
        """Create offline status for all processes"""
        return [
            ProcessInfo(
                name=name,
                status="offline",
                pid=None,
                uptime=None,
                memory=None,
                cpu=None,
            )
            for name in ALL_PROCESSES
        ]
    
    def restart_process(self, name: str) -> bool:
        """Restart a PM2 process"""
        # Check cooldown
        now = datetime.now().timestamp()
        if name in self.last_restart:
            elapsed = now - self.last_restart[name]
            if elapsed < RESTART_COOLDOWN_SECONDS:
                print(f"[{name}] Restart cooldown active ({elapsed:.0f}s elapsed)")
                return False
        
        # Check max attempts
        if name not in self.restart_attempts:
            self.restart_attempts[name] = 0
        
        if self.restart_attempts[name] >= MAX_RESTART_ATTEMPTS:
            print(f"[{name}] Max restart attempts reached ({MAX_RESTART_ATTEMPTS})")
            return False
        
        try:
            print(f"[{name}] Restarting process...")
            result = subprocess.run(
                ["pm2", "restart", name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.restart_attempts[name] += 1
                self.last_restart[name] = now
                print(f"[{name}] Restarted successfully (attempt {self.restart_attempts[name]})")
                return True
            else:
                print(f"[{name}] Restart failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[{name}] Restart timeout")
            return False
        except Exception as e:
            print(f"[{name}] Restart error: {e}")
            return False
    
    def start_process(self, name: str) -> bool:
        """Start a stopped PM2 process"""
        try:
            print(f"[{name}] Starting process...")
            result = subprocess.run(
                ["pm2", "start", name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"[{name}] Started successfully")
                return True
            else:
                print(f"[{name}] Start failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[{name}] Start error: {e}")
            return False
    
    def reset_restart_counter(self, name: str):
        """Reset restart counter for a process"""
        if name in self.restart_attempts:
            self.restart_attempts[name] = 0
    
    def get_restart_events(self) -> List[Dict]:
        """Get recent restart events"""
        events = []
        for name, count in self.restart_attempts.items():
            if count > 0:
                events.append({
                    "process": name,
                    "restart_count": count,
                    "last_restart": self.last_restart.get(name),
                })
        return events


# =============================================================================
# Health Logger
# =============================================================================

class HealthLogger:
    """Writes health status to markdown log file"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write_health_report(self, health: SystemHealth):
        """Write health status to markdown file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine overall status emoji
        if health.overall_status == "healthy":
            status_emoji = "🟢"
        elif health.overall_status == "degraded":
            status_emoji = "🟡"
        else:
            status_emoji = "🔴"
        
        content = f"""# System Health Report

**Generated:** {timestamp}
**Overall Status:** {status_emoji} {health.overall_status.upper()}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Processes | {health.total_processes} |
| Running | {health.running_processes} ✅ |
| Stopped | {health.stopped_processes} ⏹️ |
| Errored | {health.errored_processes} ❌ |

---

## Process Status

### Critical Processes

| Process | Status | PID | Memory | CPU | Uptime |
|---------|--------|-----|--------|-----|--------|
"""
        
        # Add critical processes
        for proc in health.processes:
            if proc.name in CRITICAL_PROCESSES:
                status_icon = self._status_icon(proc.status)
                memory_mb = f"{proc.memory / 1024 / 1024:.1f}MB" if proc.memory else "N/A"
                content += f"| {proc.name} | {status_icon} {proc.status} | {proc.pid or 'N/A'} | {memory_mb} | {proc.cpu or 'N/A'}% | {proc.uptime or 'N/A'} |\n"
        
        content += """
### Watcher Processes

| Process | Status | PID | Memory | CPU | Uptime |
|---------|--------|-----|--------|-----|--------|
"""
        
        # Add watcher processes
        for proc in health.processes:
            if proc.name in WATCHER_PROCESSES:
                status_icon = self._status_icon(proc.status)
                memory_mb = f"{proc.memory / 1024 / 1024:.1f}MB" if proc.memory else "N/A"
                content += f"| {proc.name} | {status_icon} {proc.status} | {proc.pid or 'N/A'} | {memory_mb} | {proc.cpu or 'N/A'}% | {proc.uptime or 'N/A'} |\n"
        
        content += """
### Support Processes

| Process | Status | PID | Memory | CPU | Uptime |
|---------|--------|-----|--------|-----|--------|
"""
        
        # Add support processes
        for proc in health.processes:
            if proc.name in SUPPORT_PROCESSES:
                status_icon = self._status_icon(proc.status)
                memory_mb = f"{proc.memory / 1024 / 1024:.1f}MB" if proc.memory else "N/A"
                content += f"| {proc.name} | {status_icon} {proc.status} | {proc.pid or 'N/A'} | {memory_mb} | {proc.cpu or 'N/A'}% | {proc.uptime or 'N/A'} |\n"
        
        # Add restart events
        if health.restart_events:
            content += """
---

## Restart Events

| Process | Restart Count | Last Restart |
|---------|---------------|--------------|
"""
            for event in health.restart_events:
                last_restart = datetime.fromtimestamp(event["last_restart"]).strftime("%Y-%m-%d %H:%M:%S") if event.get("last_restart") else "N/A"
                content += f"| {event['process']} | {event['restart_count']} | {last_restart} |\n"
        
        # Add system info
        content += f"""
---

## System Information

| Property | Value |
|----------|-------|
| Hostname | {health.system_info.get('hostname', 'N/A')} |
| Platform | {health.system_info.get('platform', 'N/A')} |
| Python | {health.system_info.get('python_version', 'N/A')} |
| Check Time | {health.system_info.get('check_time', 'N/A')} |

---

*Report generated by System Watchdog*
"""
        
        # Write to file
        with open(self.log_path, 'w') as f:
            f.write(content)
        
        print(f"Health report written to: {self.log_path}")
    
    def _status_icon(self, status: str) -> str:
        """Get icon for process status"""
        icons = {
            "online": "✅",
            "running": "✅",
            "stopped": "⏹️",
            "errored": "❌",
            "offline": "❌",
        }
        return icons.get(status, "❓")


# =============================================================================
# System Watchdog
# =============================================================================

class SystemWatchdog:
    """Main watchdog controller"""
    
    def __init__(self):
        self.monitor = ProcessMonitor()
        self.logger = HealthLogger(HEALTH_LOG)
        self.last_health_log = 0
        self.running = True
    
    def check_and_heal(self):
        """Check all processes and restart if needed"""
        processes = self.monitor.get_process_list()
        
        for proc in processes:
            # Check if process needs restart
            if proc.status in ["stopped", "errored", "offline"]:
                print(f"[{proc.name}] Process is {proc.status} - attempting restart")
                
                if proc.status == "offline":
                    self.monitor.start_process(proc.name)
                else:
                    self.monitor.restart_process(proc.name)
            else:
                # Process is running, reset restart counter
                self.monitor.reset_restart_counter(proc.name)
    
    def log_health_status(self):
        """Log current health status"""
        processes = self.monitor.get_process_list()
        
        # Calculate statistics
        running = sum(1 for p in processes if p.status in ["online", "running"])
        stopped = sum(1 for p in processes if p.status in ["stopped", "offline"])
        errored = sum(1 for p in processes if p.status == "errored")
        
        # Determine overall status
        critical_running = sum(
            1 for p in processes 
            if p.name in CRITICAL_PROCESSES and p.status in ["online", "running"]
        )
        
        if critical_running == len(CRITICAL_PROCESSES) and errored == 0:
            overall_status = "healthy"
        elif critical_running > 0:
            overall_status = "degraded"
        else:
            overall_status = "critical"
        
        # Get system info
        import platform
        system_info = {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Create health report
        health = SystemHealth(
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            total_processes=len(processes),
            running_processes=running,
            stopped_processes=stopped,
            errored_processes=errored,
            processes=processes,
            restart_events=self.monitor.get_restart_events(),
            system_info=system_info,
        )
        
        # Write report
        self.logger.write_health_report(health)
        
        return overall_status
    
    def run_once(self):
        """Run a single check cycle"""
        print(f"\n{'='*60}")
        print(f"Watchdog check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Check and heal
        self.check_and_heal()
        
        # Log health (every 5 minutes)
        now = datetime.now().timestamp()
        if now - self.last_health_log >= HEALTH_LOG_INTERVAL:
            status = self.log_health_status()
            self.last_health_log = now
            print(f"Health status: {status}")
        else:
            print(f"Next health log in {HEALTH_LOG_INTERVAL - (now - self.last_health_log):.0f}s")
    
    def run_continuous(self):
        """Run watchdog continuously"""
        print("Starting System Watchdog...")
        print(f"Monitoring {len(ALL_PROCESSES)} processes")
        print(f"Health log interval: {HEALTH_LOG_INTERVAL}s")
        print(f"Status check interval: {STATUS_CHECK_INTERVAL}s")
        print("\nPress Ctrl+C to stop")
        
        # Initial health log
        self.log_health_status()
        self.last_health_log = datetime.now().timestamp()
        
        while self.running:
            try:
                self.run_once()
                
                # Wait for next check
                import time
                for _ in range(STATUS_CHECK_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nWatchdog stopped by user")
                break
            except Exception as e:
                print(f"Watchdog error: {e}")
                import time
                time.sleep(5)
    
    def stop(self):
        """Stop the watchdog"""
        self.running = False


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="System Watchdog - Monitor and heal processes")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["check", "status", "run", "restart"],
        default="check",
        help="Command to run"
    )
    parser.add_argument(
        "--process", "-p",
        help="Specific process name (for restart command)"
    )
    
    args = parser.parse_args()
    
    watchdog = SystemWatchdog()
    
    if args.command == "check":
        # Single check and heal
        watchdog.run_once()
    
    elif args.command == "status":
        # Show current status
        watchdog.log_health_status()
        print(f"\nHealth report: {HEALTH_LOG}")
    
    elif args.command == "run":
        # Run continuously
        try:
            watchdog.run_continuous()
        except KeyboardInterrupt:
            watchdog.stop()
    
    elif args.command == "restart":
        # Restart specific process
        if args.process:
            if args.process in ALL_PROCESSES:
                watchdog.monitor.restart_process(args.process)
            else:
                print(f"Unknown process: {args.process}")
                print(f"Valid processes: {', '.join(ALL_PROCESSES)}")
        else:
            print("Please specify a process name with --process")


if __name__ == "__main__":
    main()
