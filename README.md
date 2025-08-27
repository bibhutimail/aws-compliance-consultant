
# AWS Security & Cost Reporting Tool

A professional tool for AWS consultants to assess and report on AWS account security posture and cost optimization, following AWS Well-Architected, CIS Benchmarks, and AWS Cost Explorer best practices.

## Features
- Scans major AWS services for security and compliance issues
- Classifies findings by risk (High/Medium/Low)
- Provides actionable recommendations
- Analyzes AWS cost data and generates cost optimization suggestions
- Generates a combined HTML report with tabs for Security and Cost analysis
- Visual charts for compliance, risk, cost breakdown, and savings
- Modular and extensible codebase

## Initial Setup
1. Clone this repository.
2. Create and activate a Python virtual environment (recommended):
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Ensure your AWS credentials are configured (via AWS CLI, environment, or `--profile`).

## Usage
Run a scan and generate a combined Security & Cost report (using a specific AWS CLI profile):
```sh
python main.py --profile myawsprofile --output reports/report.html
```

Or use the default profile:
```sh
python main.py --output reports/report.html
```

## Output
- The final report is generated as `reports/report.html`.
- The HTML file contains tabs for:
  - **Security Report**: Security posture, findings, recommendations, compliance charts
  - **Cost Report**: Cost breakdown, optimization recommendations, savings, cost charts

## Why use --profile?
The `--profile` option lets you specify which AWS credentials and account to use for the scan. This is useful if you manage multiple AWS accounts or roles on your machine. By setting `--profile`, you ensure the tool scans the intended AWS environment and not your default account.

## Project Structure
- `aws_security_scan/` - Core modules (scanner, rules, report)
- `reports/` - Cost report logic and generated HTML reports
- `tests/` - Unit tests

## Extending
Add new checks or services by extending modules in `aws_security_scan/` or cost logic in `reports/aws_cost_report.py`.

## Sample report
[View AWS Report](./reports/report.html)
---
© 2025 AWS Security & Cost Consultant Tool
