"""Central application configuration for the IaC Security Framework Dashboard."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Flask application configuration loaded from environment variables."""

    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_PROFILE = os.getenv("AWS_PROFILE", "iac-dashboard")
    EVIDENCE_BUCKET = os.getenv(
        "EVIDENCE_BUCKET",
        "iac-security-framework-evidence-172201861173-us-east-1",
    )

    # Flask Configuration
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
