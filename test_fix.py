#!/usr/bin/env python3
"""
Test script to verify the honeypot freeze fixes
"""

import asyncio
import sys
import os
import signal
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_honeypot():
    """Test the honeypot startup and shutdown"""
    print("🧪 Testing honeypot fixes...")

    try:
        # Import the main module
        from main import UnifiedHoneypot
        print("✅ Main module imported successfully")

        # Create honeypot instance
        honeypot = UnifiedHoneypot()
        print("✅ Honeypot instance created")

        # Test startup (with timeout)
        print("🚀 Testing startup...")
        startup_task = asyncio.create_task(honeypot.start())

        # Wait for startup to complete or timeout
        try:
            await asyncio.wait_for(startup_task, timeout=15.0)
            print("✅ Startup completed successfully")

            # Test shutdown
            print("🛑 Testing shutdown...")
            await asyncio.wait_for(honeypot.stop(), timeout=5.0)
            print("✅ Shutdown completed successfully")

        except asyncio.TimeoutError:
            print("❌ Test timeout - system may still be frozen")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test"""
    print("🔬 Honeypot Freeze Fix Verification Test")
    print("=" * 50)

    success = await test_honeypot()

    print("=" * 50)
    if success:
        print("✅ All tests passed! Freeze issues appear to be fixed.")
    else:
        print("❌ Tests failed. Issues may still exist.")

if __name__ == "__main__":
    asyncio.run(main())
