#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
curl command parser module.
Extracted from http_client_enhanced.py for CLI use.
"""

import re
import base64
from typing import Dict, Optional, Tuple


def tokenize_curl(s: str) -> list:
    """Split curl command string by shell rules, respecting single/double quotes.
    
    Args:
        s: curl command string
        
    Returns:
        List of tokens
    """
    # Line continuation: remove backslash + newline
    s = re.sub(r'\\\s*\n', '\n', s)
    s = re.sub(r'\\\s*\r\n', '\n', s)
    
    tokens = []
    i = 0
    n = len(s)
    current = []

    while i < n:
        c = s[i]
        if c in ' \t\n\r':
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            continue
        
        if c == "'":
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            while i < n and s[i] != "'":
                if s[i] == '\\':
                    i += 1
                    if i < n:
                        current.append(s[i])
                    i += 1
                else:
                    current.append(s[i])
                    i += 1
            if i < n:
                i += 1  # skip closing '
            tokens.append(''.join(current))
            current = []
            continue
        
        if c == '"':
            if current:
                tokens.append(''.join(current))
                current = []
            i += 1
            while i < n and s[i] != '"':
                if s[i] == '\\':
                    i += 1
                    if i < n:
                        current.append(s[i])
                    i += 1
                else:
                    current.append(s[i])
                    i += 1
            if i < n:
                i += 1
            tokens.append(''.join(current))
            current = []
            continue
        
        current.append(c)
        i += 1

    if current:
        tokens.append(''.join(current))
    
    return tokens


def parse_curl_command(curl_str: str) -> Dict:
    """Parse curl command string into request parameters.
    
    Args:
        curl_str: curl command string
        
    Returns:
        dict with method, url, headers, body
        
    Raises:
        ValueError: If not a valid curl command
    """
    curl_str = curl_str.strip()
    if not curl_str.lower().startswith('curl'):
        raise ValueError("Not a valid curl command (should start with 'curl')")

    tokens = tokenize_curl(curl_str)
    if not tokens:
        raise ValueError("Cannot parse curl command")

    # Remove leading "curl"
    if tokens[0].lower() == 'curl':
        tokens = tokens[1:]

    method = "GET"
    url = None
    headers = {}
    body = None
    body_parts = []
    i = 0

    while i < len(tokens):
        t = tokens[i]
        t_lower = t.lower()

        if t in ('-X', '--request'):
            i += 1
            if i < len(tokens):
                method = tokens[i].upper()
            i += 1
            continue

        if t in ('-H', '--header'):
            i += 1
            if i < len(tokens):
                h = tokens[i]
                if ':' in h:
                    k, _, v = h.partition(':')
                    headers[k.strip()] = v.strip()
            i += 1
            continue

        if t_lower in ('-d', '--data', '--data-raw', '--data-ascii'):
            i += 1
            if i < len(tokens):
                body_parts.append(tokens[i])
            i += 1
            continue

        if t_lower == '--data-binary':
            i += 1
            if i < len(tokens):
                body_parts.append(tokens[i])
            i += 1
            continue

        if t in ('-u', '--user'):
            i += 1
            if i < len(tokens):
                user_pass = tokens[i]
                if ':' in user_pass:
                    up = user_pass.split(':', 1)
                    raw = (up[0] + ':' + up[1]).encode('utf-8')
                    encoded = base64.b64encode(raw).decode('utf-8')
                    headers['Authorization'] = 'Basic ' + encoded
            i += 1
            continue

        if t in ('-b', '--cookie'):
            i += 1
            if i < len(tokens):
                cookie = tokens[i]
                headers['Cookie'] = cookie
            i += 1
            continue

        if t_lower == '--url':
            i += 1
            if i < len(tokens):
                url = tokens[i]
            i += 1
            continue

        # Unknown flag - skip
        if t.startswith('-'):
            i += 1
            continue

        # Positional argument - treat as URL if not set
        if url is None:
            url = t
        i += 1

    # Combine body parts
    if body_parts:
        body = ''.join(body_parts)

    # Validate
    if not url:
        raise ValueError("No URL found in curl command")

    return {
        'method': method,
        'url': url,
        'headers': headers,
        'body': body
    }


def curl_to_request(curl_command: str) -> Tuple[str, str, Dict, Optional[str]]:
    """Convert curl command to request parameters.
    
    Convenience wrapper around parse_curl_command.
    
    Args:
        curl_command: curl command string
        
    Returns:
        Tuple of (method, url, headers, body)
    """
    parsed = parse_curl_command(curl_command)
    return (
        parsed['method'],
        parsed['url'],
        parsed['headers'],
        parsed['body']
    )


def parse_curl_input(curl_str: str) -> Dict:
    """Parse curl from various input formats.
    
    Handles:
    - Single line curl command
    - Multi-line curl with backslash continuation
    - Curl copy-pasted from browser (may have newlines)
    
    Args:
        curl_str: curl command string (may have newlines)
        
    Returns:
        dict with method, url, headers, body
        
    Raises:
        ValueError: If not a valid curl command
    """
    # Normalize: join lines, remove line breaks within flags
    # Handle cases where browser copy has newlines in unusual places
    curl_str = curl_str.strip()
    
    # If doesn't start with curl, try to find it
    if 'curl' not in curl_str.lower():
        raise ValueError("Not a valid curl command (should contain 'curl')")
    
    # Find curl command start and take everything after it
    # Handle "curl 'URL'" on single line
    curl_start = curl_str.lower().find('curl ')
    if curl_start == -1:
        # Try other formats like "curl\n-X POST"
        lines = curl_str.split('\n')
        for i, line in enumerate(lines):
            if line.strip().lower().startswith('curl'):
                curl_start = curl_str.lower().find(line.strip().lower())
                break
    
    if curl_start >= 0:
        curl_str = curl_str[curl_start:]
    
    return parse_curl_command(curl_str)


if __name__ == "__main__":
    # Test
    test_curl = """curl -X POST 'https://api.example.com/users' -H 'Content-Type: application/json' -d '{"name": "test", "age": 25}'"""
    result = parse_curl_command(test_curl)
    print("Parsed curl command:")
    for k, v in result.items():
        print(f"  {k}: {v}")