import requests
import time
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from opero_runner import analyze_issue

MY_PROJECT_ID = "gitlab-ai-hackathon%2Fparticipants%2F6273024"
MY_TOKEN = "glpat-1oB42kUUpwfr8KM9NpQim286MQp1OjNxZ2FvCw.01.121g3pdrs"

GMAIL_SENDER = "vanshikasinghportfolio@gmail.com"
GMAIL_PASSWORD = "btzcfngthlhjmmty"
ALERT_RECIPIENT = "vanshikasinghportfolio@gmail.com"


SANITY_CHECKS = [
    {
        "name": "Sample API",
        "type": "api",
        "url": "https://http.cat/status/200",  
        "expected_status": 200,
        "timeout": 5
    },
    {
        "name": "Sample1 API",
        "type": "api",
        "url": "https://httpstat.us/503",  
        "expected_status": 200,
        "timeout": 5
    },
    {
        "name": "Sample2 API",
        "type": "api",
        "url": "https://http.cat/status/500", 
        "expected_status": 200,
        "timeout": 5
    },
]


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
    """Run a single API sanity check"""
    try:
        start = datetime.now()
        response = requests.get(check["url"], timeout=check["timeout"])
        elapsed = (datetime.now() - start).total_seconds() * 1000

        if response.status_code != check["expected_status"]:
            return {
                "status": "FAIL",
                "message": f"HTTP {response.status_code} — expected {check['expected_status']}",
                "response_time_ms": elapsed
            }
        if elapsed > 2000:
            return {
                "status": "WARN",
                "message": f"Slow response: {elapsed:.0f}ms (threshold: 2000ms)",
                "response_time_ms": elapsed
            }
        return {
            "status": "OK",
            "message": f"HTTP {response.status_code} in {elapsed:.0f}ms",
            "response_time_ms": elapsed
        }
    except requests.exceptions.Timeout:
        return {"status": "FAIL", "message": f"Timeout after {check['timeout']}s", "response_time_ms": -1}
    except Exception as e:
        return {"status": "FAIL", "message": str(e), "response_time_ms": -1}

def check_metrics(metrics):
    """Check system metrics against thresholds"""
    alerts = []
    if metrics["cpu_percent"] > 85:
        alerts.append(f"CPU critical: {metrics['cpu_percent']:.1f}% (threshold: 85%)")
    if metrics["memory_percent"] > 85:
        alerts.append(f"Memory critical: {metrics['memory_percent']:.1f}% (threshold: 85%)")
    if metrics["response_time_ms"] > 2000:
        alerts.append(f"Response time critical: {metrics['response_time_ms']:.0f}ms (threshold: 2000ms)")
    if metrics["db_connections"] > metrics["db_max_connections"]:
        alerts.append(f"DB connections exceeded: {metrics['db_connections']}/{metrics['db_max_connections']}")
    return alerts

