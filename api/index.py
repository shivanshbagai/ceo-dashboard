import sys
import os

# Ensure the repo root is on the Python path so `backend.api` can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import app
