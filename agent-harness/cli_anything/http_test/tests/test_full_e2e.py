#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E2E tests for http-test CLI.
Tests with real HTTP requests.
"""

import sys
import os
import json
import unittest
import tempfile
from click.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import http_test_cli
from core import request as req_module
from core import curl_parser
from core import history as hist_module
from core import export


@unittest.skipUnless(os.environ.get('RUN_E2E_TESTS'), "Enable with RUN_E2E_TESTS=1")
class TestHTTPRequests(unittest.TestCase):
    """Test real HTTP requests to httpbin.org."""
    
    def test_get_request(self):
        """GET request."""
        resp = req_module.get('https://httpbin.org/get', timeout=10)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_success())
    
    def test_post_request(self):
        """POST request."""
        resp = req_module.post(
            'https://httpbin.org/post',
            headers={'Content-Type': 'application/json'},
            body='{"test": true}',
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
    
    def test_put_request(self):
        """PUT request."""
        resp = req_module.put(
            'https://httpbin.org/put',
            headers={'Content-Type': 'application/json'},
            body='{"test": true}',
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
    
    def test_delete_request(self):
        """DELETE request."""
        resp = req_module.delete('https://httpbin.org/delete', timeout=10)
        self.assertEqual(resp.status_code, 200)
    
    def test_patch_request(self):
        """PATCH request."""
        resp = req_module.patch(
            'https://httpbin.org/patch',
            headers={'Content-Type': 'application/json'},
            body='{"test": true}',
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
    
    def test_custom_headers(self):
        """Custom headers."""
        resp = req_module.get(
            'https://httpbin.org/headers',
            headers={'X-Custom-Header': 'test-value'},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.json)
    
    def test_json_body(self):
        """JSON request body."""
        resp = req_module.post(
            'https://httpbin.org/post',
            headers={'Content-Type': 'application/json'},
            body='{"name": "test", "age": 25}',
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.json)
    
    def test_timeout(self):
        """Request timeout."""
        with self.assertRaises(Exception):
            req_module.get('https://httpbin.org/delay/10', timeout=1)

    def test_file_upload_request(self):
        """Multipart file upload."""
        upload_file = tempfile.NamedTemporaryFile(delete=False)
        upload_file.write(b'hello upload')
        upload_file.close()

        try:
            resp = req_module.post(
                'https://httpbin.org/post',
                body='{"description": "demo"}',
                files=[{'field': 'file', 'path': upload_file.name, 'filename': 'sample.txt'}],
                timeout=10
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(resp.json)
            self.assertIn('file', resp.json.get('files', {}))
            self.assertIn('description', resp.json.get('form', {}))
        finally:
            os.unlink(upload_file.name)


class TestCurlImport(unittest.TestCase):
    """Test curl command import."""
    
    def test_curl_basic(self):
        """Basic curl import."""
        curl_cmd = "curl https://example.com"
        result = curl_parser.parse_curl_command(curl_cmd)
        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['url'], 'https://example.com')
    
    def test_curl_complex(self):
        """Complex curl with headers and body."""
        curl_cmd = """curl -X POST 'https://api.example.com/users' -H 'Content-Type: application/json' -d '{"name": "test"}'"""
        result = curl_parser.parse_curl_command(curl_cmd)
        self.assertEqual(result['method'], 'POST')
        self.assertIn('Content-Type', result['headers'])
        self.assertIn('name', result['body'])


class TestHistory(unittest.TestCase):
    """Test history management."""
    
    def setUp(self):
        """Create temp database."""
        self.db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db.close()
        self.hist = hist_module.HistoryManager(self.db.name)
    
    def tearDown(self):
        """Clean up."""
        os.unlink(self.db.name)
    
    def test_save_and_list(self):
        """Save and list requests."""
        req_id = self.hist.save(
            name='Test Request',
            category='Test',
            method='GET',
            url='https://example.com',
            headers={'Content-Type': 'application/json'},
            body=None
        )
        self.assertIsNotNone(req_id)
        
        requests = self.hist.list()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['name'], 'Test Request')
    
    def test_category_management(self):
        """Category management."""
        cats = self.hist.list_categories()
        self.assertIn('默认分类', cats)
        
        self.hist.create_category('TestCategory')
        cats = self.hist.list_categories()
        self.assertIn('TestCategory', cats)
        
        self.hist.delete_category('TestCategory')
        cats = self.hist.list_categories()
        self.assertNotIn('TestCategory', cats)


class TestImportExport(unittest.TestCase):
    """Test import/export functionality."""
    
    def setUp(self):
        """Create temp database."""
        self.db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db.close()
        self.hist = hist_module.HistoryManager(self.db.name)
        
        self.output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.output_file.close()
    
    def tearDown(self):
        """Clean up."""
        os.unlink(self.db.name)
        os.unlink(self.output_file.name)
    
    def test_export_import(self):
        """Export and re-import."""
        self.hist.save(
            name='Test',
            category='Test',
            method='GET',
            url='https://example.com',
            headers=None,
            body=None
        )
        
        requests = self.hist.list()
        export.export_history(requests, self.output_file.name)
        
        imported = export.import_history(self.output_file.name)
        self.assertIsNotNone(imported)
        self.assertEqual(len(imported), 1)

    def test_export_import_preserves_full_request_details(self):
        """Import/export round-trip keeps request details beyond list summaries."""
        self.hist.save(
            name='Detailed',
            category='Details',
            method='POST',
            url='https://example.com/details',
            headers={'Content-Type': 'application/json'},
            body='{"hello": "world"}',
            response_info='200 OK'
        )

        count = self.hist.export_requests(self.output_file.name)
        self.assertEqual(count, 1)

        imported = export.import_history(self.output_file.name)
        self.assertEqual(imported[0]['headers'], {'Content-Type': 'application/json'})
        self.assertEqual(imported[0]['body'], '{"hello": "world"}')
        self.assertEqual(imported[0]['response_info'], '200 OK')


class TestCLIImportExport(unittest.TestCase):
    """Exercise import/export commands through the Click CLI."""

    def test_cli_import_data_persists_request_details(self):
        """import-data loads full request records into the history database."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            input_path = 'requests.json'
            with open(input_path, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        'name': 'Imported Request',
                        'category': 'Imports',
                        'method': 'PATCH',
                        'url': 'https://example.com/imported',
                        'headers': {'X-Trace': 'abc'},
                        'body': '{"value": 1}',
                        'response_info': '204 No Content'
                    }
                ], f)

            result = runner.invoke(http_test_cli.cli, ['import-data', input_path])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Imported 1 requests', result.output)

            hist = hist_module.HistoryManager('http_requests_history.db')
            requests = hist.list(detailed=True)
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]['headers'], {'X-Trace': 'abc'})
            self.assertEqual(requests[0]['response_info'], '204 No Content')

    def test_cli_export_data_writes_full_filtered_records(self):
        """export-data respects category filters and exports full records."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            hist = hist_module.HistoryManager('http_requests_history.db')
            hist.save(
                name='Keep Me',
                category='Exports',
                method='POST',
                url='https://example.com/export',
                headers={'Authorization': 'Bearer token'},
                body='{"export": true}',
                response_info='201 Created'
            )
            hist.save(
                name='Ignore Me',
                category='Other',
                method='GET',
                url='https://example.com/other',
                headers=None,
                body=None
            )

            output_path = 'export.json'
            result = runner.invoke(http_test_cli.cli, ['export-data', output_path, '-c', 'Exports'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Exported 1 requests', result.output)

            exported = export.import_history(output_path)
            self.assertEqual(len(exported), 1)
            self.assertEqual(exported[0]['name'], 'Keep Me')
            self.assertEqual(exported[0]['headers'], {'Authorization': 'Bearer token'})
            self.assertEqual(exported[0]['body'], '{"export": true}')
            self.assertEqual(exported[0]['response_info'], '201 Created')


class TestCLISubprocess(unittest.TestCase):
    """Test CLI via subprocess."""
    
    def _resolve_cli(self):
        """Find CLI path."""
        cli_path = os.environ.get('CLI_ANYTHING_FORCE_INSTALLED')
        if cli_path:
            return cli_path
        
        # Try to find in current build
        base = os.path.dirname(os.path.abspath(__file__))
        http_test_dir = os.path.join(base, '..')
        cli_file = os.path.join(http_test_dir, 'http_test_cli.py')
        
        if os.path.exists(cli_file):
            return f'python3 {cli_file}'
        
        return 'http-test'
    
    @unittest.skipIf(os.environ.get('CLI_ANYTHING_SKIP_SUBPROCESS'), "Skip subprocess tests")
    def test_cli_help(self):
        """CLI help output."""
        import subprocess
        cli = self._resolve_cli()
        
        if cli.startswith('python3 '):
            result = subprocess.run(
                [cli.split()[0], cli.split()[1], '--help'],
                capture_output=True, timeout=5
            )
        else:
            result = subprocess.run(
                [cli, '--help'],
                capture_output=True, timeout=5
            )
        
        self.assertIn(b'HTTP', result.stdout)

    @unittest.skipIf(os.environ.get('CLI_ANYTHING_SKIP_SUBPROCESS'), "Skip subprocess tests")
    def test_cli_upload_option_help(self):
        """CLI POST command exposes upload option."""
        import subprocess
        cli = self._resolve_cli()

        if cli.startswith('python3 '):
            result = subprocess.run(
                [cli.split()[0], cli.split()[1], 'post', '--help'],
                capture_output=True, timeout=5
            )
        else:
            result = subprocess.run(
                [cli, 'post', '--help'],
                capture_output=True, timeout=5
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(b'--file', result.stdout)
        self.assertIn(b'field=path', result.stdout)


if __name__ == '__main__':
    unittest.main()
