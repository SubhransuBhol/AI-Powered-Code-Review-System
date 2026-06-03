import sys
import os

# Add the parent directory (backend/) to sys.path so test imports resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
