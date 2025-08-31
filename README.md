# Medovina - Unified Honeypot

Medovina is a comprehensive Python-based honeypot application that combines features from multiple honeypot systems including Cowrie, OpenCanary, HoneyPy, and others. It provides a unified platform for detecting and analyzing unauthorized access attempts across various protocols and services.

## Features

### Core Features
- **Unified Configuration**: Single YAML configuration file for all services
- **Plugin Architecture**: Extensible plugin system for easy addition of new services
- **Comprehensive Logging**: Multiple logging outputs (file, JSON, database)
- **Real-time Monitoring**: Built-in monitoring and metrics collection
- **Management Interface**: Web-based management and control interface

### Supported Protocols
- **SSH** - SSH honeypot with authentication simulation
- **HTTP/HTTPS** - Web server honeypot with fake pages
- **Database Services** - MySQL, PostgreSQL, MongoDB honeypots
- **Mail Services** - SMTP, POP3, IMAP honeypots
- **File Services** - FTP honeypot
- **Network Services** - DNS, DHCP honeypots
- **Remote Services** - RDP, VNC honeypots
- **Chat Services** - IRC honeypot
- **VoIP Services** - SIP honeypot
- **Industrial Protocols** - Modbus, DNP3 honeypots
- **Other Services** - Telnet, SNMP, NTP, Redis, Elasticsearch, etc.

## Quick Start

### Prerequisites
- Python 3.8+
- pip for dependency management

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SirCornealious/medovina.git
cd Medovina
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the honeypot:
```bash
# Option 1: Using the management CLI (recommended)
python scripts/manage_honeypot.py run

# Option 2: Direct script execution
python scripts/run_honeypot.py

# Option 3: Direct module execution
python src/main.py
```

### Management CLI

The honeypot now includes a comprehensive CLI for management:

```bash
# Start honeypot
python scripts/manage_honeypot.py start

# Stop honeypot
python scripts/manage_honeypot.py stop

# Check status
python scripts/manage_honeypot.py status

# Show configuration
python scripts/manage_honeypot.py config

# Run interactively (with Ctrl+C to stop)
python scripts/manage_honeypot.py run
```

### Testing

Test the honeypot functionality:
```bash
# Test SSH connection (connect to localhost:22)
ssh user@localhost

# Check honeypot status
python scripts/manage_honeypot.py status

# View logs
tail -f logs/honeypot.log
tail -f logs/attacks.json
```

## Configuration

The honeypot is configured via `config/default_config.yaml`. Key configuration sections:

- **global**: Basic settings (hostname, logging, network)
- **plugins**: Individual service configurations
- **logging**: Logging configuration (file, JSON, database, syslog)
- **analysis**: GeoIP and threat intelligence settings
- **alerts**: Alerting configuration (email, Slack)
- **management**: Web interface settings
- **monitoring**: Performance monitoring settings

### Example Configuration

```yaml
global:
  hostname: "honeypot.local"
  log_level: "INFO"
  bind_address: "0.0.0.0"

plugins:
  ssh:
    enabled: true
    port: 22
    banner: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"
    fake_users:
      - username: "admin"
        password: "admin"

  http:
    enabled: true
    port: 80
    fake_pages:
      - path: "/admin"
        content_type: "text/html"
```

## Architecture

### Core Components

- **Configuration System**: YAML-based configuration with validation
- **Logging System**: Multi-format logging (text, JSON, database)
- **Plugin System**: Extensible plugin architecture for services
- **Server Framework**: Base classes for TCP/UDP server implementations
- **Connection Tracking**: Statistics and connection management

### Plugin Development

Plugins inherit from `HoneypotPlugin` and implement:

```python
from core.plugin import HoneypotPlugin

class MyHoneypotPlugin(HoneypotPlugin):
    async def start(self):
        # Start service logic
        pass

    async def stop(self):
        # Stop service logic
        pass

    def get_status(self):
        # Return plugin status
        return {"status": "running"}
```

## Usage

### Running the Honeypot

```bash
# Start all enabled services
python scripts/run_honeypot.py

# The honeypot will start all enabled plugins based on configuration
# Check logs/honeypot.log for activity
```

### Monitoring

- **Logs**: Check `logs/honeypot.log` for general activity
- **JSON Logs**: Structured attack data in `logs/attacks.json`
- **Status**: Use the management interface or check logs

### Security Considerations

⚠️ **Important**: This honeypot is designed for research and monitoring purposes only. Running it on production networks requires careful consideration:

- Ensure proper network isolation
- Monitor resource usage
- Regularly review and update configurations
- Be aware of legal implications in your jurisdiction

## Recent Fixes & Improvements

### ✅ Critical Stability Fixes (v1.1)
- **Fixed Freeze Issues**: Resolved infinite loop and startup freezing problems
- **Robust Plugin Loading**: Added multiple fallback strategies for plugin imports
- **Graceful Error Handling**: System now exits cleanly when no plugins can be loaded
- **Improved Signal Handling**: Fixed shutdown process with proper timeout handling
- **Management CLI**: Added comprehensive command-line interface for honeypot control
- **Heartbeat Monitoring**: Added periodic status updates to confirm system is alive
- **Configuration Cleanup**: Disabled unimplemented plugins to prevent startup failures

### Development Status

### ✅ Completed
- Core framework and plugin architecture
- Configuration management system
- Logging system with multiple outputs
- Base server framework for TCP/UDP services
- SSH honeypot plugin implementation
- Basic project structure and setup scripts
- **Management CLI interface**
- **Stability and error handling improvements**

### 🚧 In Progress
- Additional protocol plugins (HTTP, database, mail, etc.)
- Web-based management interface
- Monitoring and metrics collection
- Alerting system integration

### 📋 Planned
- GeoIP and threat intelligence integration
- Advanced attack analysis and reporting
- Comprehensive testing suite
- Deployment and packaging tools
- Documentation completion

## Contributing

This project welcomes contributions! Areas for contribution:

- Implementing additional protocol plugins
- Improving the web interface
- Adding new analysis features
- Writing tests and documentation
- Performance optimizations

## License

Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)

Copyright (c) 2025 @Sir_Cornealious on X

This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.

To view a copy of this license, visit: https://creativecommons.org/licenses/by-nc/4.0/

You are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- NonCommercial — You may not use the material for commercial purposes.

For commercial use, please contact: @Sir_Cornealious on X
