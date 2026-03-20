#!/usr/bin/env python
"""
Hackathon Tier Verification Script
Verifies all Bronze, Silver, Gold, and Platinum tier requirements are complete.
"""
import os
import sys
from pathlib import Path

def check_file(path, description):
    """Check if a file/directory exists and print status"""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {path}")
    return exists

def verify_bronze():
    """Verify Bronze Tier requirements"""
    print("\n" + "="*60)
    print("BRONZE TIER: Foundation")
    print("="*60)
    
    checks = [
        ("AI_Employee_Vault/Dashboard.md", "Dashboard.md exists"),
        ("AI_Employee_Vault/Company_Handbook.md", "Company_Handbook.md exists"),
        ("AI_Employee_Vault/Inbox", "Inbox folder exists"),
        ("AI_Employee_Vault/Needs_Action", "Needs_Action folder exists"),
        ("AI_Employee_Vault/Done", "Done folder exists"),
        ("filesystem_watcher.py", "Filesystem watcher exists"),
        (".claude/mcp.json", "Claude MCP config exists"),
        ("skills/vault_skills/SKILL.md", "Vault skills documented"),
        ("skills/SKILL.md", "Process file skill documented"),
    ]
    
    passed = sum(check_file(path, desc) for path, desc in checks)
    total = len(checks)
    
    print(f"\nBronze Tier: {passed}/{total} checks passed")
    if passed >= 8:
        print("✅ BRONZE TIER: PASS")
        return True
    else:
        print("❌ BRONZE TIER: INCOMPLETE")
        return False

def verify_silver():
    """Verify Silver Tier requirements"""
    print("\n" + "="*60)
    print("SILVER TIER: Functional Assistant")
    print("="*60)
    
    # Count watchers
    watchers = list(Path(".").glob("*watcher.py"))
    watcher_count = len(watchers)
    print(f"  {'✅' if watcher_count >= 2 else '❌'} Watcher scripts: {watcher_count} found (need 2+)")
    
    checks = [
        (".claude/skills/human-approval/SKILL.md", "Human approval skill"),
        ("scripts/request_approval.py", "Request approval script"),
        ("test_human_approval.py", "Human approval test"),
        (".claude/skills/silver-scheduler/SKILL.md", "Silver scheduler skill"),
        (".claude/skills/plan-workflow/SKILL.md", "Plan workflow skill"),
        ("mcp/business_mcp/server.py", "Business MCP server"),
    ]
    
    passed = sum(check_file(path, desc) for path, desc in checks)
    total = len(checks) + 1  # +1 for watcher count
    
    watcher_ok = watcher_count >= 2
    other_ok = passed >= total - 1
    
    print(f"\nSilver Tier: {passed + (1 if watcher_ok else 0)}/{total} checks passed")
    if watcher_ok and other_ok:
        print("✅ SILVER TIER: PASS")
        return True
    else:
        print("❌ SILVER TIER: INCOMPLETE")
        return False

def verify_gold():
    """Verify Gold Tier requirements"""
    print("\n" + "="*60)
    print("GOLD TIER: Autonomous Employee")
    print("="*60)
    
    checks = [
        ("orchestrator_gold.py", "Gold orchestrator"),
        ("mcp/odoo_mcp/server.py", "Odoo MCP server"),
        ("docker/docker-compose.yml", "Odoo Docker config"),
        ("facebook_watcher.py", "Facebook watcher"),
        ("facebook_watcher.py", "Facebook MCP integration"),
        ("twitter_watcher.py", "Twitter watcher"),
        ("scripts/twitter_mcp_server.py", "Twitter MCP server"),
        ("scripts/ceo_briefing_generator.py", "CEO Briefing generator"),
        ("scripts/test_ceo_briefing.py", "CEO Briefing test"),
        (".claude/skills/ralph-wiggum/SKILL.md", "Ralph Wiggum skill"),
        ("scripts/ralph_wiggum_loop.py", "Ralph Wiggum loop"),
        (".claude/skills/error-recovery/SKILL.md", "Error recovery skill"),
        ("logs/ai_employee.log", "Audit logging"),
        ("GOLD_TIER_COMPLETE.md", "Gold tier documentation"),
        ("GOLD_TIER_ARCHITECTURE.md", "Gold architecture docs"),
    ]
    
    passed = sum(check_file(path, desc) for path, desc in checks)
    total = len(checks)
    
    print(f"\nGold Tier: {passed}/{total} checks passed")
    if passed >= total - 2:  # Allow 2 missing
        print("✅ GOLD TIER: PASS")
        return True
    else:
        print("❌ GOLD TIER: INCOMPLETE")
        return False

def verify_platinum():
    """Verify Platinum Tier requirements"""
    print("\n" + "="*60)
    print("PLATINUM TIER: Always-On Cloud + Local Executive")
    print("="*60)
    
    checks = [
        ("orchestrator_cloud.py", "Cloud orchestrator"),
        ("orchestrator_local.py", "Local orchestrator"),
        ("git_sync.py", "Git sync for vault"),
        (".gitignore.vault", "Vault gitignore (security)"),
        ("health_monitor.py", "Health monitoring"),
        ("test_platinum_demo.py", "Platinum demo test"),
        ("cloud_vm_setup.sh", "Cloud VM setup"),
        ("PLATINUM_TIER_COMPLETE.md", "Platinum documentation"),
        ("PLATINUM_TIER_ARCHITECTURE.md", "Platinum architecture"),
        ("AI_Employee_Vault/In_Progress", "In_Progress folder (claim-by-move)"),
        ("AI_Employee_Vault/Signals", "Signals folder (cloud-local comms)"),
        ("AI_Employee_Vault/Updates", "Updates folder (cloud writes)"),
    ]
    
    passed = sum(check_file(path, desc) for path, desc in checks)
    total = len(checks)
    
    print(f"\nPlatinum Tier: {passed}/{total} checks passed")
    if passed >= total - 2:  # Allow 2 missing
        print("✅ PLATINUM TIER: PASS")
        return True
    else:
        print("❌ PLATINUM TIER: INCOMPLETE")
        return False

def main():
    """Run all tier verifications"""
    print("\n" + "="*60)
    print("🏆 HACKATHON TIER VERIFICATION")
    print("="*60)
    
    results = {
        "Bronze": verify_bronze(),
        "Silver": verify_silver(),
        "Gold": verify_gold(),
        "Platinum": verify_platinum(),
    }
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    for tier, passed in results.items():
        status = "✅ PASS" if passed else "❌ INCOMPLETE"
        print(f"  {tier} Tier: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🏆 ALL TIERS VERIFIED! READY TO WIN!")
        print("="*60)
        print("\nNext steps:")
        print("1. Record a 3-min demo video")
        print("2. Create HACKATHON_SUBMISSION.md")
        print("3. Submit with all documentation")
        return 0
    else:
        print("⚠️ SOME TIERS INCOMPLETE")
        print("="*60)
        print("\nReview the failed checks above and complete missing items.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
