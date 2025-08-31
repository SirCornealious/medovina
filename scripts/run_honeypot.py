#!/usr/bin/env python3
"""
Honeypot Runner Script
"""

import sys
import os
from pathlib import Path

if __name__ == "__main__":
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Add src directory to Python path
    src_dir = project_root / "src"
    sys.path.insert(0, str(src_dir))

    from main import main
    import asyncio

    # Run the honeypot
    asyncio.run(main())
