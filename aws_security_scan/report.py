# report.py: Generates HTML report using Jinja2 and Plotly
import pandas as pd
import jinja2
import plotly.graph_objs as go
import os
from datetime import datetime

class ReportGenerator:
    def generate_html_string(self):
        df = pd.DataFrame(self.findings)
        summary = self._generate_summary(df)
        charts = self._generate_charts(df)
        template = self._get_template()
        html = template.render(
            summary=summary,
            findings=df.to_dict(orient='records'),
            charts=charts,
            account_id=self.account_id,
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        )
        return html
    def __init__(self, findings, account_id):
        self.findings = findings
        self.account_id = account_id

    def generate(self, output_path):
        df = pd.DataFrame(self.findings)
        summary = self._generate_summary(df)
        charts = self._generate_charts(df)
        template = self._get_template()
        html = template.render(
            summary=summary,
            findings=df.to_dict(orient='records'),
            charts=charts,
            account_id=self.account_id,
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_summary(self, df):
        summary = {
            'total': len(df),
            'high': (df['severity'] == 'High').sum() if 'severity' in df else 0,
            'medium': (df['severity'] == 'Medium').sum() if 'severity' in df else 0,
            'low': (df['severity'] == 'Low').sum() if 'severity' in df else 0,
        }
        # Per-service severity breakdown
        if 'service' in df and 'severity' in df:
            service_table = (
                df.groupby(['service', 'severity']).size()
                .unstack(fill_value=0)
                .reset_index()
                .to_dict(orient='records')
            )
            summary['service_table'] = service_table
        else:
            summary['service_table'] = []
        return summary

    def _generate_charts(self, df):
        # Pie chart: compliant vs non-compliant
        severity_counts = df['severity'].value_counts() if 'severity' in df else {}
        pie = go.Figure(data=[go.Pie(labels=severity_counts.index, values=severity_counts.values)])
        pie_html = pie.to_html(full_html=False, include_plotlyjs='cdn')
        # Bar chart: risk levels by service
        bar = go.Figure()
        if 'service' in df and 'severity' in df:
            bar_data = df.groupby(['service', 'severity']).size().unstack(fill_value=0)
            for sev in ['High', 'Medium', 'Low']:
                if sev in bar_data:
                    bar.add_bar(name=sev, x=bar_data.index, y=bar_data[sev])
        bar_html = bar.to_html(full_html=False, include_plotlyjs=False)
        return {'pie': pie_html, 'bar': bar_html}

    def _get_template(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=os.path.dirname(__file__)))
        return env.get_template('report_template.html')
