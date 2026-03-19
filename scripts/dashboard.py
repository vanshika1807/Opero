from flask import Flask, jsonify, render_template_string
import threading
import time
import requests
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from opero_runner import analyze_issue

app = Flask(__name__)

MY_PROJECT_ID = "gitlab-ai-hackathon%2Fparticipants%2F6273024"
MY_TOKEN = "glpat-1oB42kUUpwfr8KM9NpQim286MQp1OjNxZ2FvCw.01.121g3pdrs"
GMAIL_SENDER = "vanshikasinghportfolio@gmail.com"
GMAIL_PASSWORD = "btzcfngthlhjmmty"
ALERT_RECIPIENT = "vanshikasinghportfolio@gmail.com"

SANITY_CHECKS = [
    {"name": "Sample API",  "url": "https://http.cat/status/200", "expected_status": 200, "timeout": 5},
    {"name": "Sample1 API", "url": "https://httpstat.us/503",     "expected_status": 200, "timeout": 5},
    {"name": "Sample2 API", "url": "https://http.cat/status/500", "expected_status": 200, "timeout": 5},
]

state = {
    "incidents": [],
    "total_issues": 0,
    "total_rca": 0,
    "total_emails": 0,
    "status": "Starting...",
    "last_checked": None,
    "severity_counts": {"P1": 0, "P2": 0, "P3": 0, "P4": 0},
    "service_status": {}
}

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>OPERO Dashboard</title>
  <meta http-equiv="refresh" content="15">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; }
    .header {
      background: #1a1a2e;
      padding: 20px 40px;
      border-bottom: 2px solid #7f77dd;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header h1 { font-size: 28px; color: #a29bfe; letter-spacing: 3px; }
    .header .subtitle { color: #888; font-size: 13px; margin-top: 4px; }
    .status-badge {
      background: #1d9e75; color: #e1f5ee;
      padding: 6px 16px; border-radius: 20px; font-size: 13px;
    }
    .grid {
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 20px; padding: 30px 40px 0;
    }
    .card {
      background: #1a1a2e; border: 1px solid #2d2d4e;
      border-radius: 12px; padding: 20px;
    }
    .card .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .card .value { font-size: 36px; font-weight: 700; margin-top: 8px; color: #a29bfe; }
    .card .sub { font-size: 12px; color: #555; margin-top: 4px; }
    .section { padding: 30px 40px; }
    .section h2 { font-size: 16px; color: #a29bfe; letter-spacing: 1px; margin-bottom: 16px; text-transform: uppercase; }
    .service-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 30px; }
    .service-card {
      background: #1a1a2e; border-radius: 10px; padding: 16px;
      border-left: 4px solid #2d2d4e;
    }
    .service-card.ok { border-left-color: #1d9e75; }
    .service-card.fail { border-left-color: #e24b4a; }
    .service-card.warn { border-left-color: #ef9f27; }
    .service-name { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
    .service-status { font-size: 12px; }
    .service-status.ok { color: #1d9e75; }
    .service-status.fail { color: #e24b4a; }
    .service-status.warn { color: #ef9f27; }
    .incident-table { width: 100%; border-collapse: collapse; }
    .incident-table th {
      text-align: left; font-size: 11px; color: #555;
      text-transform: uppercase; letter-spacing: 1px;
      padding: 8px 12px; border-bottom: 1px solid #2d2d4e;
    }
    .incident-table td { padding: 12px; border-bottom: 1px solid #1a1a2e; font-size: 13px; }
    .incident-table tr:hover td { background: #1a1a2e; }
    .badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .badge-p1 { background: #2d1a1a; color: #e24b4a; }
    .badge-p2 { background: #2d1f0a; color: #ef9f27; }
    .badge-p3 { background: #1e1a2e; color: #a29bfe; }
    .badge-p4 { background: #0a1f14; color: #1d9e75; }
    .badge-unknown { background: #222; color: #888; }
    .bar-chart { margin-top: 8px; }
    .bar-row { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
    .bar-label { width: 30px; font-size: 12px; color: #888; }
    .bar-track { flex: 1; background: #2d2d4e; border-radius: 4px; height: 8px; }
    .bar-fill { height: 8px; border-radius: 4px; }
    .bar-count { width: 30px; font-size: 12px; color: #888; text-align: right; }
    .last-updated { text-align: center; color: #333; font-size: 12px; padding: 20px; }
    .metric-row { display: flex; gap: 12px; margin-bottom: 20px; }
    .metric-box {
      flex: 1; background: #1a1a2e; border: 1px solid #2d2d4e;
      border-radius: 8px; padding: 14px; text-align: center;
    }
    .metric-box .m-label { font-size: 11px; color: #555; text-transform: uppercase; }
    .metric-box .m-value { font-size: 22px; font-weight: 700; margin-top: 6px; }
    .ok-color { color: #1d9e75; }
    .warn-color { color: #ef9f27; }
    .crit-color { color: #e24b4a; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>OPERO</h1>
      <div class="subtitle">Sanity Check & Incident Response Dashboard — Last checked: {{ data.last_checked or 'Starting...' }}</div>
    </div>
    <div class="status-badge">{{ data.status }}</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="label">Incidents detected</div>
      <div class="value">{{ data.incidents|length }}</div>
      <div class="sub">Total since start</div>
    </div>
    <div class="card">
      <div class="label">GitLab issues created</div>
      <div class="value">{{ data.total_issues }}</div>
      <div class="sub">Auto-created by OPERO</div>
    </div>
    <div class="card">
      <div class="label">Emails sent</div>
      <div class="value">{{ data.total_emails }}</div>
      <div class="sub">L1/L2 team notified</div>
    </div>
    <div class="card">
      <div class="label">Severity breakdown</div>
      <div class="bar-chart">
        {% set total = (data.severity_counts.P1 + data.severity_counts.P2 + data.severity_counts.P3 + data.severity_counts.P4) or 1 %}
        {% for sev, color in [('P1','#e24b4a'),('P2','#ef9f27'),('P3','#a29bfe'),('P4','#1d9e75')] %}
        <div class="bar-row">
          <div class="bar-label" style="color:{{ color }}">{{ sev }}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{{ (data.severity_counts[sev] / total * 100)|int }}%; background:{{ color }}"></div>
          </div>
          <div class="bar-count">{{ data.severity_counts[sev] }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Service health status</h2>
    <div class="service-grid">
      {% for name, svc in data.service_status.items() %}
      <div class="service-card {{ svc.status|lower }}">
        <div class="service-name">{{ name }}</div>
        <div class="service-status {{ svc.status|lower }}">
          {{ 'HEALTHY' if svc.status == 'ok' else 'DOWN' if svc.status == 'fail' else 'DEGRADED' }}
        </div>
        <div style="font-size: 11px; color: #555; margin-top: 4px;">{{ svc.message }}</div>
      </div>
      {% endfor %}
      {% if not data.service_status %}
      <div style="color: #333; padding: 20px;">Waiting for first check...</div>
      {% endif %}
    </div>

    {% if data.last_metrics %}
    <h2>System metrics</h2>
    <div class="metric-row">
      <div class="metric-box">
        <div class="m-label">CPU</div>
        <div class="m-value {{ 'crit-color' if data.last_metrics.cpu > 85 else 'warn-color' if data.last_metrics.cpu > 70 else 'ok-color' }}">
          {{ data.last_metrics.cpu }}%
        </div>
      </div>
      <div class="metric-box">
        <div class="m-label">Memory</div>
        <div class="m-value {{ 'crit-color' if data.last_metrics.memory > 85 else 'warn-color' if data.last_metrics.memory > 70 else 'ok-color' }}">
          {{ data.last_metrics.memory }}%
        </div>
      </div>
      <div class="metric-box">
        <div class="m-label">Response time</div>
        <div class="m-value {{ 'crit-color' if data.last_metrics.response_time > 2000 else 'warn-color' if data.last_metrics.response_time > 1000 else 'ok-color' }}">
          {{ data.last_metrics.response_time }}ms
        </div>
      </div>
      <div class="metric-box">
        <div class="m-label">DB connections</div>
        <div class="m-value {{ 'crit-color' if data.last_metrics.db_connections > 100 else 'ok-color' }}">
          {{ data.last_metrics.db_connections }}/100
        </div>
      </div>
    </div>
    {% endif %}

    <h2>Live incident feed</h2>
    <table class="incident-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Service</th>
          <th>Type</th>
          <th>Failure</th>
          <th>Severity</th>
          <th>Fix</th>
          <th>Notified</th>
        </tr>
      </thead>
      <tbody>
        {% for inc in data.incidents|reverse %}
        <tr>
          <td style="color:#555">{{ inc.time }}</td>
          <td>{{ inc.service }}</td>
          <td style="color:#555">{{ inc.type }}</td>
          <td>{{ inc.failure }}</td>
          <td>
            <span class="badge badge-{{ inc.severity|lower if inc.severity in ['P1','P2','P3','P4'] else 'unknown' }}">
              {{ inc.severity }}
            </span>
          </td>
          <td style="color:#888; font-size:12px">{{ inc.fix }}</td>
          <td style="color: #1d9e75; font-size:12px">Email + GitLab</td>
        </tr>
        {% endfor %}
        {% if not data.incidents %}
        <tr><td colspan="7" style="text-align:center; color:#333; padding:40px">Waiting for incidents...</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>

  <div class="last-updated">Auto-refreshes every 15 seconds</div>
</body>
</html>
"""

def get_system_metrics():
    import random
    return {
        "cpu_percent": random.uniform(20, 95),
        "memory_percent": random.uniform(40, 92),
        "response_time_ms": random.uniform(50, 3000),
        "db_connections": random.randint(5, 150),
        "db_max_connections": 100
    }

def run_api_check(check):
    try:
        start = datetime.now()
        response = requests.get(check["url"], timeout=check["timeout"])
        elapsed = (datetime.now() - start).total_seconds() * 1000
        if response.status_code != check["expected_status"]:
            return {"status": "fail", "message": f"HTTP {response.status_code}"}
        if elapsed > 2000:
            return {"status": "warn", "message": f"Slow: {elapsed:.0f}ms"}
        return {"status": "ok", "message": f"HTTP {response.status_code} in {elapsed:.0f}ms"}
    except Exception as e:
        return {"status": "fail", "message": str(e)[:60]}

def send_email_alert(service, analysis, message, metrics):
    try:
        if not GMAIL_SENDER or not GMAIL_PASSWORD:
            return
        severity_color = {"P1": "#d32f2f", "P2": "#f57c00", "P3": "#7b1fa2", "P4": "#2e7d32"}.get(analysis['severity'], "#d32f2f")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[OPERO] {analysis['severity']} Alert — {service}"
        msg["From"] = GMAIL_SENDER
        msg["To"] = ALERT_RECIPIENT
        body = f"""<html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px">
        <div style="max-width:600px;margin:auto;background:white;border-radius:8px;overflow:hidden">
        <div style="background:{severity_color};padding:20px">
        <h1 style="color:white;margin:0">OPERO Incident Alert</h1>
        <p style="color:rgba(255,255,255,0.85);margin:6px 0 0">{analysis['severity']} — {service}</p></div>
        <div style="padding:24px">
        <p><b>Service:</b> {service}</p>
        <p><b>Failure:</b> {analysis['failure']}</p>
        <p><b>Severity:</b> <span style="color:{severity_color}">{analysis['severity']}</span></p>
        <p><b>Message:</b> {message}</p>
        <p><b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p><b>Suggested fix:</b> {analysis['fix'][0]}</p>
        <hr>
        <p>CPU: {metrics['cpu_percent']:.1f}% | Memory: {metrics['memory_percent']:.1f}% | Response: {metrics['response_time_ms']:.0f}ms</p>
        </div></div></body></html>"""
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_SENDER, ALERT_RECIPIENT, msg.as_string())
        state["total_emails"] += 1
        print(f"  Email sent!")
    except Exception as e:
        print(f"  Email error: {e}")

def create_gitlab_issue(title, description):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/issues"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        data = {"title": title, "description": description, "labels": "incident,opero-auto,sanity-check"}
        response = requests.post(url, headers=headers, data=data, timeout=10)
        if response.status_code == 201:
            state["total_issues"] += 1
            print(f"  GitLab issue created!")
    except Exception as e:
        print(f"  Issue error: {e}")

def generate_rca(service_name, check_result, analysis):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/wikis"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        content = f"""# RCA — {service_name} — {datetime.now().strftime('%Y-%m-%d %H:%M')}
## Incident
- **Service:** {service_name}
- **Failure:** {analysis['failure']}
- **Severity:** {analysis['severity']}
- **Message:** {check_result['message']}
## Fix
{chr(10).join(f'- {s}' for s in analysis['fix'])}
> Auto-generated by OPERO"""
        data = {
            "title": f"RCA-{service_name.replace(' ','-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "content": content,
            "format": "markdown"
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            state["total_rca"] += 1
    except Exception as e:
        print(f"  RCA error: {e}")

def watcher():
    print("OPERO watcher started...")
    while True:
        try:
            state["last_checked"] = datetime.now().strftime("%H:%M:%S")
            state["status"] = "Watching"

            metrics = get_system_metrics()
            state["last_metrics"] = {
                "cpu": round(metrics['cpu_percent'], 1),
                "memory": round(metrics['memory_percent'], 1),
                "response_time": round(metrics['response_time_ms']),
                "db_connections": metrics['db_connections']
                }
            

            failures = []

            # API checks
            for check in SANITY_CHECKS:
                result = run_api_check(check)
                state["service_status"][check["name"]] = result
                if result["status"] in ["fail", "warn"]:
                    failures.append({
                        "service": check["name"],
                        "type": "API",
                        "result": result,
                        "log_text": f"{check['name']} {result['message']} service unavailable 503"
                    })

            # Metrics alerts
            if metrics["cpu_percent"] > 85:
                failures.append({"service": "System", "type": "CPU", "result": {"status": "fail", "message": f"CPU {metrics['cpu_percent']:.1f}%"}, "log_text": "cpu critical"})
            if metrics["memory_percent"] > 85:
                failures.append({"service": "System", "type": "Memory", "result": {"status": "fail", "message": f"Memory {metrics['memory_percent']:.1f}%"}, "log_text": "memory critical"})
            if metrics["response_time_ms"] > 2000:
                failures.append({"service": "System", "type": "Response", "result": {"status": "fail", "message": f"Response {metrics['response_time_ms']:.0f}ms"}, "log_text": "response time critical"})

            for failure in failures:
                analysis = analyze_issue(failure["log_text"])
                incident = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "service": failure["service"],
                    "type": failure["type"],
                    "failure": analysis["failure"],
                    "severity": analysis["severity"],
                    "fix": analysis["fix"][0] if analysis["fix"] else "Investigate"
                }
                state["incidents"].append(incident)
                state["severity_counts"][analysis["severity"]] = state["severity_counts"].get(analysis["severity"], 0) + 1
                print(f"Incident: {failure['service']} | {analysis['failure']} | {analysis['severity']}")
                create_gitlab_issue(f"OPERO: {analysis['failure']} — {failure['service']}", f"**Service:** {failure['service']}\n**Severity:** {analysis['severity']}\n**Fix:** {analysis['fix'][0]}")
                generate_rca(failure["service"], failure["result"], analysis)
                send_email_alert(failure["service"], analysis, failure["result"]["message"], metrics)

        except Exception as e:
            state["status"] = f"Error: {str(e)[:30]}"
            print(f"Watcher error: {e}")

        time.sleep(60)

@app.route("/")
def dashboard():
    return render_template_string(HTML, data=state)

@app.route("/api/state")
def api_state():
    return jsonify(state)

if __name__ == "__main__":
    state["last_metrics"] = {"cpu": "0", "memory": "0", "response_time": "0", "db_connections": 0}
    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    print("OPERO Dashboard running at http://localhost:5000")
    app.run(debug=False, port=5000)