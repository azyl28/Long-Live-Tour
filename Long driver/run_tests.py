"""
Test runner for the Long Driver application.

This script ensures that the Python path is set up correctly
so that the tests can find the application's source code.
"""
import unittest
import sys
from pathlib import Path

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Discover and run all tests in the 'tests' directory
loader = unittest.TestLoader()
suite = loader.discover(str(Path(__file__).parent / 'tests'))

runner = unittest.TextTestRunner()
runner.run(suite)
