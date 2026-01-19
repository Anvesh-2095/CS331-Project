# SOAR System Architecture

This document describes the high-level architecture of the SOAR platform.

The system follows a modular design consisting of alert ingestion, normalization,
correlation, incident management, playbook execution, response actuation, and
notification components. Each module operates independently and communicates
through well-defined interfaces to ensure scalability, reliability, and ease of
maintenance.

Detailed module responsibilities and interaction flows will be expanded as the
implementation progresses.



### in microservices style, the following services will be implemented

1. service to read notifications / alerts and pass them to brain
2. brain, actual logic will be written here
3. playbook, which will try to shrug off the attack / alert
4. a notification service used when SOAR platform cannot solve the problem
5. a artifact recording service which sits between controller and notification service

###### the following services will also be needed or simulated

1. a simulation of alert
2. a simulation of actuators - planning to make it synchronous to playbook service, so we can define outcome on our own while testing
