"""
Connector Manager
Factory and orchestrator for all connectors
"""

from typing import Dict, Any, Optional, List
from .base_connector import BaseConnector
from .salesforce_connector import SalesforceConnector
from .csv_connector import CSVConnector

# snowflake-connector-python is a heavy optional dependency; the Snowflake
# connector is only offered when the package is installed.
try:
    from .snowflake_connector import SnowflakeConnector
except ImportError:
    SnowflakeConnector = None


class ConnectorManager:
    """
    Manages connector lifecycle and operations
    """

    CONNECTOR_TYPES = {
        "salesforce": SalesforceConnector,
        "csv": CSVConnector,
        # "segment": SegmentConnector,  # TODO
        # "bigquery": BigQueryConnector,  # TODO
        # "redshift": RedshiftConnector,  # TODO
    }
    if SnowflakeConnector is not None:
        CONNECTOR_TYPES["snowflake"] = SnowflakeConnector

    @classmethod
    def create_connector(
        cls,
        connector_type: str,
        connection_config: Dict[str, Any],
        credentials: Dict[str, Any]
    ) -> Optional[BaseConnector]:
        """
        Factory method to create appropriate connector

        Args:
            connector_type: Type of connector (salesforce, csv, snowflake, etc)
            connection_config: Connector-specific configuration
            credentials: Authentication credentials

        Returns:
            Connector instance or None if type unknown
        """
        connector_class = cls.CONNECTOR_TYPES.get(connector_type.lower())
        if connector_class is None:
            raise ValueError(f"Unknown connector type: {connector_type}")

        return connector_class(connection_config, credentials)

    @classmethod
    def get_supported_types(cls) -> List[Dict[str, Any]]:
        """Get list of supported connector types with info"""
        return [
            {
                "type": "salesforce",
                "name": "Salesforce CRM",
                "description": "Connect to Salesforce account, contact, opportunity data",
                "auth_type": "oauth",
                "supported_sync_types": ["incremental", "full"]
            },
            {
                "type": "csv",
                "name": "CSV Upload",
                "description": "Upload CSV files from local or cloud storage",
                "auth_type": "none",
                "supported_sync_types": ["full", "incremental"]
            },
            {
                "type": "snowflake",
                "name": "Snowflake",
                "description": "Connect to Snowflake data warehouse",
                "auth_type": "basic",
                "supported_sync_types": ["incremental", "full"]
            },
            # {
            #     "type": "segment",
            #     "name": "Segment",
            #     "description": "Connect to Segment customer data platform",
            #     "auth_type": "api_key",
            #     "supported_sync_types": ["streaming"]
            # },
            # {
            #     "type": "bigquery",
            #     "name": "Google BigQuery",
            #     "description": "Connect to BigQuery tables",
            #     "auth_type": "service_account",
            #     "supported_sync_types": ["incremental", "full"]
            # },
        ]
