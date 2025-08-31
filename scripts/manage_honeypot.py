#!/usr/bin/env python3
"""
Honeypot Management CLI
Provides command-line interface for managing and monitoring the honeypot
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent

def load_config() -> Dict[str, Any]:
    """Load honeypot configuration"""
    config_path = get_project_root() / "config" / "default_config.yaml"
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def show_status():
    """Show honeypot status"""
    print("🛡️  Medovina Honeypot Status")
    print("=" * 40)

    config = load_config()

    # Check if honeypot is running (by checking for log activity)
    log_file = get_project_root() / "logs" / "honeypot.log"
    is_running = False

    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "Unified Honeypot started successfully" in last_line:
                        is_running = True
                        print(f"✅ Status: RUNNING")
                    else:
                        print(f"❓ Status: UNKNOWN")
                else:
                    print(f"❌ Status: NOT RUNNING")
        except Exception as e:
            print(f"❌ Error reading log: {e}")
    else:
        print(f"❌ Status: NOT RUNNING (no log file)")

    # Show configuration info
    print(f"\n📋 Configuration:")
    print(f"   Hostname: {config.get('global', {}).get('hostname', 'unknown')}")
    print(f"   Bind Address: {config.get('global', {}).get('bind_address', 'unknown')}")
    print(f"   Max Connections: {config.get('global', {}).get('max_connections', 'unknown')}")

    # Show enabled plugins
    plugins = config.get('plugins', {})
    enabled_plugins = [name for name, plugin_config in plugins.items()
                      if plugin_config.get('enabled', False)]

    print(f"\n🔌 Enabled Plugins ({len(enabled_plugins)}):")
    for plugin in enabled_plugins:
        plugin_config = plugins[plugin]
        if plugin == 'ssh' and plugin_config.get('enabled'):
            port = plugin_config.get('port', 'unknown')
            print(f"   • SSH Honeypot (Port {port})")
        elif plugin == 'http' and plugin_config.get('enabled'):
            port = plugin_config.get('port', 'unknown')
            print(f"   • HTTP Honeypot (Port {port})")
        else:
            print(f"   • {plugin.upper()} Honeypot")

    # Management interface info
    mgmt = config.get('management', {})
    if mgmt.get('enabled', False):
        port = mgmt.get('port', 8080)
        print(f"\n🌐 Management Interface:")
        print(f"   Port: {port}")
        print("   Status: Not implemented yet")
    print()

def show_recent_attacks(limit: int = 10):
    """Show recent attacks from JSON log"""
    print("🎯 Recent Attacks")
    print("=" * 40)

    attacks_file = get_project_root() / "logs" / "attacks.json"

    if not attacks_file.exists():
        print("No attacks logged yet")
        return

    try:
        attacks = []
        with open(attacks_file, 'r') as f:
            for line in f:
                try:
                    attacks.append(json.loads(line.strip()))
                except:
                    continue

        if not attacks:
            print("No attacks logged yet")
            return

        # Sort by timestamp (most recent first)
        attacks.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        for i, attack in enumerate(attacks[:limit]):
            timestamp = attack.get('timestamp', 'unknown')
            service = attack.get('service', 'unknown')
            source_ip = attack.get('source_ip', 'unknown')
            attack_type = attack.get('attack_type', 'unknown')

            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = timestamp

            print(f"{i+1:2d}. [{time_str}] {service.upper():8} | {source_ip:15} | {attack_type}")

        print(f"\nShowing {min(limit, len(attacks))} of {len(attacks)} total attacks")

    except Exception as e:
        print(f"Error reading attacks log: {e}")

def show_logs(lines: int = 20):
    """Show recent log entries"""
    print("📄 Recent Log Entries")
    print("=" * 40)

    log_file = get_project_root() / "logs" / "honeypot.log"

    if not log_file.exists():
        print("No log file found")
        return

    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()

        recent_lines = all_lines[-lines:]

        for line in recent_lines:
            print(line.strip())

        print(f"\nShowing last {len(recent_lines)} of {len(all_lines)} total lines")

    except Exception as e:
        print(f"Error reading log file: {e}")

def show_help():
    """Show help information"""
    print("🛡️  Medovina Honeypot Management CLI")
    print("=" * 50)
    print("Available commands:")
    print("  status      - Show honeypot status and configuration")
    print("  attacks     - Show recent attacks")
    print("  logs        - Show recent log entries")
    print("  help        - Show this help message")
    print("  exit        - Exit the CLI")
    print()
    print("Usage examples:")
    print("  python3 scripts/manage_honeypot.py status")
    print("  python3 scripts/manage_honeypot.py attacks")
    print("  python3 scripts/manage_honeypot.py logs")
    print()

def interactive_mode():
    """Run in interactive mode"""
    print("🛡️  Medovina Honeypot Management CLI")
    print("Type 'help' for available commands or 'exit' to quit")
    print()

    while True:
        try:
            cmd = input("honeypot> ").strip().lower()

            if cmd == 'exit' or cmd == 'quit':
                print("Goodbye!")
                break
            elif cmd == 'status':
                show_status()
            elif cmd == 'attacks':
                show_recent_attacks()
            elif cmd == 'logs':
                show_logs()
            elif cmd == 'help':
                show_help()
            elif cmd == '':
                continue
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'status':
            show_status()
        elif command == 'attacks':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_recent_attacks(limit)
        elif command == 'logs':
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            show_logs(lines)
        elif command == 'help':
            show_help()
        else:
            print(f"Unknown command: {command}")
            show_help()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
