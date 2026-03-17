import yaml

def load_rules():
    with open("rules/rules.yaml") as f:
        return yaml.safe_load(f)["rules"]

def analyze_issue(text):
    rules = load_rules()
    text = text.lower()

    for rule in rules:
        for keyword in rule["keywords"]:
            if keyword in text:
                return rule

    return {
        "failure": "Unknown",
        "severity": "P3",
        "fix": ["Investigate logs"]
    }

if __name__ == "__main__":
    issue = "Login API failing due to DB timeout"

    result = analyze_issue(issue)

    print("🚨 OPERO ANALYSIS")
    print("Failure:", result["failure"])
    print("Severity:", result["severity"])
    print("Fix:")
    for step in result["fix"]:
        print("-", step)