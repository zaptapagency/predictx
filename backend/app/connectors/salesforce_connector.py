"""
Salesforce Connector
Connect to Salesforce via OAuth + REST API
"""

from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
from .base_connector import BaseConnector


class SalesforceConnector(BaseConnector):
    """
    Salesforce CRM connector
    Supports Account, Contact, Opportunity, etc.
    """

    def __init__(self, connection_config: Dict[str, Any], credentials: Dict[str, Any]):
        super().__init__(connection_config, credentials)
        self.instance_url = connection_config.get("instance_url")
        self.api_version = connection_config.get("api_version", "v60.0")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")

    def test_connection(self) -> bool:
        """Test Salesforce connection"""
        try:
            response = requests.get(
                f"{self.instance_url}/services/data/",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            self.handle_error(e)
            return False

    def _refresh_access_token(self) -> None:
        """Refresh OAuth token if expired"""
        try:
            response = requests.post(
                f"{self.instance_url}/services/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.credentials.get("client_id"),
                    "client_secret": self.credentials.get("client_secret"),
                    "refresh_token": self.refresh_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.credentials["access_token"] = self.access_token
        except Exception as e:
            self.handle_error(e)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_available_tables(self) -> List[Dict[str, Any]]:
        """Get available Salesforce objects (Account, Contact, Opportunity, etc.)"""
        try:
            response = requests.get(
                f"{self.instance_url}/services/data/{self.api_version}/sobjects/",
                headers=self._get_headers()
            )
            data = response.json()

            tables = []
            for obj in data.get("sobjects", []):
                if obj.get("queryable"):
                    tables.append({
                        "name": obj["name"],
                        "path": f"salesforce.{obj['name']}",
                        "label": obj.get("label", obj["name"]),
                        "record_count": None  # SF doesn't expose this easily
                    })
            return tables
        except Exception as e:
            self.handle_error(e)
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema for Salesforce object"""
        try:
            response = requests.get(
                f"{self.instance_url}/services/data/{self.api_version}/sobjects/{table_name}/describe/",
                headers=self._get_headers()
            )
            data = response.json()

            schema = {}
            for field in data.get("fields", []):
                schema[field["name"]] = {
                    "type": self.parse_schema_field(field["type"]),
                    "label": field.get("label", field["name"]),
                    "nullable": field.get("nillable", True),
                    "length": field.get("length")
                }
            return schema
        except Exception as e:
            self.handle_error(e)
            return {}

    def fetch_data(
        self,
        table_name: str,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        incremental_field: Optional[str] = None,
        incremental_value: Optional[Any] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """Fetch data from Salesforce using SOQL"""
        try:
            # Build SOQL query
            if fields is None:
                fields = ["Id", "Name", "CreatedDate", "LastModifiedDate"]

            select_clause = ", ".join(fields)
            query = f"SELECT {select_clause} FROM {table_name}"

            # Add incremental filter
            if incremental_field and incremental_value:
                query += f" WHERE {incremental_field} > {incremental_value}"
            elif filters:
                where_parts = []
                for field, value in filters.items():
                    if isinstance(value, str):
                        where_parts.append(f"{field} = '{value}'")
                    else:
                        where_parts.append(f"{field} = {value}")
                query += " WHERE " + " AND ".join(where_parts)

            # Add limit
            if limit:
                query += f" LIMIT {limit}"

            # Execute query
            response = requests.get(
                f"{self.instance_url}/services/data/{self.api_version}/query/",
                params={"q": query},
                headers=self._get_headers()
            )

            data = response.json()
            records = []

            # Flatten Salesforce records
            for record in data.get("records", []):
                flat_record = {}
                for key, value in record.items():
                    if key != "attributes":
                        flat_record[key] = value
                records.append(flat_record)

            return records, data.get("totalSize", len(records))

        except Exception as e:
            self.handle_error(e)
            return [], 0
