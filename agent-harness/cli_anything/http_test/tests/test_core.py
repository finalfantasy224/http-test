#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for http-test CLI core modules.
Uses synthetic data, no external dependencies.
"""

import sys
import os
import json
import unittest
import tempfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core import curl_parser
from core import request as req_module
from core import history as hist_module
from core import export


class TestCurlParser(unittest.TestCase):
    """Test curl command parser."""
    
    def test_tokenize_simple(self):
        """Simple space-separated tokens."""
        tokens = curl_parser.tokenize_curl("curl https://example.com")
        self.assertEqual(tokens[0], "curl")
        self.assertEqual(tokens[1], "https://example.com")
    
    def test_tokenize_single_quotes(self):
        """Single quote handling."""
        tokens = curl_parser.tokenize_curl("curl 'hello world'")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[1], "hello world")
    
    def test_tokenize_double_quotes(self):
        """Double quote handling."""
        tokens = curl_parser.tokenize_curl('curl "hello world"')
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[1], "hello world")
    
    def test_tokenize_escaped(self):
        """Escaped characters."""
        tokens = curl_parser.tokenize_curl(r"curl 'hello\'world'")
        self.assertEqual(tokens[1], "hello'world")
    
    def test_parse_curl_basic(self):
        """Basic curl parsing."""
        result = curl_parser.parse_curl_command("curl https://example.com")
        self.assertEqual(result['method'], "GET")
        self.assertEqual(result['url'], "https://example.com")
        self.assertEqual(result['headers'], {})
    
    def test_parse_curl_headers(self):
        """Header parsing."""
        result = curl_parser.parse_curl_command(
            "curl -H 'Content-Type: application/json' https://api.example.com"
        )
        self.assertIn('Content-Type', result['headers'])
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
    
    def test_parse_curl_method(self):
        """Method override."""
        result = curl_parser.parse_curl_command(
            "curl -X POST https://api.example.com"
        )
        self.assertEqual(result['method'], "POST")
    
    def test_parse_curl_body(self):
        """Body data."""
        result = curl_parser.parse_curl_command(
            "curl -d 'name=test' https://api.example.com"
        )
        self.assertEqual(result['body'], 'name=test')
    
    def test_parse_curl_auth(self):
        """Basic auth."""
        result = curl_parser.parse_curl_command(
            "curl -u user:pass https://api.example.com"
        )
        self.assertIn('Authorization', result['headers'])
    
    def test_parse_curl_cookie(self):
        """Cookie handling."""
        result = curl_parser.parse_curl_command(
            "curl -b 'session=abc' https://api.example.com"
        )
        self.assertEqual(result['headers'].get('Cookie'), 'session=abc')
    
    def test_parse_invalid(self):
        """Invalid curl command."""
        with self.assertRaises(ValueError):
            curl_parser.parse_curl_command("not-a-curl-command")


class TestRequest(unittest.TestCase):
    """Test HTTP request module."""
    
    def test_response_creation(self):
        """Response object creation."""
        resp = req_module.Response(
            status_code=200,
            reason="OK",
            headers={"Content-Type": "application/json"},
            body='{"test": true}',
            elapsed_time=0.123
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "OK")
    
    def test_response_json_parse(self):
        """JSON body parsing."""
        resp = req_module.Response(
            status_code=200,
            reason="OK",
            headers={},
            body='{"key": "value"}',
            elapsed_time=0.1
        )
        self.assertIsNotNone(resp.json)
        self.assertEqual(resp.json['key'], "value")
    
    def test_response_status_checks(self):
        """Status code checking."""
        resp_2xx = req_module.Response(200, "OK", {}, "", 0.1)
        self.assertTrue(resp_2xx.is_success())
        self.assertFalse(resp_2xx.is_client_error())
        
        resp_4xx = req_module.Response(404, "Not Found", {}, "", 0.1)
        self.assertFalse(resp_4xx.is_success())
        self.assertTrue(resp_4xx.is_client_error())
        
        resp_5xx = req_module.Response(500, "Internal Error", {}, "", 0.1)
        self.assertTrue(resp_5xx.is_server_error())
    
    def test_response_to_dict(self):
        """Dictionary conversion."""
        resp = req_module.Response(
            status_code=200,
            reason="OK",
            headers={"Content-Type": "application/json"},
            body="test",
            elapsed_time=0.1
        )
        d = resp.to_dict()
        self.assertEqual(d['status_code'], 200)
        self.assertIn('headers', d)

    def test_parse_file_spec_with_field(self):
        """Upload file spec with explicit field name."""
        spec = req_module.parse_file_spec("avatar=/tmp/user.png")
        self.assertEqual(spec['field'], 'avatar')
        self.assertEqual(spec['path'], '/tmp/user.png')
        self.assertEqual(spec['filename'], 'user.png')

    def test_parse_file_spec_default_field(self):
        """Upload file spec defaults to file field."""
        spec = req_module.parse_file_spec("/tmp/report.txt")
        self.assertEqual(spec['field'], 'file')
        self.assertEqual(spec['path'], '/tmp/report.txt')

    def test_collect_multipart_data_json_object(self):
        """JSON body object becomes multipart form fields."""
        data = req_module.collect_multipart_data('{"name": "demo", "count": 2}')
        self.assertEqual(data, {'name': 'demo', 'count': '2'})

    def test_collect_multipart_data_raw_body(self):
        """Raw body becomes a body multipart field."""
        data = req_module.collect_multipart_data('plain text')
        self.assertEqual(data, {'body': 'plain text'})

    def test_remove_content_type_header(self):
        """Content-Type is removed before requests builds multipart boundary."""
        headers = req_module.remove_content_type_header({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
        })
        self.assertNotIn('Content-Type', headers)
        self.assertEqual(headers['Authorization'], 'Bearer token')

    def test_open_upload_files(self):
        """Upload files are opened as requests multipart tuples."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'upload-content')
            path = f.name

        try:
            files, opened = req_module.open_upload_files([
                {'field': 'file', 'path': path, 'filename': 'sample.txt'}
            ])
            self.assertEqual(files[0][0], 'file')
            self.assertEqual(files[0][1][0], 'sample.txt')
            self.assertEqual(files[0][1][1].read(), b'upload-content')
        finally:
            for file_obj in opened:
                file_obj.close()
            os.unlink(path)

    def test_send_request_with_files(self):
        """send_request passes multipart files and strips Content-Type."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'upload-content')
            path = f.name

        fake_response = mock.Mock()
        fake_response.status_code = 200
        fake_response.reason = 'OK'
        fake_response.headers = {'Content-Type': 'application/json'}
        fake_response.text = '{"ok": true}'

        try:
            with mock.patch.object(req_module.requests, 'request', return_value=fake_response) as mocked_request:
                resp = req_module.send_request(
                    'POST',
                    'https://example.com/upload',
                    headers={'Content-Type': 'application/json', 'X-Test': '1'},
                    body='{"name": "demo"}',
                    files=[{'field': 'file', 'path': path, 'filename': 'sample.txt'}]
                )

            self.assertEqual(resp.status_code, 200)
            kwargs = mocked_request.call_args.kwargs
            self.assertEqual(kwargs['headers'], {'X-Test': '1'})
            self.assertEqual(kwargs['data'], {'name': 'demo'})
            self.assertEqual(kwargs['files'][0][0], 'file')
            self.assertTrue(kwargs['files'][0][1][1].closed)
        finally:
            os.unlink(path)

    def test_send_request_rejects_upload_for_get(self):
        """GET/HEAD/OPTIONS uploads fail loudly."""
        with self.assertRaises(ValueError):
            req_module.send_request(
                'GET',
                'https://example.com/upload',
                files=[{'field': 'file', 'path': '/tmp/missing.txt', 'filename': 'missing.txt'}]
            )

    def test_send_request_preserves_positional_timeout_verify(self):
        """Existing positional timeout/verify callers keep working."""
        fake_response = mock.Mock()
        fake_response.status_code = 204
        fake_response.reason = 'No Content'
        fake_response.headers = {}
        fake_response.text = ''

        with mock.patch.object(req_module.requests, 'request', return_value=fake_response) as mocked_request:
            resp = req_module.send_request(
                'HEAD',
                'https://example.com/status',
                {'X-Test': '1'},
                None,
                7,
                False
            )

        self.assertEqual(resp.status_code, 204)
        mocked_request.assert_called_once_with(
            'HEAD',
            'https://example.com/status',
            timeout=7,
            verify=False,
            headers={'X-Test': '1'}
        )


class TestExport(unittest.TestCase):
    """Test export/import module."""
    
    def test_export_valid(self):
        """Valid data export."""
        requests = [
            {'name': 'test', 'method': 'GET', 'url': 'https://example.com'}
        ]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            path = f.name
        
        try:
            result = export.export_history(requests, path)
            self.assertTrue(result)
            
            imported = export.import_history(path)
            self.assertIsNotNone(imported)
            self.assertEqual(len(imported), 1)
        finally:
            os.unlink(path)
    
    def test_validate_import(self):
        """Import validation."""
        valid = [{'name': 'test', 'method': 'GET', 'url': 'https://example.com'}]
        self.assertTrue(export.validate_import(valid))
        
        invalid = [{'name': 'test'}]  # missing method, url
        self.assertFalse(export.validate_import(invalid))
        
        self.assertFalse(export.validate_import("not a list"))
        self.assertFalse(export.validate_import(None))


class TestHistoryManager(unittest.TestCase):
    """Test history import/export helpers."""

    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db.close()
        self.hist = hist_module.HistoryManager(self.db.name)

    def tearDown(self):
        os.unlink(self.db.name)

    def test_list_detailed_returns_full_request_records(self):
        """Detailed listing hydrates stored headers/body fields."""
        self.hist.save(
            name='Login',
            category='Auth',
            method='POST',
            url='https://example.com/login',
            headers={'Content-Type': 'application/json'},
            body='{"user": "demo"}',
            response_info='200 OK'
        )

        requests = self.hist.list(detailed=True)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['headers'], {'Content-Type': 'application/json'})
        self.assertEqual(requests[0]['body'], '{"user": "demo"}')
        self.assertEqual(requests[0]['response_info'], '200 OK')

    def test_export_requests_preserves_full_request_details(self):
        """History export keeps headers, body, and response metadata."""
        self.hist.save(
            name='Upload',
            category='Files',
            method='POST',
            url='https://example.com/upload',
            headers={'Authorization': 'Bearer token'},
            body='{"description": "demo"}',
            response_info='201 Created'
        )

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            path = f.name

        try:
            count = self.hist.export_requests(path)
            self.assertEqual(count, 1)

            imported = export.import_history(path)
            self.assertEqual(imported[0]['headers'], {'Authorization': 'Bearer token'})
            self.assertEqual(imported[0]['body'], '{"description": "demo"}')
            self.assertEqual(imported[0]['response_info'], '201 Created')
            self.assertEqual(imported[0]['method'], 'POST')
        finally:
            os.unlink(path)

    def test_import_requests_loads_exported_records(self):
        """History import uses the backing database importer."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump([
                {
                    'name': 'Imported',
                    'category': 'Imports',
                    'method': 'PUT',
                    'url': 'https://example.com/item/1',
                    'headers': {'X-Test': '1'},
                    'body': '{"ok": true}',
                    'response_info': '202 Accepted'
                }
            ], f)
            path = f.name

        try:
            count = self.hist.import_requests(path)
            self.assertEqual(count, 1)

            requests = self.hist.list(detailed=True)
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]['category'], 'Imports')
            self.assertEqual(requests[0]['headers'], {'X-Test': '1'})
            self.assertEqual(requests[0]['response_info'], '202 Accepted')
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
