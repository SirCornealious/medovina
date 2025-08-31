#!/usr/bin/env python3
"""
Honeypot Management CLI
Provides a command-line interface for managing the honeypot
"""

import argparse
import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

from main import UnifiedHoneypot

class HoneypotManager:
    """CLI manager for the honeypot"""

    def __init__(self):
        self.honeypot = None

    async def start(self, timeout=None):
        """Start the honeypot"""
        print("🚀 Starting Medovina Honeypot...")
        self.honeypot = UnifiedHoneypot()

        try:
            await self.honeypot.start()
            print("✅ Honeypot started successfully!")
        except Exception as e:
            print(f"❌ Failed to start honeypot: {e}")
            return False
        return True

    async def stop(self):
        """Stop the honeypot"""
        if self.honeypot:
            print("🛑 Stopping honeypot...")
            await self.honeypot.stop()
            print("✅ Honeypot stopped successfully!")
        else:
            print("⚠️  Honeypot is not running")

    def status(self):
        """Get honeypot status"""
        if self.honeypot:
            status = self.honeypot.get_status()
            print("📊 Honeypot Status:")
            print(f"   Running: {'✅ Yes' if status['running'] else '❌ No'}")
            print(f"   Plugins: {len(status['plugins'])} active")
            print(f"   Hostname: {status['config']['hostname']}")
            print(f"   Bind Address: {status['config']['bind_address']}")
            print(f"   Max Connections: {status['config']['max_connections']}")
        else:
            print("📊 Honeypot Status: Not initialized")

    def show_config(self):
        """Show current configuration"""
        from core.config import config_manager
        print("⚙️  Current Configuration:")
        print(f"   Hostname: {config_manager.get('global.hostname')}")
        print(f"   Log Level: {config_manager.get('global.log_level')}")
        print(f"   Bind Address: {config_manager.get('global.bind_address')}")
        print(f"   Max Connections: {config_manager.get('global.max_connections')}")

        enabled_plugins = config_manager.get_enabled_plugins()
        print(f"   Enabled Plugins ({len(enabled_plugins)}):")
        for name in enabled_plugins.keys():
            print(f"     • {name}")

def main():
    parser = argparse.ArgumentParser(
        description="Medovina Honeypot Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_honeypot.py start          # Start honeypot
  python manage_honeypot.py stop           # Stop honeypot
  python manage_honeypot.py status         # Show status
  python manage_honeypot.py config         # Show configuration
  python manage_honeypot.py run            # Run interactively
        """
    )

    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status', 'config', 'run'],
        help='Command to execute'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='Timeout for start command in seconds'
    )

    args = parser.parse_args()
    manager = HoneypotManager()

    if args.command == 'start':
        print("🔄 Starting honeypot in background...")
        try:
            success = asyncio.run(manager.start(timeout=args.timeout))
            if success:
                print("✅ Honeypot is now running in the background")
                print("💡 Use 'python manage_honeypot.py stop' to stop it")
            else:
                print("❌ Failed to start honeypot")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n🛑 Startup interrupted by user")
            asyncio.run(manager.stop())
            sys.exit(1)

    elif args.command == 'stop':
        asyncio.run(manager.stop())

    elif args.command == 'status':
        manager.status()

    elif args.command == 'config':
        manager.show_config()

    elif args.command == 'run':
        print("🎮 Running honeypot interactively...")
        print("🛑 Press Ctrl+C to stop")
        try:
            asyncio.run(manager.start())
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
            asyncio.run(manager.stop())

if __name__ == "__main__":
    main()