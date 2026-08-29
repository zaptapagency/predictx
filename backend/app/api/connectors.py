"""
Data Connectors API
Manage data source connections and syncs
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from app.db.models_saas import User, Organization
from app.db.connector_models import (
    DataConnection, DataSource, SyncLog, CustomerData,
    FieldMapping, ConnectorStatus, ConnectorType
)
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.connectors.connector_manager import ConnectorManager
from app.utils.time import utcnow

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateConnectionRequest(BaseModel):
    name: str
    connector_type: str
    description: Optional[str] = None
    config: Dict[str, Any]
    credentials: Dict[str, Any]


class CreateDataSourceRequest(BaseModel):
    connection_id: int
    name: str
    source_path: str
    primary_key: str
    sync_type: str = "incremental"
    incremental_field: Optional[str] = None


class SyncSourceRequest(BaseModel):
    sync_type: str = "manual"  # manual, scheduled
    force_full: bool = False


# ============================================================================
# CONNECTOR TYPES
# ============================================================================

@router.get("/types")
def get_connector_types():
    """Get list of supported connector types"""
    return {"types": ConnectorManager.get_supported_types()}


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@router.post("/connections")
def create_connection(
    request: CreateConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new data connection"""

    try:
        # Validate connector type
        connector = ConnectorManager.create_connector(
            request.connector_type,
            request.config,
            request.credentials
        )

        # Test connection
        if not connector.test_connection():
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect: {connector.last_error}"
            )

        # Create connection record
        db_connection = DataConnection(
            organization_id=current_user.organization_id,
            name=request.name,
            connector_type=request.connector_type,
            description=request.description,
            config=request.config,
            credentials=request.credentials,
            created_by_id=current_user.id,
            last_tested_at=utcnow(),
            last_tested_status="success"
        )

        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)

        # Create status record
        status = ConnectorStatus(
            connection_id=db_connection.id,
            organization_id=current_user.organization_id,
            is_healthy=True,
            last_tested_time=utcnow()
        )
        db.add(status)
        db.commit()

        return {
            "id": db_connection.id,
            "name": db_connection.name,
            "connector_type": db_connection.connector_type,
            "status": "success",
            "message": "Connection created and tested successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/connections")
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all connections for organization"""

    connections = db.query(DataConnection).filter(
        DataConnection.organization_id == current_user.organization_id
    ).all()

    return {
        "connections": [
            {
                "id": c.id,
                "name": c.name,
                "connector_type": c.connector_type,
                "is_active": c.is_active,
                "last_tested_at": c.last_tested_at,
                "last_tested_status": c.last_tested_status
            }
            for c in connections
        ]
    }


@router.get("/connections/{connection_id}")
def get_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get connection details"""

    connection = db.query(DataConnection).filter(
        DataConnection.id == connection_id,
        DataConnection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    status = db.query(ConnectorStatus).filter(
        ConnectorStatus.connection_id == connection_id
    ).first()

    # `credentials` and `config` are deliberately omitted: config carries
    # refresh tokens and client ids alongside the harmless instance URL, and
    # there is no client-side use for either.
    return {
        "id": connection.id,
        "name": connection.name,
        "connector_type": connection.connector_type,
        "is_active": connection.is_active,
        "created_at": connection.created_at,
        "status": {
            "is_healthy": status.is_healthy if status else None,
            "last_sync_time": status.last_sync_time if status else None,
            "total_records": status.total_records if status else 0,
            "error_count_24h": status.error_count_24h if status else 0
        }
    }


@router.post("/connections/{connection_id}/test")
def test_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection"""

    connection = db.query(DataConnection).filter(
        DataConnection.id == connection_id,
        DataConnection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        connector = ConnectorManager.create_connector(
            connection.connector_type,
            connection.config,
            connection.credentials
        )

        is_valid = connector.test_connection()

        connection.last_tested_at = utcnow()
        connection.last_tested_status = "success" if is_valid else "failed"
        connection.test_error = connector.last_error if not is_valid else None

        db.commit()

        return {
            "connection_id": connection_id,
            "is_valid": is_valid,
            "error": connector.last_error if not is_valid else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DATA SOURCE MANAGEMENT
# ============================================================================

@router.post("/sources")
def create_data_source(
    request: CreateDataSourceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new data source from connection"""

    # Verify connection exists
    connection = db.query(DataConnection).filter(
        DataConnection.id == request.connection_id,
        DataConnection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Get schema from connector
        connector = ConnectorManager.create_connector(
            connection.connector_type,
            connection.config,
            connection.credentials
        )

        schema = connector.get_table_schema(request.source_path)

        if not schema:
            raise Exception("Could not fetch schema")

        # Create data source
        data_source = DataSource(
            connection_id=request.connection_id,
            organization_id=current_user.organization_id,
            name=request.name,
            source_path=request.source_path,
            schema=schema,
            primary_key=request.primary_key,
            sync_type=request.sync_type,
            incremental_field=request.incremental_field,
            is_active=True
        )

        db.add(data_source)
        db.commit()
        db.refresh(data_source)

        return {
            "id": data_source.id,
            "name": data_source.name,
            "schema": schema,
            "message": "Data source created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
def list_data_sources(
    connection_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List data sources"""

    query = db.query(DataSource).filter(
        DataSource.organization_id == current_user.organization_id
    )

    if connection_id:
        query = query.filter(DataSource.connection_id == connection_id)

    sources = query.all()

    return {
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "connection_id": s.connection_id,
                "sync_type": s.sync_type,
                "record_count": s.record_count
            }
            for s in sources
        ]
    }


# ============================================================================
# SYNC OPERATIONS
# ============================================================================

@router.post("/sources/{source_id}/sync")
def sync_data_source(
    source_id: int,
    request: SyncSourceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger sync of data source"""

    source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.organization_id == current_user.organization_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    connection = source.connection

    try:
        # Create sync log
        sync_log = SyncLog(
            data_source_id=source_id,
            organization_id=current_user.organization_id,
            sync_type=request.sync_type,
            status="running",
            started_at=utcnow()
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)

        # Queue background sync
        background_tasks.add_task(
            perform_sync,
            source_id,
            connection.connector_type,
            connection.config,
            connection.credentials,
            sync_log.id,
            current_user.organization_id,
            db
        )

        return {
            "sync_id": sync_log.id,
            "status": "running",
            "message": "Sync started in background"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def perform_sync(
    source_id: int,
    connector_type: str,
    config: Dict,
    credentials: Dict,
    sync_log_id: int,
    org_id: int,
    db: Session
):
    """Background task to perform actual sync"""
    try:
        # Get data source and connector
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        connector = ConnectorManager.create_connector(connector_type, config, credentials)

        # Fetch data
        incremental_field = source.incremental_field if source.sync_type == "incremental" else None
        incremental_value = source.last_synced_value if incremental_field else None

        records, total_count = connector.fetch_data(
            source.source_path,
            incremental_field=incremental_field,
            incremental_value=incremental_value
        )

        # Store records
        inserted = 0
        updated = 0
        for record in records:
            customer_id = record.get(source.primary_key)

            existing = db.query(CustomerData).filter(
                CustomerData.organization_id == org_id,
                CustomerData.data_source_id == source_id,
                CustomerData.customer_id == customer_id
            ).first()

            if existing:
                existing.customer_data = record
                existing.updated_at = utcnow()
                updated += 1
            else:
                customer_data = CustomerData(
                    organization_id=org_id,
                    data_source_id=source_id,
                    customer_id=customer_id,
                    customer_data=record,
                    raw_fields=extract_numeric_fields(record)
                )
                db.add(customer_data)
                inserted += 1

        # Update sync log
        sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id).first()
        sync_log.status = "success"
        sync_log.completed_at = utcnow()
        sync_log.duration_seconds = (sync_log.completed_at - sync_log.started_at).total_seconds()
        sync_log.records_fetched = total_count
        sync_log.records_inserted = inserted
        sync_log.records_updated = updated

        # Update source
        source.record_count = total_count
        if incremental_field and records:
            source.last_synced_value = records[-1].get(incremental_field)

        db.commit()

    except Exception as e:
        sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id).first()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        sync_log.completed_at = utcnow()
        db.commit()


def extract_numeric_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract numeric and categorical fields for prediction features"""
    raw_fields = {}
    for key, value in record.items():
        if isinstance(value, (int, float)):
            raw_fields[key] = value
        elif isinstance(value, bool):
            raw_fields[key] = 1 if value else 0
        elif isinstance(value, str) and value.replace(".", "", 1).replace("-", "", 1).isdigit():
            try:
                raw_fields[key] = float(value)
            except:
                raw_fields[key] = value
    return raw_fields


@router.get("/sources/{source_id}/syncs")
def get_sync_history(
    source_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync history for a data source"""

    # Verify access
    source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.organization_id == current_user.organization_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    syncs = db.query(SyncLog).filter(
        SyncLog.data_source_id == source_id
    ).order_by(desc(SyncLog.started_at)).limit(limit).all()

    return {
        "syncs": [
            {
                "id": s.id,
                "status": s.status,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "records_fetched": s.records_fetched,
                "records_inserted": s.records_inserted,
                "records_updated": s.records_updated,
                "error_message": s.error_message
            }
            for s in syncs
        ]
    }
