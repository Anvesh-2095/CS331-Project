A) Shape Meaning (Notation Used)

Rectangle → External Entity (outside the SOAR system)

Oval / Bubble → Process (functional module inside the SOAR system)

Cylinder → Data Store (persistent storage/database)

Arrow → Data Flow (data moving between entities, processes, and stores)

B) External Entities (Rectangles)

External Security Tools: Provide security alerts and receive response commands.

Security Analyst: Receives notifications/reports and performs manual updates/approvals.

System Administrator: Creates or updates playbooks.

Notification Service: Sends incident/failure alerts to the analyst.

C) Data Stores (Cylinders)

D1 Alert Repository: Stores raw and normalized alerts.

D2 Incident Store: Stores incident records and lifecycle state.

D3 Playbook Store: Stores playbook definitions and versions.

D4 Audit Log Store: Stores logs, artifacts, failures, and reports.

D) Process Flow (Level 1 Decomposition)

1.0 Alert Ingestion receives security alerts from external security tools.

2.0 Alert Normalization converts alerts into a common internal format and stores them in D1.

3.0 Alert Correlation groups related normalized alerts into correlated alert groups.

4.0 Incident Management creates and updates incidents and stores them in D2.

5.0 Playbook Selection & Execution selects the correct playbook using incident context and retrieves playbook definitions from D3.

6.0 Response Actuation executes selected response actions and sends response commands to external tools.

7.0 Failure Handling & Escalation captures failures, records artifacts/logs in D4, and triggers notifications when automation fails.

8.0 Reporting & Audit Logging generates incident summaries/compliance reports and archives them in D4.

E) Key Outputs

Response commands are sent to external security tools.

Incident/failure notifications are sent to the security analyst through the notification service.

Reports and audit logs are maintained for compliance and traceability.
