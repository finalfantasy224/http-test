#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workflow management module for http-test CLI.
Extends history_db to support workflows with ordered requests.
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class WorkflowDB:
    """Workflow database manager."""
    
    def __init__(self, db_path="http_requests_history.db"):
        """Initialize workflow database."""
        self.db_path = db_path
        self._init_workflow_table()
    
    def _init_workflow_table(self):
        """Create workflow tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT '默认分类',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Workflow steps table (ordered requests in a workflow)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                request_id INTEGER,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                body TEXT,
                extract_var TEXT,
                condition TEXT,
                description TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_workflow(self, name: str, category: str = "默认分类", 
                  description: str = None) -> int:
        """Create a new workflow.
        
        Args:
            name: Workflow name
            category: Category
            description: Description
            
        Returns:
            Workflow ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflows (name, category, description, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (name, category, description, datetime.now()))
        
        workflow_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return workflow_id
    
    def add_step(self, workflow_id: int, step_order: int, method: str, url: str,
                headers: Optional[Dict] = None, body: Optional[str] = None,
                extract_var: Optional[str] = None,
                condition: Optional[str] = None,
                description: str = None,
                request_id: Optional[int] = None) -> int:
        """Add step to workflow.
        
        Args:
            workflow_id: Workflow ID
            step_order: Step order (1-based)
            method: HTTP method
            url: Request URL (can use {{variable}} placeholders)
            headers: Request headers
            body: Request body
            extract_var: Variable to extract from response (e.g., "data.userId" -> stores as userId)
            condition: Condition to proceed (e.g., "status == 200")
            description: Step description
            request_id: Link to existing request in history
            
        Returns:
            Step ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        headers_json = json.dumps(headers) if headers else None
        
        cursor.execute('''
            INSERT INTO workflow_steps 
            (workflow_id, step_order, request_id, method, url, headers, body, 
             extract_var, condition, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (workflow_id, step_order, request_id, method, url, headers_json, body,
              extract_var, condition, description))
        
        step_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return step_id
    
    def get_workflow(self, workflow_id: int) -> Optional[Dict]:
        """Get workflow details.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, category, description, created_at, updated_at
            FROM workflows
            WHERE id = ?
        ''', (workflow_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'description': row[3],
            'created_at': row[4],
            'updated_at': row[5]
        }
    
    def get_workflow_steps(self, workflow_id: int) -> List[Dict]:
        """Get all steps in a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of step dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, step_order, request_id, method, url, headers, body,
                   extract_var, condition, description
            FROM workflow_steps
            WHERE workflow_id = ?
            ORDER BY step_order
        ''', (workflow_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        steps = []
        for row in rows:
            headers = json.loads(row[5]) if row[5] else {}
            steps.append({
                'id': row[0],
                'step_order': row[1],
                'request_id': row[2],
                'method': row[3],
                'url': row[4],
                'headers': headers,
                'body': row[6],
                'extract_var': row[7],
                'condition': row[8],
                'description': row[9]
            })
        
        return steps
    
    def list_workflows(self, category: str = None) -> List[Dict]:
        """List all workflows.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of workflow dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT id, name, category, description, created_at
                FROM workflows
                WHERE category = ?
                ORDER BY updated_at DESC
            ''', (category,))
        else:
            cursor.execute('''
                SELECT id, name, category, description, created_at
                FROM workflows
                ORDER BY updated_at DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': row[0], 'name': row[1], 'category': row[2],
                'description': row[3], 'created_at': row[4]} for row in rows]
    
    def delete_workflow(self, workflow_id: int) -> bool:
        """Delete workflow and its steps.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflow_steps WHERE workflow_id = ?', (workflow_id,))
        cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def delete_step(self, step_id: int) -> bool:
        """Delete a step from workflow.
        
        Args:
            step_id: Step ID
            
        Returns:
            True if deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflow_steps WHERE id = ?', (step_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def run_workflow(self, workflow_id: int, 
                 initial_vars: Dict = None) -> Dict:
        """Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            initial_vars: Initial variables
            
        Returns:
            Execution result with steps results
        """
        from core import request as req_module
        
        workflow = self.get_workflow(workflow_id)
        steps = self.get_workflow_steps(workflow_id)
        
        if not workflow or not steps:
            return {'success': False, 'error': 'Workflow not found'}
        
        # Variables extracted from responses
        vars = initial_vars or {}
        results = []
        
        for step in steps:
            # Replace variables in URL and body
            url = self._replace_vars(step['url'], vars)
            body = self._replace_vars(step['body'], vars) if step['body'] else None
            headers = {k: self._replace_vars(v, vars) for k, v in step['headers'].items()}
            
            # Execute request
            try:
                resp = req_module.send_request(
                    method=step['method'],
                    url=url,
                    headers=headers,
                    body=body,
                    timeout=30
                )
                
                step_result = {
                    'step_order': step['step_order'],
                    'status_code': resp.status_code,
                    'success': resp.is_success(),
                    'elapsed_time': resp.elapsed_time,
                    'response': resp.to_dict()
                }
                
                # Extract variable from response if configured
                if step['extract_var'] and resp.json:
                    self._extract_var(step['extract_var'], resp.json, vars)
                
                # Check condition if configured
                if step['condition']:
                    if not self._eval_condition(step['condition'], vars):
                        return {
                            'success': False,
                            'step': step['step_order'],
                            'error': f"Condition failed: {step['condition']}",
                            'results': results
                        }
                
                results.append(step_result)
                
            except Exception as e:
                return {
                    'success': False,
                    'step': step['step_order'],
                    'error': str(e),
                    'results': results
                }
        
        return {
            'success': True,
            'workflow_name': workflow['name'],
            'results': results,
            'vars': vars
        }
    
    def _replace_vars(self, text: str, vars: Dict) -> str:
        """Replace {{variable}} placeholders in text."""
        if not text:
            return text
        for key, value in vars.items():
            text = text.replace('{{' + key + '}}', str(value))
        return text
    
    def _extract_var(self, extract_var: str, response: Dict, vars: Dict):
        """Extract variable from response JSON."""
        # e.g., "data.userId" -> extract response["data"]["userId"]
        parts = extract_var.split('.')
        value = response
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return
        if value is not None:
            # Use last part as variable name
            vars[parts[-1]] = value
    
    def _eval_condition(self, condition: str, vars: Dict) -> bool:
        """Evaluate condition string."""
        try:
            # Simple condition evaluation
            # e.g., "status == 200", "code == 0"
            local_vars = vars.copy()
            local_vars['True'] = True
            local_vars['False'] = False
            return eval(condition, {"__builtins__": {}}, local_vars)
        except:
            return True


def format_workflow_human(workflow: Dict, steps: List[Dict]) -> str:
    """Format workflow for human display."""
    lines = []
    lines.append(f"Workflow: {workflow['name']} (ID: {workflow['id']})")
    lines.append(f"Category: {workflow['category']}")
    if workflow['description']:
        lines.append(f"Description: {workflow['description']}")
    lines.append(f"Steps: {len(steps)}")
    lines.append("")
    
    for step in steps:
        lines.append(f"  [{step['step_order']}] {step['method']} {step['url']}")
        if step['description']:
            lines.append(f"      {step['description']}")
        if step['extract_var']:
            lines.append(f"      Extract: {step['extract_var']}")
        if step['condition']:
            lines.append(f"      Condition: {step['condition']}")
    
    return '\n'.join(lines)


def format_result_human(result: Dict) -> str:
    """Format execution result for human display."""
    lines = []
    
    if result.get('success'):
        lines.append(f"✓ Workflow '{result.get('workflow_name', '')}' completed successfully")
    else:
        lines.append(f"✗ Workflow failed at step {result.get('step', '?')}")
        if result.get('error'):
            lines.append(f"  Error: {result['error']}")
    
    lines.append("")
    
    for r in result.get('results', []):
        status = "✓" if r.get('success') else "✗"
        lines.append(f"  Step {r['step_order']}: {r['status_code']} ({r['elapsed_time']:.2f}s) {status}")
    
    return '\n'.join(lines)