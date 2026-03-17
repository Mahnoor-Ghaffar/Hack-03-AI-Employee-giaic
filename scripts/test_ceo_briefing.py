#!/usr/bin/env python3
"""
CEO Briefing - Test Suite

Test the CEO briefing generator functionality.

Usage:
    python scripts/test_ceo_briefing.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ceo_briefing import CEOBriefing


def test_get_week_date_range():
    """Test week date range calculation."""
    print("\n" + "=" * 60)
    print("TEST: Week Date Range")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nCurrent week range: {week_start} to {week_end}")
    print("✓ Week date range calculated")
    
    print("\n✅ Week date range test passed!")
    return True


def test_get_tasks_completed():
    """Test getting completed tasks."""
    print("\n" + "=" * 60)
    print("TEST: Get Tasks Completed")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nGetting tasks for: {week_start} to {week_end}")
    tasks = briefing.get_tasks_completed(week_start, week_end)
    
    print(f"✓ Tasks completed: {len(tasks)}")
    
    if tasks:
        print("\nRecent tasks:")
        for task in tasks[:5]:
            print(f"  - {task['description'][:50]} ({task['completed_date']})")
    
    print("\n✅ Get tasks completed test passed!")
    return True


def test_get_emails_sent():
    """Test getting sent emails."""
    print("\n" + "=" * 60)
    print("TEST: Get Emails Sent")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nGetting emails for: {week_start} to {week_end}")
    emails = briefing.get_emails_sent(week_start, week_end)
    
    print(f"✓ Emails sent: {len(emails)}")
    
    if emails:
        print("\nRecent emails:")
        for email in emails[:5]:
            print(f"  - To: {email.get('recipient', 'N/A')[:30]}, Subject: {email.get('subject', 'N/A')[:40]}")
    
    print("\n✅ Get emails sent test passed!")
    return True


def test_get_social_media_activity():
    """Test getting social media activity."""
    print("\n" + "=" * 60)
    print("TEST: Get Social Media Activity")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nGetting social activity for: {week_start} to {week_end}")
    activity = briefing.get_social_media_activity(week_start, week_end)
    
    print(f"✓ Social media activity retrieved")
    print(f"\nPlatform activity:")
    print(f"  LinkedIn: {activity['linkedin']['posts']} posts")
    print(f"  Facebook: {activity['facebook']['posts']} posts")
    print(f"  Instagram: {activity['instagram']['posts']} posts")
    print(f"  Twitter: {activity['twitter']['tweets']} tweets")
    
    print("\n✅ Get social media activity test passed!")
    return True


def test_get_pending_approvals():
    """Test getting pending approvals."""
    print("\n" + "=" * 60)
    print("TEST: Get Pending Approvals")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    print("\nGetting pending approvals...")
    approvals = briefing.get_pending_approvals()
    
    print(f"✓ Pending approvals: {len(approvals)}")
    
    if approvals:
        print("\nPending items:")
        for approval in approvals[:5]:
            print(f"  - {approval['description'][:40]} ({approval['type']})")
    
    print("\n✅ Get pending approvals test passed!")
    return True


def test_get_financial_summary():
    """Test getting financial summary."""
    print("\n" + "=" * 60)
    print("TEST: Get Financial Summary")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nGetting financial summary for: {week_start} to {week_end}")
    summary = briefing.get_financial_summary(week_start, week_end)
    
    print(f"✓ Financial summary retrieved")
    print(f"\nSummary:")
    print(f"  Income: ${summary['income']['total']:,.2f} ({summary['income']['transactions']} transactions)")
    print(f"  Expense: ${summary['expense']['total']:,.2f} ({summary['expense']['transactions']} transactions)")
    print(f"  Net: ${summary['net']:,.2f}")
    print(f"  Margin: {summary['margin']:.1f}%")
    
    print("\n✅ Get financial summary test passed!")
    return True


def test_get_system_health():
    """Test getting system health."""
    print("\n" + "=" * 60)
    print("TEST: Get System Health")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    print("\nGetting system health...")
    health = briefing.get_system_health()
    
    print(f"✓ System health retrieved")
    print(f"\nOverall: {health['overall']}")
    print("\nComponents:")
    for component in health['components']:
        print(f"  {component['name']}: {component['status']} - {component['details']}")
    
    if health['issues']:
        print("\nIssues:")
        for issue in health['issues']:
            print(f"  ⚠️ {issue}")
    
    print("\n✅ Get system health test passed!")
    return True


def test_generate_weekly_briefing():
    """Test generating weekly briefing."""
    print("\n" + "=" * 60)
    print("TEST: Generate Weekly Briefing")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    week_start, week_end = briefing.get_week_date_range()
    
    print(f"\nGenerating weekly briefing: {week_start} to {week_end}")
    result = briefing.generate_weekly_briefing(
        period_start=week_start,
        period_end=week_end
    )
    
    print(f"✓ Status: {result['status']}")
    print(f"✓ Briefing file: {result['briefing_file']}")
    print(f"\nSummary:")
    print(f"  Tasks Completed: {result['summary']['tasks_completed']}")
    print(f"  Emails Sent: {result['summary']['emails_sent']}")
    print(f"  Revenue: ${result['summary']['revenue']:,.2f}")
    print(f"  Net Profit: ${result['summary']['net_profit']:,.2f}")
    print(f"  System Health: {result['system_health']}")
    
    print("\n✅ Generate weekly briefing test passed!")
    return True


def test_generate_daily_briefing():
    """Test generating daily briefing."""
    print("\n" + "=" * 60)
    print("TEST: Generate Daily Briefing")
    print("=" * 60)
    
    briefing = CEOBriefing(vault_path="AI_Employee_Vault")
    
    print("\nGenerating daily briefing...")
    result = briefing.generate_daily_briefing()
    
    print(f"✓ Status: {result['status']}")
    print(f"✓ Briefing file: {result['briefing_file']}")
    print(f"✓ Date: {result['date']}")
    
    print("\n✅ Generate daily briefing test passed!")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CEO BRIEFING - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Week Date Range", test_get_week_date_range),
        ("Get Tasks Completed", test_get_tasks_completed),
        ("Get Emails Sent", test_get_emails_sent),
        ("Get Social Media Activity", test_get_social_media_activity),
        ("Get Pending Approvals", test_get_pending_approvals),
        ("Get Financial Summary", test_get_financial_summary),
        ("Get System Health", test_get_system_health),
        ("Generate Weekly Briefing", test_generate_weekly_briefing),
        ("Generate Daily Briefing", test_generate_daily_briefing)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
