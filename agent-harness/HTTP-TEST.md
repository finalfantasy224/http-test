# HTTP-TEST CLI Harness Specification

## Purpose

This document defines the CLI architecture for the http-test tool - a Python-based HTTP client testing application. The CLI harness enables agents and users to send HTTP requests, manage history, and parse curl commands from the command line.

## Target Software

- **Name**: http-test
- **Type**: Python HTTP Client Tool (CLI + Tkinter GUI)
- **Location**: `/home/kang-an/demo/http-test`
- **Main Files**:
  - `http_client_enhanced.py` - GUI version with Tkinter
  - `http_client_cli.py` - Existing basic CLI (to be replaced/enhanced)
  - `history_db.py` - SQLite-based history storage

## Supported Operations

### Command Groups

1. **Request Commands** - Send HTTP requests
   - `send` - Send HTTP request with method, URL, headers, body
   - `get` - Shorthand for GET requests
   - `post` - Shorthand for POST requests
   - `put` - Shorthand for PUT requests
   - `delete` - Shorthand for DELETE requests
   - `patch` - Shorthand for PATCH requests
   - File upload support for `send`, `post`, `put`, `patch`, and `delete` via `-F/--file field=path`

2. **History Commands** - Manage request history
   - `history list` - List saved requests
   - `history show` - Show request details
   - `history delete` - Delete history entry
   - `history clear` - Clear all history

3. **Category Commands** - Organize requests
   - `category list` - List categories
   - `category create` - Create new category
   - `category delete` - Delete category

4. **Import/Export** - Data management
   - `import curl` - Parse and import curl command
   - `export` - Export history to JSON
   - `import` - Import history from JSON

5. **Session Commands** - REPL mode
   - Interactive shell for multiple requests
   - State persistence between commands

## State Model

### In-Memory State (REPL mode)
```python
{
    "current_method": "GET",
    "current_url": None,
    "current_headers": {},
    "current_body": None,
    "last_response": None,
    "session_history": []
}
```

### File-Based State
- `http_requests_history.db` - SQLite database
- `~/.http-test/session.json` - Session state file

## Output Formats

### Human-Readable
- Box-drawing characters for tables
- Color-coded status (green=2xx, yellow=3xx, red=4xx/5xx)
- Formatted JSON with syntax highlighting

### Machine-Readable (--json)
```json
{
    "success": true,
    "status_code": 200,
    "reason": "OK",
    "headers": {...},
    "body": "...",
    "elapsed_time": 0.123
}
```

## Architecture

### Core Modules

1. **core/request.py** - HTTP request handling
   - `send_request(method, url, headers, body, timeout, verify)`
   - Response parsing and formatting

2. **core/history.py** - SQLite history management
   - Uses existing `history_db.py` module
   - CRUD operations for saved requests

3. **core/curl_parser.py** - curl command parsing
   - Extracted from `http_client_enhanced.py`
   - Tokenizer with quote handling

4. **core/export.py** - Import/Export functionality
   - JSON serialization of requests
   - Batch import/export operations

### CLI Entry Point

- Package: `cli_anything.http_test`
- Command: `http-test` (via setup.py console_scripts)
- REPL: `http-test` (no args for interactive mode)

## Implementation Notes

### Key Features from Enhanced GUI

1. **curl Import** - Parse curl commands with proper tokenization:
   - Single quotes, double quotes
   - Escaped characters
   - Multi-line (backslash continuation)

2. **History Management** - Uses existing SQLite schema:
    - `requests` table (id, name, category, method, url, headers, body, response_info)
    - `categories` table (id, name, color)
    - CLI import/export should use the full stored request records, not the list-view summaries, so backups round-trip without dropping headers or body data

3. **Multiple HTTP Methods** - Full support:
   - GET, POST, PUT, DELETE
   - PATCH, HEAD, OPTIONS

4. **Multipart File Upload** - Mirrors the enhanced GUI Files tab:
   - `-F/--file field=path` can be repeated for multiple files
   - Bare file paths use the default field name `file`
   - JSON object bodies become multipart form fields
   - Raw bodies become a `body` multipart field
   - Manual `Content-Type` headers are removed so requests can generate a valid multipart boundary

### REPL Features

- Tab completion for commands
- Command history (up/down arrows)
- State persistence between commands
- Exit with `exit` or `Ctrl+D`

## Test Strategy

### Unit Tests
- curl parser tokenizer
- HTTP request builder
- History CRUD operations

### E2E Tests
- Real HTTP requests to httpbin.org
- Full history workflow
- curl import → send → save → export
- multipart upload request construction and CLI upload options

### Output Verification
- Status code validation
- Response format check
- JSON output validation
