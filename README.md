# CI/CD Microservices (Python)

A set of FastAPI microservices — user, course, and notification services, built with automated testing and a continuous integration pipeline via GitHub Actions.

## What it does

Rather than one monolithic application, this project splits functionality across independent services that each handle a single responsibility:

- **User service** — user accounts and related data
- **Course service** — course records and management
- **Notification service** — handling notifications between services

Each service is built with FastAPI and has its own pytest test suite. On every push, GitHub Actions automatically installs dependencies and runs the full test suite — catching broken code before it's merged rather than relying on manual testing.

## Tech stack

- **Python / FastAPI** — each microservice's REST API
- **pytest** — automated test suites
- **GitHub Actions** — CI pipeline (install - test - report)


## CI pipeline

Every push triggers a GitHub Actions workflow that:
1. Spins up a clean Python environment
2. Installs dependencies
3. Runs the pytest suite
4. Reports pass/fail status on the commit/PR

This means broken code is caught automatically rather than discovered after deployment.

## Why microservices

Building this as separate services was a deliberate choice to practice service isolation, each service can be developed, tested, and in principle deployed independently, which mirrors how backend teams structure larger systems in production.

## Related project

I also built a second CI/CD pipeline project in Java, covering the same core ideas in a different language and framework.

## What I'd improve with more time

- Add integration tests covering service to service communication, not just unit tests within each service
- Containerise each service with Docker and add a docker-compose setup for running the full system locally
- Extend the pipeline to include automated deployment (CD), not just CI

## Project background

Built as part of my Continuous Integration and Continuous Delivery module during my BEng (Hons) in Software and Electronic Engineering, to get hands on practice with the testing and automation practices used in professional software teams.
