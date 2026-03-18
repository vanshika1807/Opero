import requests
import random
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from opero_runner import analyze_issue

# UPDATE THESE
PROJECT_ID = "gitlab-ai-hackathon%2Fparticipants%2F6273024"
TOKEN = "glpat-gUiq5JwkC_x1Lo6m3bgc6W86MQp1OjNxZ2FvCw.01.121sb7cj9"

errors = [
    "Database connection timeout",
    "Authentication failure",
    "503 Service Unavailable"
]

def create_issue(title, description):
    url = f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/issues"
    headers = {"PRIVATE-TOKEN": TOKEN}
    data = {"title": title, "description": description}
    response = requests.post(url, headers=headers, data=data)
    print("Issue created:", response.status_code)
    print("Response:", response.text)
    return response

def simulate_monitor():
    if random.choice([True, False]):
        error = random.choice(errors)
        print(f"Detected error: {error}")

        result = analyze_issue(error)

        description = f"""
## OPERO Auto-Detected Incident

**Error:** {error}
**Service:** Login API
**Time:** {datetime.now()}
**Environment:** Production

## OPERO Pre-Analysis
- **Failure type:** {result['failure']}
- **Severity:** {result['severity']}
- **Suggested fix:** {result['fix'][0] if result['fix'] else 'Investigate logs'}
"""
        create_issue("OPERO Incident Detected", description)
    else:
        print("System healthy - no incident detected")

if __name__ == "__main__":
    simulate_monitor()