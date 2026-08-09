# IaC Security Framework - Dashboard UI

## Project Title and Purpose
**IaC Security Framework - Dashboard UI** is a read-only, dynamic visualization layer built to monitor and review Infrastructure as Code (IaC) security scans. The dashboard fetches and parses structured JSON data exported directly to an AWS S3 bucket by the upstream IaC Security Framework pipeline. 

Its primary purpose is to provide security engineers and developers with a centralized, intuitive interface to review Pre-Deployment and Post-Deployment risk scores, investigate critical findings, review AI-assisted enriched remediation guidance, and access raw evidence artifacts without interacting directly with the pipeline or AWS console.

---

## Software and Hardware Requirements
- **Operating System:** macOS, Linux, or Windows (WSL recommended)
- **Hardware:** Minimal requirements (2GB RAM, 1 CPU core)
- **Software:** 
  - Python 3.9 or higher
  - AWS CLI installed and configured
  - A modern web browser (Chrome, Firefox, Safari, Edge)

---

## Programming Languages, Libraries, and Frameworks Used
- **Backend:** Python 3, Flask, Boto3 (AWS SDK for Python)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Styling Framework:** Bootstrap 5
- **Data Visualization:** Chart.js
- **Templating:** Jinja2

---

## Installation Procedure

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SajanaRajapaksha/iac-security-dashboard.git
   cd iac-security-dashboard
   ```

2. **Create a Python Virtual Environment:**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the Virtual Environment:**
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```

---

## Dependency Installation
With the virtual environment activated, install the required Python dependencies:
```bash
pip install -r requirements.txt
```

---

## Dataset Preparation
This application does not require a traditional ML "dataset" to be prepared locally. Instead, the "dataset" comprises the structured output files exported by the IaC Security Framework pipeline.

Ensure the upstream pipeline has successfully exported data to the designated S3 bucket. The dashboard expects the following object structure in S3:
```text
s3://<BUCKET_NAME>/dashboard/<SCAN_ID>/scan-summary.json
s3://<BUCKET_NAME>/dashboard/<SCAN_ID>/findings.json
s3://<BUCKET_NAME>/dashboard/<SCAN_ID>/evidence-manifest.json
s3://<BUCKET_NAME>/raw/<SCAN_ID>/...
```

---

## Configuration Requirements

1. **AWS Configuration:**
   The dashboard requires AWS credentials to access the S3 bucket. If you have an AWS profile set up (e.g., via AWS SSO or IAM keys), ensure you are authenticated:
   ```bash
   aws configure --profile iac-dashboard
   # OR
   aws sso login --profile iac-dashboard
   ```

2. **Application Configuration:**
   Configuration variables can be adjusted in `config.py` (or overridden via environment variables if implemented).
   - `S3_BUCKET_NAME`: Name of the S3 bucket (e.g., `iac-security-framework-evidence-172201861173-us-east-1`).
   - `AWS_REGION`: The AWS region (default: `us-east-1`).
   - `AWS_PROFILE`: The local AWS CLI profile to use (default: `iac-dashboard`).

---

## Instructions for Running the System

To start the Flask development server, ensure your virtual environment is active and your AWS credentials are valid. 

Run the following command:
```bash
# If using the default 'iac-dashboard' profile:
flask run --port=5000

# If using a specific AWS profile (e.g., 'dashboard'):
AWS_PROFILE=dashboard flask run --port=5000
```

Once the server starts, open your web browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Instructions for Training or Evaluating Models
*Not Applicable.* The dashboard itself does not train or evaluate machine learning models. 

However, it natively supports visualizing **AI-Assisted Enriched Remediation** that is processed by the upstream IaC Security Framework (which leverages LLMs like OpenAI/Claude for contextual remediation). The dashboard dynamically parses the `finding.remediation.source` fields to distinguish between standard Prowler remediation and AI-generated guidance.

---

## Default User Credentials or Test Accounts
*Not Applicable.* This dashboard is designed to run locally on the user's machine as a development server (`localhost`). There is no built-in authentication layer or user management system within the Flask application itself. Security is handled entirely by AWS IAM permissions (the user must have `s3:GetObject` and `s3:ListBucket` permissions for the target bucket).

---

## Known Limitations
1. **Read-Only:** The dashboard is strictly a visualization layer. You cannot approve scans, trigger pipeline reruns, or modify findings directly from the UI.
2. **Synchronous S3 Fetching:** The dashboard fetches JSON files synchronously from S3 on page load. Navigating large datasets or experiencing slow network connections may result in minor page load delays.
3. **Data Dependency:** The dashboard's layout is tightly coupled with the specific JSON schema exported by the IaC Security Framework. If the upstream framework alters its export schema, the dashboard templates will require updates.

---

## External Services or API Keys Required
1. **AWS S3:** The system inherently relies on Amazon S3 to function.
2. **AWS Credentials:** You must have valid AWS credentials configured on the host machine to read from the target S3 bucket. No third-party API keys (like OpenAI or GitHub) are required by the dashboard, as all external integrations are handled upstream by the pipeline before the data reaches S3.
