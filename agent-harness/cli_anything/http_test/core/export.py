#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import/Export module for http-test CLI.
"""

import json
import os
from typing import List, Dict, Optional


def export_history(requests: List[Dict], output_path: str) -> bool:
    """Export requests to JSON file.
    
    Args:
        requests: List of request dictionaries
        output_path: Output file path
        
    Returns:
        True if successful
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(requests, f, indent=2, default=str)
        return True
    except Exception:
        return False


def import_history(input_path: str) -> Optional[List[Dict]]:
    """Import requests from JSON file.
    
    Args:
        input_path: Input file path
        
    Returns:
        List of request dictionaries or None
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def format_export_json(requests: List[Dict]) -> str:
    """Format requests as JSON string."""
    return json.dumps(requests, indent=2, default=str)


def validate_import(data: any) -> bool:
    """Validate imported data structure.
    
    Args:
        data: Imported data
        
    Returns:
        True if valid
    """
    if not isinstance(data, list):
        return False
    for item in data:
        if not isinstance(item, dict):
            return False
        required = ['name', 'method', 'url']
        if not all(k in item for k in required):
            return False
    return True