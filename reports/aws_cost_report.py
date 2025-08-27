def generate_html_fragment(df, recs):
    if df.empty or 'cost' not in df.columns or 'service' not in df.columns:
        # Friendly message if no cost data
        try:
            account_id = boto3.client('sts').get_caller_identity()['Account']
        except Exception:
            account_id = 'Unknown'
        scan_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        return f'''
        <h2>AWS Cost Report</h2>
        <div style="background:#e8f4fa;padding:10px;border-radius:6px;margin-bottom:20px;">
        <b>Executive Summary</b><br>
        <b>Account ID:</b> {account_id}<br>
        <b>Scan Time:</b> {scan_time}<br>
        <b>No cost data available for this account or time period.</b>
        </div>
        '''
    total_cost = df['cost'].sum()
    projected_cost = total_cost - sum(r['potential_savings'] for r in recs)
    savings = total_cost - projected_cost
    pie = go.Figure([go.Pie(labels=df['service'], values=df['cost'])])
    pie_html = pie.to_html(full_html=False, include_plotlyjs='cdn')
    bar = go.Figure()
    bar.add_bar(name='Current', x=['Cost'], y=[total_cost])
    bar.add_bar(name='Optimized', x=['Cost'], y=[projected_cost])
    bar_html = bar.to_html(full_html=False, include_plotlyjs=False)
    # Get account ID
    try:
        account_id = boto3.client('sts').get_caller_identity()['Account']
    except Exception:
        account_id = 'Unknown'
    scan_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    template_str = '''
    <h2>AWS Cost Report</h2>
    <div style="background:#e8f4fa;padding:10px;border-radius:6px;margin-bottom:20px;">
    <b>Executive Summary</b><br>
    <b>Account ID:</b> {{ account_id }}<br>
    <b>Scan Time:</b> {{ scan_time }}<br>
    <b>Current Cost:</b> ${{ '%.2f' % total_cost }} / month<br>
    <b>Projected Cost After Optimization:</b> ${{ '%.2f' % projected_cost }} / month<br>
    <b>Potential Savings:</b> ${{ '%.2f' % savings }} ({{ (savings/total_cost*100) | round(1) }}%)
    </div>
    <h3>Cost by Service</h3>
    {{ pie_html | safe }}
    <h3>Optimization Recommendations</h3>
    <table border=1><tr><th>Service</th><th>Resource ID</th><th>Recommendation</th><th>Potential Savings</th></tr>
    {% for r in recs %}<tr><td>{{ r.service }}</td><td>{{ r.resource_id if r.resource_id is defined else '' }}</td><td>{{ r.recommendation }}</td><td>${{ '%.2f' % r.potential_savings }}</td></tr>{% endfor %}
    </table>
    <h3>EC2 Idle Instance Report</h3>
    {% if recs|selectattr('service', 'equalto', 'EC2')|list %}
    <table border=1><tr><th>Instance ID</th><th>Idle Hours</th><th>Total Hours</th><th>Recommendation</th></tr>
    {% for r in recs if r.service == 'EC2' %}
    <tr><td>{{ r.resource_id }}</td><td>{{ r.recommendation.split('(')[1].split('h/')[0] }}</td><td>{{ r.recommendation.split('/')[1].split('h')[0] }}</td><td>{{ r.recommendation }}</td></tr>
    {% endfor %}
    </table>
    {% else %}<p>No idle EC2 instances detected.</p>{% endif %}
    <h3>Before vs After Optimization</h3>
    {{ bar_html | safe }}
    <h3>Raw Data</h3>
    {{ df.to_html(index=False) }}
    '''
    env = jinja2.Environment()
    template = env.from_string(template_str)
    html = template.render(
        total_cost=total_cost,
        projected_cost=projected_cost,
        savings=savings,
        pie_html=pie_html,
        bar_html=bar_html,
        recs=recs,
        df=df,
        account_id=account_id,
        scan_time=scan_time
    )
    return html

import argparse
import boto3
import pandas as pd
import plotly.graph_objs as go
import jinja2
import os
from datetime import datetime, timedelta

# 1. Fetch cost and usage data
def get_cost_and_usage(start_date, end_date, granularity='MONTHLY', session=None):
    if session is None:
        session = boto3.Session()
    ce = session.client('ce')
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity=granularity,
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}, {'Type': 'DIMENSION', 'Key': 'REGION'}]
    )
    return response

