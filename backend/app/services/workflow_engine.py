"""
Workflow Execution Engine
Executes workflows and actions in response to predictions
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import json
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.db.workflow_models import (
    Workflow, WorkflowExecution, ActionExecution, WorkflowAction, ExecutionStatus
)
from app.db.connector_models import DataConnection


class WorkflowEngine:
    """
    Executes workflows and individual actions
    Supports: Email, Slack, Salesforce, Webhooks, Tasks
    """

    def __init__(self, db: Session):
        self.db = db

    def execute_workflow(
        self,
        workflow_id: int,
        customer_id: str,
        trigger_data: Dict[str, Any],
        prediction_id: Optional[int] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow for a customer
        """
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow or not workflow.is_active:
            return None

        # Check segment filter
        if workflow.segment_filter:
            if not self._matches_segment(customer_id, workflow.segment_filter):
                return None

        # Create execution record
        execution = WorkflowExecution(
            organization_id=workflow.organization_id,
            workflow_id=workflow_id,
            customer_id=customer_id,
            prediction_id=prediction_id,
            status=ExecutionStatus.RUNNING,
            trigger_data=trigger_data,
            started_at=datetime.utcnow()
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        try:
            # Execute actions in sequence
            results = []
            for action in sorted(workflow.actions, key=lambda a: a.sequence):
                if not action.is_active:
                    continue

                # Check conditions
                if action.condition_expression:
                    if not self._evaluate_condition(
                        action.condition_expression,
                        trigger_data
                    ):
                        action_exec = ActionExecution(
                            workflow_execution_id=execution.id,
                            action_id=action.id,
                            sequence=action.sequence,
                            status=ExecutionStatus.SKIPPED
                        )
                        self.db.add(action_exec)
                        continue

                # Execute action
                action_result = self._execute_action(
                    execution,
                    action,
                    customer_id,
                    trigger_data
                )
                results.append(action_result)

            # Update execution
            execution.status = ExecutionStatus.SUCCESS
            execution.execution_results = results
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()

        # Update workflow run count
        workflow.run_count = (workflow.run_count or 0) + 1

        self.db.commit()
        return execution

    def _execute_action(
        self,
        execution: WorkflowExecution,
        action: WorkflowAction,
        customer_id: str,
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute individual action"""

        action_exec = ActionExecution(
            workflow_execution_id=execution.id,
            action_id=action.id,
            sequence=action.sequence,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        try:
            config = action.config
            action_type = action.action_type.value

            if action_type == "email":
                result = self._execute_email(config, trigger_data)

            elif action_type == "slack":
                result = self._execute_slack(config, trigger_data)

            elif action_type == "salesforce":
                result = self._execute_salesforce(
                    execution.organization_id,
                    config,
                    customer_id,
                    trigger_data
                )

            elif action_type == "webhook":
                result = self._execute_webhook(config, trigger_data)

            elif action_type == "task":
                result = self._execute_task(config, trigger_data)

            else:
                raise ValueError(f"Unknown action type: {action_type}")

            action_exec.status = ExecutionStatus.SUCCESS
            action_exec.response_data = result.get("response_data")
            action_exec.external_id = result.get("external_id")

        except Exception as e:
            action_exec.status = ExecutionStatus.FAILED
            action_exec.error_message = str(e)

        action_exec.completed_at = datetime.utcnow()
        action_exec.duration_seconds = (
            action_exec.completed_at - action_exec.started_at
        ).total_seconds()

        self.db.add(action_exec)
        self.db.commit()

        return {
            "action_id": action.id,
            "status": action_exec.status.value,
            "external_id": action_exec.external_id
        }

    def _execute_email(self, config: Dict, data: Dict) -> Dict:
        """Send email"""
        to = self._render_template(config.get("to_field"), data)
        subject = self._render_template(config.get("subject_template"), data)
        body = self._render_template(config.get("body_template"), data)

        # TODO: Use email service (SendGrid, AWS SES, etc)
        # For now, log
        print(f"EMAIL: {to} | {subject}")

        return {
            "response_data": {"sent": True},
            "external_id": f"email_{datetime.utcnow().timestamp()}"
        }

    def _execute_slack(self, config: Dict, data: Dict) -> Dict:
        """Send Slack message"""
        channel = config.get("channel")
        message = self._render_template(config.get("message_template"), data)

        # TODO: Use Slack SDK
        # For now, log
        print(f"SLACK: {channel} | {message}")

        return {
            "response_data": {"sent": True},
            "external_id": f"slack_{datetime.utcnow().timestamp()}"
        }

    def _execute_salesforce(
        self,
        org_id: int,
        config: Dict,
        customer_id: str,
        data: Dict
    ) -> Dict:
        """Update Salesforce record"""
        object_type = config.get("object")  # Account, Contact, Opportunity
        action = config.get("action")  # create, update
        field_mapping = config.get("field_mapping")  # {sf_field: template}

        # Build payload
        payload = {}
        for sf_field, template in field_mapping.items():
            payload[sf_field] = self._render_template(template, data)

        # TODO: Get Salesforce connection, update record
        # For now, log
        print(f"SALESFORCE: {object_type} {action} | {payload}")

        return {
            "response_data": {"updated": True},
            "external_id": f"sf_{customer_id}"
        }

    def _execute_webhook(self, config: Dict, data: Dict) -> Dict:
        """Call webhook"""
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        payload_template = config.get("payload_template", {})

        # Render payload
        payload = self._render_template(payload_template, data)

        # Call webhook
        response = requests.request(
            method,
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        return {
            "response_data": {
                "status_code": response.status_code,
                "response": response.text[:500]
            },
            "external_id": f"webhook_{response.status_code}"
        }

    def _execute_task(self, config: Dict, data: Dict) -> Dict:
        """Create task"""
        title = self._render_template(config.get("title_template"), data)
        description = self._render_template(config.get("description_template"), data)
        owner_id = config.get("owner_id")

        # TODO: Create task in task management system
        # For now, log
        print(f"TASK: {title} | {description}")

        return {
            "response_data": {"created": True},
            "external_id": f"task_{datetime.utcnow().timestamp()}"
        }

    def _render_template(self, template: Any, data: Dict) -> Any:
        """
        Render template with data
        Supports: {field_name}, {field.nested}, conditionals
        """
        if isinstance(template, dict):
            return {k: self._render_template(v, data) for k, v in template.items()}

        if isinstance(template, list):
            return [self._render_template(v, data) for v in template]

        if not isinstance(template, str):
            return template

        # Replace variables: {customer_name} -> data['customer_name']
        result = template
        matches = re.findall(r'\{([^}]+)\}', template)

        for match in matches:
            value = self._get_nested_value(data, match)
            if value is not None:
                result = result.replace(f"{{{match}}}", str(value))

        return result

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict"""
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _evaluate_condition(self, expression: str, data: Dict) -> bool:
        """
        Evaluate simple JS-like conditions
        Supports: data.field > value, data.field == value, data.field in [list]
        """
        # Replace data.field with actual values
        expr = expression
        matches = re.findall(r'data\.(\w+)', expression)

        for match in matches:
            value = data.get(match)
            if isinstance(value, str):
                expr = expr.replace(f"data.{match}", f"'{value}'")
            else:
                expr = expr.replace(f"data.{match}", str(value))

        try:
            return eval(expr)
        except:
            return False

    def _matches_segment(self, customer_id: str, segment_filter: Dict) -> bool:
        """Check if customer matches segment"""
        # TODO: Query customer segment membership
        # For now, return true
        return True
