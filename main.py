import argparse
from aws_security_scan.scanner import Scanner
from aws_security_scan.report import ReportGenerator
import boto3
import sys
import importlib.util
import os

def main():
    parser = argparse.ArgumentParser(description="AWS Security & Best Practices Reporting Tool")
    parser.add_argument('--profile', type=str, help='AWS CLI profile name', default=None)
    parser.add_argument('--output', type=str, help='Output HTML report file', default='reports/report.html')
    args = parser.parse_args()

    scanner = Scanner(profile=args.profile)
    findings, account_id = scanner.run_all_checks()

    # Generate security report HTML fragment
    report = ReportGenerator(findings, account_id)
    security_html = report.generate_html_string()

    # Dynamically import cost report module from reports/
    cost_report_path = os.path.join(os.path.dirname(__file__), 'reports', 'aws_cost_report.py')
    spec = importlib.util.spec_from_file_location('aws_cost_report', cost_report_path)
    cost_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cost_mod)

    # Prepare session for cost report
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    today = cost_mod.datetime.utcnow().date()
    first = today.replace(day=1)
    last_month_end = first - cost_mod.timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    cost_data = cost_mod.get_cost_and_usage(str(last_month_start), str(last_month_end + cost_mod.timedelta(days=1)), session=session)
    df = cost_mod.analyze_costs(cost_data)
    recs = cost_mod.generate_recommendations(df, session=session, start_date=cost_mod.datetime.combine(last_month_start, cost_mod.datetime.min.time()), end_date=cost_mod.datetime.combine(last_month_end + cost_mod.timedelta(days=1), cost_mod.datetime.min.time()))
    cost_html = cost_mod.generate_html_fragment(df, recs)

    # Combine both reports in a tabbed HTML page
    html = f'''
    <html><head><title>AWS Security & Cost Report</title>
    <style>
    .tab {{ overflow: hidden; border-bottom: 1px solid #ccc; }}
    .tab button {{ background: #f1f1f1; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; }}
    .tab button.active {{ background: #ccc; }}
    .tabcontent {{ display: none; padding: 20px; }}
    </style>
    <script>
    function openTab(evt, tabName) {{
      var i, tabcontent, tablinks;
      tabcontent = document.getElementsByClassName("tabcontent");
      for (i = 0; i < tabcontent.length; i++) {{ tabcontent[i].style.display = "none"; }}
      tablinks = document.getElementsByClassName("tablinks");
      for (i = 0; i < tablinks.length; i++) {{ tablinks[i].className = tablinks[i].className.replace(" active", ""); }}
      document.getElementById(tabName).style.display = "block";
      evt.currentTarget.className += " active";
    }}
    window.onload = function() {{ document.getElementById('defaultOpen').click(); }}
    </script>
    </head><body>
    <h1>AWS Security & Cost Report</h1>
    <div class="tab">
      <button class="tablinks" id="defaultOpen" onclick="openTab(event, 'Security')">Security Report</button>
      <button class="tablinks" onclick="openTab(event, 'Cost')">Cost Report</button>
    </div>
    <div id="Security" class="tabcontent">{security_html}</div>
    <div id="Cost" class="tabcontent">{cost_html}</div>
    </body></html>
    '''
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Combined report generated: {args.output}")

if __name__ == "__main__":
    main()
