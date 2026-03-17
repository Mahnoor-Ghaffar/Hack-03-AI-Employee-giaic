#!/usr/bin/env python3
"""
Business MCP Server - Quick Start Script

This script helps you quickly set up and test the Business MCP Server.

Usage:
    python mcp/business_mcp/quickstart.py
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def print_step(step_num, text):
    """Print formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 60)


def check_python():
    """Check Python version."""
    print_header("BUSINESS MCP SERVER - QUICK START")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    if sys.version_info < (3, 10):
        print("⚠️  Warning: Python 3.10+ recommended")
    else:
        print("✓ Python version OK")


def install_dependencies():
    """Install required dependencies."""
    print_step(1, "Installing Dependencies")
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print(f"✗ Requirements file not found: {requirements_file}")
        return False
    
    print(f"Installing from: {requirements_file}")
    print("This may take a few minutes...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def install_playwright():
    """Install Playwright browsers."""
    print_step(2, "Installing Playwright Browsers")
    
    print("Installing Chromium browser for LinkedIn automation...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        print("✓ Playwright browsers installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Playwright installation warning: {e}")
        print("You can install later with: playwright install")
        return True  # Non-fatal


def check_env():
    """Check environment configuration."""
    print_step(3, "Checking Environment Configuration")
    
    env_file = Path(__file__).parent.parent.parent / '.env'
    
    if env_file.exists():
        print(f"✓ Found .env file: {env_file}")
        
        # Check for required variables
        content = env_file.read_text()
        required_vars = ['VAULT_PATH', 'GMAIL_CREDENTIALS_FILE']
        
        for var in required_vars:
            if var in content:
                print(f"  ✓ {var} configured")
            else:
                print(f"  ⚠️  {var} not found in .env")
        
        return True
    else:
        print(f"✗ .env file not found: {env_file}")
        print("\nCreate .env file with:")
        print("  VAULT_PATH=AI_Employee_Vault")
        print("  GMAIL_CREDENTIALS_FILE=gmail_credentials.json")
        print("  LINKEDIN_EMAIL=your-email@example.com")
        print("  LINKEDIN_PASSWORD=your-password")
        return False


def check_gmail_credentials():
    """Check Gmail credentials."""
    print_step(4, "Checking Gmail Credentials")
    
    creds_file = Path(__file__).parent.parent.parent / 'gmail_credentials.json'
    
    if creds_file.exists():
        print(f"✓ Gmail credentials found: {creds_file}")
        return True
    else:
        print(f"✗ Gmail credentials not found: {creds_file}")
        print("\nGenerate credentials with:")
        print("  python generate_gmail_credentials.py")
        return False


def test_server():
    """Test MCP server."""
    print_step(5, "Testing MCP Server")
    
    print("Running basic server test...")
    
    try:
        from mcp.business_mcp.server import BusinessMCPServer
        print("✓ Server module imported successfully")
        
        # Test instantiation
        server = BusinessMCPServer()
        print("✓ Server instantiated successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import server: {e}")
        return False
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        return False


def show_usage():
    """Show usage instructions."""
    print_header("SETUP COMPLETE!")
    
    print("\n✅ Business MCP Server is ready to use!")
    
    print("\n📖 Usage Instructions:")
    print("\n1. Run the MCP server:")
    print("   python mcp/business_mcp/server.py")
    
    print("\n2. Add to Claude Code MCP configuration:")
    print('   See mcp/business_mcp/README.md for details')
    
    print("\n3. Available tools:")
    print("   - send_email: Send emails via Gmail")
    print("   - post_linkedin: Post to LinkedIn")
    print("   - log_activity: Log business activities")
    
    print("\n4. Run tests:")
    print("   python mcp/business_mcp/test_server.py")
    
    print("\n5. View documentation:")
    print("   mcp/business_mcp/README.md")
    
    print("\n" + "=" * 60)
    print("📧 Support: Check logs/ai_employee.log for issues")
    print("=" * 60)


def main():
    """Main quick start routine."""
    print_header("BUSINESS MCP SERVER - QUICK START GUIDE")
    
    # Check Python
    check_python()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies. Please fix and try again.")
        return 1
    
    # Install Playwright
    install_playwright()
    
    # Check environment
    env_ok = check_env()
    
    # Check Gmail credentials
    gmail_ok = check_gmail_credentials()
    
    # Test server
    if not test_server():
        print("\n❌ Server test failed. Please check configuration.")
        return 1
    
    # Show usage
    show_usage()
    
    # Warnings
    if not env_ok:
        print("\n⚠️  Warning: .env file not configured properly")
    
    if not gmail_ok:
        print("\n⚠️  Warning: Gmail credentials not set up")
        print("   Email sending will not work until credentials are configured")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
