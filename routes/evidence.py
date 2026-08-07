"""Evidence routes — evidence manifest and raw evidence viewer."""

import hashlib
import json

from flask import Blueprint, render_template, current_app

evidence_bp = Blueprint("evidence", __name__)

# Maximum size in bytes to render inline (500KB)
MAX_INLINE_SIZE = 512_000


@evidence_bp.route("/scans/<scan_id>/evidence")
def evidence_manifest(scan_id):
    """Evidence manifest page listing all artifacts for a scan."""
    s3 = current_app.config["S3_SERVICE"]

    manifest = s3.get_evidence_manifest(scan_id)
    if not manifest:
        return render_template(
            "error.html",
            error_title="Evidence Manifest Not Found",
            error_message=f"No evidence manifest found for scan: {scan_id}",
            error_code=404,
        ), 404

    artifacts = manifest.get("artifacts", [])
    generated_at = manifest.get("generated_at", "Unknown")

    # Add human-readable size
    for artifact in artifacts:
        size = artifact.get("size_bytes", 0)
        artifact["_human_size"] = _format_bytes(size)
        # Determine category from type
        artifact["_category"] = artifact.get("type", "UNKNOWN")

    return render_template(
        "evidence.html",
        scan_id=scan_id,
        artifacts=artifacts,
        generated_at=generated_at,
    )


@evidence_bp.route("/scans/<scan_id>/evidence/<path:artifact_key>")
def raw_evidence_viewer(scan_id, artifact_key):
    """Raw evidence viewer with SHA-256 integrity verification."""
    s3 = current_app.config["S3_SERVICE"]

    # Get the evidence manifest first for SHA-256 comparison
    manifest = s3.get_evidence_manifest(scan_id)
    expected_hash = None
    artifact_meta = None

    if manifest:
        for artifact in manifest.get("artifacts", []):
            if artifact.get("s3_key") == artifact_key:
                expected_hash = artifact.get("sha256")
                artifact_meta = artifact
                break

    # Fetch the raw evidence
    raw_bytes, content_type = s3.get_raw_evidence(artifact_key)

    if raw_bytes is None:
        return render_template(
            "error.html",
            error_title="Evidence Not Found",
            error_message=f"Evidence artifact not found: {artifact_key}",
            error_code=404,
        ), 404

    # Calculate SHA-256 hash
    computed_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Determine verification status
    if expected_hash:
        hash_verified = computed_hash.lower() == expected_hash.lower()
        verification_status = "VERIFIED" if hash_verified else "HASH_MISMATCH"
    else:
        hash_verified = None
        verification_status = "NO_MANIFEST_HASH"

    # Try to parse as JSON for pretty-printing
    content = None
    is_json = False
    is_truncated = False
    total_size = len(raw_bytes)

    try:
        if total_size > MAX_INLINE_SIZE:
            # Truncate for display but note the full size
            decoded = raw_bytes[:MAX_INLINE_SIZE].decode("utf-8", errors="replace")
            is_truncated = True
        else:
            decoded = raw_bytes.decode("utf-8", errors="replace")

        # Try JSON pretty-print
        try:
            parsed_json = json.loads(raw_bytes)
            content = json.dumps(parsed_json, indent=2)
            is_json = True
            if len(content) > MAX_INLINE_SIZE:
                content = content[:MAX_INLINE_SIZE]
                is_truncated = True
        except (json.JSONDecodeError, ValueError):
            content = decoded
    except Exception:
        content = f"[Binary content — {total_size} bytes]"

    return render_template(
        "raw_evidence.html",
        scan_id=scan_id,
        artifact_key=artifact_key,
        artifact_meta=artifact_meta,
        content=content,
        is_json=is_json,
        is_truncated=is_truncated,
        total_size=total_size,
        computed_hash=computed_hash,
        expected_hash=expected_hash,
        verification_status=verification_status,
        human_size=_format_bytes(total_size),
    )


def _format_bytes(size_bytes):
    """Format bytes to human-readable string."""
    if not isinstance(size_bytes, (int, float)):
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
