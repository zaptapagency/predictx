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
    Workflow, WorkflowExecution, WorkflowActionExecution, WorkflowAction, ExecutionStatus
)
from app.db.connector_models import DataConnection
from app.utils.time import utcnow
from app.services.channels import (
    ChannelError, DeliveryResult, deliver_email, deliver_salesforce_task,
    deliver_slack, deliver_webhook,
)


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
            started_at=utcnow()
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
                        action_exec = WorkflowActionExecution(
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

            # A workflow is only successful if its steps were. Individual
            # failures are captured per action, so check them before
            # declaring the run a success.
            step_failures = [r for r in results if r.get("status") == ExecutionStatus.FAILED.value]
            if step_failures and len(step_failures) == len(results):
                execution.status = ExecutionStatus.FAILED
                execution.error_message = step_failures[0].get("error")
            elif step_failures:
                execution.status = ExecutionStatus.PARTIAL
                execution.error_message = (
                    f"{len(step_failures)} of {len(results)} steps failed: "
                    f"{step_failures[0].get('error')}"
                )
            else:
                execution.status = ExecutionStatus.SUCCESS
            execution.execution_results = results
            execution.completed_at = utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = utcnow()
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

        action_exec = WorkflowActionExecution(
            workflow_execution_id=execution.id,
            action_id=action.id,
            sequence=action.sequence,
            status=ExecutionStatus.RUNNING,
            started_at=utcnow()
        )

        try:
            config = action.config
            action_type = action.action_type.value

            org_id = execution.organization_id

            if action_type == "email":
                result = self._execute_email(org_id, config, trigger_data)

            elif action_type == "slack":
                result = self._execute_slack(org_id, config, trigger_data)

            elif action_type == "salesforce":
                result = self._execute_salesforce(
                    execution.organization_id,
                    config,
                    customer_id,
                    trigger_data
                )

            elif action_type == "webhook":
                result = self._execute_webhook(org_id, config, trigger_data)

            elif action_type == "task":
                result = self._execute_task(org_id, config, trigger_data)

            else:
                raise ValueError(f"Unknown action type: {action_type}")

            action_exec.status = ExecutionStatus.SUCCESS
            action_exec.response_data = result.get("response_data")
            action_exec.external_id = result.get("external_id")

        except Exception as e:
            action_exec.status = ExecutionStatus.FAILED
            action_exec.error_message = str(e)

        action_exec.completed_at = utcnow()
        action_exec.duration_seconds = (
            action_exec.completed_at - action_exec.started_at
        ).total_seconds()

        self.db.add(action_exec)
        self.db.commit()

        return {
            "action_id": action.id,
            "status": action_exec.status.value,
            "external_id": action_exec.external_id,
            "error": action_exec.error_message,
        }

    def _execute_email(self, org_id: int, config: Dict, data: Dict) -> Dict:
        """Send a real email."""
        to = self._render_template(config.get("to_field"), data)
        subject = self._render_template(config.get("subject_template"), data)
        body = self._render_template(config.get("body_template"), data) or ""

        paragraphs = "".join(f"<p>{line}</p>" for line in str(body).split("\n") if line.strip())
        result = deliver_email(
            self.db, org_id,
            to=to, subject=subject or "A message from your team",
            body_html=f"<html><body>{paragraphs}</body></html>", body_text=str(body),
        )
        return {"response_data": result.response_data, "external_id": result.external_id}

    def _execute_slack(self, org_id: int, config: Dict, data: Dict) -> Dict:
        """Post a real Slack message."""
        message = self._render_template(config.get("message_template"), data)
        result = deliver_slack(
            self.db, org_id,
            text=str(message), webhook_url=config.get("webhook_url"),
        )
        return {"response_data": result.response_data, "external_id": result.external_id}

    def _execute_salesforce(
        self,
        org_id: int,
        config: Dict,
        customer_id: str,
        data: Dict
    ) -> Dict:
        """
        Create a Salesforce task from the workflow step.

        The engine's original contract was arbitrary field updates on any
        object. That needs write support the Salesforce connector does not
        have yet, so this delivers the one write we can make safely and the
        field_mapping is rendered into the task description rather than
        silently dropped.
        """
        field_mapping = config.get("field_mapping") or {}
        rendered = {k: self._render_template(v, data) for k, v in field_mapping.items()}
        details = "\n".join(f"{k}: {v}" for k, v in rendered.items())

        result = deliver_salesforce_task(
            self.db, org_id,
            subject=self._render_template(config.get("subject"), data) or f"Follow up: {customer_id}",
            description=details,
            account_id=config.get("account_id"),
            contact_id=config.get("contact_id"),
        )
        return {"response_data": result.response_data, "external_id": result.external_id}

    def _execute_webhook(self, org_id: int, config: Dict, data: Dict) -> Dict:
        """Call the configured webhook."""
        payload = self._render_template(config.get("payload_template", {}), data)
        result = deliver_webhook(
            self.db, org_id,
            payload=payload if isinstance(payload, dict) else {"payload": payload},
            url=config.get("url"),
            method=config.get("method", "POST"),
            headers=config.get("headers"),
        )
        return {"response_data": result.response_data, "external_id": result.external_id}

    def _execute_task(self, org_id: int, config: Dict, data: Dict) -> Dict:
        """
        Create a real task in the Action Center.

        Workflow tasks used to be a print statement. They now become Action
        rows, which means they show up in the same queue as model-generated
        work and can be executed and tracked there.
        """
        from app.db.action_models import Action, ActionPriority, ActionStatus

        title = self._render_template(config.get("title_template"), data)
        description = self._render_template(config.get("description_template"), data)
        owner_id = config.get("owner_id")

        if not title:
            raise ChannelError("Task step has no title_template, so there is nothing to create.")

        task = Action(
            organization_id=org_id,
            title=str(title),
            description=str(description or ""),
            action_type="task",
            priority=config.get("priority") or ActionPriority.MEDIUM,
            status=ActionStatus.PENDING,
            entity_type="customer",
            entity_id=str(data.get("customer_id") or "unknown"),
            entity_name=str(data.get("customer_name") or data.get("customer_id") or "Unknown"),
            assigned_to_id=owner_id,
            action_config={"source": "workflow"},
        )
        self.db.add(task)
        self.db.flush()

        return {"response_data": {"action_id": task.id, "title": task.title},
                "external_id": f"action_{task.id}"}

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
        """
        Check a customer against a segment filter.

        The filter is a dict of field -> expected value, matched against the
        customer's most recent synced record. An unknown field does not match:
        a filter nobody can satisfy should send nothing, not everything.
        """
        from app.db.connector_models import CustomerData

        if not segment_filter:
            return True

        record = self.db.query(CustomerData).filter(
            CustomerData.customer_id == customer_id
        ).order_by(CustomerData.synced_at.desc()).first()

        if not record:
            return False

        fields = {str(k).lower(): v for k, v in (record.customer_data or {}).items()}

        for field, expected in segment_filter.items():
            actual = fields.get(str(field).lower())
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif str(actual) != str(expected):
                return False

        return True
