#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP Test CLI - Main entry point.
A stateful CLI for HTTP testing with REPL support.
"""

import sys
import os
import json
import click
from typing import Optional, Dict

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core import request as req_module
from core import history as hist_module
from core import export as export_module
from core import curl_parser


# Global state for REPL mode
class State:
    """REPL session state."""
    
    def __init__(self):
        self.current_method = "GET"
        self.current_url = None
        self.current_headers = {}
        self.current_body = None
        self.last_response = None
        self.session_history = []
        self.json_mode = False
    
    def reset(self):
        """Reset current request state."""
        self.current_method = "GET"
        self.current_url = None
        self.current_headers = {}
        self.current_body = None


# Global state instance
_state = State()


def echo_json(data: any):
    """Echo data in JSON mode."""
    if _state.json_mode:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(data)


def echo_error(msg: str):
    """Echo error message."""
    click.echo(f"Error: {msg}", err=True)


# HTTP Request Commands

def parse_headers(header):
    """Parse repeated Key: Value header options."""
    headers = {}
    for h in header:
        if ':' in h:
            k, v = h.split(':', 1)
            headers[k.strip()] = v.strip()
    return headers


def parse_upload_options(upload_file):
    """Parse repeated file upload options."""
    return req_module.parse_file_specs(upload_file) if upload_file else None

@click.group()
@click.option('--json', 'json_output', is_flag=True, help='JSON output mode')
@click.pass_context
def cli(ctx, json_output):
    """HTTP Test CLI - Send HTTP requests and manage history."""
    ctx.ensure_object(dict)
    ctx.obj['json_mode'] = json_output
    _state.json_mode = json_output


@cli.command()
@click.argument('url')
@click.option('-m', '--method', default='GET', 
              type=click.Choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']),
              help='HTTP method')
@click.option('-H', '--header', multiple=True, help='Request header (Key: Value)')
@click.option('-d', '--data', help='Request body')
@click.option('-F', '--file', 'upload_file', multiple=True,
              help='Upload file as field=path (repeatable); bare path uses field name "file"')
@click.option('-t', '--timeout', default=30, help='Timeout in seconds')
@click.option('--no-verify', is_flag=True, help='Skip SSL verification')
@click.pass_context
def send(ctx, url, method, header, data, upload_file, timeout, no_verify):
    """Send HTTP request."""
    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    headers = parse_headers(header)
    
    # Send request
    try:
        resp = req_module.send_request(
            method=method,
            url=url,
            headers=headers if headers else None,
            body=data,
            files=parse_upload_options(upload_file),
            timeout=timeout,
            verify=not no_verify
        )
        
        _state.last_response = resp
        
        if ctx.obj.get('json_mode'):
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-d', '--data')
@click.option('-F', '--file', 'upload_file', multiple=True,
              help='Upload file as field=path (repeatable); bare path uses field name "file"')
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def patch(url, header, data, upload_file, timeout, no_verify):
    """Send PATCH request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.patch(url, headers, data, timeout, not no_verify, parse_upload_options(upload_file))
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def head(url, header, timeout, no_verify):
    """Send HEAD request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.send_request('HEAD', url, headers, None, timeout, not no_verify)
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def options(url, header, timeout, no_verify):
    """Send OPTIONS request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.send_request('OPTIONS', url, headers, None, timeout, not no_verify)
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


