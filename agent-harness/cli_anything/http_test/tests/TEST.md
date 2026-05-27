# HTTP-Test CLI Test Plan

## Overview

This document outlines the test strategy for the http-test CLI harness.

## Test Categories

### 1. Unit Tests (test_core.py)

Test individual modules in isolation with synthetic data.

#### curl_parser.py Tests
- `test_tokenize_simple` - Simple space-separated tokens
- `test_tokenize_single_quotes` - Single quote handling
- `test_tokenize_double_quotes` - Double quote handling
- `test_tokenize_escaped` - Escaped characters
- `test_tokenize_newline` - Line continuation
- `test_parse_curl_basic` - Basic curl parsing
- `test_parse_curl_headers` - Header parsing (-H)
- `test_parse_curl_method` - Method override (-X)
- `test_parse_curl_body` - Body data (-d, --data-raw)
- `test_parse_curl_auth` - Basic auth (-u)
- `test_parse_curl_cookie` - Cookie handling (-b)
- `test_parse_invalid` - Invalid curl command

#### request.py Tests
- `test_response_creation` - Response object creation
- `test_response_json_parse` - JSON body parsing
- `test_response_status_checks` - Status code checking
- `test_response_to_dict` - Dictionary conversion
- `test_parse_file_spec_with_field` - Parse explicit multipart field mapping
- `test_parse_file_spec_default_field` - Parse bare path with default `file` field
- `test_collect_multipart_data_json_object` - Convert JSON object body to form fields
- `test_collect_multipart_data_raw_body` - Convert raw body to `body` form field
- `test_remove_content_type_header` - Remove manual Content-Type before multipart upload
- `test_open_upload_files` - Open files into requests-compatible tuples
- `test_send_request_with_files` - Build multipart request arguments and close handles
- `test_send_request_rejects_upload_for_get` - Reject upload for GET/HEAD/OPTIONS

#### history.py Tests
- `test_history_list` - List requests
- `test_history_search` - Search functionality
- `test_list_detailed_returns_full_request_records` - Hydrate summary rows into full stored request details
- `test_export_requests_preserves_full_request_details` - Export full request metadata through the history manager
- `test_import_requests_loads_exported_records` - Import JSON records through the SQLite-backed history layer

#### export.py Tests
- `test_export_valid` - Valid data export
- `test_import_valid` - Valid import
- `test_validate_import` - Import validation

### 2. E2E Tests (test_full_e2e.py)

Test real HTTP requests and full workflows.

#### HTTP Request Tests
- `test_get_request` - GET to httpbin.org/get
- `test_post_request` - POST to httpbin.org/post
- `test_put_request` - PUT to httpbin.org/put
- `test_delete_request` - DELETE to httpbin.org/delete
- `test_patch_request` - PATCH to httpbin.org/patch
- `test_header_options` - Custom headers
- `test_json_body` - JSON request body
- `test_timeout` - Request timeout handling
- `test_ssl_verify` - SSL verification toggle
- `test_file_upload_request` - Real multipart upload to httpbin.org/post when E2E is enabled

#### curl Import Tests
- `test_curl_basic` - Basic curl import
- `test_curl_complex` - Complex curl with headers and body

#### History Tests
- `test_save_and_retrieve` - Save request, retrieve from history
- `test_category_management` - Create/list/delete category

#### Import/Export Tests
- `test_export_import` - Export and re-import requests
- `test_export_import_preserves_full_request_details` - Preserve headers, body, and response metadata during round-trip

### 3. CLI Integration Tests

Test the CLI interface itself.

#### Command Tests
- `test_cli_get_command` - CLI get command
- `test_cli_post_command` - CLI post command
- `test_cli_history_command` - CLI history list
- `test_cli_json_output` - JSON output mode
- `test_cli_upload_option_help` - Upload option exposed on CLI request commands
- `test_cli_import_data_persists_request_details` - Import command stores full request details in history
- `test_cli_export_data_writes_full_filtered_records` - Export command writes full filtered records

## Test Execution

```bash
# Run all tests
pytest -v --tb=short

# Run unit tests only
pytest -v --tb=short tests/test_core.py

# Run E2E tests only
pytest -v --tb=short tests/test_full_e2e.py

# Run with coverage
pytest --cov=cli_anything.http_test --cov-report=term-missing
```

## Test Results

| Category | Status | Notes |
|----------|--------|-------|
| Unit Tests | ✅ Passed | `python3 tests/test_core.py` ran 29 tests |
| E2E Tests | ✅ Passed | `python3 tests/test_full_e2e.py` ran 19 tests, with 9 network tests skipped by default |
| CLI Integration | ✅ Passed | `python3 -m unittest discover -s tests -v` includes CLI help and upload option checks |

## Upload Refinement Notes

