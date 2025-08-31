"""
Base server framework for honeypot services
"""

import asyncio
import socket
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .logger import logger
from .config import config_manager


class BaseHoneypotServer(ABC):
    """Base class for honeypot network servers"""

    def __init__(self, name: str, host: str = "0.0.0.0", port: int = 0,
                 max_connections: int = 1000, timeout: int = 300):
        self.name = name
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.timeout = timeout
        self.logger = logger.get_logger(f'server.{name}')
        self.server: Optional[asyncio.AbstractServer] = None
        self.active_connections = 0
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def start(self) -> None:
        """Start the server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_connection,
                self.host,
                self.port,
                limit=65536  # Maximum buffer size
            )

            addr = self.server.sockets[0].getsockname()
            self.logger.info(f"{self.name} server started on {addr[0]}:{addr[1]}")

        except Exception as e:
            self.logger.error(f"Failed to start {self.name} server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info(f"{self.name} server stopped")

        self.executor.shutdown(wait=True)

    async def handle_connection(self, reader: asyncio.StreamReader,
                              writer: asyncio.StreamWriter) -> None:
        """Handle incoming connection"""
        client_addr = writer.get_extra_info('peername')
        client_ip, client_port = client_addr[0], client_addr[1]

        self.active_connections += 1

        if self.active_connections > self.max_connections:
            self.logger.warning(f"Connection limit exceeded from {client_ip}:{client_port}")
            writer.close()
            await writer.wait_closed()
            self.active_connections -= 1
            return

        connection_id = f"{client_ip}:{client_port}_{asyncio.current_task().get_name()}"

        self.logger.info(f"New connection from {client_ip}:{client_port} (total: {self.active_connections})")

        try:
            # Log the attack attempt
            attack_data = {
                'service': self.name,
                'source_ip': client_ip,
                'source_port': client_port,
                'destination_port': self.port,
                'protocol': 'tcp',
                'connection_id': connection_id
            }

            # Handle the connection with timeout
            await asyncio.wait_for(
                self._handle_client(reader, writer, attack_data),
                timeout=self.timeout
            )

        except asyncio.TimeoutError:
            self.logger.info(f"Connection timeout from {client_ip}:{client_port}")
        except Exception as e:
            self.logger.error(f"Error handling connection from {client_ip}:{client_port}: {e}")
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

            self.active_connections -= 1
            self.logger.info(f"Connection closed from {client_ip}:{client_port} (total: {self.active_connections})")

    @abstractmethod
    async def _handle_client(self, reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter,
                           attack_data: Dict[str, Any]) -> None:
        """Handle client interaction - to be implemented by subclasses"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return {
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'active_connections': self.active_connections,
            'max_connections': self.max_connections,
            'running': self.server is not None and not self.server.is_served()
        }


class UDPServer(BaseHoneypotServer):
    """Base class for UDP-based honeypot servers"""

    def __init__(self, name: str, host: str = "0.0.0.0", port: int = 0,
                 max_connections: int = 1000, timeout: int = 300):
        super().__init__(name, host, port, max_connections, timeout)
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional['HoneypotUDPProtocol'] = None

    async def start(self) -> None:
        """Start UDP server"""
        try:
            loop = asyncio.get_event_loop()
            self.protocol = HoneypotUDPProtocol(self)

            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: self.protocol,
                local_addr=(self.host, self.port)
            )

            self.logger.info(f"UDP {self.name} server started on {self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Failed to start UDP {self.name} server: {e}")
            raise

    async def stop(self) -> None:
        """Stop UDP server"""
        if self.transport:
            self.transport.close()
            self.logger.info(f"UDP {self.name} server stopped")

    @abstractmethod
    def handle_datagram(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming UDP datagram"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get UDP server status"""
        return {
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'protocol': 'udp',
            'running': self.transport is not None and not self.transport.is_closing()
        }


class HoneypotUDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for honeypot"""

    def __init__(self, server: UDPServer):
        self.server = server
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming datagram"""
        try:
            self.server.handle_datagram(data, addr)
        except Exception as e:
            self.server.logger.error(f"Error handling UDP datagram from {addr}: {e}")


class ConnectionTracker:
    """Tracks connection statistics"""

    def __init__(self):
        self.connections_total = 0
        self.connections_active = 0
        self.connections_by_ip: Dict[str, int] = {}
        self.attacks_logged = 0

    def add_connection(self, ip: str) -> None:
        """Track new connection"""
        self.connections_total += 1
        self.connections_active += 1
        self.connections_by_ip[ip] = self.connections_by_ip.get(ip, 0) + 1

    def remove_connection(self, ip: str) -> None:
        """Track connection removal"""
        self.connections_active = max(0, self.connections_active - 1)

    def log_attack(self) -> None:
        """Track logged attack"""
        self.attacks_logged += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'connections_total': self.connections_total,
            'connections_active': self.connections_active,
            'unique_ips': len(self.connections_by_ip),
            'attacks_logged': self.attacks_logged,
            'top_ips': sorted(self.connections_by_ip.items(),
                            key=lambda x: x[1], reverse=True)[:10]
        }


# Global connection tracker
connection_tracker = ConnectionTracker()
