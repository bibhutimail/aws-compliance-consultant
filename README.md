# AWS Security & Best Practices Reporting Tool

A professional tool for AWS consultants to assess and report on AWS account security posture, following AWS Well-Architected and CIS Benchmarks.

## Features
- Scans major AWS services for security and compliance issues
- Classifies findings by risk (High/Medium/Low)
- Provides actionable recommendations
- Generates consultant-style HTML reports with charts
- Modular and extensible codebase

## Setup
1. Clone this repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Ensure your AWS credentials are configured (via AWS CLI, environment, or `--profile`).


## Usage
Run a scan and generate a report (using a specific AWS CLI profile):
```sh
python main.py --profile myawsprofile --output report.html
```

Or use the default profile:
```sh
python main.py --output report.html
```

### Why use --profile?
The `--profile` option lets you specify which AWS credentials and account to use for the scan. This is useful if you manage multiple AWS accounts or roles on your machine. By setting `--profile`, you ensure the tool scans the intended AWS environment and not your default account.

## Project Structure
- `aws_security_scan/` - Core modules (scanner, rules, report)
- `reports/` - Generated HTML reports
- `tests/` - Unit tests

## Sample Report
See `reports/sample_report.html` for an example output.

## Extending
Add new checks or services by extending modules in `aws_security_scan/`.

---
© 2025 AWS Security Consultant Tool