The CLI now mirrors the GUI Files tab for multipart uploads:

```bash
http-test post https://httpbin.org/post -F file=./sample.txt
http-test send https://httpbin.org/post -m POST -F avatar=./avatar.png -d '{"user":"demo"}'
```

Upload behavior under test:
- `-F/--file` accepts `field=path` and can be repeated.
- Bare paths default to field name `file`.
- JSON object body data becomes multipart form fields.
- Raw body data becomes a `body` multipart form field.
- User-provided `Content-Type` is removed for multipart requests so the `requests` library can generate the required boundary.
- `GET`, `HEAD`, and `OPTIONS` fail loudly when files are provided.
- Existing positional `send_request(..., timeout, verify)` callers remain compatible after adding `files`.

## Import/Export Refinement Notes

The CLI now mirrors the GUI's history backup behavior instead of exporting only list summaries:

- `export-data` writes full request records, including headers, body, and `response_info`.
- `export-data -c <category>` filters by category without losing request detail fields.
- `import-data` validates the JSON file, then imports via the SQLite-backed history layer used by the GUI.

## Known Limitations

1. Tests require network connectivity to httpbin.org
2. REPL mode tests are manual-only
3. SSL verification tests may fail on systems without proper certificates

## Latest Test Results

Verification run after adding multipart upload support:

```text
python3 -m py_compile http_test_cli.py core/request.py tests/test_core.py tests/test_full_e2e.py
# passed with no output

python3 tests/test_core.py
Ran 25 tests in 0.004s
OK

python3 tests/test_full_e2e.py
Ran 16 tests in 0.741s
OK (skipped=9)

python3 -m unittest discover -s tests -v
Ran 41 tests in 0.556s
OK (skipped=9)
```

`python3 -m pytest -v --tb=short tests/test_core.py` was also attempted, but this environment does not have `pytest` installed (`No module named pytest`), so the stdlib `unittest` runner was used for verification.

## Latest Test Results - 2026-05-27

Verification run after refining full-detail request import/export:

