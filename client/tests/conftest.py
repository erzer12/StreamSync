"""
conftest.py – pytest configuration for client tests.

Adds the `client/` directory to sys.path so that flat imports like
`from capture import ...` and `import main` work whether pytest is
invoked from `client/` or from the repository root.
"""

import sys
from pathlib import Path

# Insert client/ directory at the front of sys.path
_CLIENT_DIR = Path(__file__).parent.parent
if str(_CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CLIENT_DIR))
