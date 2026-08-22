"""
CSV Connector
Upload and sync CSV files
"""

from typing import List, Dict, Any, Optional
import csv
import io
from .base_connector import BaseConnector


class CSVConnector(BaseConnector):
    """
    CSV file connector
    Supports one-time uploads and recurring syncs from S3/GCS
    """

    def __init__(self, connection_config: Dict[str, Any], credentials: Dict[str, Any]):
        super().__init__(connection_config, credentials)
        self.file_path = connection_config.get("file_path")
        self.storage_type = connection_config.get("storage_type", "local")  # local, s3, gcs
        self.delimiter = connection_config.get("delimiter", ",")
        self.encoding = connection_config.get("encoding", "utf-8")

    def test_connection(self) -> bool:
        """Test CSV file is accessible"""
        try:
            self._read_csv_file(limit=1)
            return True
        except Exception as e:
            self.handle_error(e)
            return False

    def _read_csv_file(self, limit: Optional[int] = None) -> tuple[List[Dict], int]:
        """Read CSV file and return records"""
        try:
            records = []
            total_count = 0

            if self.storage_type == "local":
                with open(self.file_path, 'r', encoding=self.encoding) as f:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    for i, row in enumerate(reader):
                        if limit and i >= limit:
                            break
                        # Convert string values to appropriate types
                        record = self._convert_types(row)
                        records.append(record)
                        total_count += 1

            elif self.storage_type == "s3":
                import boto3
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=self.credentials.get("aws_access_key_id"),
                    aws_secret_access_key=self.credentials.get("aws_secret_access_key")
                )
                bucket = self.config.get("s3_bucket")
                key = self.file_path

                response = s3.get_object(Bucket=bucket, Key=key)
                body = response['Body'].read().decode(self.encoding)

                reader = csv.DictReader(io.StringIO(body), delimiter=self.delimiter)
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    record = self._convert_types(row)
                    records.append(record)
                    total_count += 1

            return records, total_count

        except Exception as e:
            self.handle_error(e)
            return [], 0

    def _convert_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Attempt to convert string values to appropriate types"""
        converted = {}
        for key, value in row.items():
            if value is None or value == "":
                converted[key] = None
            elif value.lower() in ["true", "false"]:
                converted[key] = value.lower() == "true"
            elif value.replace(".", "", 1).isdigit():
                try:
                    if "." in value:
                        converted[key] = float(value)
                    else:
                        converted[key] = int(value)
                except ValueError:
                    converted[key] = value
            else:
                converted[key] = value
        return converted

    def get_available_tables(self) -> List[Dict[str, Any]]:
        """CSV has only one table - the file itself"""
        try:
            _, count = self._read_csv_file()
            return [{
                "name": self.file_path.split("/")[-1].replace(".csv", ""),
                "path": f"csv.{self.file_path}",
                "record_count": count
            }]
        except Exception as e:
            self.handle_error(e)
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Infer schema from CSV header row and sample data"""
        try:
            records, _ = self._read_csv_file(limit=100)

            if not records:
                return {}

            schema = {}
            sample_record = records[0]

            for field, value in sample_record.items():
                # Infer type from sample
                if isinstance(value, bool):
                    field_type = "boolean"
                elif isinstance(value, int):
                    field_type = "number"
                elif isinstance(value, float):
                    field_type = "number"
                else:
                    field_type = "string"

                schema[field] = {
                    "type": field_type,
                    "nullable": True,
                    "length": None
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
        """Fetch records from CSV"""
        try:
            records, total_count = self._read_csv_file()

            # Filter by specific fields
            if fields:
                records = [
                    {k: v for k, v in record.items() if k in fields}
                    for record in records
                ]

            # Apply filters
            if filters:
                filtered = []
                for record in records:
                    match = True
                    for field, value in filters.items():
                        if record.get(field) != value:
                            match = False
                            break
                    if match:
                        filtered.append(record)
                records = filtered

            # Incremental sync
            if incremental_field and incremental_value:
                records = [
                    r for r in records
                    if r.get(incremental_field) and r.get(incremental_field) > incremental_value
                ]

            # Apply limit
            if limit:
                records = records[:limit]

            return records, len(records)

        except Exception as e:
            self.handle_error(e)
            return [], 0
