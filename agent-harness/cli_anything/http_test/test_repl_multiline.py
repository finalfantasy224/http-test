#!/usr/bin/env python3
# Test REPL mode with multi-line input

import sys
import io

# Mock stdin for multi-line input
test_input = """curl 'https://httpbin.org/post' \
  -H 'Content-Type: application/json' \
  -d '{\"test\": \"multi-line\"}'
exit
"""

# Use the test input
sys.stdin = io.StringIO(test_input)

# Run REPL
sys.path.insert(0, '.')
from http_test_cli import repl

try:
    repl()
    print("REPL completed")
except Exception as e:
    print(f"Error: {e}")