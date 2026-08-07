"""S3 Service — sole module for AWS S3 communication.

All dashboard data retrieval from S3 goes through this service.
This module is strictly read-only: no put_object, delete_object, or any write operations.
"""

import ast
import json
import logging
import re

import boto3
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3Service:
    """Read-only S3 service for retrieving IaC Security Framework evidence."""

    def __init__(self, bucket, region, profile):
        """Initialize S3 client using the specified AWS profile.

        Args:
            bucket: S3 bucket name.
            region: AWS region.
            profile: AWS CLI profile name for credentials.
        """
        self.bucket = bucket
        self.region = region
        self.profile = profile
        self._client = None

    @property
    def client(self):
        """Lazily create and return S3 client."""
        if self._client is None:
            try:
                session = boto3.Session(
                    profile_name=self.profile, region_name=self.region
                )
                self._client = session.client("s3")
            except (BotoCoreError, NoCredentialsError) as e:
                logger.error("Failed to create S3 client: %s", e)
                raise
        return self._client

    # ── Discovery ──────────────────────────────────────────────────────

    def list_scan_ids(self):
        """List all available scan IDs under the dashboard/ prefix.

        Returns:
            list[str]: Scan IDs (e.g. ['SCAN-90dd65fc']), or empty list on error.
        """
        try:
            resp = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix="dashboard/", Delimiter="/"
            )
            scan_ids = []
            for prefix in resp.get("CommonPrefixes", []):
                # Extract scan ID from 'dashboard/SCAN-xxxx/'
                parts = prefix["Prefix"].strip("/").split("/")
                if len(parts) >= 2:
                    scan_ids.append(parts[1])
            return sorted(scan_ids, reverse=True)
        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to list scan IDs: %s", e)
            return []

    # ── Dashboard JSON retrieval ───────────────────────────────────────

    def get_scan_summary(self, scan_id):
        """Fetch scan-summary.json for a given scan.

        Args:
            scan_id: The scan identifier (e.g. 'SCAN-90dd65fc').

        Returns:
            dict or None: Parsed JSON, or None if not found / malformed.
        """
        key = f"dashboard/{scan_id}/scan-summary.json"
        return self.get_json_object(key)

    def get_findings(self, scan_id):
        """Fetch findings.json for a given scan.

        Args:
            scan_id: The scan identifier.

        Returns:
            dict or None: Parsed JSON, or None if not found / malformed.
        """
        key = f"dashboard/{scan_id}/findings.json"
        return self.get_json_object(key)

    def get_evidence_manifest(self, scan_id):
        """Fetch evidence-manifest.json for a given scan.

        Args:
            scan_id: The scan identifier.

        Returns:
            dict or None: Parsed JSON, or None if not found / malformed.
        """
        key = f"dashboard/{scan_id}/evidence-manifest.json"
        return self.get_json_object(key)

    # ── Generic object retrieval ───────────────────────────────────────

    def get_json_object(self, key):
        """Retrieve and parse a JSON object from S3.

        Args:
            key: The full S3 object key.

        Returns:
            dict or None: Parsed JSON, or None on error.
        """
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            body = resp["Body"].read()
            return json.loads(body)
        except self.client.exceptions.NoSuchKey:
            logger.warning("S3 object not found: %s", key)
            return None
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                logger.warning("S3 object not found: %s", key)
            elif error_code in ("AccessDenied", "403"):
                logger.error("Access denied for S3 object: %s", key)
            else:
                logger.error("S3 ClientError for %s: %s", key, e)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Malformed JSON in S3 object %s: %s", key, e)
            return None
        except (BotoCoreError, NoCredentialsError) as e:
            logger.error("AWS error retrieving %s: %s", key, e)
            return None

    def get_raw_evidence(self, key):
        """Retrieve raw evidence bytes from S3.

        Args:
            key: The full S3 object key.

        Returns:
            tuple: (bytes_content, content_type) or (None, None) on error.
        """
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            body = resp["Body"].read()
            content_type = resp.get("ContentType", "application/octet-stream")
            return body, content_type
        except self.client.exceptions.NoSuchKey:
            logger.warning("Raw evidence not found: %s", key)
            return None, None
        except ClientError as e:
            logger.error("S3 ClientError for raw evidence %s: %s", key, e)
            return None, None
        except (BotoCoreError, NoCredentialsError) as e:
            logger.error("AWS error retrieving raw evidence %s: %s", key, e)
            return None, None

    def object_exists(self, key):
        """Check if an S3 object exists.

        Args:
            key: The full S3 object key.

        Returns:
            bool: True if object exists, False otherwise.
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except (ClientError, BotoCoreError):
            return False

    def list_raw_evidence(self, scan_id):
        """List all objects under raw/<scan_id>/.

        Args:
            scan_id: The scan identifier.

        Returns:
            list[dict]: List of object metadata dicts with 'Key', 'Size', 'LastModified'.
        """
        try:
            prefix = f"raw/{scan_id}/"
            resp = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return resp.get("Contents", [])
        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to list raw evidence for %s: %s", scan_id, e)
            return []

    # ── Data normalization helpers ─────────────────────────────────────

    @staticmethod
    def normalize_severity(severity_value):
        """Normalize severity values, handling Prowler's string-encoded dict format.

        Prowler exports severity as: "{'ORIGINAL': 'MEDIUM', 'NORMALIZED': 'MEDIUM', 'SOURCE': '...'}"
        This safely extracts the NORMALIZED value.

        Args:
            severity_value: String severity or string-encoded dict.

        Returns:
            str: Normalized severity string (e.g. 'MEDIUM', 'HIGH').
        """
        if not severity_value:
            return "UNKNOWN"

        if isinstance(severity_value, dict):
            return severity_value.get("NORMALIZED", severity_value.get("ORIGINAL", "UNKNOWN"))

        severity_str = str(severity_value).strip()

        # Check if it looks like a string-encoded dict
        if severity_str.startswith("{") and severity_str.endswith("}"):
            try:
                parsed = ast.literal_eval(severity_str)
                if isinstance(parsed, dict):
                    return parsed.get("NORMALIZED", parsed.get("ORIGINAL", "UNKNOWN"))
            except (ValueError, SyntaxError):
                # Try regex fallback
                match = re.search(r"'NORMALIZED'\s*:\s*'(\w+)'", severity_str)
                if match:
                    return match.group(1)
                match = re.search(r"'ORIGINAL'\s*:\s*'(\w+)'", severity_str)
                if match:
                    return match.group(1)
                return "UNKNOWN"

        return severity_str.upper()

    @staticmethod
    def normalize_resource_name(resource_value):
        """Normalize resource_name which can be a string or dict (Prowler format).

        Args:
            resource_value: String resource name or dict with 'id', 'arn', 'name' etc.

        Returns:
            str: Human-readable resource identifier.
        """
        if not resource_value:
            return "Unknown"

        if isinstance(resource_value, dict):
            # Prefer ARN, then name, then id
            return (
                resource_value.get("arn")
                or resource_value.get("name")
                or resource_value.get("id")
                or "Unknown"
            )

        return str(resource_value)

    @staticmethod
    def safe_value(value, default="NOT_AVAILABLE"):
        """Return value if it's meaningful, otherwise return default.

        Treats None, 'NOT_AVAILABLE', 'N/A', 'UNKNOWN', and empty strings as missing.

        Args:
            value: The value to check.
            default: Default to return if value is missing.

        Returns:
            The original value or default.
        """
        if value is None:
            return default
        if isinstance(value, str) and value.strip() in ("", "NOT_AVAILABLE", "N/A"):
            return default
        return value
