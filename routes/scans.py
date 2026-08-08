"""Scan routes — scan history and scan details pages."""

from flask import Blueprint, render_template, current_app, abort

scans_bp = Blueprint("scans", __name__)


@scans_bp.route("/scans")
def scan_history():
    """Scan history page listing all available scans."""
    s3 = current_app.config["S3_SERVICE"]

    scan_ids = s3.list_scan_ids()
    scans = []

    for scan_id in scan_ids:
        summary = s3.get_scan_summary(scan_id)
        if summary:
            scans.append(summary)

    return render_template("scans.html", scans=scans)


@scans_bp.route("/scans/<scan_id>")
def scan_details(scan_id):
    """Scan details page — central investigation view for a single scan."""
    s3 = current_app.config["S3_SERVICE"]

    # Validate scan_id format
    if not _is_valid_scan_id(scan_id):
        abort(404)

    summary = s3.get_scan_summary(scan_id)
    if not summary:
        return render_template(
            "error.html",
            error_title="Scan Not Found",
            error_message=f"No scan data found for ID: {scan_id}",
            error_code=404,
        ), 404

    # Calculate Score Delta
    pre = summary.get("pre_deployment", {})
    runtime = summary.get("runtime", {})
    
    pre_score = pre.get("risk_score")
    post_score = runtime.get("risk_score")
    
    delta = None
    direction = None
    if isinstance(pre_score, (int, float)) and isinstance(post_score, (int, float)):
        delta = post_score - pre_score
        if delta > 0:
            direction = "IMPROVED"
        elif delta < 0:
            direction = "DEGRADED"
        else:
            direction = "UNCHANGED"
            
    summary["_delta"] = delta
    summary["_direction"] = direction

    # Get findings and separate them
    findings_data = s3.get_findings(scan_id)
    all_findings = findings_data.get("findings", []) if findings_data else []

    pre_findings = []
    post_findings = []
    
    # Severity counts and source counts for charts
    pre_severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    post_severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    pre_source_counts = {"CHECKOV": 0, "REGO/CONFTEST": 0, "OTHER": 0}
    
    for f in all_findings:
        f["_normalized_severity"] = s3.normalize_severity(f.get("severity"))
        f["_normalized_resource"] = s3.normalize_resource_name(f.get("resource_name"))
        f["_finding_key"] = f.get("finding_record_key") or s3.generate_finding_key(f)
        
        phase = f.get("phase", "").upper()
        severity = f["_normalized_severity"]
        scanner = f.get("scanner", "").upper()
        
        # Categorize by phase
        if phase in ("PRE_DEPLOYMENT", "STATIC", "CODE", "PLAN"):
            pre_findings.append(f)
            if severity in pre_severity_counts:
                pre_severity_counts[severity] += 1
            else:
                pre_severity_counts["UNKNOWN"] += 1
                
            # Count sources for pre-deployment
            if "CHECKOV" in scanner:
                pre_source_counts["CHECKOV"] += 1
            elif "REGO" in scanner or "CONFTEST" in scanner or "POLICY" in scanner:
                pre_source_counts["REGO/CONFTEST"] += 1
            else:
                pre_source_counts["OTHER"] += 1
        else:
            # Everything else (RUNTIME, POST_DEPLOYMENT, etc.) goes to post
            post_findings.append(f)
            if severity in post_severity_counts:
                post_severity_counts[severity] += 1
            else:
                post_severity_counts["UNKNOWN"] += 1

    chart_data = {
        "pre_severity_counts": pre_severity_counts,
        "post_severity_counts": post_severity_counts,
        "pre_source_counts": pre_source_counts,
        "has_pre": len(pre_findings) > 0,
        "has_post": len(post_findings) > 0,
    }

    # Pipeline lifecycle stages
    pipeline_stages = _build_pipeline_stages(summary)

    return render_template(
        "scan_details.html",
        scan=summary,
        scan_id=scan_id,
        pre_findings=pre_findings,
        post_findings=post_findings,
        chart_data=chart_data,
        pipeline_stages=pipeline_stages,
    )



def _is_valid_scan_id(scan_id):
    """Validate scan ID format (alphanumeric with hyphens)."""
    import re
    return bool(re.match(r"^[A-Za-z0-9\-]+$", scan_id))