def send_email_alert(service, analysis, message, metrics):
    try:
        if not GMAIL_SENDER or not GMAIL_PASSWORD or not ALERT_RECIPIENT:
            print("  Email skipped — Gmail env vars not set")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[OPERO] {analysis['severity']} Alert — {service}"
        msg["From"] = GMAIL_SENDER
        msg["To"] = ALERT_RECIPIENT

        severity_color = {
            "P1": "#d32f2f",
            "P2": "#f57c00",
            "P3": "#7b1fa2",
            "P4": "#2e7d32"
        }.get(analysis['severity'], "#d32f2f")

        body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
  <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

    <div style="background: {severity_color}; padding: 20px;">
      <h1 style="color: white; margin: 0; font-size: 22px;">OPERO Incident Alert</h1>
      <p style="color: rgba(255,255,255,0.85); margin: 6px 0 0;">{analysis['severity']} — {service}</p>
    </div>

    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr style="background: #f9f9f9;">
          <td style="padding: 10px; font-weight: bold; width: 140px;">Service</td>
          <td style="padding: 10px;">{service}</td>
        </tr>
        <tr>
          <td style="padding: 10px; font-weight: bold;">Failure type</td>
          <td style="padding: 10px;">{analysis['failure']}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 10px; font-weight: bold;">Severity</td>
          <td style="padding: 10px;"><strong style="color: {severity_color}">{analysis['severity']}</strong></td>
        </tr>
        <tr>
          <td style="padding: 10px; font-weight: bold;">Message</td>
          <td style="padding: 10px;">{message}</td>
        </tr>
        <tr style="background: #f9f9f9;">
          <td style="padding: 10px; font-weight: bold;">Detected at</td>
          <td style="padding: 10px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
      </table>

      <div style="background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 10px; color: #2e7d32;">Suggested Fix</h3>
        <ul style="margin: 0; padding-left: 20px;">
          {''.join(f'<li style="margin-bottom:6px">{step}</li>' for step in analysis['fix'])}
        </ul>
      </div>

      <div style="background: #f5f5f5; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 10px;">System Metrics at Time of Alert</h3>
        <table style="width: 100%;">
          <tr>
            <td style="padding: 4px 0;">CPU Usage</td>
            <td style="padding: 4px 0; text-align:right; font-weight:bold; color: {'#d32f2f' if metrics['cpu_percent'] > 85 else '#2e7d32'}">{metrics['cpu_percent']:.1f}%</td>
          </tr>
          <tr>
            <td style="padding: 4px 0;">Memory Usage</td>
            <td style="padding: 4px 0; text-align:right; font-weight:bold; color: {'#d32f2f' if metrics['memory_percent'] > 85 else '#2e7d32'}">{metrics['memory_percent']:.1f}%</td>
          </tr>
          <tr>
            <td style="padding: 4px 0;">Response Time</td>
            <td style="padding: 4px 0; text-align:right; font-weight:bold; color: {'#d32f2f' if metrics['response_time_ms'] > 2000 else '#2e7d32'}">{metrics['response_time_ms']:.0f}ms</td>
          </tr>
          <tr>
            <td style="padding: 4px 0;">DB Connections</td>
            <td style="padding: 4px 0; text-align:right; font-weight:bold; color: {'#d32f2f' if metrics['db_connections'] > metrics['db_max_connections'] else '#2e7d32'}">{metrics['db_connections']}/{metrics['db_max_connections']}</td>
          </tr>
        </table>
      </div>

      <div style="text-align: center;">
        <a href="https://gitlab.com/gitlab-ai-hackathon/participants/6273024/-/issues"
           style="background: #7b1fa2; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
          View GitLab Issues
        </a>
      </div>
    </div>

    <div style="background: #f5f5f5; padding: 12px 24px; text-align: center; color: #999; font-size: 12px;">
      Auto-generated by OPERO — Incident Monitoring & Response Agent
    </div>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_SENDER, ALERT_RECIPIENT, msg.as_string())
        print(f"  Email alert sent to {ALERT_RECIPIENT}!")

    except Exception as e:
        print(f"  Email error: {e}")

def create_gitlab_issue(title, description):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/issues"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        data = {
            "title": title,
            "description": description,
            "labels": "incident,opero-auto,sanity-check"
        }
        response = requests.post(url, headers=headers, data=data, timeout=20)
        if response.status_code == 201:
            print(f"  GitLab issue created: #{response.json()['iid']}")
        return response.status_code == 201
    except Exception as e:
        print(f"  Issue creation error: {e}")
    return False

def generate_rca(service_name, check_result, analysis):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/wikis"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        content = f"""# RCA — {service_name} — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Incident Summary
- **Service:** {service_name}
- **Detected at:** {datetime.now()}
- **Check result:** {check_result['message']}

## OPERO Analysis
- **Failure type:** {analysis['failure']}
- **Severity:** {analysis['severity']}

## Resolution Steps
{chr(10).join(f'- {step}' for step in analysis['fix'])}

