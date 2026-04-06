# Assignment 8: Data Access Layer (DAL) and System Testing

**Course:** CS 331 (Software Engineering Lab)

**Project:** Security Orchestration, Automation, and Response (SOAR) Platform

---

## Part A: Data Access Layer (DAL) Implementation \[20 Marks]

The Data Access Layer (DAL) for this SOAR platform was implemented using **SQLAlchemy**, a Python Object-Relational Mapper (ORM), communicating with a **PostgreSQL** database. This architecture successfully abstracts the application logic from the underlying SQL queries.

### 1. Database Connection and Session Management

The DAL core is managed in `database.py`. It utilizes a connection pool and session factory to securely manage database transactions across all microservices.

* **Engine Configuration:** Connects to PostgreSQL via `psycopg2`.

* **Session Management:** Uses `sessionmaker` to generate isolated, thread-safe database sessions for each API request using FastAPI's dependency injection (`Depends(get\_db)`).

### 2. Database Schemas and Models

The database schemas were created using SQLAlchemy Declarative Base classes (`models.py`). This allows the application to define tables as Python objects.

Key tables implemented in the DAL include:

* **`users` (Auth Service):** Stores analyst and admin credentials using `UUID` primary keys, securely hashed passwords (bcrypt), and Enum role-based access controls.

* **`refresh\_tokens` (Auth Service):** Manages sliding session cryptography and token revocation mapping.

* **`security\_alerts` (Ingestion Service):** Stores raw telemetry from external network tools, mapping string severities to normalized integers.

* **`incidents` (Correlation Service):** Acts as the parent table in a One-to-Many relationship with `security\_alerts`, grouping correlated events together for analyst review.

---

## Part B: Software Testing (White Box \& Black Box) \[20 Marks]

Testing was automated using the **Pytest** framework and FastAPI's `TestClient`. To ensure tests did not corrupt production data, the testing suite was configured to dynamically generate an isolated, in-memory **SQLite** database (`sqlite:///:memory:`) using a `StaticPool`.

### Test Case 1: Internal Business Logic (White Box Testing)

* **Module Tested:** Correlation Engine (`evaluate\_alert\_rules` function).

* **Methodology:** White Box (Branch Coverage).

* **Description:** This test evaluates the internal logic paths of the correlation engine. Because we know the internal code requires exactly 3 alerts to trigger an incident, we use the DAL to manually inject 3 mock alerts directly into the database, trigger the Python function, and verify that the internal `Incident` object was successfully instantiated with a `High` severity level.

* **Result:** PASSED.

### Test Case 2: Endpoint Validation (Black Box Testing)

* **Module Tested:** Authentication API (`/api/v1/auth/login`).

* **Methodology:** Black Box API Testing.

* **Description:** This test evaluates the system strictly from the outside, exactly as an end-user or frontend client would. The tester has no knowledge of the internal Python routing or SQLAlchemy database queries. The test sends a JSON payload containing a valid email but an invalid password to the endpoint. It expects the system to reject the input and return a specific external output: an HTTP `401 Unauthorized` status code with the detail "Incorrect email or password".

* **Result:** PASSED.

### Test Case 3: Data Transformation (White Box Testing)

* **Module Tested:** Ingestion Service (`normalize\_severity` function).

* **Methodology:** White Box (Unit Testing).

* **Description:** Tests the internal BLL transformation logic to ensure string inputs from external security tools (e.g., "fatal", "INFO") are correctly transformed into integers (e.g., 4, 1) before hitting the DAL.

* **Result:** PASSED.

### Test Case 4: Sliding Session Cryptography (White Box Testing)

* **Module Tested:** Authentication Service (`refresh\_session` function).

* **Methodology:** White Box (Integration Testing).

* **Description:** Tests the internal security mechanisms of the JWT token generation. It simulates a time delay using `time.sleep(1)` to ensure the cryptographic algorithms generate a mathematically unique JWT token based on the UNIX timestamp, verifying that the new token successfully bypasses the database `UNIQUE` constraints.

* **Result:** PASSED.