# Save request to history
@cli.command()
@click.argument('name')
@click.option('-c', '--category', default='默认分类', help='Category name')
@click.option('-m', '--method', default='GET', help='HTTP method')
@click.option('-u', '--url', required=True, help='Request URL')
@click.option('-H', '--header', multiple=True, help='Request headers')
@click.option('-d', '--data', help='Request body')
def save(name, category, method, url, header, data):
    """Save request to history."""
    headers = parse_headers(header)
    
    hist = hist_module.HistoryManager()
    try:
        req_id = hist.save(name, category, method, url, headers, data)
        click.echo(f"Saved request #{req_id}: {name}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


# Search history
@cli.command()
@click.argument('keyword')
def search(keyword):
    """Search requests in history."""
    hist = hist_module.HistoryManager()
    try:
        results = hist.search(keyword)
        if results:
            if _state.json_mode:
                echo_json(results)
            else:
                click.echo(f"Found {len(results)} matching requests:")
                for req in results:
                    click.echo(f"  [{req['id']}] {req['method']} {req['name']}")
                    click.echo(f"      {req['url']}")
        else:
            click.echo(f"No results found for: {keyword}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def get(url, header, timeout, no_verify):
    """Send GET request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.get(url, headers, timeout, not no_verify)
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-d', '--data')
@click.option('-F', '--file', 'upload_file', multiple=True,
              help='Upload file as field=path (repeatable); bare path uses field name "file"')
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def post(url, header, data, upload_file, timeout, no_verify):
    """Send POST request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.post(url, headers, data, timeout, not no_verify, parse_upload_options(upload_file))
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-d', '--data')
@click.option('-F', '--file', 'upload_file', multiple=True,
              help='Upload file as field=path (repeatable); bare path uses field name "file"')
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def put(url, header, data, upload_file, timeout, no_verify):
    """Send PUT request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.put(url, headers, data, timeout, not no_verify, parse_upload_options(upload_file))
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('-H', '--header', multiple=True)
@click.option('-F', '--file', 'upload_file', multiple=True,
              help='Upload file as field=path (repeatable); bare path uses field name "file"')
@click.option('-t', '--timeout', default=30)
@click.option('--no-verify', is_flag=True)
def delete(url, header, upload_file, timeout, no_verify):
    """Send DELETE request."""
    headers = parse_headers(header)
    
    try:
        resp = req_module.delete(url, headers, timeout, not no_verify, parse_upload_options(upload_file))
        _state.last_response = resp
        if _state.json_mode:
            echo_json(resp.to_dict())
        else:
            echo_json(req_module.format_response_human(resp))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('curl_command')
def curl(curl_command):
    """Parse and import curl command."""
    try:
        result = curl_parser.parse_curl_command(curl_command)
        if _state.json_mode:
            echo_json(result)
        else:
            click.echo("Parsed curl command:")
            click.echo(f"  Method: {result['method']}")
            click.echo(f"  URL: {result['url']}")
            click.echo(f"  Headers: {len(result['headers'])}")
            for k, v in result['headers'].items():
                click.echo(f"    {k}: {v}")
            if result['body']:
                click.echo(f"  Body: {result['body']}")
    except ValueError as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.option('-f', '--file', type=click.Path(), help='Read curl from file')
@click.option('-n', '--name', help='Name to save in history')
@click.option('-c', '--category', default='默认分类', help='Category')
def curl_import(file, name, category):
    """Import curl command from file or stdin and save to history.
    
    Examples:
        http-test curlimport -f request.curl -n "My API"
        curl -X POST https://api.example.com | http-test curlimport -n "My API"
    """
    import sys
    
    curl_str = ""
    if file:
        try:
            with open(file, 'r') as f:
                curl_str = f.read()
        except Exception as e:
            echo_error(f"Cannot read file: {e}")
            sys.exit(1)
    else:
        click.echo("Paste curl command (Ctrl+D to submit, Ctrl+C to cancel):")
        try:
            curl_str = click.get_text_stream('stdin').read()
        except Exception as e:
            echo_error(f"Cannot read stdin: {e}")
            sys.exit(1)
    
    if not curl_str.strip():
        echo_error("No curl command provided")
        sys.exit(1)
    
    try:
        result = curl_parser.parse_curl_input(curl_str)
        
        if name:
            hist = hist_module.HistoryManager()
            req_id = hist.save(
                name=name,
                category=category,
                method=result['method'],
                url=result['url'],
                headers=result['headers'],
                body=result['body']
            )
            click.echo(f"Saved request #{req_id}: {name}")
            if _state.json_mode:
                echo_json({'request_id': req_id, 'parsed': result})
        else:
            if _state.json_mode:
                echo_json(result)
            else:
                click.echo("Parsed curl command:")
                click.echo(f"  Method: {result['method']}")
                click.echo(f"  URL: {result['url']}")
                click.echo(f"  Headers: {len(result['headers'])}")
                for k, v in result['headers'].items():
                    click.echo(f"    {k}: {v}")
                if result['body']:
                    click.echo(f"  Body: {result['body']}")
                click.echo("")
                click.echo("Use -n <name> to save to history")
    except ValueError as e:
        echo_error(str(e))
        sys.exit(1)


# History Commands

@cli.group()
def history():
    """Manage request history."""
    pass


@history.command('list')
@click.option('-c', '--category', help='Filter by category')
def history_list(category):
    """List saved requests."""
    hist = hist_module.HistoryManager()
    try:
        requests = hist.list(category)
        if _state.json_mode:
            echo_json(requests)
        else:
            echo_json(hist_module.format_history_human(requests))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@history.command('show')
@click.argument('request_id', type=int)
def history_show(request_id):
    """Show request details."""
    hist = hist_module.HistoryManager()
    try:
        req = hist.get(request_id)
        if req:
            if _state.json_mode:
                echo_json(req)
            else:
                click.echo(f"Name: {req['name']}")
                click.echo(f"Method: {req['method']}")
                click.echo(f"URL: {req['url']}")
                click.echo(f"Category: {req['category']}")
                # Display headers if available
                headers = req.get('headers')
                if headers:
                    click.echo("Headers:")
                    if isinstance(headers, dict):
                        for k, v in headers.items():
                            click.echo(f"  {k}: {v}")
                    else:
                        click.echo(f"  {headers}")
                # Display body if available
                body = req.get('body')
                if body:
                    click.echo(f"Body: {body}")
                # Display response_info if available
                response_info = req.get('response_info')
                if response_info:
                    click.echo(f"Response: {response_info}")
        else:
            echo_error("Request not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@history.command('delete')
@click.argument('request_id', type=int)
def history_delete(request_id):
    """Delete request from history."""
    hist = hist_module.HistoryManager()
    try:
        if hist.delete(request_id):
            click.echo(f"Deleted request {request_id}")
        else:
            echo_error("Request not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


# Category Commands

@cli.group()
def category():
    """Manage categories."""
    pass


@category.command('list')
def category_list():
    """List all categories."""
    hist = hist_module.HistoryManager()
    try:
        cats = hist.list_categories()
        if _state.json_mode:
            echo_json(cats)
        else:
            for c in cats:
                click.echo(c)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@category.command('create')
@click.argument('name')
def category_create(name):
    """Create new category."""
    hist = hist_module.HistoryManager()
    try:
        if hist.create_category(name):
            click.echo(f"Created category: {name}")
        else:
            echo_error("Category may already exist")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@category.command('delete')
@click.argument('name')
def category_delete(name):
    """Delete category."""
    hist = hist_module.HistoryManager()
    try:
        if hist.delete_category(name):
            click.echo(f"Deleted category: {name}")
        else:
            echo_error("Category not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


# Import/Export Commands

@cli.command()
@click.argument('input_file', type=click.Path())
def import_data(input_file):
    """Import requests from JSON file."""
    hist = hist_module.HistoryManager()
    try:
        data = export_module.import_history(input_file)
        if data is None or not export_module.validate_import(data):
            echo_error("Invalid import file")
            sys.exit(1)

        imported_count = hist.import_requests(input_file)
        if imported_count == 0 and data:
            echo_error("Import failed")
            sys.exit(1)

        message = {
            'imported': imported_count,
            'input_file': input_file
        }
        if _state.json_mode:
            echo_json(message)
        else:
            click.echo(f"Imported {imported_count} requests from {input_file}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument('output_file', type=click.Path())
@click.option('-c', '--category', help='Filter by category')
def export_data(output_file, category):
    """Export requests to JSON file."""
    hist = hist_module.HistoryManager()
    try:
        exported_count = hist.export_requests(output_file, category)
        message = {
            'exported': exported_count,
            'output_file': output_file,
            'category': category
        }
        if _state.json_mode:
            echo_json(message)
        else:
            click.echo(f"Exported {exported_count} requests to {output_file}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


# Workflow Commands

@cli.group()
def workflow():
    """Manage workflows."""
    pass


@workflow.command('create')
@click.argument('name')
@click.option('-c', '--category', default='默认分类', help='Category')
@click.option('-d', '--description', help='Description')
def workflow_create(name, category, description):
    """Create a new workflow."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        wf_id = wf.create_workflow(name, category, description)
        click.echo(f"Created workflow #{wf_id}: {name}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('add')
@click.argument('workflow_id', type=int)
@click.option('-m', '--method', default='GET', help='HTTP method')
@click.option('-u', '--url', required=True, help='Request URL')
@click.option('-H', '--header', multiple=True, help='Request headers')
@click.option('-d', '--data', help='Request body')
@click.option('-e', '--extract', help='Extract var (e.g., data.token)')
@click.option('--condition', help='Condition (e.g., code == 0)')
@click.option('--desc', help='Step description')
def workflow_add(workflow_id, method, url, header, data, extract, condition, desc):
    """Add step to workflow."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        headers = {}
        for h in header:
            if ':' in h:
                k, v = h.split(':', 1)
                headers[k.strip()] = v.strip()
        
        wf = wf_module.WorkflowDB()
        steps = wf.get_workflow_steps(workflow_id)
        step_order = len(steps) + 1
        
        step_id = wf.add_step(
            workflow_id=workflow_id,
            step_order=step_order,
            method=method,
            url=url,
            headers=headers,
            body=data,
            extract_var=extract,
            condition=condition,
            description=desc
        )
        click.echo(f"Added step #{step_order} to workflow #{workflow_id}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('list')
@click.option('-c', '--category', help='Filter by category')
def workflow_list(category):
    """List all workflows."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        workflows = wf.list_workflows(category)
        if workflows:
            for w in workflows:
                steps = wf.get_workflow_steps(w['id'])
                click.echo(f"[{w['id']}] {w['name']} ({len(steps)} steps)")
                if w['category']:
                    click.echo(f"    Category: {w['category']}")
        else:
            click.echo("No workflows found.")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('show')
@click.argument('workflow_id', type=int)
def workflow_show(workflow_id):
    """Show workflow details."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        workflow = wf.get_workflow(workflow_id)
        if workflow:
            steps = wf.get_workflow_steps(workflow_id)
            click.echo(wf_module.format_workflow_human(workflow, steps))
        else:
            echo_error("Workflow not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('run')
@click.argument('workflow_id', type=int)
def workflow_run(workflow_id):
    """Run workflow."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        result = wf.run_workflow(workflow_id)
        click.echo(wf_module.format_result_human(result))
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('delete')
@click.argument('workflow_id', type=int)
def workflow_delete(workflow_id):
    """Delete workflow."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        if wf.delete_workflow(workflow_id):
            click.echo(f"Deleted workflow #{workflow_id}")
        else:
            echo_error("Workflow not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('step-delete')
@click.argument('step_id', type=int)
def workflow_step_delete(step_id):
    """Delete a step from workflow."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        wf = wf_module.WorkflowDB()
        if wf.delete_step(step_id):
            click.echo(f"Deleted step #{step_id}")
        else:
            echo_error("Step not found")
            sys.exit(1)
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('import')
@click.argument('request_id', type=int)
@click.argument('workflow_id', type=int)
@click.option('-e', '--extract', help='Extract var (e.g., data.token)')
@click.option('--condition', help='Condition (e.g., code == 0)')
@click.option('--desc', help='Step description')
def workflow_import(request_id, workflow_id, extract, condition, desc):
    """Import request from history as workflow step.
    
    Example: workflow import 5 1 -e data.token
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from core import workflow as wf_module
    try:
        hist = hist_module.HistoryManager()
        req = hist.get(request_id)
        if not req:
            echo_error(f"Request #{request_id} not found")
            sys.exit(1)
        
        wf = wf_module.WorkflowDB()
        steps = wf.get_workflow_steps(workflow_id)
        step_order = len(steps) + 1
        
        step_id = wf.add_step(
            workflow_id=workflow_id,
            step_order=step_order,
            method=req['method'],
            url=req['url'],
            headers=req.get('headers'),
            body=req.get('body'),
            extract_var=extract,
            condition=condition,
            description=desc or req.get('name')
        )
        click.echo(f"Imported request #{request_id} as step #{step_order} in workflow #{workflow_id}")
    except Exception as e:
        echo_error(str(e))
        sys.exit(1)


@workflow.command('curl')
@click.argument('workflow_id', type=int)
@click.option('-f', '--file', type=click.Path(), help='Read curl from file')
@click.option('-e', '--extract', help='Extract var (e.g., data.token)')
@click.option('--condition', help='Condition (e.g., code == 0)')
@click.option('--desc', help='Step description')
def workflow_curl(workflow_id, file, extract, condition, desc):
    """Import curl directly to workflow.
    
    Examples:
        http-test workflow curl 1 -f request.curl
        cat request.curl | http-test workflow curl 1
    """
    import sys
    
    curl_str = ""
    if file:
        try:
            with open(file, 'r') as f:
                curl_str = f.read()
        except Exception as e:
            echo_error(f"Cannot read file: {e}")
            sys.exit(1)
    else:
        try:
            curl_str = click.get_text_stream('stdin').read()
        except Exception:
            echo_error("No curl provided. Use -f flag or pipe curl command")
            sys.exit(1)
    
    if not curl_str.strip():
        echo_error("No curl command provided")
        sys.exit(1)
    
    try:
        result = curl_parser.parse_curl_input(curl_str)
        
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
        from core import workflow as wf_module
        wf = wf_module.WorkflowDB()
        steps = wf.get_workflow_steps(workflow_id)
        step_order = len(steps) + 1
        
        step_id = wf.add_step(
            workflow_id=workflow_id,
            step_order=step_order,
            method=result['method'],
            url=result['url'],
            headers=result['headers'],
            body=result['body'],
            extract_var=extract,
            condition=condition,
            description=desc
        )
        click.echo(f"Added curl as step #{step_order} in workflow #{workflow_id}")
    except ValueError as e:
        echo_error(str(e))
        sys.exit(1)


# REPL Mode

def is_url(text: str) -> bool:
    """Check if input is a URL."""
    return text.startswith(('http://', 'https://'))

def repl():
    """Interactive REPL mode."""
    click.echo("HTTP Test CLI - REPL Mode")
    click.echo("Type 'help' for commands, 'exit' to quit")
    click.echo("")
    
    while True:
        try:
            line = input("http-test> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("")
            break
        
        if not line:
            continue
        
        if line == 'exit' or line == 'quit':
            break
        
        if line == 'help':
            click.echo("HTTP Commands:")
            click.echo("  curl <args>       - Send curl command (full curl syntax supported)")
            click.echo("  get <url>        - Send GET request")
            click.echo("  post <url>       - Send POST request (-F field=path for upload)")
            click.echo("  put <url>        - Send PUT request (-F field=path for upload)")
            click.echo("  delete <url>     - Send DELETE request (-F field=path for upload)")
            click.echo("  patch <url>     - Send PATCH request (-F field=path for upload)")
            click.echo("  head <url>      - Send HEAD request")
            click.echo("  options <url>   - Send OPTIONS request")
            click.echo("")
            click.echo("History Commands:")
            click.echo("  history           - List saved requests")
            click.echo("  history <id>      - Show request details")
            click.echo("  save \"name\" -u <url> [-m POST] [-c category] - Save request")
            click.echo("  search <keyword>    - Search requests")
            click.echo("")
            click.echo("Workflow Commands:")
            click.echo("  wf create \"name\" -c <category> - Create workflow")
            click.echo("  wf add <id> -u <url> [-m POST] [-d data] [-e var] - Add step")
            click.echo("  wf show <id>       - Show workflow details")
            click.echo("  wf run <id>        - Run workflow")
            click.echo("  wf list            - List all workflows")
            click.echo("  wf import <req> <wf> - Import history request to workflow")
            click.echo("  wf curl <wf>       - Import curl to workflow")
            click.echo("")
            click.echo("Curl Import Commands:")
            click.echo("  curlimport -f file.curl -n \"name\" - Save curl to history")
            click.echo("")
            click.echo("Category Commands:")
            click.echo("  categories        - List categories")
            click.echo("")
            click.echo("Direct URL (auto-GET):")
            click.echo("  https://example.com    - Send GET to URL")
            continue
        
        # Parse command - support more complex curl with quoted args
        try:
            # Auto-detect URL: just enter URL for GET
            if is_url(line):
                resp = req_module.get(line, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('curl '):
                # Parse full curl command
                result = curl_parser.parse_curl_command(line)
                resp = req_module.send_request(
                    method=result['method'],
                    url=result['url'],
                    headers=result['headers'],
                    body=result['body'],
                    timeout=20
                )
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('get ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.get(url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('post ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.post(url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('put ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.put(url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('delete ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.delete(url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('patch ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.patch(url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('head ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.send_request('HEAD', url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line.startswith('options ') and len(line.split()) >= 2:
                url = line.split(maxsplit=1)[1]
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                resp = req_module.send_request('OPTIONS', url, timeout=20)
                _state.last_response = resp
                echo_json(req_module.format_response_human(resp))
            
            elif line == 'history':
                hist = hist_module.HistoryManager()
                requests = hist.list()
                echo_json(hist_module.format_history_human(requests))
            
            elif line.startswith('history ') and len(line.split()) == 2:
                try:
                    req_id = int(line.split()[1])
                    hist = hist_module.HistoryManager()
                    req = hist.get(req_id)
                    if req:
                        click.echo(f"Name: {req['name']}")
                        click.echo(f"Method: {req['method']}")
                        click.echo(f"URL: {req['url']}")
                        click.echo(f"Category: {req['category']}")
                        headers = req.get('headers')
                        if headers:
                            click.echo("Headers:")
                            if isinstance(headers, dict):
                                for k, v in headers.items():
                                    click.echo(f"  {k}: {v}")
                            else:
                                click.echo(f"  {headers}")
                        body = req.get('body')
                        if body:
                            click.echo(f"Body: {body}")
                except ValueError:
                    click.echo("Usage: history <id>")
            
            elif line.startswith('history delete ') or line.startswith('history del '):
                try:
                    parts = line.split()
                    req_id = int(parts[2])
                    hist = hist_module.HistoryManager()
                    if hist.delete(req_id):
                        click.echo(f"Deleted request {req_id}")
                    else:
                        click.echo(f"Request {req_id} not found")
                except (ValueError, IndexError):
                    click.echo("Usage: history delete <id>")
            
            elif line == 'categories':
                hist = hist_module.HistoryManager()
                cats = hist.list_categories()
                click.echo("Categories: " + ", ".join(cats))
            
            elif line.startswith('save ') and len(line.split()) >= 3:
                # parse: save "name" -u url [-m method] [-c category] [-d data]
                parts = line.split()
                try:
                    name = parts[1].strip('"')
                    url = None
                    method = 'GET'
                    category = '默认分类'
                    data = None
                    headers = {}
                    
                    i = 2
                    while i < len(parts):
                        if parts[i] == '-u' and i + 1 < len(parts):
                            url = parts[i + 1]
                            i += 2
                        elif parts[i] == '-m' and i + 1 < len(parts):
                            method = parts[i + 1]
                            i += 2
                        elif parts[i] == '-c' and i + 1 < len(parts):
                            category = parts[i + 1]
                            i += 2
                        elif parts[i] == '-d' and i + 1 < len(parts):
                            data = parts[i + 1]
                            i += 2
                        elif parts[i] == '-H' and i + 1 < len(parts):
                            h = parts[i + 1]
                            if ':' in h:
                                k, v = h.split(':', 1)
                                headers[k.strip()] = v.strip()
                            i += 2
                        else:
                            i += 1
                    
                    if url:
                        hist = hist_module.HistoryManager()
                        req_id = hist.save(name, category, method, url, headers, data)
                        click.echo(f"Saved request #{req_id}: {name}")
                    else:
                        click.echo("Usage: save \"name\" -u <url> [-m POST] [-c category] [-d data]")
                except Exception as e:
                    echo_error(str(e))
            
            elif line.startswith('search ') and len(line.split()) >= 2:
                keyword = line.split(maxsplit=1)[1]
                hist = hist_module.HistoryManager()
                results = hist.search(keyword)
                if results:
                    click.echo(f"Found {len(results)} matching requests:")
                    for req in results:
                        click.echo(f"  [{req['id']}] {req['method']} {req['name']}")
                else:
                    click.echo(f"No results found for: {keyword}")
            
            # Workflow commands in REPL
            elif line.startswith('wf create '):
                # wf create "name" -c category
                name = None
                category = '默认分类'
                
                # Parse: wf create "name" -c category
                # Simple parsing - extract quoted name first
                if '"' in line:
                    start = line.index('"') + 1
                    end = line.index('"', start)
                    name = line[start:end]
                
                # Find -c and get category
                if '-c' in line:
                    parts = line.split('-c')
                    if len(parts) > 1:
                        category_part = parts[1].strip()
                        if category_part:
                            category = category_part.split()[0] if category_part.split() else '默认分类'
                
                if name:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                    from core import workflow as wf_module
                    wf = wf_module.WorkflowDB()
                    wf_id = wf.create_workflow(name, category)
                    click.echo(f"Created workflow #{wf_id}: {name}")
                else:
                    click.echo("Usage: wf create \"name\" -c category")
            
            elif line.startswith('wf show '):
                # Extract workflow ID
                wf_id = None
                for part in line.split():
                    if part.isdigit():
                        wf_id = int(part)
                        break
                
                if wf_id:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                    from core import workflow as wf_module
                    wf = wf_module.WorkflowDB()
                    workflow = wf.get_workflow(wf_id)
                    if workflow:
                        steps = wf.get_workflow_steps(wf_id)
                        click.echo(wf_module.format_workflow_human(workflow, steps))
                    else:
                        click.echo("Workflow not found")
                else:
                    click.echo("Usage: wf show <id>")
            
            elif line.startswith('wf run '):
                # Extract workflow ID
                wf_id = None
                for part in line.split():
                    if part.isdigit():
                        wf_id = int(part)
                        break
                
                if wf_id:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                    from core import workflow as wf_module
                    wf = wf_module.WorkflowDB()
                    workflow = wf.get_workflow(wf_id)
                    if not workflow:
                        click.echo(f"Workflow #{wf_id} not found. Use 'wf list' to see available workflows.")
                    else:
                        result = wf.run_workflow(wf_id)
                        click.echo(wf_module.format_result_human(result))
                else:
                    click.echo("Usage: wf run <id>")
            
            elif line == 'wf list':
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                from core import workflow as wf_module
                wf = wf_module.WorkflowDB()
                workflows = wf.list_workflows()
                if workflows:
                    for w in workflows:
                        steps = wf.get_workflow_steps(w['id'])
                        click.echo(f"[{w['id']}] {w['name']} ({len(steps)} steps)")
                else:
                    click.echo("No workflows. Create one: wf create \"name\"")
            
            elif line.startswith('wf add '):
                # wf add <id> -u <url> [-m POST] [-d data]
                wf_id = None
                for part in line.split():
                    if part.isdigit():
                        wf_id = int(part)
                        break
                
                if not wf_id:
                    click.echo("Usage: wf add <id> -u <url>")
                else:
                    # Find -u
                    u_idx = line.find('-u')
                    url = None
                    method = 'GET'
                    if u_idx > 0:
                        rest = line[u_idx+2:].strip()
                        # Get URL until -m or end
                        url = rest.split()[0] if rest.split() and not rest.split()[0].startswith('-') else rest
                        # Remove trailing options
                        for opt in ['-m', '-d', '-e']:
                            if opt in url:
                                url = url.split(opt)[0].strip()
                    
                    # Find -m
                    if '-m' in line:
                        method = line.split('-m')[1].strip().split()[0] if '-m' in line else 'GET'
                    
                    if url:
                        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                        from core import workflow as wf_module
                        wf = wf_module.WorkflowDB()
                        steps = wf.get_workflow_steps(wf_id)
                        step_order = len(steps) + 1
                        wf.add_step(wf_id, step_order, method, url, {}, None, None)
                        click.echo(f"Added step #{step_order} to workflow #{wf_id}")
                    else:
                        click.echo("Usage: wf add <id> -u <url>")
            
            elif line == 'exit' or line == 'quit':
                
                if not wf_id:
                    click.echo("Usage: wf add <id> -u <url>")
                else:
                    # Simple string searching for options
                    url = None
                    method = 'GET'
                    data = None
                    extract = None
                    headers = {}
                    
                    # Find -u and get URL
                    u_idx = line.find('-u')
                    if u_idx > 0:
                        rest = line[u_idx+2:].strip()
                        for sep in [' -m', ' -d', ' -e']:
                            if sep in rest:
                                url = rest[:rest.index(sep)].strip()
                                break
                        if not url:
                            url = rest.strip()
                    
                    # Find -m method
                    m_idx = line.find('-m')
                    if m_idx > 0:
                        rest = line[m_idx+2:].strip()
                        method = rest.split()[0] if rest.split() else 'GET'
                    
                    # Find -d data
                    d_idx = line.find('-d')
                    if d_idx > 0:
                        rest = line[d_idx+2:].strip()
                        data = rest.split()[0] if rest.split() else None
                    
                    # Find -e extract
                    e_idx = line.find('-e')
                    if e_idx > 0:
                        rest = line[e_idx+2:].strip()
                        extract = rest.split()[0] if rest.split() else None
                    
                    if url:
                        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                        from core import workflow as wf_module
                        wf = wf_module.WorkflowDB()
                        steps = wf.get_workflow_steps(wf_id)
                        step_order = len(steps) + 1
                        wf.add_step(wf_id, step_order, method, url, headers, data, extract)
                        click.echo(f"Added step #{step_order} to workflow #{wf_id}")
                    else:
                        click.echo("Usage: wf add <id> -u <url>")
            
            elif line == 'exit' or line == 'quit':
                break
            
            elif line.startswith('curlimport ') or line == 'curlimport':
                # curlimport -n "name" [-c category]
                name = None
                category = '默认分类'
                
                if '-n' in line:
                    n_idx = line.find('-n')
                    rest = line[n_idx+2:].strip()
                    name = rest.split()[0].strip('"') if rest.split() else None
                
                if '-c' in line:
                    c_idx = line.find('-c')
                    rest = line[c_idx+2:].strip()
                    category = rest.split()[0] if rest.split() else '默认分类'
                
                if name:
                    hist = hist_module.HistoryManager()
                    req_id = hist.save(name, category, 'GET', '', {}, None)
                    click.echo(f"Note: curlimport needs preceding curl command")
                    click.echo("Use: pipe curl into http-test curlimport -n 'name'")
                else:
                    click.echo("Usage: curlimport -n \"name\" -c category")
                    click.echo("Or: cat file.curl | http-test curlimport -n \"name\"")
            
            elif line.startswith('wf curl '):
                # wf curl <id> - parse from stdin
                wf_id = None
                for part in line.split():
                    if part.isdigit():
                        wf_id = int(part)
                        break
                
                if wf_id:
                    click.echo("Use: cat file.curl | http-test (runs in REPL mode)")
                    click.echo("Or use CLI: http-test workflow curl <wf_id> -f file.curl")
                else:
                    click.echo("Usage: wf curl <workflow_id>")
            
            elif line.startswith('wf import '):
                # wf import <req_id> <wf_id>
                parts = line.split()
                req_id = None
                wf_id = None
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if req_id is None:
                            req_id = int(part)
                        elif wf_id is None:
                            wf_id = int(part)
                
                if req_id and wf_id:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
                    from core import workflow as wf_module
                    hist = hist_module.HistoryManager()
                    req = hist.get(req_id)
                    if req:
                        wf = wf_module.WorkflowDB()
                        steps = wf.get_workflow_steps(wf_id)
                        step_order = len(steps) + 1
                        wf.add_step(wf_id, step_order, req['method'], req['url'], 
                                   req.get('headers'), req.get('body'))
                        click.echo(f"Imported request #{req_id} as step #{step_order}")
                    else:
                        click.echo(f"Request #{req_id} not found")
                else:
                    click.echo("Usage: wf import <request_id> <workflow_id>")
            
            else:
                click.echo(f"Unknown command: {line}")
                click.echo("Type 'help' for available commands")
        except Exception as e:
            echo_error(str(e))


# Main entry point

if __name__ == '__main__':
    # Check for REPL mode (no args)
    if len(sys.argv) == 1:
        repl()
    else:
        cli(obj={})
