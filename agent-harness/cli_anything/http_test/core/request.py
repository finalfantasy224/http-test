#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP request module for http-test CLI.
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple, BinaryIO


class Response:
    """HTTP response container."""
    
    def __init__(self, status_code: int, reason: str, headers: Dict, 
                 body: str, elapsed_time: float):
        self.status_code = status_code
        self.reason = reason
        self.headers = headers
        self.body = body
        self.elapsed_time = elapsed_time
        self._json = None
    
    @property
    def json(self) -> Optional[Dict]:
        """Parse body as JSON."""
        if self._json is None:
            try:
                self._json = json.loads(self.body)
            except (json.JSONDecodeError, ValueError):
                self._json = None
        return self._json
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'status_code': self.status_code,
            'reason': self.reason,
            'headers': dict(self.headers),
            'body': self.body,
            'elapsed_time': self.elapsed_time
        }
    
    def is_success(self) -> bool:
        """Check if response is 2xx."""
        return 200 <= self.status_code < 300
    
    def is_redirect(self) -> bool:
        """Check if response is 3xx."""
        return 300 <= self.status_code < 400
    
    def is_client_error(self) -> bool:
        """Check if response is 4xx."""
        return 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """Check if response is 5xx."""
        return 500 <= self.status_code < 600


def send_request(method: str, url: str, 
               headers: Optional[Dict] = None,
               body: Optional[str] = None,
               timeout: int = 30,
               verify: bool = True,
               files: Optional[List[Dict[str, str]]] = None) -> Response:
    """Send HTTP request.
    
    Args:
        method: HTTP method (GET, POST, PUT, etc.)
        url: Target URL
        headers: Optional request headers
        body: Optional request body
        timeout: Request timeout in seconds
        verify: SSL certificate verification
        files: Optional upload file specs with field/path/filename
        
    Returns:
        Response object
    """
    start_time = datetime.now()
    
    method_upper = method.upper()
    allowed_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
    if method_upper not in allowed_methods:
        raise ValueError(f"Unsupported HTTP method: {method}")
    if files and method_upper in {'GET', 'HEAD', 'OPTIONS'}:
        raise ValueError(f"{method_upper} requests do not support file upload")

    kwargs = {
        'timeout': timeout,
        'verify': verify,
    }

    request_headers = dict(headers or {})
    opened_files = []
    try:
        if files:
            request_headers = remove_content_type_header(request_headers)
            upload_files, opened_files = open_upload_files(files)
            kwargs['files'] = upload_files
            multipart_data = collect_multipart_data(body)
            if multipart_data:
                kwargs['data'] = multipart_data
        elif body and method_upper in ('POST', 'PUT', 'PATCH', 'DELETE'):
            kwargs['data'] = body

        if request_headers:
            kwargs['headers'] = request_headers

        resp = requests.request(method_upper, url, **kwargs)
    finally:
        for file_obj in opened_files:
            file_obj.close()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    return Response(
        status_code=resp.status_code,
        reason=resp.reason,
        headers=dict(resp.headers),
        body=resp.text,
        elapsed_time=elapsed
    )


def parse_file_spec(file_spec: str) -> Dict[str, str]:
    """Parse a CLI upload spec in field=path or path form."""
    if '=' in file_spec:
        field, path = file_spec.split('=', 1)
        field = field.strip()
        path = path.strip()
    else:
        field = 'file'
        path = file_spec.strip()

    if not field:
        raise ValueError("Upload field name cannot be empty")
    if not path:
        raise ValueError("Upload file path cannot be empty")

    return {
        'field': field,
        'path': path,
        'filename': os.path.basename(path)
    }


def parse_file_specs(file_specs: Tuple[str, ...]) -> List[Dict[str, str]]:
    """Parse multiple CLI upload file specs."""
    return [parse_file_spec(file_spec) for file_spec in file_specs]


