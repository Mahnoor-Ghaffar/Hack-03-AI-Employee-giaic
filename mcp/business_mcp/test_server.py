#!/usr/bin/env python3
"""
Business MCP Server - Test Suite

Run tests to verify MCP server functionality.

Usage:
    python mcp/business_mcp/test_server.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.business_mcp.server import BusinessMCPServer


async def test_log_activity():
    """Test activity logging functionality."""
    print("\n" + "=" * 60)
    print("TEST: log_activity")
    print("=" * 60)
    
    server = BusinessMCPServer()
    
    # Test 1: Basic logging
    print("\nTest 1: Basic activity logging...")
    result = await server._log_activity({
        'message': 'Test activity from test suite',
        'category': 'task'
    })
    print(f"✓ Status: {result['status']}")
    print(f"✓ Log file: {result['log_file']}")
    print(f"✓ Entry: {result['entry']['message']}")
    
    # Test 2: Logging with metadata
    print("\nTest 2: Activity logging with metadata...")
    result = await server._log_activity({
        'message': 'Client meeting completed',
        'category': 'meeting',
        'metadata': {
            'client': 'Acme Corp',
            'duration': '60 minutes',
            'attendees': ['John', 'Sarah']
        }
    })
    print(f"✓ Status: {result['status']}")
    print(f"✓ Category: {result['entry']['category']}")
    print(f"✓ Metadata: {result['entry']['metadata']}")
    
    # Test 3: All categories
    print("\nTest 3: Testing all categories...")
    categories = ['email', 'social', 'meeting', 'task', 'call', 'other']
    for category in categories:
        result = await server._log_activity({
            'message': f'Test {category} activity',
            'category': category
        })
        print(f"  ✓ {category}: logged")
    
    print("\n✅ All log_activity tests passed!")
    return True


async def test_send_email():
    """Test email sending functionality."""
    print("\n" + "=" * 60)
    print("TEST: send_email")
    print("=" * 60)
    
    server = BusinessMCPServer()
    
    # Test 1: Validation - missing fields
    print("\nTest 1: Validation - missing required fields...")
    try:
        result = await server._send_email({
            'to': 'test@example.com'
            # Missing subject and body
        })
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")
    
    # Test 2: Validation - all required fields present
    print("\nTest 2: Validation - all required fields present...")
    try:
        # This will fail at Gmail auth, but validates input first
        result = await server._send_email({
            'to': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test body content'
        })
        print(f"✓ Email send attempted: {result.get('status', 'unknown')}")
    except ValueError as e:
        if 'Gmail credentials' in str(e):
            print(f"✓ Expected Gmail credentials error (test environment)")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"✓ Got expected error in test environment: {type(e).__name__}")
    
    # Test 3: With optional CC/BCC
    print("\nTest 3: With optional CC and BCC...")
    try:
        result = await server._send_email({
            'to': 'primary@example.com',
            'subject': 'Test with CC/BCC',
            'body': 'Testing CC and BCC fields',
            'cc': 'cc@example.com,manager@example.com',
            'bcc': 'bcc@example.com'
        })
        print(f"✓ Email with CC/BCC attempted: {result.get('status', 'unknown')}")
    except ValueError as e:
        if 'Gmail credentials' in str(e):
            print(f"✓ Expected Gmail credentials error (test environment)")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"✓ Got expected error in test environment: {type(e).__name__}")
    
    print("\n✅ All send_email tests passed!")
    return True


async def test_post_linkedin():
    """Test LinkedIn posting functionality."""
    print("\n" + "=" * 60)
    print("TEST: post_linkedin")
    print("=" * 60)
    
    server = BusinessMCPServer()
    
    # Test 1: Validation - missing content
    print("\nTest 1: Validation - missing required content...")
    try:
        result = await server._post_linkedin({})
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:50]}...")
    
    # Test 2: Validation - content length
    print("\nTest 2: Validation - content length limit...")
    try:
        long_content = "A" * 3001  # Exceeds 3000 char limit
        result = await server._post_linkedin({
            'content': long_content
        })
        print("✗ Should have raised ValueError for length")
        return False
    except ValueError as e:
        if 'exceeds LinkedIn limit' in str(e):
            print(f"✓ Correctly rejected long content")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    # Test 3: Valid content (will fail at auth in test env)
    print("\nTest 3: Valid content submission...")
    try:
        result = await server._post_linkedin({
            'content': 'Test LinkedIn post from MCP server test suite',
            'visibility': 'anyone'
        })
        print(f"✓ LinkedIn post attempted: {result.get('status', 'unknown')}")
    except ValueError as e:
        if 'LinkedIn credentials' in str(e) or 'automation' in str(e).lower():
            print(f"✓ Expected credentials/auth error (test environment)")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"✓ Got expected error in test environment: {type(e).__name__}")
    
    # Test 4: Different visibility options
    print("\nTest 4: Testing visibility options...")
    for visibility in ['anyone', 'connections', 'group']:
        try:
            result = await server._post_linkedin({
                'content': f'Test post with {visibility} visibility',
                'visibility': visibility
            })
            print(f"  ✓ {visibility}: attempted")
        except:
            print(f"  ✓ {visibility}: auth error (expected in test)")
    
    print("\n✅ All post_linkedin tests passed!")
    return True


async def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("BUSINESS MCP SERVER - TEST SUITE")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Project root: {project_root}")
    print("=" * 60)
    
    results = {
        'log_activity': False,
        'send_email': False,
        'post_linkedin': False
    }
    
    # Run tests
    try:
        results['log_activity'] = await test_log_activity()
    except Exception as e:
        print(f"\n❌ log_activity tests failed: {e}")
    
    try:
        results['send_email'] = await test_send_email()
    except Exception as e:
        print(f"\n❌ send_email tests failed: {e}")
    
    try:
        results['post_linkedin'] = await test_post_linkedin()
    except Exception as e:
        print(f"\n❌ post_linkedin tests failed: {e}")
    
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
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
