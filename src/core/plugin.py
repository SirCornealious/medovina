"""
Plugin system for Unified Honeypot
"""

import os
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional
from pathlib import Path

from .config import config_manager
from .logger import logger


class HoneypotPlugin(ABC):
    """Base class for all honeypot plugins"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logger.get_logger(f'plugin.{name}')
        self.running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the plugin service"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the plugin service"""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information"""
        pass

    def log_attack(self, attack_data: Dict[str, Any]) -> None:
        """Log attack information"""
        attack_data['plugin'] = self.name
        logger.log_attack(attack_data)


class PluginManager:
    """Manages loading and lifecycle of honeypot plugins"""

    def __init__(self):
        self.plugins: Dict[str, HoneypotPlugin] = {}
        self.plugin_classes: Dict[str, Type[HoneypotPlugin]] = {}
        self._load_builtin_plugins()

    def _load_builtin_plugins(self) -> None:
        """Load built-in plugin classes"""
        print("🔍 Loading built-in plugins...")

        # Try multiple import strategies for SSH plugin
        ssh_plugin_loaded = False

        # Strategy 1: Try relative import
        try:
            print("   Importing SSH plugin (relative import)...")
            from ..plugins.ssh import SSHHoneypotPlugin
            self.plugin_classes['ssh'] = SSHHoneypotPlugin
            ssh_plugin_loaded = True
            print(f"   ✅ SSH plugin loaded successfully")
        except ImportError:
            print("   ⚠️  Relative import failed, trying absolute import...")

        # Strategy 2: Try absolute import
        if not ssh_plugin_loaded:
            try:
                print("   Importing SSH plugin (absolute import)...")
                from plugins.ssh.ssh_server import SSHHoneypotPlugin
                self.plugin_classes['ssh'] = SSHHoneypotPlugin
                ssh_plugin_loaded = True
                print(f"   ✅ SSH plugin loaded successfully")
            except ImportError:
                print("   ⚠️  Absolute import failed, trying sys.path approach...")

        # Strategy 3: Try sys.path approach
        if not ssh_plugin_loaded:
            try:
                print("   Importing SSH plugin (sys.path approach)...")
                import sys
                import os
                # Add the plugins directory to path
                plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)

                from ssh.ssh_server import SSHHoneypotPlugin
                self.plugin_classes['ssh'] = SSHHoneypotPlugin
                ssh_plugin_loaded = True
                print(f"   ✅ SSH plugin loaded successfully")
            except ImportError as e:
                print(f"   ❌ All SSH plugin import strategies failed: {e}")
            except Exception as e:
                print(f"   ❌ Error loading SSH plugin: {e}")

        if not ssh_plugin_loaded:
            print("   ⚠️  SSH plugin could not be loaded - SSH functionality will be disabled")

    def load_external_plugins(self, plugin_dir: str = "plugins") -> None:
        """Load external plugins from directory"""
        if not os.path.exists(plugin_dir):
            return

        for item in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, item)
            if os.path.isdir(plugin_path) and not item.startswith('_'):
                self._load_plugin_from_directory(plugin_path)

    def _load_plugin_from_directory(self, plugin_path: str) -> None:
        """Load plugin from directory"""
        plugin_name = os.path.basename(plugin_path)
        init_file = os.path.join(plugin_path, '__init__.py')

        if os.path.exists(init_file):
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_name}", init_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, HoneypotPlugin) and
                        obj != HoneypotPlugin):
                        self.plugin_classes[plugin_name] = obj
                        break

            except Exception as e:
                print(f"Error loading plugin {plugin_name}: {e}")

    def create_plugin(self, name: str, config: Dict[str, Any]) -> Optional[HoneypotPlugin]:
        """Create plugin instance"""
        print(f"   Creating plugin instance: {name}")
        if name in self.plugin_classes:
            try:
                plugin_class = self.plugin_classes[name]
                print(f"   Plugin class found: {plugin_class}")
                plugin = plugin_class(name, config)
                self.plugins[name] = plugin
                print(f"   ✅ Plugin instance created: {name}")
                return plugin
            except Exception as e:
                print(f"   ❌ Error creating plugin {name}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ❌ Plugin class not found for: {name}")
            print(f"      Available plugins: {list(self.plugin_classes.keys())}")
        return None

    def get_plugin(self, name: str) -> Optional[HoneypotPlugin]:
        """Get plugin instance by name"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, HoneypotPlugin]:
        """Get all loaded plugins"""
        return self.plugins

    async def start_all_plugins(self) -> None:
        """Start all enabled plugins"""
        enabled_plugins = config_manager.get_enabled_plugins()
        print(f"🚀 Starting {len(enabled_plugins)} enabled plugin(s)")

        for plugin_name, plugin_config in enabled_plugins.items():
            print(f"   Starting plugin: {plugin_name}")
            plugin = self.create_plugin(plugin_name, plugin_config)
            if plugin:
                try:
                    await plugin.start()
                    plugin.running = True
                    print(f"   ✅ Started plugin: {plugin_name}")
                except Exception as e:
                    print(f"   ❌ Error starting plugin {plugin_name}: {e}")
            else:
                print(f"   ⚠️  Failed to create plugin: {plugin_name}")

    async def stop_all_plugins(self) -> None:
        """Stop all running plugins"""
        for plugin in self.plugins.values():
            if plugin.running:
                try:
                    await plugin.stop()
                    plugin.running = False
                    print(f"Stopped plugin: {plugin.name}")
                except Exception as e:
                    print(f"Error stopping plugin {plugin.name}: {e}")

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        status = {}
        for name, plugin in self.plugins.items():
            status[name] = plugin.get_status()
        return status


# Global plugin manager instance
plugin_manager = PluginManager()
