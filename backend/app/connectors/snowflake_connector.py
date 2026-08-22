"""
Snowflake Connector
Connect to Snowflake data warehouse
"""

from typing import List, Dict, Any, Optional
import snowflake.connector
from .base_connector import BaseConnector


class SnowflakeConnector(BaseConnector):
    """
    Snowflake data warehouse connector
    """

    def __init__(self, connection_config: Dict[str, Any], credentials: Dict[str, Any]):
        super().__init__(connection_config, credentials)
        self.account = connection_config.get("account")
        self.warehouse = connection_config.get("warehouse")
        self.database = connection_config.get("database")
        self.schema = connection_config.get("schema", "PUBLIC")
        self.user = credentials.get("user")
        self.password = credentials.get("password")
        self.connection = None

    def _connect(self) -> bool:
        """Establish Snowflake connection"""
        try:
            self.connection = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            return True
        except Exception as e:
            self.handle_error(e)
            return False

    def test_connection(self) -> bool:
        """Test Snowflake connection"""
        try:
            if not self.connection:
                self._connect()

            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            self.handle_error(e)
            return False

    def get_available_tables(self) -> List[Dict[str, Any]]:
        """Get list of tables in Snowflake"""
        try:
            if not self.connection:
                self._connect()

            cursor = self.connection.cursor()
            query = f"""
                SELECT TABLE_NAME, TABLE_SCHEMA, ROW_COUNT
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{self.schema}'
                AND TABLE_TYPE = 'BASE TABLE'
            """
            cursor.execute(query)

            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "name": row[0],
                    "path": f"{self.database}.{self.schema}.{row[0]}",
                    "record_count": row[2]
                })

            cursor.close()
            return tables

        except Exception as e:
            self.handle_error(e)
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema for Snowflake table"""
        try:
            if not self.connection:
                self._connect()

            cursor = self.connection.cursor()
            query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                AND TABLE_SCHEMA = '{self.schema}'
            """
            cursor.execute(query)

            schema = {}
            for row in cursor.fetchall():
                schema[row[0]] = {
                    "type": self.parse_schema_field(row[1]),
                    "nullable": row[2] == "YES",
                    "length": None
                }

            cursor.close()
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
        """Fetch data from Snowflake"""
        try:
            if not self.connection:
                self._connect()

            cursor = self.connection.cursor()

            # Build query
            if fields is None:
                select_clause = "*"
            else:
                select_clause = ", ".join(fields)

            query = f"SELECT {select_clause} FROM {table_name}"

            # Add filters
            where_parts = []
            if incremental_field and incremental_value:
                where_parts.append(f"{incremental_field} > '{incremental_value}'")
            if filters:
                for field, value in filters.items():
                    if isinstance(value, str):
                        where_parts.append(f"{field} = '{value}'")
                    else:
                        where_parts.append(f"{field} = {value}")

            if where_parts:
                query += " WHERE " + " AND ".join(where_parts)

            if limit:
                query += f" LIMIT {limit}"

            # Execute query
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            records = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

            # Get total count
            total_query = f"SELECT COUNT(*) FROM {table_name}"
            if where_parts:
                total_query += " WHERE " + " AND ".join(where_parts)
            cursor.execute(total_query)
            total_count = cursor.fetchone()[0]

            cursor.close()
            return records, total_count

        except Exception as e:
            self.handle_error(e)
            return [], 0
