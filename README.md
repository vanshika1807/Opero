# OPERO 🚀

AI-powered Incident Triage Agent for L1/L2 Support Teams

---

## 🧩 Problem

L1/L2 support teams spend significant time manually analyzing logs, identifying failure types, and deciding severity. This delays resolution and increases system downtime.

---

## 💡 Solution

OPERO is an AI agent that automates incident triage by:

* Identifying failure type
* Predicting severity (P1–P4)
* Suggesting actionable fixes

---

## ⚙️ How it works

1. User provides an issue or log snippet
2. OPERO analyzes the problem
3. Returns structured triage output

---

## 📊 Example

**Input:**
Login API failing with 500 error and DB timeout

**Output:**

* 🔍 Failure: Database Timeout
* ⚠️ Severity: P1 (Critical)
* 🧠 Root Cause: Connection pool exhaustion
* 🛠️ Fix:

  * Check DB connectivity
  * Restart service
  * Optimize queries

---

## 🚀 Impact

* Reduces debugging time
* Speeds up incident resolution
* Improves developer productivity

---

## 🛠️ Tech Stack

* GitLab Duo Agent Platform
* YAML-based agent + flow configuration
* AI-driven analysis

---

## 📌 Status

✅ Agent implemented
✅ Flow configured
✅ CI pipeline passed
✅ Demo ready

---
