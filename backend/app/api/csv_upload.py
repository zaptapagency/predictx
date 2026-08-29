"""
CSV Upload

Lets a user get their own data into the platform without any external
system: upload a CSV, it is parsed in memory and written straight to
CustomerData. Nothing touches the filesystem, which matters because the
container's disk does not survive a redeploy.
"""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_saas import User
from app.db.connector_models import (
    DataConnection, DataSource, SyncLog, CustomerData,
)
from app.services.auth_service import get_current_user
from app.utils.time import utcnow

router = APIRouter(prefix="/api/connectors/csv", tags=["connectors"])

MAX_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_ROWS = 50_000

# Column names commonly used to identify a customer, best match first.
ID_CANDIDATES = [
    "customer_id", "customerid", "id", "account_id", "accountid",
    "user_id", "userid", "email", "account", "customer", "company",
]


def _coerce(value: str) -> Any:
    """Turn a CSV string into a number/bool where it clearly is one."""
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        if "." in v or "e" in low:
            return float(v)
        return int(v)
    except ValueError:
        return v


def _numeric_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """Pull out the fields a model can actually train on."""
    out = {}
    for key, value in record.items():
        if isinstance(value, bool):
            out[key] = 1 if value else 0
        elif isinstance(value, (int, float)):
            out[key] = value
    return out


def _pick_id_column(headers: List[str]) -> str:
    lowered = {h.lower().replace(" ", "_"): h for h in headers}
    for candidate in ID_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    return headers[0]


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    name: str = Form(None),
    id_column: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV of customer records and load it into the platform."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization")

    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File is {len(raw) // 1024 // 1024}MB; the limit is {MAX_BYTES // 1024 // 1024}MB",
        )
    if not raw.strip():
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode file; save it as UTF-8")

    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames
    if not headers:
        raise HTTPException(status_code=400, detail="No header row found")
    headers = [h for h in headers if h and h.strip()]
    if not headers:
        raise HTTPException(status_code=400, detail="Header row is blank")

    key_column = id_column or _pick_id_column(headers)
    if key_column not in headers:
        raise HTTPException(
            status_code=400,
            detail=f"id_column '{key_column}' is not in the file. Columns: {', '.join(headers)}",
        )

    rows: List[Dict[str, Any]] = []
    for i, row in enumerate(reader):
        if i >= MAX_ROWS:
            raise HTTPException(
                status_code=413,
                detail=f"File has more than {MAX_ROWS:,} rows",
            )
        record = {h: _coerce(row.get(h)) for h in headers}
        if all(v is None for v in record.values()):
            continue  # skip blank lines
        rows.append(record)

    if not rows:
        raise HTTPException(status_code=400, detail="File has a header but no data rows")

    org_id = current_user.organization_id
    display_name = name or filename.rsplit(".", 1)[0]

    # Record it as a connection + source so it shows up alongside other connectors.
    connection = DataConnection(
        organization_id=org_id,
        name=display_name,
        connector_type="csv",
        description=f"Uploaded from {filename}",
        config={"storage_type": "upload", "filename": filename},
        credentials={},
        created_by_id=current_user.id,
        last_tested_at=utcnow(),
        last_tested_status="success",
    )
    db.add(connection)
    db.flush()

    sample = rows[0]
    source = DataSource(
        connection_id=connection.id,
        organization_id=org_id,
        name=display_name,
        source_path=filename,
        schema={
            "fields": [
                {
                    "name": h,
                    "type": type(sample.get(h)).__name__ if sample.get(h) is not None else "string",
                }
                for h in headers
            ]
        },
        primary_key=key_column,
        sync_type="full",
        record_count=len(rows),
    )
    db.add(source)
    db.flush()

    sync_log = SyncLog(
        data_source_id=source.id,
        organization_id=org_id,
        sync_type="manual",
        status="running",
        started_at=utcnow(),
    )
    db.add(sync_log)
    db.flush()

    inserted = 0
    skipped_no_id = 0
    seen = set()
    for record in rows:
        raw_key = record.get(key_column)
        if raw_key is None or str(raw_key).strip() == "":
            skipped_no_id += 1
            continue
        customer_id = str(raw_key)
        if customer_id in seen:
            continue  # last-write-wins would need an update; keep the first
        seen.add(customer_id)
        db.add(CustomerData(
            organization_id=org_id,
            data_source_id=source.id,
            customer_id=customer_id,
            customer_data=record,
            raw_fields=_numeric_fields(record),
        ))
        inserted += 1

    completed = utcnow()
    sync_log.status = "success"
    sync_log.completed_at = completed
    sync_log.duration_seconds = int((completed - sync_log.started_at).total_seconds())
    sync_log.records_fetched = len(rows)
    sync_log.records_inserted = inserted
    source.record_count = inserted

    db.commit()

    numeric_cols = sorted(_numeric_fields(sample).keys())
    return {
        "success": True,
        "data_source_id": source.id,
        "connection_id": connection.id,
        "name": display_name,
        "rows_in_file": len(rows),
        "customers_loaded": inserted,
        "skipped_missing_id": skipped_no_id,
        "duplicate_ids_skipped": len(rows) - inserted - skipped_no_id,
        "id_column": key_column,
        "columns": headers,
        "numeric_columns": numeric_cols,
        "message": f"Loaded {inserted} customers from {filename}",
    }


@router.get("/preview/{source_id}")
def preview_source(
    source_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Show the first rows loaded from an uploaded source."""
    source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.organization_id == current_user.organization_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    rows = db.query(CustomerData).filter(
        CustomerData.data_source_id == source_id,
    ).limit(min(limit, 100)).all()

    return {
        "name": source.name,
        "record_count": source.record_count,
        "id_column": source.primary_key,
        "rows": [r.customer_data for r in rows],
    }


@router.get("/customers")
def list_customers(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All customer records loaded for this organization."""
    q = db.query(CustomerData).filter(
        CustomerData.organization_id == current_user.organization_id,
    )
    total = q.count()
    rows = q.order_by(CustomerData.id.desc()).limit(min(limit, 200)).all()
    return {
        "total": total,
        "customers": [
            {
                "customer_id": r.customer_id,
                "data_source_id": r.data_source_id,
                "synced_at": r.synced_at,
                **(r.customer_data or {}),
            }
            for r in rows
        ],
    }
