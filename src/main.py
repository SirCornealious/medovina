#!/usr/bin/env python3
"""
Unified Honeypot Main Application
"""

import asyncio
import signal
import sys
import os
import threading
import time
from typing import Optional, Dict, Any

# Add src directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import config_manager
from core.logger import logger
from core.plugin import plugin_manager


class UnifiedHoneypot:
    """Main honeypot application class"""

    def __init__(self):
        self.running = False
        self.main_logger = logger.get_logger('main')

    async def start(self) -> None:
        """Start the honeypot system"""
        self.main_logger.info("Starting Unified Honeypot...")
        print("🔄 Initializing honeypot system...")

        try:
            print("📋 Loading configuration...")
            # Config is already loaded during initialization

            print("🔌 Loading external plugins...")
            plugin_manager.load_external_plugins()
            print(f"   Found {len(plugin_manager.plugin_classes)} plugin(s)")

            print("🚀 Starting enabled plugins...")
            enabled_plugins = config_manager.get_enabled_plugins()
            print(f"   Starting {len(enabled_plugins)} enabled plugin(s): {list(enabled_plugins.keys())}")

            await plugin_manager.start_all_plugins()

            # Check if any plugins actually started successfully
            active_plugins = plugin_manager.get_all_plugins()
            if not active_plugins:
                print("❌ No plugins could be started successfully!")
                print("   Check plugin implementations and configuration.")
                print("   Only SSH plugin is currently implemented.")
                return

            self.running = True
            self.main_logger.info("Unified Honeypot started successfully")
            print("✅ Honeypot started successfully!")
            print(f"📊 Status: {len(active_plugins)} plugin(s) running")
            print("📝 Logs: Check logs/honeypot.log and logs/attacks.json")
            print("🛑 Press Ctrl+C to stop")

            # Show active plugins
            print("🔧 Active plugins:")
            for plugin_name, plugin in active_plugins.items():
                status = plugin.get_status()
                port = status.get('port', 'unknown')
                print(f"   • {plugin_name}: port {port}")

            # Keep running until interrupted
            print("\n🕐 Honeypot is now running in the background...")
            print("   Use Ctrl+C to stop or check logs for activity")

            # Main monitoring loop with heartbeat
            heartbeat_counter = 0
            while self.running:
                try:
                    await asyncio.sleep(1)
                    heartbeat_counter += 1

                    # Print heartbeat every 60 seconds to show system is alive
                    if heartbeat_counter % 60 == 0:
                        active_plugins = plugin_manager.get_all_plugins()
                        print(f"💓 Honeypot heartbeat - {len(active_plugins)} plugin(s) active")

                except asyncio.CancelledError:
                    print("🔄 Main loop cancelled, shutting down...")
                    break
                except Exception as e:
                    self.main_logger.error(f"Error in main loop: {e}")
                    # Continue running despite errors
                    continue

        except Exception as e:
            self.main_logger.error(f"Error starting honeypot: {e}")
            print(f"❌ Error starting honeypot: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the honeypot system"""
        print("🛑 Stopping Unified Honeypot...")
        self.main_logger.info("Stopping Unified Honeypot...")

        try:
            await plugin_manager.stop_all_plugins()
            self.running = False
            self.main_logger.info("Unified Honeypot stopped")
            print("✅ Unified Honeypot stopped successfully")
        except Exception as e:
            self.main_logger.error(f"Error stopping honeypot: {e}")
            print(f"❌ Error during shutdown: {e}")
            # Ensure running flag is still set to False even on error
            self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'running': self.running,
            'plugins': plugin_manager.get_plugin_status(),
            'config': {
                'hostname': config_manager.get('global.hostname'),
                'bind_address': config_manager.get('global.bind_address'),
                'max_connections': config_manager.get('global.max_connections')
            }
        }


async def main():
    """Main entry point"""
    honeypot = UnifiedHoneypot()

    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
        # Directly set the running flag to break out of the infinite loop
        honeypot.running = False
        # Create task to stop plugins asynchronously
        asyncio.create_task(honeypot.stop())

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await honeypot.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        # Give time for graceful shutdown
        try:
            await asyncio.wait_for(honeypot.stop(), timeout=10.0)
        except asyncio.TimeoutError:
            print("⚠️  Shutdown timeout - forcing exit")
        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        # Attempt graceful shutdown even on fatal errors
        try:
            await honeypot.stop()
        except Exception:
            pass  # Ignore shutdown errors during fatal exit
        sys.exit(1)


if __name__ == "__main__":
    # Run the honeypot
    asyncio.run(main())
