from opero_runner import analyze_issue

result = analyze_issue(error)

description += f"""

Predicted Failure: {result['failure']}
Predicted Severity: {result['severity']}
"""