```text
python3 -m py_compile agent-harness/cli_anything/http_test/core/history.py agent-harness/cli_anything/http_test/http_test_cli.py agent-harness/cli_anything/http_test/tests/test_core.py agent-harness/cli_anything/http_test/tests/test_full_e2e.py
# passed with no output

python3 -m unittest discover -s agent-harness/cli_anything/http_test/tests -v
test_parse_curl_auth (test_core.TestCurlParser.test_parse_curl_auth)
Basic auth. ... ok
test_parse_curl_basic (test_core.TestCurlParser.test_parse_curl_basic)
Basic curl parsing. ... ok
test_parse_curl_body (test_core.TestCurlParser.test_parse_curl_body)
Body data. ... ok
test_parse_curl_cookie (test_core.TestCurlParser.test_parse_curl_cookie)
Cookie handling. ... ok
test_parse_curl_headers (test_core.TestCurlParser.test_parse_curl_headers)
Header parsing. ... ok
test_parse_curl_method (test_core.TestCurlParser.test_parse_curl_method)
Method override. ... ok
test_parse_invalid (test_core.TestCurlParser.test_parse_invalid)
Invalid curl command. ... ok
test_tokenize_double_quotes (test_core.TestCurlParser.test_tokenize_double_quotes)
Double quote handling. ... ok
test_tokenize_escaped (test_core.TestCurlParser.test_tokenize_escaped)
Escaped characters. ... ok
test_tokenize_simple (test_core.TestCurlParser.test_tokenize_simple)
Simple space-separated tokens. ... ok
test_tokenize_single_quotes (test_core.TestCurlParser.test_tokenize_single_quotes)
Single quote handling. ... ok
test_export_valid (test_core.TestExport.test_export_valid)
Valid data export. ... ok
test_validate_import (test_core.TestExport.test_validate_import)
Import validation. ... ok
test_export_requests_preserves_full_request_details (test_core.TestHistoryManager.test_export_requests_preserves_full_request_details)
History export keeps headers, body, and response metadata. ... ok
test_import_requests_loads_exported_records (test_core.TestHistoryManager.test_import_requests_loads_exported_records)
History import uses the backing database importer. ... ok
test_list_detailed_returns_full_request_records (test_core.TestHistoryManager.test_list_detailed_returns_full_request_records)
Detailed listing hydrates stored headers/body fields. ... ok
test_collect_multipart_data_json_object (test_core.TestRequest.test_collect_multipart_data_json_object)
JSON body object becomes multipart form fields. ... ok
test_collect_multipart_data_raw_body (test_core.TestRequest.test_collect_multipart_data_raw_body)
Raw body becomes a body multipart field. ... ok
test_open_upload_files (test_core.TestRequest.test_open_upload_files)
Upload files are opened as requests multipart tuples. ... ok
test_parse_file_spec_default_field (test_core.TestRequest.test_parse_file_spec_default_field)
Upload file spec defaults to file field. ... ok
test_parse_file_spec_with_field (test_core.TestRequest.test_parse_file_spec_with_field)
Upload file spec with explicit field name. ... ok
test_remove_content_type_header (test_core.TestRequest.test_remove_content_type_header)
Content-Type is removed before requests builds multipart boundary. ... ok
test_response_creation (test_core.TestRequest.test_response_creation)
Response object creation. ... ok
test_response_json_parse (test_core.TestRequest.test_response_json_parse)
JSON body parsing. ... ok
test_response_status_checks (test_core.TestRequest.test_response_status_checks)
Status code checking. ... ok
test_response_to_dict (test_core.TestRequest.test_response_to_dict)
Dictionary conversion. ... ok
test_send_request_rejects_upload_for_get (test_core.TestRequest.test_send_request_rejects_upload_for_get)
GET/HEAD/OPTIONS uploads fail loudly. ... ok
test_send_request_with_files (test_core.TestRequest.test_send_request_with_files)
send_request passes multipart files and strips Content-Type. ... ok
test_cli_export_data_writes_full_filtered_records (test_full_e2e.TestCLIImportExport.test_cli_export_data_writes_full_filtered_records)
export-data respects category filters and exports full records. ... ok
test_cli_import_data_persists_request_details (test_full_e2e.TestCLIImportExport.test_cli_import_data_persists_request_details)
import-data loads full request records into the history database. ... ok
test_cli_help (test_full_e2e.TestCLISubprocess.test_cli_help)
CLI help output. ... ok
test_cli_upload_option_help (test_full_e2e.TestCLISubprocess.test_cli_upload_option_help)
CLI POST command exposes upload option. ... ok
test_curl_basic (test_full_e2e.TestCurlImport.test_curl_basic)
Basic curl import. ... ok
test_curl_complex (test_full_e2e.TestCurlImport.test_curl_complex)
Complex curl with headers and body. ... ok
test_custom_headers (test_full_e2e.TestHTTPRequests.test_custom_headers)
Custom headers. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_delete_request (test_full_e2e.TestHTTPRequests.test_delete_request)
DELETE request. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_file_upload_request (test_full_e2e.TestHTTPRequests.test_file_upload_request)
Multipart file upload. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_get_request (test_full_e2e.TestHTTPRequests.test_get_request)
GET request. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_json_body (test_full_e2e.TestHTTPRequests.test_json_body)
JSON request body. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_patch_request (test_full_e2e.TestHTTPRequests.test_patch_request)
PATCH request. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_post_request (test_full_e2e.TestHTTPRequests.test_post_request)
POST request. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_put_request (test_full_e2e.TestHTTPRequests.test_put_request)
PUT request. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_timeout (test_full_e2e.TestHTTPRequests.test_timeout)
Request timeout. ... skipped 'Enable with RUN_E2E_TESTS=1'
test_category_management (test_full_e2e.TestHistory.test_category_management)
Category management. ... ok
test_save_and_list (test_full_e2e.TestHistory.test_save_and_list)
Save and list requests. ... ok
test_export_import (test_full_e2e.TestImportExport.test_export_import)
Export and re-import. ... ok
test_export_import_preserves_full_request_details (test_full_e2e.TestImportExport.test_export_import_preserves_full_request_details)
Import/export round-trip keeps request details beyond list summaries. ... ok

----------------------------------------------------------------------
Ran 47 tests in 0.734s

OK (skipped=9)
```

Summary for this refinement:
- 38 tests passed locally
- 9 network-backed E2E tests remained skipped because `RUN_E2E_TESTS=1` was not enabled
- 0 failures
- New coverage now exercises full-detail `import-data` / `export-data` behavior and category-filtered exports

## Latest Test Results - 2026-05-27 Upload Compatibility Fix

Verification run after post-review fix for `send_request()` positional compatibility:

```text
python3 -m py_compile http_test_cli.py core/request.py tests/test_core.py tests/test_full_e2e.py
# passed with no output

python3 tests/test_core.py
Ran 29 tests in 0.150s
OK

python3 tests/test_full_e2e.py
Ran 19 tests in 0.843s
OK (skipped=9)

python3 -m unittest discover -s tests -v
Ran 48 tests in 0.790s
OK (skipped=9)
```

Summary for the upload compatibility fix:
- 39 tests passed locally
- 9 network-backed E2E tests remained skipped because `RUN_E2E_TESTS=1` was not enabled
- 0 failures
- New regression coverage confirms old positional `send_request('HEAD', url, headers, None, timeout, verify)` callers still work after adding the keyword upload argument.
