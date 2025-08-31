"""
SSH Honeypot Server Implementation
"""

import asyncio
from typing import Dict, Any, List
from pathlib import Path

from ...core.plugin import HoneypotPlugin
from ...core.server import BaseHoneypotServer
from ...core.logger import logger


class SSHConnectionHandler:
    """Handles individual SSH connections"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                 plugin: 'SSHHoneypotPlugin'):
        self.reader = reader
        self.writer = writer
        self.plugin = plugin
        self.authenticated = False
        self.username = ""
        self.client_addr = writer.get_extra_info('peername')

    async def handle_connection(self) -> None:
        """Handle SSH connection"""
        try:
            # Send SSH banner
            banner = self.plugin.config.get('banner', 'SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1')
            self.writer.write(f"{banner}\r\n".encode())
            await self.writer.drain()

            # Read client version
            client_version = await self.reader.read(1024)
            if client_version:
                self.plugin.log_attack({
                    'service': 'ssh',
                    'client_version': client_version.decode().strip(),
                    'source_ip': self.client_addr[0],
                    'source_port': self.client_addr[1]
                })

            # Handle SSH protocol negotiation and authentication attempts
            while True:
                try:
                    data = await asyncio.wait_for(self.reader.read(1024), timeout=30.0)
                    if not data:
                        break

                    # Parse basic SSH protocol messages
                    await self._process_ssh_message(data)

                except asyncio.TimeoutError:
                    break

        except Exception as e:
            self.plugin.logger.error(f"Error in SSH connection handler: {e}")

    async def _process_ssh_message(self, data: bytes) -> None:
        """Process SSH protocol messages"""
        try:
            # Basic SSH message parsing (simplified)
            if len(data) < 6:  # Minimum SSH packet size
                return

            # Look for authentication attempts
            data_str = data.decode('utf-8', errors='ignore').lower()

            if 'userauth' in data_str or 'password' in data_str:
                # Extract username if possible
                if 'userauth-request' in data_str:
                    # This is a simplified parser - real SSH would need proper protocol parsing
                    self.plugin.log_attack({
                        'service': 'ssh',
                        'attack_type': 'authentication_attempt',
                        'source_ip': self.client_addr[0],
                        'source_port': self.client_addr[1],
                        'payload': data.hex()[:100]  # Log first 100 chars of hex
                    })

            # Send generic SSH disconnect message for failed auth
            if not self.authenticated:
                disconnect_msg = b'\x00\x00\x00\x0c\x01\x00\x00\x00\x02Authentication failed\r\n'
                self.writer.write(disconnect_msg)
                await self.writer.drain()

        except UnicodeDecodeError:
            # Binary SSH data
            self.plugin.log_attack({
                'service': 'ssh',
                'attack_type': 'protocol_probe',
                'source_ip': self.client_addr[0],
                'source_port': self.client_addr[1],
                'payload': data.hex()[:100]
            })


class SSHHoneypotPlugin(HoneypotPlugin):
    """SSH Honeypot Plugin"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.port = config.get('port', 22)
        self.banner = config.get('banner', 'SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1')
        self.fake_users = config.get('fake_users', [])
        self.auth_methods = config.get('auth_methods', ['password', 'keyboard-interactive'])
        self.shell_commands = config.get('shell_commands', ['whoami', 'ls', 'pwd', 'cat', 'echo'])

        # Create server instance
        from ...core.server import BaseHoneypotServer
        self.server = SSHServer(self.name, "0.0.0.0", self.port, self)

    async def start(self) -> None:
        """Start SSH honeypot"""
        self.logger.info(f"Starting SSH honeypot on port {self.port}")
        await self.server.start()

    async def stop(self) -> None:
        """Stop SSH honeypot"""
        self.logger.info("Stopping SSH honeypot")
        await self.server.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        return {
            'name': self.name,
            'type': 'ssh',
            'port': self.port,
            'running': True,  # Would check server status in real implementation
            'banner': self.banner,
            'fake_users_count': len(self.fake_users),
            'auth_methods': self.auth_methods
        }


class SSHServer(BaseHoneypotServer):
    """SSH Server implementation"""

    def __init__(self, name: str, host: str, port: int, plugin: SSHHoneypotPlugin):
        super().__init__(name, host, port)
        self.plugin = plugin

    async def _handle_client(self, reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter,
                           attack_data: Dict[str, Any]) -> None:
        """Handle SSH client connection"""
        handler = SSHConnectionHandler(reader, writer, self.plugin)
        await handler.handle_connection()
