import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parents[1] / "server"
ROOT = SERVER.parent
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))
