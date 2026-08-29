"""
Playbook steps must deliver, and a run that failed must say so.

The engine used to print each step to stdout and mark the whole workflow
successful regardless. These tests pin the corrected behaviour.
"""

import uuid

import pytest
import requests

from app.database import engine
from app.db.action_models import Action
from app.db.connector_models import CustomerData, DataConnection, DataSource
from app.db.database import Base, SessionLocal
from app.db.models_saas import Organization
from app.db.workflow_models import (
    ActionType, ExecutionStatus, Workflow, WorkflowAction, WorkflowTrigger,
)
from app.services.workflow_engine import WorkflowEngine


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def org(db):
    """An organization with an owner, since most rows require a creator."""
    from app.db.models_saas import User

    organization = Organization(name=f"WF {uuid.uuid4().hex[:6]}", slug=uuid.uuid4().hex[:10])
    db.add(organization)
    db.flush()

    owner = User(
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        username=uuid.uuid4().hex[:8],
        hashed_password="x",
        full_name="Owner",
        organization_id=organization.id,
    )
    db.add(owner)
    db.commit()
    db.refresh(organization)
    organization._owner_id = owner.id
    return organization


def _workflow(db, org, action_type, config, segment_filter=None):
    workflow = Workflow(
        organization_id=org.id,
        name="Test playbook",
        trigger_type=WorkflowTrigger.PREDICTION_CREATED,
        is_active=True,
        segment_filter=segment_filter,
    )
    db.add(workflow)
    db.flush()
    db.add(WorkflowAction(
        workflow_id=workflow.id,
        sequence=1,
        action_type=action_type,
        config=config,
        is_active=True,
    ))
    db.commit()
    db.refresh(workflow)
    return workflow


def test_webhook_step_actually_posts(db, org, monkeypatch):
    posted = {}

    class Resp:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(requests, "request",
                        lambda method, url, **kw: (posted.update({"url": url, "json": kw.get("json")}), Resp())[1])

    workflow = _workflow(db, org, ActionType.WEBHOOK, {
        "url": "https://example.com/hook",
        "payload_template": {"customer": "{customer_name}"},
    })

    execution = WorkflowEngine(db).execute_workflow(
        workflow.id, "C1", {"customer_name": "Acme"}
    )

    assert execution.status == ExecutionStatus.SUCCESS
    assert posted["url"] == "https://example.com/hook"
    assert posted["json"] == {"customer": "Acme"}


def test_a_workflow_whose_only_step_failed_is_not_successful(db, org, monkeypatch):
    monkeypatch.setattr("app.services.channels.time.sleep", lambda _s: None)
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: (_ for _ in ()).throw(requests.Timeout()))

    workflow = _workflow(db, org, ActionType.WEBHOOK, {
        "url": "https://example.com/hook", "payload_template": {},
    })

    execution = WorkflowEngine(db).execute_workflow(workflow.id, "C1", {})

    assert execution.status == ExecutionStatus.FAILED
    assert "timed out" in (execution.error_message or "")


def test_slack_step_without_an_integration_fails_loudly(db, org):
    workflow = _workflow(db, org, ActionType.SLACK, {"message_template": "hello"})

    execution = WorkflowEngine(db).execute_workflow(workflow.id, "C1", {})

    assert execution.status == ExecutionStatus.FAILED
    assert "not connected" in (execution.error_message or "").lower()


def test_task_step_creates_a_real_action(db, org):
    workflow = _workflow(db, org, ActionType.TASK, {
        "title_template": "Follow up with {customer_name}",
        "description_template": "They are at risk.",
    })

    execution = WorkflowEngine(db).execute_workflow(
        workflow.id, "C1", {"customer_name": "Acme", "customer_id": "C1"}
    )

    assert execution.status == ExecutionStatus.SUCCESS

    task = db.query(Action).filter(
        Action.organization_id == org.id,
        Action.title == "Follow up with Acme",
    ).one()
    assert task.action_type == "task"
    assert task.entity_id == "C1"


def test_segment_filter_excludes_customers_who_do_not_match(db, org):
    """A filter that matches nobody must send nothing, not everything."""
    connection = DataConnection(organization_id=org.id, name="csv", connector_type="csv",
                                config={}, credentials={}, created_by_id=org._owner_id)
    db.add(connection)
    db.flush()
    source = DataSource(organization_id=org.id, connection_id=connection.id,
                        name="rows", source_path="rows", schema={},
                        primary_key="customer_id")
    db.add(source)
    db.flush()
    db.add(CustomerData(organization_id=org.id, data_source_id=source.id,
                        customer_id="C1", customer_data={"plan": "free"}, raw_fields={}))
    db.commit()

    workflow = _workflow(db, org, ActionType.TASK,
                         {"title_template": "Upsell"},
                         segment_filter={"plan": "enterprise"})

    assert WorkflowEngine(db).execute_workflow(workflow.id, "C1", {}) is None

    workflow2 = _workflow(db, org, ActionType.TASK,
                          {"title_template": "Upsell"},
                          segment_filter={"plan": "free"})

    assert WorkflowEngine(db).execute_workflow(workflow2.id, "C1", {}) is not None
