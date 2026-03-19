from flask import Flask, jsonify, render_template_string
import threading
import time
import requests
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from opero_runner import analyze_issue

app = Flask(__name__)

MY_PROJECT_ID = "gitlab-ai-hackathon%2Fparticipants%2F6273024"
MY_TOKEN = "glpat-1oB42kUUpwfr8KM9NpQim286MQp1OjNxZ2FvCw.01.121g3pdrs"
GITHUB_REPO = "facebook/create-react-app"
SEEN_RUN_IDS = set()

# In-memory state
state = {
    "incidents": [],
    "total_issues": 0,
    "total_rca": 0,
    "status": "Watching",
    "last_checked": None,
    "severity_counts": {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
}

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>OPERO Dashboard</title>
  <meta http-equiv="refresh" content="15">
  <style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: #f6f8fb;
    color: #2d3436;
  }

  .header {
    background: white;
    padding: 20px 40px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header h1 {
    font-size: 24px;
    font-weight: 600;
    color: #2d3436;
  }

  .header .subtitle {
    color: #6b7280;
    font-size: 13px;
    margin-top: 4px;
  }

  .status-badge {
    background: #e6f7f1;
    color: #059669;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }

  .status-badge.error {
    background: #fde8e8;
    color: #dc2626;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    padding: 30px 40px 0;
  }

  .card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 18px;
    transition: all 0.2s ease;
  }

  .card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
  }

  .card .label {
    font-size: 12px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .card .value {
    font-size: 28px;
    font-weight: 600;
    margin-top: 8px;
    color: #111827;
  }

  .card .sub {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 4px;
  }

  .section {
    padding: 30px 40px;
  }

  .section h2 {
    font-size: 16px;
    color: #374151;
    margin-bottom: 16px;
    font-weight: 600;
  }

  .incident-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }

  .incident-table th {
    text-align: left;
    font-size: 12px;
    color: #6b7280;
    padding: 12px;
    background: #f9fafb;
  }

  .incident-table td {
    padding: 12px;
    font-size: 13px;
    border-top: 1px solid #f1f5f9;
  }

  .incident-table tr:hover td {
    background: #f9fafb;
  }

  .badge {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
  }

  .badge-p1 { background: #fee2e2; color: #dc2626; }
  .badge-p2 { background: #fef3c7; color: #d97706; }
  .badge-p3 { background: #e0e7ff; color: #4f46e5; }
  .badge-p4 { background: #dcfce7; color: #16a34a; }
  .badge-unknown { background: #f3f4f6; color: #6b7280; }

  .last-updated {
    text-align: center;
    color: #9ca3af;
    font-size: 12px;
    padding: 20px;
  }

  .bar-chart { margin-top: 8px; }

  .bar-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 6px 0;
  }

  .bar-label {
    width: 30px;
    font-size: 12px;
    color: #6b7280;
  }

  .bar-track {
    flex: 1;
    background: #e5e7eb;
    border-radius: 6px;
    height: 8px;
  }

  .bar-fill {
    height: 8px;
    border-radius: 6px;
    transition: width 0.5s;
  }

  .bar-count {
    width: 30px;
    font-size: 12px;
    color: #6b7280;
    text-align: right;
  }
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>OPERO</h1>
      <div class="subtitle">Monitors real-world CI failures from GitHub, analyzes them using AI, and automatically creates triaged incidents in GitLab — {{ data.last_checked or 'Starting...' }}</div>
    </div>
    <div class="status-badge">{{ data.status }}</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="label">Total incidents detected</div>
      <div class="value">{{ data.incidents|length }}</div>
      <div class="sub">From {{ repo }}</div>
    </div>
    <div class="card">
      <div class="label">GitLab issues created</div>
      <div class="value">{{ data.total_issues }}</div>
      <div class="sub">Auto-created by OPERO</div>
    </div>
    <div class="card">
      <div class="label">RCA reports generated</div>
      <div class="value">{{ data.total_rca }}</div>
      <div class="sub">Wiki pages auto-generated</div>
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
    <h2>Live incident feed</h2>
    <table class="incident-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Workflow</th>
          <th>Branch</th>
          <th>Failure type</th>
          <th>Severity</th>
          <th>Fix</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
        {% for inc in data.incidents|reverse %}
        <tr>
          <td style="color:#555">{{ inc.time }}</td>
          <td>{{ inc.workflow }}</td>
          <td style="color:#555">{{ inc.branch }}</td>
          <td>{{ inc.failure }}</td>
          <td>
            <span class="badge badge-{{ inc.severity|lower if inc.severity in ['P1','P2','P3','P4'] else 'unknown' }}">
              {{ inc.severity }}
            </span>
          </td>
          <td style="color:#888; font-size:12px">{{ inc.fix }}</td>
          <td><a href="{{ inc.url }}" target="_blank" style="color:#7f77dd; font-size:12px">View</a></td>
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

def get_failed_runs():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
        headers = {"Accept": "application/vnd.github+json"}
        params = {"status": "failure", "per_page": 10}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("workflow_runs", [])
    except Exception as e:
        print(f"GitHub API error: {e}")
    return []

def get_job_logs(run_id):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs"
        headers = {"Accept": "application/vnd.github+json"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            jobs = response.json().get("jobs", [])
            failed = [j for j in jobs if j["conclusion"] == "failure"]
            if failed:
                job = failed[0]
                steps_failed = [s["name"] for s in job.get("steps", []) if s.get("conclusion") == "failure"]
                return f"Job '{job['name']}' failed at steps: {', '.join(steps_failed)}"
    except Exception as e:
        print(f"Log fetch error: {e}")
    return ""

def create_gitlab_issue(title, description):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/issues"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        data = {"title": title, "description": description, "labels": "incident,opero-auto"}
        response = requests.post(url, headers=headers, data=data, timeout=10)
        if response.status_code == 201:
            state["total_issues"] += 1
            return True
    except Exception as e:
        print(f"Issue creation error: {e}")
    return False

def generate_rca(run, result, log):
    try:
        url = f"https://gitlab.com/api/v4/projects/{MY_PROJECT_ID}/wikis"
        headers = {"PRIVATE-TOKEN": MY_TOKEN}
        content = f"""# RCA — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Incident Source
- **Project:** {GITHUB_REPO}
- **Workflow:** {run['name']}
- **Branch:** {run['head_branch']}
- **Failed at:** {run['updated_at']}
- **GitHub URL:** {run['html_url']}

## OPERO Analysis
- **Failure type:** {result['failure']}
- **Severity:** {result['severity']}

## Log Details
{log}

## Resolution Steps
{chr(10).join(f'- {step}' for step in result['fix'])}

> Auto-generated by OPERO
"""
        data = {
            "title": f"RCA-{run['id']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "content": content,
            "format": "markdown"
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            state["total_rca"] += 1
    except Exception as e:
        print(f"RCA error: {e}")

def watcher():
    print("OPERO watcher started...")
    while True:
        try:
            state["last_checked"] = datetime.now().strftime("%H:%M:%S")
            state["status"] = "Watching"
            runs = get_failed_runs()
            for run in runs:
                run_id = run["id"]
                if run_id in SEEN_RUN_IDS:
                    continue
                SEEN_RUN_IDS.add(run_id)

                log = get_job_logs(run_id)
                analyze_text = f"{run['name']} {run['head_branch']} {log} integration tests node".lower()
                result = analyze_issue(analyze_text)

                incident = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "workflow": run["name"],
                    "branch": run["head_branch"],
                    "failure": result["failure"],
                    "severity": result["severity"],
                    "fix": result["fix"][0] if result["fix"] else "Investigate logs",
                    "url": run["html_url"]
                }
                state["incidents"].append(incident)
                state["severity_counts"][result["severity"]] = \
                    state["severity_counts"].get(result["severity"], 0) + 1

                print(f"Incident: {result['failure']} | {result['severity']}")
                create_gitlab_issue(
                    f"OPERO: {result['failure']} in {run['name']}",
                    f"**Workflow:** {run['name']}\n**Branch:** {run['head_branch']}\n**Severity:** {result['severity']}\n**Fix:** {result['fix'][0]}\n**URL:** {run['html_url']}"
                )
                generate_rca(run, result, log)

        except Exception as e:
            state["status"] = f"Error: {str(e)[:30]}"
            print(f"Watcher error: {e}")

        time.sleep(60)

@app.route("/")
def dashboard():
    return render_template_string(HTML, data=state, repo=GITHUB_REPO)

@app.route("/api/state")
def api_state():
    return jsonify(state)

if __name__ == "__main__":
    # if not MY_TOKEN:
    #     print("Set GITLAB_TOKEN environment variable first!")
    #     print("Run: set GITLAB_TOKEN=your-token-here")
    #     exit(1)
    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    print("Dashboard running at http://localhost:5000")
    app.run(debug=False, port=5000)