<!-- # OPERO 
### Operational Incident Response & Orchestration Agent

> **GitLab AI Hackathon 2026** - Built on Github Duo Agent Platform

This is an AI-powered powered tool that helps the L1 and L2 support teams during issue triaging, auto creating Github Issues & RCA documentation - all without human intervention.

---

## Problem Statement

L1/L2 support teams spend a good amount time in-
    * manually analyzing logs, identifying failure types
    * deciding severity & sometimes there can similar cases , issues that might have hanppened before but team is not able to recall it.
    * Along with that sometime while creating the RCAs the important key-points and factir are genrally missed.
    * Sometime the team is not able to detect the problem and the actual root cause & sometime they to cinvey the same to us but they were not able to because of all of these containts 
    
    This delays resolution and increases system downtime & MTTR. 
 
* Being a SRE by myself, these points that I have mentioned above are nothing my the pain-points that I usually hear from my peers who actually work in these L1/L2 support teams.

---

## Solution Proposed

OPERO watches your pipelines 24/7 and the moment something fails:

1. **Detects** the failure automatically
2. **Classifies** the failure type (DB timeout, auth error, CI failure, etc.)
3. **Predicts severity** (P1 Critical -> P4 Low) with reasoning
4. **Suggests fixes** with actionable steps
5. **Creates a GitLab issue** automatically
6. **Generates an RCA report** as a Wiki page
7. **Shows everything** in a real-time web dashboard

---

## Architecture

1. Github/GitLab  CI failure
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

--- -->


### OPERO