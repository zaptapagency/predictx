"""
Data Connector Models
Manage connections to customer data sources
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base
from app.services.crypto import EncryptedJSON
from app.utils.time import utcnow


class ConnectorType(str, enum.Enum):
    SALESFORCE = "salesforce"
    SEGMENT = "segment"
    MIXPANEL = "mixpanel"
    CSV = "csv"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    WEBHOOK = "webhook"
    API = "api"


class DataConnection(Base):
    """
    Active connection to a data source
    """
    __tablename__ = "data_connections"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Connection metadata
    name = Column(String(255), nullable=False)  # "Production Salesforce"
    connector_type = Column(String(50), nullable=False, index=True)  # salesforce, csv, etc
    description = Column(Text, nullable=True)

    # Connection config (encrypted in production)
    config = Column(JSON, nullable=False)  # {
    #   "instance_url": "https://xxx.salesforce.com",
    #   "client_id": "...",
    #   "refresh_token": "...",
    #   etc
    # }

    # OAuth tokens / passwords. Encrypted at rest by EncryptedJSON; reads still
    # yield a plain dict.
    credentials = Column(EncryptedJSON, nullable=False)

    # Connection status
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    last_tested_status = Column(String(50), nullable=True)  # success, failed
    test_error = Column(Text, nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    organization = relationship("Organization")
    created_by = relationship("User")

    def __repr__(self):
        return f"<DataConnection {self.name} ({self.connector_type})>"


class DataSource(Base):
    """
    A specific table/dataset within a connection
    Example: Salesforce.Account, Snowflake.public.customers
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("data_connections.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Source metadata
    name = Column(String(255), nullable=False)  # "Account"
    source_path = Column(String(255), nullable=False)  # Full path in source system
    description = Column(Text, nullable=True)

    # Schema info
    schema = Column(JSON, nullable=False)  # {
    #   "Account_Id": {"type": "string", "key": true},
    #   "Account_Name": {"type": "string"},
    #   "Annual_Revenue": {"type": "float"},
    #   "Industry": {"type": "string"},
    #   etc
    # }

    # Sync config
    primary_key = Column(String(255), nullable=False)  # Which field uniquely identifies records
    sync_type = Column(String(50), default="incremental")  # full or incremental

    # For incremental syncs
    incremental_field = Column(String(255), nullable=True)  # Field to track changes (updated_at, etc)
    last_synced_value = Column(String(255), nullable=True)  # Last value of incremental field

    # Status
    is_active = Column(Boolean, default=True)
    record_count = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    connection = relationship("DataConnection")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<DataSource {self.name}>"


class SyncLog(Base):
    """
    Log of data sync operations
    """
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Sync operation
    sync_type = Column(String(50), nullable=False)  # manual, scheduled, webhook
    status = Column(String(50), nullable=False, index=True)  # running, success, failed

    # Results
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Performance
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Relationships
    data_source = relationship("DataSource")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<SyncLog {self.data_source_id} - {self.status}>"


class CustomerData(Base):
    """
    Raw customer data from connectors
    Denormalized table for fast access
    """
    __tablename__ = "customer_data"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)

    # Data
    customer_id = Column(String(255), nullable=False, index=True)  # External ID
    customer_data = Column(JSON, nullable=False)  # Full record

    # Raw fields for predictions
    raw_fields = Column(JSON, nullable=False)  # Extracted numeric/categorical fields

    # Metadata
    synced_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    organization = relationship("Organization")
    data_source = relationship("DataSource")

    def __repr__(self):
        return f"<CustomerData org={self.organization_id} customer={self.customer_id}>"


class ConnectorCredential(Base):
    """
    Encrypted storage for API keys, tokens, passwords
    """
    __tablename__ = "connector_credentials"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("data_connections.id"), nullable=False, unique=True)

    # Encrypted values (decrypt on use)
    encrypted_data = Column(Text, nullable=False)  # Encrypted JSON
    encryption_version = Column(Integer, default=1)

    # Rotation tracking
    created_at = Column(DateTime, default=utcnow)
    rotated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # For tokens that expire

    # Relationships
    connection = relationship("DataConnection")

    def __repr__(self):
        return f"<ConnectorCredential connection={self.connection_id}>"


class FieldMapping(Base):
    """
    Map source fields to ForecastX model fields
    """
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)

    # Mapping
    source_field = Column(String(255), nullable=False)  # "Annual_Revenue"
    target_field = Column(String(255), nullable=False)  # "annual_revenue"
    field_type = Column(String(50), nullable=False)  # string, number, boolean, datetime

    # Usage
    is_identifier = Column(Boolean, default=False)  # Is this the customer ID?
    is_feature = Column(Boolean, default=True)  # Use in predictions?
    is_target = Column(Boolean, default=False)  # Target variable (churn_flag)?

    # Transformation
    transformation = Column(String(255), nullable=True)  # null, lowercase, upper, round, etc

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    data_source = relationship("DataSource")

    def __repr__(self):
        return f"<FieldMapping {self.source_field} → {self.target_field}>"


class ConnectorStatus(Base):
    """
    Current status and health of connectors
    """
    __tablename__ = "connector_status"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("data_connections.id"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Health
    is_healthy = Column(Boolean, default=True)
    error_count_24h = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Sync tracking
    last_sync_time = Column(DateTime, nullable=True)
    last_successful_sync = Column(DateTime, nullable=True)
    days_since_sync = Column(Integer, nullable=True)

    # Performance
    avg_sync_duration_seconds = Column(Integer, nullable=True)
    total_records = Column(Integer, default=0)

    # Quota
    api_calls_used = Column(Integer, default=0)
    api_calls_limit = Column(Integer, nullable=True)
    quota_reset_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    connection = relationship("DataConnection")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<ConnectorStatus connection={self.connection_id}>"
