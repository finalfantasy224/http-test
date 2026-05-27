#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
History management module for http-test CLI.
Uses the existing history_db.py infrastructure.
"""

import json
import sys
import os
from typing import List, Optional, Dict

# Add parent to path for import (original http-test directory)
# Path: agent-harness/cli_anything/http_test/core/history.py -> http-test/
_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)           # http_test
_grandparent = os.path.dirname(_parent)    # cli_anything
_original = os.path.dirname(_grandparent)  # agent-harness
_root = os.path.dirname(_original)          # http-test
sys.path.insert(0, _root)

from history_db import HistoryDB


class HistoryManager:
    """Manages HTTP request history."""
    
    def __init__(self, db_path: str = "http_requests_history.db"):
        """Initialize history manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db = HistoryDB(db_path)
    
    def save(self, name: str, category: str, method: str, url: str,
           headers: Optional[Dict], body: Optional[str],
           response_info: Optional[str] = None) -> int:
        """Save request to history.
        
        Args:
            name: Request name
            category: Category name
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            response_info: Response info string
            
        Returns:
            Request ID
        """
        return self.db.save_request(
            name=name,
            category=category,
            method=method,
            url=url,
            headers=headers,
            body=body,
            response_info=response_info
        )
    
    def list(self, category: Optional[str] = None, detailed: bool = False) -> List[Dict]:
        """List saved requests.
        
        Args:
            category: Optional category filter
            detailed: Include full stored request details
            
        Returns:
            List of request dictionaries
        """
        requests = self.db.get_all_requests(category)
        if detailed:
            detailed_requests = []
            for request_summary in requests:
                request_detail = self.get(request_summary['id'])
                if request_detail:
                    detailed_requests.append(request_detail)
            return detailed_requests
        return requests
    
    def get(self, request_id: int) -> Optional[Dict]:
        """Get request details.
        
        Args:
            request_id: Request ID
            
        Returns:
            Request dictionary or None
        """
        req = self.db.get_request_by_id(request_id)
        if not req:
            return None
        return req
    
    def delete(self, request_id: int) -> bool:
        """Delete request from history.
        
        Args:
            request_id: Request ID
            
        Returns:
            True if deleted
        """
        return self.db.delete_request(request_id)
    
    def list_categories(self) -> List[str]:
        """List all categories.
        
        Returns:
            List of category names
        """
        cats = self.db.get_categories()
        return [c['name'] for c in cats]
    
    def create_category(self, name: str) -> bool:
        """Create new category.
        
        Args:
            name: Category name
            
        Returns:
            True if created
        """
        return self.db.add_category(name)
    
    def search(self, keyword: str) -> List[Dict]:
        """Search requests by keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching requests
        """
        results = self.db.search_requests(keyword)
        return results
    
    def update(self, request_id: int, name: str, category: str, method: str, 
             url: str, headers: Optional[Dict], body: Optional[str]) -> bool:
        """Update existing request.
        
        Args:
            request_id: Request ID
            name: Request name
            category: Category name
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            
        Returns:
            True if updated
        """
        self.db.update_request(request_id, name, category, method, url, headers, body)
        return True
    
    def delete_category(self, name: str) -> bool:
        """Delete category.
        
        Args:
            name: Category name
            
        Returns:
            True if deleted
        """
        return self.db.delete_category(name)

    def import_requests(self, file_path: str) -> int:
        """Import requests from a JSON export file.

        Args:
            file_path: Path to JSON file

        Returns:
            Number of imported requests
        """
        return self.db.import_requests(file_path)

    def export_requests(self, file_path: str, category: Optional[str] = None) -> int:
        """Export saved requests to JSON.

        Exports the full stored request records so round-trips preserve headers,
        body, response metadata, and request ids when available.

        Args:
            file_path: Output JSON file path
            category: Optional category filter

        Returns:
            Number of exported requests
        """
        if category is None:
            return self.db.export_requests(file_path)

        requests = self.list(category, detailed=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2, default=str)
        return len(requests)


def format_history_human(requests: List[Dict]) -> str:
    """Format history list for human display."""
    if not requests:
        return "No requests in history."
    
    lines = []
    for req in requests:
        lines.append(f"[{req['id']}] {req['method']} {req['name']}")
        lines.append(f"    URL: {req['url']}")
        lines.append(f"    Category: {req['category']}")
        lines.append("")
    
    return '\n'.join(lines)


def format_history_json(requests: List[Dict]) -> str:
    """Format history as JSON."""
    import json
    return json.dumps(requests, indent=2, default=str)
