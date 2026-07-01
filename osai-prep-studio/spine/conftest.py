"""Make ``osai_spine`` importable when pytest runs from the spine/ directory."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
