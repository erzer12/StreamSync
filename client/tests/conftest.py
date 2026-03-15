"""pytest configuration - adds client/ to sys.path for flat imports."""

import sys
from pathlib import Path

# Insert client/ into sys.path so imports like "from capture import ..." work
client_dir = Path(__file__).parent.parent
if str(client_dir) not in sys.path:
    sys.path.insert(0, str(client_dir))