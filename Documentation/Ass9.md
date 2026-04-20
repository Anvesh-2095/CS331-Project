### Q1. a) Test Plan for SOAR Platform

**Objective of Testing**

To systematically verify that the Security Orchestration, Automation, and Response (SOAR) microservices communicate securely, process data accurately, and enforce strict Role-Based Access Control (RBAC).

**Scope**

Testing will cover the core backend microservices:

- Authentication Service (JWT generation, sliding sessions, role validation).

- Ingestion Service (Data normalization, payload validation).

- Correlation Engine (Business logic, incident generation thresholds).

- *Out of Scope:* Third-party external tools (e.g., actual CrowdStrike or Palo Alto APIs).

**Types of Testing**

- **Unit Testing (White Box):** Validating internal logic branches (e.g., threshold triggers) using isolated, in-memory databases.

- **API Testing (Black Box):** Validating endpoint responses, status codes, and Pydantic schema enforcement from an external client perspective.

- **Integration Testing:** Verifying message passing over the RabbitMQ message broker.

**Tools**

- **Testing Framework:** `pytest`

- **HTTP Client:** FastAPI `TestClient` (`httpx`)

- **Mocking:** Python `unittest.mock` (`@patch`) for external RabbitMQ/SMTP dependencies.

- **Database:** `SQLAlchemy` with an in-memory `SQLite` StaticPool for isolated test runs.

**Entry and Exit Criteria**

- **Entry Criteria:** Source code must compile without syntax errors, and the local virtual environment dependencies must be fully installed.

- **Exit Criteria:** 100% of defined Unit and API tests must pass, and critical security defects must be resolved before deployment.

---

### Q1. b) Test Cases for Authentication Module

| **ID**    | **Test Scenario / Description** | **Input Data**                              | **Expected Output**                                     | **Actual Output**              | **Status** |
| --------- | ------------------------------- | ------------------------------------------- | ------------------------------------------------------- | ------------------------------ | ---------- |
| **TC-01** | Valid Login (Black Box)         | Correct `email` and `password`              | HTTP 200, returns `access_token` and `refresh_token`    | HTTP 200, Tokens received      | Pass       |
| **TC-02** | Invalid Password (Black Box)    | Correct `email`, wrong `password`           | HTTP 401 Unauthorized, "Incorrect email or password"    | HTTP 401 Unauthorized          | Pass       |
| **TC-03** | Missing Payload Fields          | JSON missing the `email` key                | HTTP 422 Unprocessable Entity                           | HTTP 422 Unprocessable Entity  | Pass       |
| **TC-04** | Sliding Session Refresh         | Valid `refresh_token` string                | HTTP 200, returns brand new `access_token`              | HTTP 200, New token received   | Pass       |
| **TC-05** | Expired Refresh Token           | `refresh_token` past expiration date        | HTTP 401 Unauthorized, "Token expired"                  | HTTP 401 Unauthorized          | Pass       |
| **TC-06** | Invalid JWT Signature           | Tampered/Fake `access_token` string         | HTTP 401 Unauthorized, "Could not validate credentials" | HTTP 401 Unauthorized          | Pass       |
| **TC-07** | Database Transaction Failure    | Valid login, but DB connection drops        | HTTP 500 Internal Server Error                          | HTTP 500 Internal Server Error | Pass       |
| **TC-08** | Case-Insensitive Email Login    | Email capitalized (e.g., `Test@soar.local`) | HTTP 200, normal login success                          | HTTP 200, Tokens received      | Pass       |

---

### Q2. b) Defect Analysis

**Defect 1: Testing Database Dialect Crash**

- **Bug ID:** BUG-001

- **Description:** The testing framework failed to create the temporary database tables, throwing a `sqlite3.OperationalError: no such table: users`.

- **Steps to reproduce:** Run `pytest` configured with an in-memory SQLite database against SQLAlchemy models using PostgreSQL-specific data types.

- **Expected vs Actual Result:** Expected tables to build successfully. Actually resulted in an immediate crash during the test setup phase.

- **Severity:** High (Blocked all testing).

- **Suggested Fix:** Swapped `from sqlalchemy.dialects.postgresql import UUID` to the generic `from sqlalchemy import UUID` in `models.py` to allow cross-database compatibility.

**Defect 2: String/UUID Type Mismatch in DAL**

- **Bug ID:** BUG-002

- **Description:** Attempting to refresh a session resulted in a 500 Server Error: `AttributeError: 'str' object has no attribute 'hex'`.

- **Steps to reproduce:** Execute a POST request to `/api/v1/auth/refresh` with a valid refresh token.

- **Expected vs Actual Result:** Expected a new session token. Actual result was a crash during the database lookup.

- **Severity:** Medium (Broke session persistence).

- **Suggested Fix:** The JWT payload extracts the `user_id` as a string. Cast the string back to a Python UUID object `uuid.UUID(user_id)` before passing it to the SQLAlchemy query filter.

**Defect 3: Cryptographic Integrity Constraint Failure**

- **Bug ID:** BUG-003

- **Description:** Fast automated testing caused a `UNIQUE constraint failed: refresh_tokens.token_string` database error.

- **Steps to reproduce:** Run the login and refresh endpoints within the same chronological second using automated unit tests.

- **Expected vs Actual Result:** Expected the refresh token to be saved to the database. Actual result was a rejection due to a duplicate token string.

- **Severity:** Low (Only occurs in automated testing, not human use).

- **Suggested Fix:** Introduced a `time.sleep(1)` artificial delay in the test script to allow the UNIX timestamp to increment, ensuring the cryptographic generation of a unique JWT signature.
