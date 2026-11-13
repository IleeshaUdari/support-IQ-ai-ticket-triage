# SupportIQ AI — System Architecture

## 1. Overview

SupportIQ AI is an AI-assisted customer support ticket triage system. It classifies incoming support messages, recommends priority and routing, and escalates uncertain or sensitive decisions for human review.

The project demonstrates a complete applied machine learning workflow, from synthetic data preparation and model training to API serving, persistent storage, operational monitoring, and human oversight.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Operations interface | Streamlit |
| Backend API | FastAPI, Pydantic |
| Machine learning | scikit-learn |
| Text representation | TF-IDF |
| Classification model | Logistic Regression |
| Database | SQLite |
| Model serialization | joblib |
| Automated testing | pytest |
| Containerization | Docker Compose |
| Continuous integration | GitHub Actions |

## 3. System Components

### Streamlit Dashboard

Provides ticket monitoring, filtering, AI confidence inspection, human review workflows, and review history.

The dashboard communicates with the backend through HTTP APIs. It does not access the SQLite database directly.

### FastAPI Backend

Validates incoming requests, executes AI-assisted ticket triage, manages ticket records, and exposes review endpoints.

### Classification Model

Transforms support messages into TF-IDF features and predicts a ticket category using a trained Logistic Regression classifier.

### Decision Engine

Combines the classifier output with deterministic business rules to recommend priority, assigned team, and whether human review is required.

### SQLite Database

Stores support tickets, AI predictions, and review history. The database supports auditing of human corrections.

## 4. Ticket Processing Workflow

1. A user submits a support message.
2. FastAPI validates the request.
3. The trained classifier predicts the ticket category and produces a model score.
4. The decision engine applies priority and escalation rules.
5. The backend stores the ticket and AI prediction.
6. The dashboard displays the ticket and its recommended decision.
7. A human reviewer can confirm or correct the decision.
8. The system records the review history.

## 5. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health status |
| POST | `/api/v1/tickets` | Create and classify ticket |
| GET | `/api/v1/tickets` | List tickets |
| GET | `/api/v1/tickets/{ticket_id}` | Retrieve ticket |
| PATCH | `/api/v1/tickets/{ticket_id}/review` | Apply human review |
| GET | `/api/v1/tickets/{ticket_id}/reviews` | Retrieve review history |

## 6. Human-in-the-Loop Design

SupportIQ does not treat every model prediction as automatically reliable.

Low-confidence predictions and tickets matching sensitive escalation rules are flagged for human review.

Reviewers can correct category, priority, and status. These actions are recorded separately from the original AI prediction.

## 7. Model Evaluation

The initial classifier was evaluated using a held-out portion of a synthetic support-ticket dataset.

The original evaluation reported perfect classification metrics on that synthetic test set. These results do not establish performance on real customer messages because the dataset is small and template-based.

Before production use, the model requires evaluation on representative, independently labeled real-world data, calibration analysis, drift monitoring, and review of false negatives in escalation decisions.

## 8. Security and Limitations

The current implementation is a portfolio MVP, not a fully secured multi-user production system.

Additional requirements for real deployment include authentication, role-based authorization, HTTPS, secret management, rate limiting, database backups, privacy controls, data retention policies, and operational monitoring.

SQLite is appropriate for this small local demonstration. PostgreSQL would be a better choice for larger multi-user deployments.

## 9. Deployment Architecture

Docker Compose runs two application services: FastAPI and Streamlit.

The dashboard communicates with the API through the internal Docker network. The API uses the trained model and persistent SQLite storage.

The deployment is intended for local demonstration and development.

## 10. Future Improvements

- Representative real-world training and evaluation data
- Model confidence calibration
- PostgreSQL migration
- User authentication and RBAC
- Structured application logging
- Model and dataset version tracking
- Monitoring for drift and prediction quality
- Automated retraining with approval gates
- Production-grade deployment and secrets management