def _build_pipeline_stages(summary):
    """Build pipeline lifecycle stages from scan summary data.

    Returns:
        list[dict]: Each with 'name', 'status', 'icon'.
    """
    pre = summary.get("pre_deployment", {})
    deployment = summary.get("deployment", {})
    runtime = summary.get("runtime", {})
    cleanup = summary.get("cleanup", {})
    scan_status = summary.get("scan_status", "UNKNOWN")

    # Determine stage states based on exported data
    stages = []

    # Repository Acquisition
    repo = summary.get("repository", {})
    repo_status = "COMPLETED" if repo.get("name") not in (None, "NOT_AVAILABLE") else "NOT_AVAILABLE"
    stages.append({"name": "Repository Acquisition", "status": repo_status})

    # Terraform Validation — infer from whether pre-deployment data exists
    tf_valid = "COMPLETED" if pre.get("total_findings") is not None else "NOT_AVAILABLE"
    stages.append({"name": "Terraform Validation", "status": tf_valid})

    # Checkov
    checkov_count = pre.get("checkov_finding_count")
    checkov_status = "COMPLETED" if checkov_count is not None else "NOT_AVAILABLE"
    stages.append({"name": "Checkov Analysis", "status": checkov_status})

    # Policy Validation
    policy_count = pre.get("policy_finding_count")
    policy_status = "COMPLETED" if policy_count is not None else "NOT_AVAILABLE"
    stages.append({"name": "Policy Validation", "status": policy_status})

    # Finding Enrichment
    enrichment_status = "COMPLETED" if pre.get("total_findings") is not None else "NOT_AVAILABLE"
    stages.append({"name": "Finding Enrichment", "status": enrichment_status})

    # Pre-Deployment Risk
    pre_score = pre.get("risk_score")
    pre_risk_status = "COMPLETED" if isinstance(pre_score, (int, float)) else "NOT_AVAILABLE"
    stages.append({"name": "Pre-Deployment Risk Scoring", "status": pre_risk_status})

    # Deployment Authorization
    auth = deployment.get("authorization_decision", "NOT_AVAILABLE")
    if auth in (None, "NOT_AVAILABLE"):
        auth_status = "NOT_AVAILABLE"
    else:
        auth_status = "COMPLETED"
    stages.append({"name": "Deployment Authorization", "status": auth_status})

    # Terraform Deployment
    deploy_status_val = deployment.get("status", "NOT_AVAILABLE")
    if deploy_status_val in (None, "NOT_AVAILABLE"):
        deploy_stage = "NOT_AVAILABLE"
    elif deploy_status_val == "BLOCKED":
        deploy_stage = "BLOCKED"
    elif deploy_status_val in ("SUCCESS", "COMPLETED"):
        deploy_stage = "COMPLETED"
    else:
        deploy_stage = deploy_status_val
    stages.append({"name": "Terraform Deployment", "status": deploy_stage})

    # Runtime Resource Discovery
    runtime_count = runtime.get("finding_count")
    runtime_disc_status = "COMPLETED" if runtime_count is not None else "NOT_AVAILABLE"
    stages.append({"name": "Runtime Resource Discovery", "status": runtime_disc_status})

    # Prowler Analysis
    prowler_status = "COMPLETED" if runtime_count is not None and runtime_count >= 0 else "NOT_AVAILABLE"
    stages.append({"name": "Prowler Analysis", "status": prowler_status})

    # Post-Deployment Risk
    post_score = runtime.get("risk_score")
    post_risk_status = "COMPLETED" if isinstance(post_score, (int, float)) else "NOT_AVAILABLE"
    stages.append({"name": "Post-Deployment Risk Scoring", "status": post_risk_status})

    # Security Review
    decision = summary.get("final_decision", {}).get("decision", "NOT_AVAILABLE")
    review_status = "COMPLETED" if decision not in (None, "NOT_AVAILABLE") else "NOT_AVAILABLE"
    stages.append({"name": "Security Review", "status": review_status})

    # Terraform Destroy
    destroy = cleanup.get("destroy_status", "NOT_EXECUTED")
    stages.append({"name": "Terraform Destroy", "status": destroy})

    # Cleanup Verification
    verify = cleanup.get("verification_status", "NOT_EXECUTED")
    stages.append({"name": "Cleanup Verification", "status": verify})

    return stages
