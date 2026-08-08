"""Dashboard route — main overview page."""

from flask import Blueprint, render_template, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Main dashboard page listing scans and high-level KPIs."""
    s3 = current_app.config["S3_SERVICE"]

    scan_ids = s3.list_scan_ids()
    scans = []
    
    # Global KPIs
    total_findings = 0
    critical_findings = 0
    high_findings = 0
    review_required = 0
    critical_risk_scans = 0

    for scan_id in scan_ids:
        summary = s3.get_scan_summary(scan_id)
        if not summary:
            continue
            
        # Add basic info to scan dict
        pre = summary.get("pre_deployment", {})
        runtime = summary.get("runtime", {})
        decision_info = summary.get("final_decision", {})
        cleanup = summary.get("cleanup", {})
        
        # Calculate Delta
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
                
        # Append derived fields for the template
        summary["_delta"] = delta
        summary["_direction"] = direction
        
        scans.append(summary)

        # Aggregate KPIs
        total_findings += pre.get("total_findings", 0) + runtime.get("finding_count", 0)
        critical_findings += pre.get("critical_count", 0) + runtime.get("critical_count", 0)
        high_findings += pre.get("high_count", 0) + runtime.get("high_count", 0)
        review_required += pre.get("review_required_finding_count", 0)
        
        if pre.get("risk_band", "") in ("CRITICAL_RISK", "HIGH_RISK"):
            critical_risk_scans += 1

    return render_template(
        "dashboard.html",
        scans=scans,
        total_scans=len(scans),
        critical_risk_scans=critical_risk_scans,
        total_findings=total_findings,
        critical_findings=critical_findings,
        high_findings=high_findings,
        review_required=review_required,
    )
