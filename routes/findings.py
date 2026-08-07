"""Findings routes — findings list and finding detail pages."""

from urllib.parse import quote, unquote
from flask import Blueprint, render_template, current_app, abort

findings_bp = Blueprint("findings", __name__)


@findings_bp.route("/scans/<scan_id>/findings")
def findings_list(scan_id):
    """Findings page for a specific scan with filters."""
    s3 = current_app.config["S3_SERVICE"]

    findings_data = s3.get_findings(scan_id)
    if not findings_data:
        return render_template(
            "error.html",
            error_title="Findings Not Found",
            error_message=f"No findings data found for scan: {scan_id}",
            error_code=404,
        ), 404

    findings = findings_data.get("findings", [])

    # Normalize all findings for display
    scanners = set()
    phases = set()
    categories = set()
    severities = set()

    for f in findings:
        f["_normalized_severity"] = s3.normalize_severity(f.get("severity"))
        f["_normalized_resource"] = s3.normalize_resource_name(f.get("resource_name"))
        f["_finding_key"] = quote(f.get("finding_id", ""), safe="")

        scanners.add(f.get("scanner", "unknown"))
        phases.add(f.get("phase", "UNKNOWN"))
        categories.add(f.get("security_category", "UNKNOWN"))
        severities.add(f["_normalized_severity"])

    return render_template(
        "findings.html",
        scan_id=scan_id,
        findings=findings,
        scanners=sorted(scanners),
        phases=sorted(phases),
        categories=sorted(categories),
        severities=sorted(severities),
    )


@findings_bp.route("/scans/<scan_id>/findings/<finding_key>")
def finding_details(scan_id, finding_key):
    """Finding detail page with full information and remediation."""
    s3 = current_app.config["S3_SERVICE"]

    findings_data = s3.get_findings(scan_id)
    if not findings_data:
        return render_template(
            "error.html",
            error_title="Findings Not Found",
            error_message=f"No findings data found for scan: {scan_id}",
            error_code=404,
        ), 404

    # Find the specific finding by its ID
    decoded_key = unquote(finding_key)
    finding = None
    for f in findings_data.get("findings", []):
        if f.get("finding_id") == decoded_key:
            finding = f
            break

    if not finding:
        return render_template(
            "error.html",
            error_title="Finding Not Found",
            error_message=f"Finding '{decoded_key}' not found in scan {scan_id}",
            error_code=404,
        ), 404

    # Normalize for display
    finding["_normalized_severity"] = s3.normalize_severity(finding.get("severity"))
    finding["_normalized_resource"] = s3.normalize_resource_name(
        finding.get("resource_name")
    )
    finding["_normalized_full_address"] = s3.normalize_resource_name(
        finding.get("full_address")
    )

    return render_template(
        "finding_details.html",
        scan_id=scan_id,
        finding=finding,
    )
