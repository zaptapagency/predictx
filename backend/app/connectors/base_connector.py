"""
Base Connector Class
All connectors inherit from this
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class BaseConnector(ABC):
    """
    Abstract base class for all data connectors
    """

    def __init__(self, connection_config: Dict[str, Any], credentials: Dict[str, Any]):
        """
        Initialize connector with config and credentials

        Args:
            connection_config: Connector-specific configuration
            credentials: API keys, tokens, passwords (should be encrypted at rest)
        """
        self.config = connection_config
        self.credentials = credentials
        self.last_error = None

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if connection is valid

        Returns:
            True if connection works, False otherwise
        """
        pass

    @abstractmethod
    def get_available_tables(self) -> List[Dict[str, Any]]:
        """
        Get list of available tables/objects

        Returns:
            List of {name, path, record_count, last_modified}
        """
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema for a specific table

        Args:
            table_name: Name of table to inspect

        Returns:
            Schema dict: {field_name: {type, nullable, length}}
        """
        pass

    @abstractmethod
    def fetch_data(
        self,
        table_name: str,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        incremental_field: Optional[str] = None,
        incremental_value: Optional[Any] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Fetch data from table

        Args:
            table_name: Table to fetch from
            fields: Specific fields to fetch (all if None)
            filters: Optional filters {field: value}
            limit: Max records to fetch
            incremental_field: Field for incremental sync (e.g., updated_at)
            incremental_value: Only fetch records where incremental_field > this

        Returns:
            Tuple of (records, total_count)
        """
        pass

    def parse_schema_field(self, field_type: str) -> str:
        """
        Convert connector's field type to standard type
        """
        type_map = {
            'string': 'string', 'text': 'string', 'varchar': 'string',
            'integer': 'number', 'int': 'number', 'bigint': 'number',
            'float': 'number', 'decimal': 'number', 'double': 'number',
            'boolean': 'boolean', 'bool': 'boolean',
            'datetime': 'datetime', 'timestamp': 'datetime', 'date': 'date',
            'json': 'json', 'object': 'json',
        }
        return type_map.get(field_type.lower(), 'string')

    def handle_error(self, error: Exception) -> None:
        """Log error for debugging"""
        self.last_error = str(error)
        print(f"Connector error: {error}")
