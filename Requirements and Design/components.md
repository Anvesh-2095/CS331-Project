Q2) Components present in the SOAR project (Application Components)
==================================================================

A) Core Processing Components
----------------------------

- IngestionService
  - Receives alerts from external tools (simulated).
  - Validates incoming alert schema and publishes alert data internally.

- Alert Normalization Module
  - Converts tool-specific alert formats into a single common internal schema.

- Correlation Engine
  - Groups related alerts using attributes such as IPs, timestamps, severity, and category.

- Incident Manager
  - Creates and maintains incidents with lifecycle states:
    - Open -> In Progress -> Escalated -> Resolved


B) Orchestration + Automation Components
---------------------------------------

- BrainService (Decision Engine)
  - Selects response playbooks based on incident context.
  - Commands the playbook execution service.

- PlaybookService
  - Executes ordered playbook steps.
  - Tracks step success/failure and triggers retry logic.

- Playbook Store
  - Stores playbook definitions and versions for auditability and rollback.


C) Response / Actuation Components
----------------------------------

- ActuatorSimulator (Interface)
  - Provides a standard contract for all automated response actions.

- FirewallActuator
  - Simulates response actions such as blocking an IP or isolating a host.

- EmailActuator
  - Simulates response actions such as deleting phishing emails or quarantining messages.


D) Logging, Reporting & Escalation Components
---------------------------------------------

- Failure Handling & Escalation Service
  - Captures automation failures (tool unavailable, permission error, execution error).
  - Escalates to analysts when automation cannot complete.

- ArtifactService
  - Records incident activity logs and failure artifacts.
  - Generates incident summary and compliance-ready reports.

- AuditLog Store
  - Stores all system events including:
    - alert ingestion logs
    - normalization logs
    - playbook execution logs
    - response action logs
    - failure logs


E) Human Interaction Components
-------------------------------

- NotificationService
  - Sends notifications for:
    - incident creation
    - escalation
    - automation failures
    - high-risk manual approval requests

- Security Analyst Interface (Logical Component)
  - Allows analysts to review incidents, approve actions, and update incident status.

- System Administrator Interface (Logical Component)
  - Allows administrators to create, update, and version playbooks.
