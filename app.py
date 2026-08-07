"""IaC Security Framework Dashboard — Flask Application.

A read-only visualization layer for security scan data stored in AWS S3.
This application does not modify any data, recalculate scores, or trigger pipeline actions.
"""

import logging
from flask import Flask, render_template
from config import Config
from services.s3_service import S3Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    """Application factory for the IaC Security Framework Dashboard."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize S3 Service (read-only)
    s3_service = S3Service(
        bucket=Config.EVIDENCE_BUCKET,
        region=Config.AWS_REGION,
        profile=Config.AWS_PROFILE,
    )
    app.config["S3_SERVICE"] = s3_service

    # Register Blueprints
    from routes.dashboard import dashboard_bp
    from routes.scans import scans_bp
    from routes.findings import findings_bp
    from routes.evidence import evidence_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(findings_bp)
    app.register_blueprint(evidence_bp)

    # Register template utilities
    app.jinja_env.globals.update(
        normalize_severity=S3Service.normalize_severity,
        normalize_resource=S3Service.normalize_resource_name,
        safe_value=S3Service.safe_value,
    )

    # ── Error handlers ─────────────────────────────────────────────

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "error.html",
            error_title="Page Not Found",
            error_message="The requested page could not be found.",
            error_code=404,
        ), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template(
            "error.html",
            error_title="Internal Server Error",
            error_message="An unexpected error occurred. Please try again.",
            error_code=500,
        ), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "error.html",
            error_title="Access Denied",
            error_message="You do not have permission to access this resource.",
            error_code=403,
        ), 403

    return app


# Create the application instance
app = create_app()