## Sanity Check Details
- **Response time:** {check_result.get('response_time_ms', 'N/A')}ms
- **Status:** {check_result['status']}

> Auto-generated by OPERO Sanity Runner
"""
        data = {
            "title": f"RCA-{service_name.replace(' ','-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "content": content,
            "format": "markdown"
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            print(f"  RCA wiki page created")
    except Exception as e:
        print(f"  RCA error: {e}")

def run_sanity_suite():
    """Run full sanity check suite"""
    print(f"\n{'='*55}")
    print(f"OPERO Sanity Check — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    failures = []

    # 1. API checks
    print("\nAPI Endpoint Checks:")
    for check in SANITY_CHECKS:
        result = run_api_check(check)
        status_symbol = "OK" if result["status"] == "OK" else "FAIL" if result["status"] == "FAIL" else "WARN"
        print(f"  [{status_symbol}] {check['name']}: {result['message']}")

        if result["status"] in ["FAIL", "WARN"]:
            failures.append({
                "service": check["name"],
                "type": "API",
                "result": result,
                "log_text": f"{check['name']} {result['message']} service unavailable 503"
            })

    # 2. System metrics check
    print("\nSystem Metrics:")
    metrics = get_system_metrics()
    print(f"  CPU     : {metrics['cpu_percent']:.1f}%")
    print(f"  Memory  : {metrics['memory_percent']:.1f}%")
    print(f"  Resp    : {metrics['response_time_ms']:.0f}ms")
    print(f"  DB conn : {metrics['db_connections']}/{metrics['db_max_connections']}")

    metric_alerts = check_metrics(metrics)
    for alert in metric_alerts:
        print(f"  [ALERT] {alert}")
        failures.append({
            "service": "System Metrics",
            "type": "METRIC",
            "result": {"status": "FAIL", "message": alert, "response_time_ms": 0},
            "log_text": alert
        })

    # 3. Triage failures with OPERO
    if failures:
        print(f"\nOPERO Triaging {len(failures)} failure(s)...")
        for failure in failures:
            analysis = analyze_issue(failure["log_text"])
            print(f"\n  Service : {failure['service']}")
            print(f"  Failure : {analysis['failure']}")
            print(f"  Severity: {analysis['severity']}")
            print(f"  Fix     : {analysis['fix'][0]}")

            description = f"""
## OPERO Sanity Check Alert

**Service:** {failure['service']}
**Check type:** {failure['type']}
**Status:** {failure['result']['status']}
**Message:** {failure['result']['message']}
**Detected at:** {datetime.now()}

## OPERO Analysis
- **Failure type:** {analysis['failure']}
- **Severity:** {analysis['severity']}
- **Suggested fix:** {analysis['fix'][0]}

## System Metrics at time of failure
- CPU: {metrics['cpu_percent']:.1f}%
- Memory: {metrics['memory_percent']:.1f}%
- Response time: {metrics['response_time_ms']:.0f}ms
- DB connections: {metrics['db_connections']}/{metrics['db_max_connections']}

> Auto-triaged by OPERO Sanity Runner
"""
            create_gitlab_issue(
                f"OPERO Alert: {analysis['failure']} — {failure['service']}",
                description
            )
            generate_rca(failure['service'], failure['result'], analysis)
            send_email_alert(
                failure['service'],
                analysis,
                failure['result']['message'],
                metrics
            )
    else:
        print("\nAll checks passed — system healthy!")

    return len(failures)

def watch(interval=2 * 60 * 60 ):
    """Run sanity checks continuously"""
    print("OPERO Sanity Runner started...")
    print(f"Checking every {interval} seconds\n")
    while True:
        try:
            failures = run_sanity_suite()
            if failures:
                print(f"\n{failures} incident(s) triaged and reported to GitLab")
            print(f"\nNext check in {interval} seconds...")
        except Exception as e:
            print(f"Runner error: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    watch(interval=2 * 60 * 60 )