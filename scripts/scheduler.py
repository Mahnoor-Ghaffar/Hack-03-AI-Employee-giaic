#!/usr/bin/env python3
"""
AI Employee Scheduler - Gold Tier

Schedules and runs automated tasks:
- CEO Weekly Briefing (Monday 7:00 AM)
- Daily system health checks
- Weekly accounting summaries

Usage:
    python scripts/scheduler.py start
    python scripts/ceo_briefing.py auto  # Direct run

For production: Use Windows Task Scheduler or cron
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler')

# Configuration
VAULT_PATH = Path('AI_Employee_Vault')
LOGS_PATH = VAULT_PATH / 'Logs'
SCHEDULER_LOG = LOGS_PATH / 'scheduler.log'

# Ensure logs directory exists
LOGS_PATH.mkdir(parents=True, exist_ok=True)


def run_ceo_briefing():
    """Run CEO weekly briefing."""
    logger.info('Running CEO Weekly Briefing...')
    
    try:
        from scripts.ceo_briefing import CEOBriefing
        
        briefing = CEOBriefing(vault_path=str(VAULT_PATH))
        result = briefing.generate_weekly_briefing()
        
        logger.info(f"CEO briefing generated: {result['briefing_file']}")
        logger.info(f"Tasks: {result['summary']['tasks_completed']}, "
                   f"Revenue: ${result['summary']['revenue']:,.2f}, "
                   f"Health: {result['system_health']}")
        
        return True
        
    except Exception as e:
        logger.error(f'Error running CEO briefing: {e}', exc_info=True)
        return False


def run_daily_health_check():
    """Run daily system health check."""
    logger.info('Running daily health check...')
    
    try:
        from scripts.ceo_briefing import CEOBriefing
        
        briefing = CEOBriefing(vault_path=str(VAULT_PATH))
        health = briefing.get_system_health()
        
        logger.info(f"System health: {health['overall']}")
        
        if health['issues']:
            for issue in health['issues']:
                logger.warning(f"Issue: {issue}")
        
        return True
        
    except Exception as e:
        logger.error(f'Error running health check: {e}', exc_info=True)
        return False


def run_weekly_accounting_summary():
    """Run weekly accounting summary."""
    logger.info('Running weekly accounting summary...')
    
    try:
        from scripts.accounting_manager import AccountingManager
        
        accounting = AccountingManager(vault_path=str(VAULT_PATH))
        result = accounting.generate_weekly_summary()
        
        logger.info(f"Accounting summary: {result['summary_file']}")
        logger.info(f"Income: ${result['totals']['total_income']:,.2f}, "
                   f"Expense: ${result['totals']['total_expense']:,.2f}, "
                   f"Profit: ${result['totals']['net_profit']:,.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f'Error running accounting summary: {e}', exc_info=True)
        return False


def start_scheduler():
    """Start the scheduler (for development/testing only)."""
    logger.info('=' * 60)
    logger.info('AI Employee Scheduler Starting...')
    logger.info('=' * 60)
    logger.info('NOTE: For production, use Windows Task Scheduler or cron')
    logger.info('=' * 60)
    
    # Run initial checks
    logger.info('Running initial tasks...')
    
    # Run CEO briefing
    run_ceo_briefing()
    
    # Run health check
    run_daily_health_check()
    
    # Run accounting summary
    run_weekly_accounting_summary()
    
    logger.info('All scheduled tasks completed.')
    logger.info('Scheduler stopped. Use Task Scheduler for production.')


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='AI Employee Scheduler')
    parser.add_argument('command', choices=['start', 'briefing', 'health', 'accounting'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    logger.info(f'Scheduler command: {args.command}')
    
    if args.command == 'start':
        start_scheduler()
        
    elif args.command == 'briefing':
        run_ceo_briefing()
        
    elif args.command == 'health':
        run_daily_health_check()
        
    elif args.command == 'accounting':
        run_weekly_accounting_summary()
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
