# SupportIQ AI

**AI-Powered Customer Support Ticket Triage with Human-in-the-Loop Review**

SupportIQ AI is an end-to-end machine learning application that helps support teams classify customer tickets, prioritize issues, route requests, and review uncertain AI decisions.

Built with Python, FastAPI, scikit-learn, Streamlit, SQLite, Docker, and GitHub Actions.

## Key Features

- Automated ticket category classification
- Rule-based priority recommendation
- Team routing recommendations
- Confidence-aware human escalation
- Persistent ticket and prediction records
- Human review and audit history
- Interactive operations dashboard
- REST API with OpenAPI documentation
- Automated tests and containerized deployment

## Architecture

Streamlit Dashboard → FastAPI Backend → ML Classifier + Decision Engine → SQLite Database

The classifier uses TF-IDF and Logistic Regression. The decision engine combines predictions with business rules and review thresholds.

## Technology Stack

Python 3.13 · FastAPI · scikit-learn · Streamlit · SQLite · pytest · Docker Compose · GitHub Actions

## Getting Started

### Requirements

- Docker Desktop with Linux container support
- Docker Compose

### Run with Docker

```bash
docker compose build
docker compose up -d
```

Open the dashboard at `http://localhost:8501` and API documentation at `http://localhost:8000/docs`.

### Run Tests

```bash
python -m pytest tests/ -v
```

Install the dependencies from `requirements.txt` before running tests locally.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Check application health |
| POST | `/api/v1/tickets` | Classify a new ticket |
| GET | `/api/v1/tickets` | List tickets |
| GET | `/api/v1/tickets/{ticket_id}` | View ticket details |
| PATCH | `/api/v1/tickets/{ticket_id}/review` | Record human review |
| GET | `/api/v1/tickets/{ticket_id}/reviews` | View review history |

## Machine Learning

The initial model uses TF-IDF text features and Logistic Regression.

The training dataset contains synthetic customer support messages across billing, delivery, account, and technical categories.

The reported evaluation results are based on synthetic data and should not be interpreted as production accuracy.

## Engineering Highlights

- Separation of model inference and business rules
- Human oversight for uncertain decisions
- Persistent prediction and review history
- API-driven dashboard architecture
- Automated backend and client tests
- Reproducible container build configuration

## Screenshots

Add screenshots of:

1. Operations Overview
2. Ticket Queue
3. AI Insights
4. Human Review
5. Review History

## Limitations

This is a portfolio demonstration, not a production-ready customer support platform.

Authentication, authorization, privacy controls, model monitoring, representative evaluation data, and production infrastructure are future improvements.

## Architecture Documentation

See `docs/architecture.md` for the component design, data flow, decision workflow, and engineering tradeoffs.

## Author

AI Engineering Portfolio Project