def remove_content_type_header(headers: Dict[str, str]) -> Dict[str, str]:
    """Remove Content-Type so requests can add multipart boundary."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() != 'content-type'
    }


def collect_multipart_data(body: Optional[str]) -> Optional[Dict[str, str]]:
    """Convert body text into multipart text fields."""
    if not body:
        return None

    try:
        parsed_body = json.loads(body)
        if isinstance(parsed_body, dict):
            return {str(key): str(value) for key, value in parsed_body.items()}
    except json.JSONDecodeError:
        pass

    return {'body': body}


def open_upload_files(files: List[Dict[str, str]]) -> Tuple[List[Tuple[str, Tuple[str, BinaryIO]]], List[BinaryIO]]:
    """Open upload files and build requests-compatible multipart tuples."""
    opened_files = []
    upload_files = []
    try:
        for file_info in files:
            file_obj = open(file_info['path'], 'rb')
            opened_files.append(file_obj)
            upload_files.append((
                file_info['field'],
                (file_info.get('filename') or os.path.basename(file_info['path']), file_obj)
            ))
        return upload_files, opened_files
    except Exception:
        for file_obj in opened_files:
            file_obj.close()
        raise


def format_response_human(response: Response) -> str:
    """Format response for human display."""
    lines = []
    
    # Status line
    status_color = _get_status_color(response.status_code)
    lines.append("┌" + "─" * 58 + "┐")
    lines.append(f"│  Status: {response.status_code} {response.reason:<42}│")
    lines.append(f"│  Time:  {response.elapsed_time:.3f}s{'':<44}│")
    
    # Size
    size = len(response.body)
    if size < 1024:
        size_text = f"{size} B"
    elif size < 1024 * 1024:
        size_text = f"{size/1024:.2f} KB"
    else:
        size_text = f"{size/(1024*1024):.2f} MB"
    lines.append(f"│  Size:  {size_text:<48}│")
    lines.append("└" + "─" * 58 + "┘")
    
    # Headers
    if response.headers:
        lines.append("\n┌─ Headers ────────────────────────────────────────┐")
        for k, v in response.headers.items():
            lines.append(f"│ {k}: {v}")
        lines.append("└" + "─" * 58 + "┘")
    
    # Body
    lines.append("\n┌─ Body ──────────────────────────────────────────────┐")
    if response.json:
        lines.append(json.dumps(response.json, indent=2, ensure_ascii=False))
    else:
        lines.append(response.body[:5000] if response.body else "(empty)")
    lines.append("└" + "─" * 58 + "┘")
    
    return '\n'.join(lines)


def _get_status_color(code: int) -> str:
    """Get status code color for display."""
    if 200 <= code < 300:
        return 'green'
    elif 300 <= code < 400:
        return 'yellow'
    return 'red'


def format_response_json(response: Response) -> str:
    """Format response as JSON."""
    return json.dumps({
        'success': response.is_success(),
        'status_code': response.status_code,
        'reason': response.reason,
        'headers': dict(response.headers),
        'body': response.body,
        'elapsed_time': response.elapsed_time
    }, indent=2, ensure_ascii=False)


# Alias for convenience
def get(url: str, headers: Optional[Dict] = None, 
        timeout: int = 30, verify: bool = True) -> Response:
    """Send GET request."""
    return send_request('GET', url, headers=headers, 
                       timeout=timeout, verify=verify)


def post(url: str, headers: Optional[Dict] = None, body: Optional[str] = None,
        timeout: int = 30, verify: bool = True,
        files: Optional[List[Dict[str, str]]] = None) -> Response:
    """Send POST request."""
    return send_request('POST', url, headers=headers, body=body, files=files,
                     timeout=timeout, verify=verify)


def put(url: str, headers: Optional[Dict] = None, body: Optional[str] = None,
        timeout: int = 30, verify: bool = True,
        files: Optional[List[Dict[str, str]]] = None) -> Response:
    """Send PUT request."""
    return send_request('PUT', url, headers=headers, body=body, files=files,
                        timeout=timeout, verify=verify)


def delete(url: str, headers: Optional[Dict] = None,
           timeout: int = 30, verify: bool = True,
           files: Optional[List[Dict[str, str]]] = None) -> Response:
    """Send DELETE request."""
    return send_request('DELETE', url, headers=headers, files=files,
                        timeout=timeout, verify=verify)


def patch(url: str, headers: Optional[Dict] = None, body: Optional[str] = None,
         timeout: int = 30, verify: bool = True,
         files: Optional[List[Dict[str, str]]] = None) -> Response:
    """Send PATCH request."""
    return send_request('PATCH', url, headers=headers, body=body, files=files,
                        timeout=timeout, verify=verify)
