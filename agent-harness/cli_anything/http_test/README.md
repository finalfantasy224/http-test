# HTTP-Test CLI Harness

A Click-based CLI harness for the `http-test` HTTP client. It supports one-shot HTTP requests, curl parsing, history management, import/export, workflows, and multipart file uploads.

## Install

From `agent-harness/`:

```bash
pip install -e .
```

## Basic usage

```bash
http-test get https://httpbin.org/get
http-test post https://httpbin.org/post -H 'Content-Type: application/json' -d '{"name":"demo"}'
http-test --json send https://httpbin.org/get
```

## File upload

Use `-F/--file` with `field=path`. Repeat it for multiple files. If you pass a bare path, the field name defaults to `file`.

```bash
http-test post https://httpbin.org/post -F file=./sample.txt
http-test send https://httpbin.org/post -m POST -F avatar=./avatar.png -d '{"user":"demo"}'
```

When files are present, the CLI sends `multipart/form-data`. It removes any manual `Content-Type` header so `requests` can generate the required multipart boundary. JSON object body data is sent as form fields; non-JSON body data is sent as a `body` field. Uploads are supported for `POST`, `PUT`, `PATCH`, and `DELETE`.

## Request import/export

The harness now round-trips full saved request records through the same SQLite-backed history model as the GUI. Exported JSON keeps headers, body, response metadata, and request ids when available.

```bash
http-test export-data requests.json
http-test export-data auth-requests.json -c Auth
http-test import-data requests.json
http-test --json export-data requests.json
```

This makes exported files suitable for backup, sharing, and re-import without losing request details.

## Tests

From `agent-harness/cli_anything/http_test/`:

```bash
pytest -v --tb=short
pytest -v --tb=short tests/test_core.py
RUN_E2E_TESTS=1 pytest -v --tb=short tests/test_full_e2e.py
```
