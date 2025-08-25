import argparse
from aws_security_scan.scanner import Scanner
from aws_security_scan.report import ReportGenerator
import boto3
import sys


def main():
    parser = argparse.ArgumentParser(description="AWS Security & Best Practices Reporting Tool")
    parser.add_argument('--profile', type=str, help='AWS CLI profile name', default=None)
    parser.add_argument('--output', type=str, help='Output HTML report file', default='reports/report.html')
    args = parser.parse_args()

    scanner = Scanner(profile=args.profile)
    findings, account_id = scanner.run_all_checks()

    report = ReportGenerator(findings, account_id)
    report.generate(args.output)
    print(f"Report generated: {args.output}")

if __name__ == "__main__":
    main()
