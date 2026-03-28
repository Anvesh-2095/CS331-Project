**Q1. Core BLL Modules and UI Interaction**

**1. The Authentication & Authorization Module**

- **Implementation:** Handles the generation and validation of OAuth2 JWTs and sliding sessions.
- **UI
   Interaction:** The React Dashboard sends user credentials via a form.
   The BLL validates these against the hashed database values and returns an
   Access Token and Refresh Token. Subsequent UI requests (like clicking a
   dashboard button) include this token, which the BLL validates before
   permitting the action.

**2. The Alert Correlation Engine (The "Brain")**

- **Implementation:** Maintains a sliding time-window buffer in memory to group isolated
   security events.
- **UI
   Interaction:** The UI does not process alerts. It periodically polls (or
   uses WebSockets) to ask the BLL: "Are there new incidents?" The
   BLL reads its internal buffer, applies correlation math, updates the
   PostgreSQL database, and serves the finalized incident list to the UI's
   data grid.

**3. The Playbook Execution Engine**

- **Implementation:** Parses YAML/JSON workflow configurations and executes sequential security
   actions.
- **UI
   Interaction:** When a Security Analyst uses the CLI or Dashboard to
   issue a manual override (e.g., soar-cli override --target 10.0.0.5), the
   Presentation Layer simply sends an HTTP POST request. The BLL takes over,
   checks if the action is valid, translates it into a message for the
   RabbitMQ bus, and commands the Actuator service to block the IP.

---

**Q2.**

**A) Implementation of Business Rules**

- **Access
   Control Rules (RBAC):** Implemented in the Auth Service. A strict
   business rule dictates that System Administrators receive a 60-minute
   sliding session, while Security Analysts receive a 30-minute session.
   Furthermore, the API Gateway enforces a rule where only tokens containing
   the role: admin claim can send POST/DELETE requests to the Playbook
   database.
- **Correlation
   Threshold Rules:** Implemented in the Orchestrator. The rule states: If
   a distinct source_ip triggers $\ge 3$ alerts within a $300$-second window,
   the BLL elevates the grouping from "Alerts" to an
   "Incident" and triggers a playbook.
- **Escalation
   Rules:** Implemented in the Playbook Service. If an automated actuator
   fails to isolate a host within 5 seconds, the business rule mandates an
   automatic fallback to the Notification Service to alert a human analyst
   via Slack/Email.

**B) Validation Logic**

- **API
   Payload Validation:** Using Python's Pydantic library, the Ingestion
   Service strictly enforces schemas. If an external security tool sends an
   alert missing a mandatory tool_id or uses a malformed IPv4 address for source_ip,
   the BLL immediately rejects the payload with a 422 Unprocessable Entity
   error before it ever reaches the RabbitMQ bus.
- **Cryptographic
   Validation:** The Auth BLL strictly validates the cryptographic
   signature of the JSON Web Token on every single API request. If an analyst
   modifies their token payload to say role: admin, the validation logic
   catches the mismatched signature and drops the request.
- **State
   Validation:** Before executing a manual override playbook, the BLL
   checks the Incident Store. If the incident status is already marked as resolved,
   the validation logic rejects the redundant command.

**C) Data Transformation**

- **Ingestion
   Normalization:** Security tools speak different languages. A BLL
   transformer function catches incoming raw JSON logs and normalizes
   severity mappings (e.g., transforming a vendor's "CRITICAL"
   string into a standardized integer $4$) so the Correlation Engine can
   perform mathematical comparisons.
- **ORM
   to DTO Serialization:** In the database, an Incident is stored
   relationally across multiple PostgreSQL tables (Incidents, Attached
   Alerts, Audit Logs) using Foreign Keys. When the Analyst Dashboard
   requests incident details, the BLL uses Object-Relational Mapping
   (SQLAlchemy) to gather the scattered data and transforms it into a single,
   cohesive Data Transfer Object (a nested JSON response). The React UI
   simply loops through this JSON to render its tables, completely blind to
   the underlying SQL structure.