# 2. Analyze costs and build DataFrame
def analyze_costs(cost_data):
    rows = []
    for result in cost_data['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            region = group['Keys'][1]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            rows.append({'service': service, 'region': region, 'cost': amount})
    df = pd.DataFrame(rows)
    return df

# 3. Generate recommendations (simple heuristics)
def generate_recommendations(df, session=None, start_date=None, end_date=None):
    recs = []
    # Return empty if df is empty or missing 'service' column
    if df.empty or 'service' not in df.columns:
        return recs
    # Lower threshold for demo
    for service, group in df.groupby('service'):
        total = group['cost'].sum()
        if total > 10:
            recs.append({
                'service': service,
                'recommendation': f'Consider rightsizing or reserved pricing for {service}.',
                'potential_savings': round(total * 0.2, 2)
            })
    # EC2 idle analysis
    if session is not None and start_date and end_date:
        ec2 = session.client('ec2')
        cw = session.client('cloudwatch')
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for inst in reservation['Instances']:
                instance_id = inst['InstanceId']
                # Get average CPUUtilization for the month
                metrics = cw.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_date,
                    EndTime=end_date,
                    Period=3600,
                    Statistics=['Average']
                )
                datapoints = metrics.get('Datapoints', [])
                idle_hours = sum(1 for d in datapoints if d['Average'] < 5)
                total_hours = len(datapoints)
                if total_hours > 0 and idle_hours > 0:
                    recs.append({
                        'service': 'EC2',
                        'resource_id': instance_id,
                        'recommendation': f'Instance {instance_id} was idle ({idle_hours}h/{total_hours}h) last month. Consider stopping during off-hours.',
                        'potential_savings': 0.1 * df[df['service']=='Amazon Elastic Compute Cloud - Compute']['cost'].sum()  # Example: 10% savings
                    })
    return recs

# 4. Generate HTML report with charts
def generate_html_report(df, recs, output_path, ec2_idle=None):
    total_cost = df['cost'].sum()
    projected_cost = total_cost - sum(r['potential_savings'] for r in recs)
    savings = total_cost - projected_cost
    # Pie chart: cost by service
    pie = go.Figure([go.Pie(labels=df['service'], values=df['cost'])])
    pie_html = pie.to_html(full_html=False, include_plotlyjs='cdn')
    # Bar chart: before vs after
    bar = go.Figure()
    bar.add_bar(name='Current', x=['Cost'], y=[total_cost])
    bar.add_bar(name='Optimized', x=['Cost'], y=[projected_cost])
    bar_html = bar.to_html(full_html=False, include_plotlyjs=False)
    # Jinja2 template
    template_str = '''
    <html><head><title>AWS Cost Report</title></head><body>
    <h1>AWS Cost Report</h1>
    <p><b>Current Cost:</b> ${{ '%.2f' % total_cost }} / month<br>
    <b>Projected Cost After Optimization:</b> ${{ '%.2f' % projected_cost }} / month<br>
    <b>Potential Savings:</b> ${{ '%.2f' % savings }} ({{ (savings/total_cost*100) | round(1) }}%)</p>
    <h2>Cost by Service</h2>
    {{ pie_html | safe }}
    <h2>Optimization Recommendations</h2>
    <table border=1><tr><th>Service</th><th>Resource ID</th><th>Recommendation</th><th>Potential Savings</th></tr>
    {% for r in recs %}<tr><td>{{ r.service }}</td><td>{{ r.resource_id if r.resource_id is defined else '' }}</td><td>{{ r.recommendation }}</td><td>${{ '%.2f' % r.potential_savings }}</td></tr>{% endfor %}
    </table>
    <h2>EC2 Idle Instance Report</h2>
    {% if recs|selectattr('service', 'equalto', 'EC2')|list %}
    <table border=1><tr><th>Instance ID</th><th>Idle Hours</th><th>Total Hours</th><th>Recommendation</th></tr>
    {% for r in recs if r.service == 'EC2' %}
    <tr><td>{{ r.resource_id }}</td><td>{{ r.recommendation.split('(')[1].split('h/')[0] }}</td><td>{{ r.recommendation.split('/')[1].split('h')[0] }}</td><td>{{ r.recommendation }}</td></tr>
    {% endfor %}
    </table>
    {% else %}<p>No idle EC2 instances detected.</p>{% endif %}
    <h2>Before vs After Optimization</h2>
    {{ bar_html | safe }}
    <h2>Raw Data</h2>
    {{ df.to_html(index=False) }}
    </body></html>
    '''
    env = jinja2.Environment()
    template = env.from_string(template_str)
    html = template.render(
        total_cost=total_cost,
        projected_cost=projected_cost,
        savings=savings,
        pie_html=pie_html,
        bar_html=bar_html,
        recs=recs,
        df=df
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AWS Cost Explorer & Optimization Report")
    parser.add_argument('--profile', type=str, help='AWS CLI profile name', default=None)
    parser.add_argument('--output', type=str, help='Output HTML report file', default='reports/cost_report.html')
    args = parser.parse_args()

    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    today = datetime.utcnow().date()
    first = today.replace(day=1)
    last_month_end = first - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    cost_data = get_cost_and_usage(str(last_month_start), str(last_month_end + timedelta(days=1)), session=session)
    df = analyze_costs(cost_data)
    recs = generate_recommendations(df, session=session, start_date=datetime.combine(last_month_start, datetime.min.time()), end_date=datetime.combine(last_month_end + timedelta(days=1), datetime.min.time()))
    generate_html_report(df, recs, args.output)
