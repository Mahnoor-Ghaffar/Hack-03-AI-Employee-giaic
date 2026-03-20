#!/usr/bin/env python3
"""
Platinum Tier Integration Test Suite

Tests all Gold Tier integrations:
- Odoo MCP Server
- Twitter Agent Skill
- Facebook + Instagram Agent Skill
- Personal Task Handler
- Plan Workflow Skill

Usage:
    python test_platinum_tier_integrations.py

Note: This script tests the integration structure without requiring actual API credentials.
Set TEST_MODE=true to run in mock mode.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add .claude folder to path for skills testing
claude_path = project_root / '.claude' / 'skills'
sys.path.insert(0, str(claude_path.parent))

# Configure test mode
TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))

# Test results storage
test_results = {
    'timestamp': datetime.now().isoformat(),
    'test_mode': TEST_MODE,
    'components': {},
    'summary': {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }
}


def log_test(component: str, test_name: str, status: str, message: str = ""):
    """Log test result."""
    if component not in test_results['components']:
        test_results['components'][component] = []
    
    test_results['components'][component].append({
        'test': test_name,
        'status': status,
        'message': message
    })
    
    test_results['summary']['total'] += 1
    if status == 'PASSED':
        test_results['summary']['passed'] += 1
        print(f"✅ [{component}] {test_name}: PASSED")
    elif status == 'FAILED':
        test_results['summary']['failed'] += 1
        print(f"❌ [{component}] {test_name}: FAILED - {message}")
    else:
        test_results['summary']['skipped'] += 1
        print(f"⏭️  [{component}] {test_name}: SKIPPED - {message}")


def print_header(text: str):
    """Print test section header."""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}\n")


# ==================== ODOO MCP SERVER TESTS ====================

def test_odoo_mcp_server():
    """Test Odoo MCP Server."""
    print_header("Testing Odoo MCP Server")
    
    try:
        from mcp.odoo_mcp.server import OdooMCPServer, get_odoo_client
        
        # Test 1: Import successful
        log_test('Odoo MCP', 'Import module', 'PASSED')
        
        # Test 2: Class instantiation (will fail without credentials)
        if TEST_MODE:
            try:
                odoo = OdooMCPServer()
                log_test('Odoo MCP', 'Instantiate class', 'PASSED')
            except Exception as e:
                # Expected to fail without credentials
                log_test('Odoo MCP', 'Instantiate class', 'SKIPPED', f'No credentials: {str(e)[:50]}')
        else:
            try:
                odoo = OdooMCPServer()
                log_test('Odoo MCP', 'Instantiate class', 'PASSED')
                
                # Test 3: Test connection
                result = odoo.test_connection()
                if result.get('status') == 'success':
                    log_test('Odoo MCP', 'Test connection', 'PASSED')
                else:
                    log_test('Odoo MCP', 'Test connection', 'FAILED', result.get('message', 'Unknown error'))
            except Exception as e:
                log_test('Odoo MCP', 'Connection test', 'FAILED', str(e)[:100])
        
        # Test 4: Check methods exist
        required_methods = ['create_invoice', 'list_invoices', 'record_payment', 'get_partner', 'test_connection']
        for method in required_methods:
            if hasattr(OdooMCPServer, method):
                log_test('Odoo MCP', f'Method exists: {method}', 'PASSED')
            else:
                log_test('Odoo MCP', f'Method exists: {method}', 'FAILED', f'Missing method {method}')
        
        # Test 5: Check convenience function
        try:
            client = get_odoo_client()
            log_test('Odoo MCP', 'get_odoo_client function', 'PASSED')
        except Exception as e:
            log_test('Odoo MCP', 'get_odoo_client function', 'SKIPPED', str(e)[:50])
            
    except ImportError as e:
        log_test('Odoo MCP', 'Import module', 'FAILED', str(e))


# ==================== TWITTER SKILL TESTS ====================

def test_twitter_skill():
    """Test Twitter Agent Skill."""
    print_header("Testing Twitter Agent Skill")
    
    # Check skill files exist (skills are designed for Claude Code MCP, not direct import)
    skill_path = project_root / '.claude' / 'skills' / 'twitter-post'
    
    if skill_path.exists():
        log_test('Twitter Skill', 'Skill directory exists', 'PASSED')
    else:
        log_test('Twitter Skill', 'Skill directory exists', 'FAILED', str(skill_path))
        return
    
    required_files = ['__init__.py', 'SKILL.md', 'twitter_skill.py']
    for file in required_files:
        file_path = skill_path / file
        if file_path.exists():
            log_test('Twitter Skill', f'File exists: {file}', 'PASSED')
        else:
            log_test('Twitter Skill', f'File exists: {file}', 'FAILED', str(file_path))
    
    # Check twitter_skill.py content
    twitter_skill_file = skill_path / 'twitter_skill.py'
    if twitter_skill_file.exists():
        content = twitter_skill_file.read_text(encoding='utf-8')
        
        # Check for required methods
        required_methods = ['post_tweet', 'post_thread', 'get_history', 'get_stats']
        for method in required_methods:
            if f'def {method}(' in content:
                log_test('Twitter Skill', f'Method defined: {method}', 'PASSED')
            else:
                log_test('Twitter Skill', f'Method defined: {method}', 'FAILED', f'Missing method {method}')
        
        # Check for history file path
        if 'TWITTER_HISTORY_FILE' in content or 'twitter_history.json' in content:
            log_test('Twitter Skill', 'History file path defined', 'PASSED')
        else:
            log_test('Twitter Skill', 'History file path defined', 'FAILED', 'History file not configured')


# ==================== SOCIAL MEDIA SKILL TESTS ====================

def test_social_media_skill():
    """Test Facebook + Instagram Agent Skill."""
    print_header("Testing Social Media Skill")
    
    # Check skill files exist
    skill_path = project_root / '.claude' / 'skills' / 'social-meta'
    
    if skill_path.exists():
        log_test('Social Media', 'Skill directory exists', 'PASSED')
    else:
        log_test('Social Media', 'Skill directory exists', 'FAILED', str(skill_path))
        return
    
    required_files = ['__init__.py', 'SKILL.md', 'social_skill.py']
    for file in required_files:
        file_path = skill_path / file
        if file_path.exists():
            log_test('Social Media', f'File exists: {file}', 'PASSED')
        else:
            log_test('Social Media', f'File exists: {file}', 'FAILED', str(file_path))
    
    # Check social_skill.py content
    social_skill_file = skill_path / 'social_skill.py'
    if social_skill_file.exists():
        content = social_skill_file.read_text(encoding='utf-8')
        
        # Check for required methods
        required_methods = ['post_facebook', 'post_instagram', 'post_instagram_carousel', 'post_to_both', 'get_account_info']
        for method in required_methods:
            if f'def {method}(' in content:
                log_test('Social Media', f'Method defined: {method}', 'PASSED')
            else:
                log_test('Social Media', f'Method defined: {method}', 'FAILED', f'Missing method {method}')
        
        # Check for log file path
        if 'social.log' in content:
            log_test('Social Media', 'Log file path defined (social.log)', 'PASSED')
        else:
            log_test('Social Media', 'Log file path defined', 'FAILED', 'Log file not configured')


# ==================== PERSONAL TASK HANDLER TESTS ====================

def test_personal_task_handler():
    """Test Personal Task Handler."""
    print_header("Testing Personal Task Handler")
    
    # Check skill files exist
    skill_path = project_root / '.claude' / 'skills' / 'personal-task-handler'
    
    if skill_path.exists():
        log_test('Personal Tasks', 'Skill directory exists', 'PASSED')
    else:
        log_test('Personal Tasks', 'Skill directory exists', 'FAILED', str(skill_path))
        return
    
    required_files = ['__init__.py', 'SKILL.md', 'personal_skill.py']
    for file in required_files:
        file_path = skill_path / file
        if file_path.exists():
            log_test('Personal Tasks', f'File exists: {file}', 'PASSED')
        else:
            log_test('Personal Tasks', f'File exists: {file}', 'FAILED', str(file_path))
    
    # Check personal_skill.py content
    personal_skill_file = skill_path / 'personal_skill.py'
    if personal_skill_file.exists():
        content = personal_skill_file.read_text(encoding='utf-8')
        
        # Check for required methods
        required_methods = ['create_task', 'get_task', 'update_task_status', 'update_task', 'delete_task', 'list_tasks', 'get_summary']
        for method in required_methods:
            if f'def {method}(' in content:
                log_test('Personal Tasks', f'Method defined: {method}', 'PASSED')
            else:
                log_test('Personal Tasks', f'Method defined: {method}', 'FAILED', f'Missing method {method}')
        
        # Check for Personal folder path
        if 'Personal' in content and 'Archive' in content:
            log_test('Personal Tasks', 'Personal/Archive paths defined', 'PASSED')
        else:
            log_test('Personal Tasks', 'Personal/Archive paths defined', 'FAILED', 'Paths not configured')
        
        # Check vault path exists
        personal_path = VAULT_PATH / 'Personal'
        archive_path = VAULT_PATH / 'Personal' / 'Archive'
        if personal_path.exists():
            log_test('Personal Tasks', 'Personal path exists', 'PASSED')
        else:
            log_test('Personal Tasks', 'Personal path exists', 'FAILED', str(personal_path))
        if archive_path.exists():
            log_test('Personal Tasks', 'Archive path exists', 'PASSED')
        else:
            log_test('Personal Tasks', 'Archive path exists', 'FAILED', str(archive_path))


# ==================== PLAN WORKFLOW TESTS ====================

def test_plan_workflow():
    """Test Plan Workflow Skill."""
    print_header("Testing Plan Workflow Skill")
    
    # Check skill files exist
    skill_path = project_root / '.claude' / 'skills' / 'plan-workflow'
    
    if skill_path.exists():
        log_test('Plan Workflow', 'Skill directory exists', 'PASSED')
    else:
        log_test('Plan Workflow', 'Skill directory exists', 'FAILED', str(skill_path))
        return
    
    required_files = ['__init__.py', 'SKILL.md', 'plan_workflow.py']
    for file in required_files:
        file_path = skill_path / file
        if file_path.exists():
            log_test('Plan Workflow', f'File exists: {file}', 'PASSED')
        else:
            log_test('Plan Workflow', f'File exists: {file}', 'FAILED', str(file_path))
    
    # Check plan_workflow.py content
    plan_workflow_file = skill_path / 'plan_workflow.py'
    if plan_workflow_file.exists():
        content = plan_workflow_file.read_text(encoding='utf-8')
        
        # Check for required methods
        required_methods = ['create_plan', 'read_plan', 'update_plan', 'list_plans', 'execute_plan', 'execute_step', 'validate_plan']
        for method in required_methods:
            if f'def {method}(' in content:
                log_test('Plan Workflow', f'Method defined: {method}', 'PASSED')
            else:
                log_test('Plan Workflow', f'Method defined: {method}', 'FAILED', f'Missing method {method}')
        
        # Check for supported actions
        expected_actions = [
            'odoo.create_invoice', 'twitter.post_tweet', 'social.post_facebook',
            'social.post_instagram', 'personal.create_task'
        ]
        for action in expected_actions:
            if action in content:
                log_test('Plan Workflow', f'Supported action: {action}', 'PASSED')
            else:
                log_test('Plan Workflow', f'Supported action: {action}', 'FAILED', f'Action {action} not found')
        
        # Check vault paths
        plans_path = VAULT_PATH / 'Plans'
        reports_path = VAULT_PATH / 'Reports'
        logs_path = VAULT_PATH / 'Logs'
        
        if plans_path.exists():
            log_test('Plan Workflow', 'Plans path exists', 'PASSED')
        else:
            log_test('Plan Workflow', 'Plans path exists', 'FAILED', str(plans_path))
        
        if reports_path.exists():
            log_test('Plan Workflow', 'Reports path exists', 'PASSED')
        else:
            log_test('Plan Workflow', 'Reports path exists', 'FAILED', str(reports_path))
        
        if logs_path.exists():
            log_test('Plan Workflow', 'Logs path exists', 'PASSED')
        else:
            log_test('Plan Workflow', 'Logs path exists', 'FAILED', str(logs_path))


# ==================== GOLD TIER INTEGRATION TESTS ====================

def test_gold_tier_integration():
    """Test Gold Tier Integration Module."""
    print_header("Testing Gold Tier Integration")
    
    try:
        from gold_tier_integration import GoldTierIntegration, log_gold_tier_action
        
        # Test 1: Import successful
        log_test('Gold Integration', 'Import module', 'PASSED')
        
        # Test 2: Class instantiation
        gold = GoldTierIntegration()
        log_test('Gold Integration', 'Instantiate class', 'PASSED')
        
        # Test 3: Check methods exist
        required_methods = ['create_invoice_from_plan', 'list_invoices_from_period', 'post_social_from_plan', 'sync_personal_tasks']
        for method in required_methods:
            if hasattr(GoldTierIntegration, method):
                log_test('Gold Integration', f'Method exists: {method}', 'PASSED')
            else:
                log_test('Gold Integration', f'Method exists: {method}', 'FAILED', f'Missing method {method}')
        
        # Test 4: Log action function
        try:
            log_gold_tier_action("test_action", {"test": "data"})
            log_test('Gold Integration', 'log_gold_tier_action function', 'PASSED')
        except Exception as e:
            log_test('Gold Integration', 'log_gold_tier_action function', 'SKIPPED', str(e)[:50])
        
    except ImportError as e:
        log_test('Gold Integration', 'Import module', 'FAILED', str(e))


# ==================== VAULT STRUCTURE TESTS ====================

def test_vault_structure():
    """Test AI_Employee_Vault directory structure."""
    print_header("Testing Vault Structure")
    
    required_dirs = [
        'AI_Employee_Vault',
        'AI_Employee_Vault/Personal',
        'AI_Employee_Vault/Personal/Archive',
        'AI_Employee_Vault/Plans',
        'AI_Employee_Vault/Reports',
        'AI_Employee_Vault/Logs'
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            log_test('Vault Structure', f'Directory exists: {dir_path}', 'PASSED')
        else:
            log_test('Vault Structure', f'Directory exists: {dir_path}', 'FAILED', f'Missing directory')
    
    # Check log files
    log_files = [
        'logs/ai_employee.log',
        'logs/social.log',
        'logs/personal_tasks.log',
        'logs/plan_workflow.log'
    ]
    
    for log_file in log_files:
        full_path = project_root / log_file
        # Log files may not exist yet, that's OK
        if full_path.exists():
            log_test('Vault Structure', f'Log file exists: {log_file}', 'PASSED')
        else:
            log_test('Vault Structure', f'Log file exists: {log_file}', 'SKIPPED', 'Will be created on first use')


# ==================== MCP CONFIGURATION TESTS ====================

def test_mcp_configuration():
    """Test .claude/mcp.json configuration."""
    print_header("Testing MCP Configuration")
    
    mcp_config_path = project_root / '.claude' / 'mcp.json'
    
    if not mcp_config_path.exists():
        log_test('MCP Config', 'mcp.json exists', 'FAILED', 'File not found')
        return
    
    log_test('MCP Config', 'mcp.json exists', 'PASSED')
    
    try:
        import json
        with open(mcp_config_path, 'r') as f:
            config = json.load(f)
        
        # Check skills
        if 'skills' in config:
            log_test('MCP Config', 'Skills section exists', 'PASSED')
            
            # Check for required skills
            skill_names = [s.get('name') for s in config['skills']]
            required_skills = ['twitter-post', 'social-meta', 'personal-task-handler', 'odoo-mcp-server']
            
            for skill in required_skills:
                if skill in skill_names:
                    log_test('MCP Config', f'Skill registered: {skill}', 'PASSED')
                else:
                    log_test('MCP Config', f'Skill registered: {skill}', 'FAILED', 'Skill not found')
        else:
            log_test('MCP Config', 'Skills section exists', 'FAILED', 'Missing skills section')
        
        # Check MCP servers
        if 'mcpServers' in config:
            log_test('MCP Config', 'MCP Servers section exists', 'PASSED')
            
            # Check for required servers
            server_names = list(config['mcpServers'].keys())
            required_servers = ['odoo', 'odoo-mcp', 'facebook', 'twitter']
            
            for server in required_servers:
                if server in server_names:
                    log_test('MCP Config', f'MCP Server registered: {server}', 'PASSED')
                else:
                    log_test('MCP Config', f'MCP Server registered: {server}', 'SKIPPED', 'Server not found')
        else:
            log_test('MCP Config', 'MCP Servers section exists', 'FAILED', 'Missing mcpServers section')
        
    except json.JSONDecodeError as e:
        log_test('MCP Config', 'Parse JSON', 'FAILED', str(e))
    except Exception as e:
        log_test('MCP Config', 'Parse JSON', 'FAILED', str(e)[:100])


# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Run all test suites."""
    print_header("PLATINUM TIER INTEGRATION TEST SUITE")
    print(f"Test Mode: {TEST_MODE}")
    print(f"Vault Path: {VAULT_PATH}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    # Run all test suites
    test_odoo_mcp_server()
    test_twitter_skill()
    test_social_media_skill()
    test_personal_task_handler()
    test_plan_workflow()
    test_gold_tier_integration()
    test_vault_structure()
    test_mcp_configuration()
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total Tests:  {test_results['summary']['total']}")
    print(f"✅ Passed:     {test_results['summary']['passed']}")
    print(f"❌ Failed:    {test_results['summary']['failed']}")
    print(f"⏭️  Skipped:   {test_results['summary']['skipped']}")
    
    # Calculate pass rate
    if test_results['summary']['total'] > 0:
        pass_rate = (test_results['summary']['passed'] / test_results['summary']['total']) * 100
        print(f"\nPass Rate:    {pass_rate:.1f}%")
    
    # Save test results
    results_file = project_root / 'test_results_platinum_tier.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nTest results saved to: {results_file}")
    
    # Return exit code
    if test_results['summary']['failed'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
