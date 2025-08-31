#!/usr/bin/env python3
"""
Test connection script to verify honeypot functionality
"""

import socket
import time
import sys

def test_ssh_connection(host="localhost", port=22):
    """Test SSH connection to honeypot"""
    try:
        print(f"Testing SSH connection to {host}:{port}...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        sock.connect((host, port))

        # Receive banner
        banner = sock.recv(1024)
        print(f"Received banner: {banner.decode().strip()}")

        # Send client version
        client_version = b"SSH-2.0-TestClient-1.0\r\n"
        sock.send(client_version)

        # Wait a bit and see if we get any response
        time.sleep(1)
        response = sock.recv(1024)
        if response:
            print(f"Received response: {response.hex()}")

        sock.close()
        print("SSH test completed")

    except Exception as e:
        print(f"SSH test failed: {e}")

def test_status_check():
    """Test if honeypot is running by checking logs"""
    try:
        with open("logs/honeypot.log", "r") as f:
            lines = f.readlines()[-5:]  # Last 5 lines
            print("Recent log entries:")
            for line in lines:
                print(f"  {line.strip()}")
    except FileNotFoundError:
        print("Log file not found - honeypot may not be running")
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        test_status_check()
    else:
        test_ssh_connection()
        time.sleep(2)  # Wait for logs to be written
        test_status_check()
