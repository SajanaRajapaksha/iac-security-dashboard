"""Dashboard route — main overview page."""

from flask import Blueprint, render_template, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Main dashboard page with KPI cards, recent scans, and charts."""
    s3 = current_app.config["S3_SERVICE"]

    scan_ids = s3.list_scan_ids()
    summaries = []
    total_findings = 0
    critical_findings = 0
    high_findings = 0
    review_required = 0
    pre_scores = []
    post_scores = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    scanner_counts = {}
    decision_counts = {}

    for scan_id in scan_ids:
        summary = s3.get_scan_summary(scan_id)
        if not summary:
            continue
        summaries.append(summary)

        # Aggregate pre-deployment stats
        pre = summary.get("pre_deployment", {})
        total_findings += pre.get("total_findings", 0)
        critical_findings += pre.get("critical_count", 0)
        high_findings += pre.get("high_count", 0)
        review_required += pre.get("review_required_finding_count", 0)

        severity_counts["CRITICAL"] += pre.get("critical_count", 0)
        severity_counts["HIGH"] += pre.get("high_count", 0)
        severity_counts["MEDIUM"] += pre.get("medium_count", 0)
        severity_counts["LOW"] += pre.get("low_count", 0)
        severity_counts["UNKNOWN"] += pre.get("unknown_count", 0)

        # Add runtime counts
        runtime = summary.get("runtime", {})
        total_findings += runtime.get("finding_count", 0)
        critical_findings += runtime.get("critical_count", 0)
        high_findings += runtime.get("high_count", 0)
        severity_counts["CRITICAL"] += runtime.get("critical_count", 0)
        severity_counts["HIGH"] += runtime.get("high_count", 0)
        severity_counts["MEDIUM"] += runtime.get("medium_count", 0)
        severity_counts["LOW"] += runtime.get("low_count", 0)
        severity_counts["UNKNOWN"] += runtime.get("unknown_count", 0)

        # Collect scores
        pre_score = pre.get("risk_score")
        if isinstance(pre_score, (int, float)):
            pre_scores.append(pre_score)

        post_score = runtime.get("risk_score")
        if isinstance(post_score, (int, float)):
            post_scores.append(post_score)

        # Scanner counts from pre-deployment
        checkov_count = pre.get("checkov_finding_count", 0)
        policy_count = pre.get("policy_finding_count", 0)
        if checkov_count:
            scanner_counts["Checkov"] = scanner_counts.get("Checkov", 0) + checkov_count
        if policy_count:
            scanner_counts["Conftest/Rego"] = scanner_counts.get("Conftest/Rego", 0) + policy_count

        runtime_count = runtime.get("finding_count", 0)
        if runtime_count:
            scanner_counts["Prowler"] = scanner_counts.get("Prowler", 0) + runtime_count

        # Decision distribution
        decision = summary.get("final_decision", {}).get("decision", "NOT_AVAILABLE")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    avg_pre = round(sum(pre_scores) / len(pre_scores), 1) if pre_scores else "N/A"
    avg_post = round(sum(post_scores) / len(post_scores), 1) if post_scores else "N/A"

    # Identify critical/high risk scans
    critical_risk_scans = sum(
        1 for s in summaries
        if s.get("pre_deployment", {}).get("risk_band", "") in ("CRITICAL_RISK", "HIGH_RISK")
    )

    # Build chart data
    chart_data = {
        "scan_labels": [s.get("scan_id", "Unknown") for s in summaries],
        "pre_scores": [
            s.get("pre_deployment", {}).get("risk_score", 0) for s in summaries
        ],
        "post_scores": [
            s.get("runtime", {}).get("risk_score", 0) for s in summaries
        ],
        "severity_counts": severity_counts,
        "scanner_counts": scanner_counts,
        "decision_counts": decision_counts,
    }

    return render_template(
        "dashboard.html",
        summaries=summaries,
        total_scans=len(summaries),
        critical_risk_scans=critical_risk_scans,
        avg_pre=avg_pre,
        avg_post=avg_post,
        total_findings=total_findings,
        critical_findings=critical_findings,
        high_findings=high_findings,
        review_required=review_required,
        chart_data=chart_data,
    )
