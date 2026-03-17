#!/usr/bin/env python3
"""
Accounting Manager - Test Suite

Test the accounting manager functionality.

Usage:
    python scripts/accounting_manager.py test
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.accounting_manager import AccountingManager


def test_log_transaction():
    """Test transaction logging."""
    print("\n" + "=" * 60)
    print("TEST: Log Transactions")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    # Test 1: Log income
    print("\nTest 1: Logging income transaction...")
    result = accounting.log_transaction(
        date="2026-03-14",
        type="income",
        amount=5000.00,
        description="Client payment - Project Alpha",
        category="revenue",
        reference="INV-001"
    )
    print(f"✓ Status: {result['status']}")
    print(f"✓ Transaction ID: {result['transaction_id']}")
    print(f"✓ File: {result['file']}")
    
    # Test 2: Log expense
    print("\nTest 2: Logging expense transaction...")
    result = accounting.log_transaction(
        date="2026-03-14",
        type="expense",
        amount=150.00,
        description="Software subscription - Adobe Creative Cloud",
        category="software",
        reference="SUB-001"
    )
    print(f"✓ Status: {result['status']}")
    print(f"✓ Transaction ID: {result['transaction_id']}")
    
    # Test 3: Log another expense
    print("\nTest 3: Logging another expense...")
    result = accounting.log_transaction(
        date="2026-03-15",
        type="expense",
        amount=1000.00,
        description="Office Rent - March 2026",
        category="rent",
        reference="RENT-MAR-2026"
    )
    print(f"✓ Status: {result['status']}")
    print(f"✓ Transaction ID: {result['transaction_id']}")
    
    # Test 4: Log another income
    print("\nTest 4: Logging another income...")
    result = accounting.log_transaction(
        date="2026-03-15",
        type="income",
        amount=3000.00,
        description="Client B - Website Design",
        category="revenue",
        reference="INV-002"
    )
    print(f"✓ Status: {result['status']}")
    print(f"✓ Transaction ID: {result['transaction_id']}")
    
    print("\n✅ All log_transaction tests passed!")
    return True


def test_get_transactions():
    """Test retrieving transactions."""
    print("\n" + "=" * 60)
    print("TEST: Get Transactions")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    # Test 1: Get all transactions
    print("\nTest 1: Getting all transactions...")
    transactions = accounting.get_transactions()
    print(f"✓ Total transactions: {len(transactions)}")
    
    # Test 2: Get income only
    print("\nTest 2: Getting income transactions...")
    income = accounting.get_transactions(type="income")
    print(f"✓ Income transactions: {len(income)}")
    for t in income:
        print(f"  - {t['date']}: ${t['amount']:,.2f} - {t['description']}")
    
    # Test 3: Get expenses only
    print("\nTest 3: Getting expense transactions...")
    expenses = accounting.get_transactions(type="expense")
    print(f"✓ Expense transactions: {len(expenses)}")
    for t in expenses:
        print(f"  - {t['date']}: ${t['amount']:,.2f} - {t['description']}")
    
    # Test 4: Get by category
    print("\nTest 4: Getting software expenses...")
    software = accounting.get_transactions(type="expense", category="software")
    print(f"✓ Software expenses: {len(software)}")
    
    print("\n✅ All get_transactions tests passed!")
    return True


def test_get_totals():
    """Test getting totals."""
    print("\n" + "=" * 60)
    print("TEST: Get Totals")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    print("\nTest: Getting accounting totals...")
    totals = accounting.get_totals()
    
    print(f"✓ Total Income:   ${totals['total_income']:,.2f}")
    print(f"✓ Total Expense:  ${totals['total_expense']:,.2f}")
    print(f"✓ Balance:        ${totals['balance']:,.2f}")
    print(f"✓ Transactions:   {totals['transaction_count']}")
    print(f"✓ Income Count:   {totals['income_count']}")
    print(f"✓ Expense Count:  {totals['expense_count']}")
    
    print("\n✅ Get totals test passed!")
    return True


def test_get_balance():
    """Test getting balance."""
    print("\n" + "=" * 60)
    print("TEST: Get Balance")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    print("\nTest: Getting current balance...")
    balance = accounting.get_balance()
    print(f"✓ Current Balance: ${balance:,.2f}")
    
    print("\n✅ Get balance test passed!")
    return True


def test_generate_weekly_summary():
    """Test generating weekly summary."""
    print("\n" + "=" * 60)
    print("TEST: Generate Weekly Summary")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    print("\nTest: Generating weekly summary...")
    result = accounting.generate_weekly_summary()
    
    print(f"✓ Status: {result['status']}")
    print(f"✓ Summary file: {result['summary_file']}")
    print(f"✓ Period: {result['period']['start']} to {result['period']['end']}")
    print(f"✓ Total Income: ${result['totals']['total_income']:,.2f}")
    print(f"✓ Total Expense: ${result['totals']['total_expense']:,.2f}")
    print(f"✓ Net Profit: ${result['totals']['net_profit']:,.2f}")
    
    print("\n✅ Generate weekly summary test passed!")
    return True


def test_generate_monthly_report():
    """Test generating monthly report."""
    print("\n" + "=" * 60)
    print("TEST: Generate Monthly Report")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    print("\nTest: Generating monthly report for March 2026...")
    result = accounting.generate_monthly_report(year=2026, month=3)
    
    print(f"✓ Status: {result['status']}")
    print(f"✓ Report file: {result['report_file']}")
    print(f"✓ Period: {result['period']['month_name']}")
    print(f"✓ Total Income: ${result['totals']['total_income']:,.2f}")
    print(f"✓ Total Expense: ${result['totals']['total_expense']:,.2f}")
    print(f"✓ Net Profit: ${result['totals']['net_profit']:,.2f}")
    print(f"✓ Profit Margin: {result['totals']['profit_margin']:.1f}%")
    
    print("\n✅ Generate monthly report test passed!")
    return True


def test_validation():
    """Test input validation."""
    print("\n" + "=" * 60)
    print("TEST: Input Validation")
    print("=" * 60)
    
    accounting = AccountingManager(vault_path="AI_Employee_Vault")
    
    # Test 1: Invalid type
    print("\nTest 1: Testing invalid type...")
    try:
        accounting.log_transaction(
            date="2026-03-14",
            type="invalid",  # Should be 'income' or 'expense'
            amount=100.00,
            description="Test"
        )
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")
    
    # Test 2: Invalid amount
    print("\nTest 2: Testing invalid amount...")
    try:
        accounting.log_transaction(
            date="2026-03-14",
            type="income",
            amount=-100.00,  # Should be positive
            description="Test"
        )
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")
    
    # Test 3: Zero amount
    print("\nTest 3: Testing zero amount...")
    try:
        accounting.log_transaction(
            date="2026-03-14",
            type="income",
            amount=0,  # Should be positive
            description="Test"
        )
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")
    
    print("\n✅ All validation tests passed!")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ACCOUNTING MANAGER - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Log Transactions", test_log_transaction),
        ("Get Transactions", test_get_transactions),
        ("Get Totals", test_get_totals),
        ("Get Balance", test_get_balance),
        ("Generate Weekly Summary", test_generate_weekly_summary),
        ("Generate Monthly Report", test_generate_monthly_report),
        ("Input Validation", test_validation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
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
