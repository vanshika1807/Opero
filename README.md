# OPERO 🚀

This is an AI-powered powered tool that helps the L1 and L2 support teams during issue triaging, RCA documantionation creation plus this agent can help the team in ahering to the SLA/SLO/SLI

---

## 🧩 Problem

L1/L2 support teams spend a good amount time in manually analyzing logs, identifying failure types, deciding severity & sometimes there can similar cases & issues that might have hanppened before but team is not able to recall it. This delays resolution and increases system downtime & MTTR

---

## 💡 Solution

OPERO is an AI agent that automates incident triage by:

* Identifying failure type
* Predicting severity (P1–P4)
* gives the user a report, on what is wrong
* plus it gives the proper documention & a guidance to adhere to the SLAs

---

## ⚙️ How it works

1. The user tells OPERO about the problem
2. OPERO analyzes the problem
3. OPERO gives the user a report, on what is wrong

---

## 📊 Example

**Input:**
The login API is not working and is giving a 500 error and a database timeout

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

* It saves time when trying to figure out what is wrong
* Speeds up incident resolution
* It makes the developers more productive

---

## 🛠️ Tech Stack

* GitLab Duo Agent Platform
* It uses YAML to configure the agent and the flow
* AI-driven analysis

---

## 📌 Status

✅ Agent implemented
✅ Flow configured
✅ CI pipeline passed
✅ Demo ready

---
