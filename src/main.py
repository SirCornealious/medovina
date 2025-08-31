#!/usr/bin/env python3
"""
Unified Honeypot Main Application
"""

import asyncio
import signal
import sys
import os
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

        try:
            # Load external plugins
            plugin_manager.load_external_plugins()

            # Start all enabled plugins
            await plugin_manager.start_all_plugins()

            self.running = True
            self.main_logger.info("Unified Honeypot started successfully")

            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.main_logger.error(f"Error starting honeypot: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the honeypot system"""
        self.main_logger.info("Stopping Unified Honeypot...")

        try:
            await plugin_manager.stop_all_plugins()
            self.running = False
            self.main_logger.info("Unified Honeypot stopped")
        except Exception as e:
            self.main_logger.error(f"Error stopping honeypot: {e}")

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
        print(f"\nReceived signal {signum}. Shutting down...")
        asyncio.create_task(honeypot.stop())

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await honeypot.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the honeypot
    asyncio.run(main())
