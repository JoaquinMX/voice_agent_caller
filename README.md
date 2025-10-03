# Voice Agent Caller Platform

A modular, cloud-native platform for running natural-language, Spanish-speaking voice agents that can place and receive phone calls in Mexico, capture structured information, and integrate with enterprise systems.

## Why This Project Exists
Businesses operating in Mexico need automated phone agents that sound natural in Spanish, comply with local telecom regulations, and can reliably gather customer information. This repository provides the baseline implementation and scaffolding for such a platform.

## High-Level Architecture
The system is composed of independently deployable FastAPI services, shared infrastructure, and managed cloud offerings:

| Layer | Responsibilities | Technologies |
| --- | --- | --- |
| Telephony Edge | Terminate Mexican PSTN calls, validate Twilio webhooks, stream media, ensure compliance prompts. | **Twilio Programmable Voice**, FastAPI, Redis pub/sub |
| Speech & Voice | Real-time speech recognition and neural TTS for natural Mexican Spanish. | **Amazon Transcribe Streaming**, **Amazon Polly Neural**, WebSocket audio gateway |
| Conversation Brain | Maintain dialogue state, orchestrate LLM reasoning, fill slots, perform retrieval. | FastAPI, **OpenAI GPT-4o**, Redis, Qdrant vector store, PostgreSQL |
| Backend APIs | Persist contacts, call outcomes, transcripts, CRM integrations. | FastAPI, **PostgreSQL** (with pgvector), SQLAlchemy |
| Async Processing | Background tasks for analytics, QA, CRM sync. | **Celery**, Redis, S3-compatible object storage |
| Observability & Ops | Unified logging, metrics, and traces; alerting and QA review. | **OpenTelemetry**, Prometheus, Grafana, Loki |
| Infrastructure | Provisioning, secrets, deployment automation. | Terraform, Docker, Kubernetes (future), GitHub Actions |

A more detailed architecture description is available in [`docs/architecture.md`](docs/architecture.md).

## Repository Layout
```
├── docker-compose.yml          # Local orchestration of core services and dependencies
├── services/
│   ├── telephony_gateway/      # Twilio webhooks and audio streaming bridge
│   ├── conversation_orchestrator/  # Dialogue manager + LLM integration surface
│   └── backend_api/            # Persistence, CRM connectors, reporting APIs
├── docs/
│   └── architecture.md         # Extended architecture documentation
├── infra/
│   └── terraform/              # Terraform modules (placeholders for future build-out)
├── pyproject.toml              # Shared tooling configuration (ruff, pytest)
├── Makefile                    # Developer quality-of-life commands
└── .env.example                # Sample environment variables required to run the stack
```

## Local Development
1. **Install dependencies** (Python 3.11+):
   ```bash
   python -m pip install --upgrade pip
   make deps
   ```
2. **Start the stack**:
   ```bash
   docker compose up --build
   ```
3. **Verify health checks**:
   - Telephony Gateway: <http://localhost:8080/healthz>
   - Conversation Orchestrator: <http://localhost:8081/healthz>
   - Backend API: <http://localhost:8082/healthz>
4. **Run quality checks**:
   ```bash
   make lint
   make format
   ```

> **Note:** Replace secrets in `.env.example` before deploying to any shared environment. Use AWS Secrets Manager or HashiCorp Vault in production.
> Ensure valid AWS credentials are exported locally so the telephony gateway can reach Amazon Transcribe and Polly during development.

## Implementation Roadmap
The delivery plan follows five incremental phases to ensure production readiness:

### Phase 0 – Foundations (Current)
- Bootstrap FastAPI microservices with Docker builds and shared tooling.
- Establish code quality workflow (ruff, pytest) and environment templates.
- Author architecture and operational documentation.

### Phase 1 – Telephony MVP
- Configure Twilio numbers for Mexican routes and SIP trunks.
- Implement webhook signature validation, call state persistence, and WebSocket media gateway.
- Integrate Amazon Transcribe streaming pipeline for live transcription.

### Phase 2 – Conversational Core (Current)
- Introduce dialogue state store in Redis and session transcript persistence in Postgres/S3.
- Connect OpenAI GPT-4o for bilingual reasoning; add deterministic slot-filling for compliance flows.
- Generate Amazon Polly neural Spanish speech with SSML for playback through Twilio `<Stream>` responses.

**Delivered in this repository:**
- Redis-backed conversation state service with slot-filling dialogue manager and GPT-4o fallback for nuanced Spanish replies.
- Backend persistence for call sessions and transcript segments, enabling analytics and QA review.
- Telephony gateway integration with Amazon Transcribe streaming and Polly speech synthesis (with Redis caching) for low-latency natural responses.

### Phase 3 – Retrieval & Integrations (Next)
- Stand up Qdrant with pgvector-backed metadata syncing for knowledge grounding (FAQs, CRM data).
- Build CRM connector abstractions (Salesforce, HubSpot) and configure secure credential storage.
- Implement Celery workers for post-call analytics, QA scoring, and downstream notifications.

### Phase 4 – Experience & Tooling
- Develop supervisor dashboard (Next.js + Grafana panels) with live transcripts and whisper monitoring.
- Add consent management, call disposition workflows, and escalation triggers.
- Automate regression testing (Pytest + pytest-asyncio) and load testing (k6) in CI/CD.

### Phase 5 – Hardening & Scale
- Deploy to Kubernetes with HPA, PodDisruptionBudgets, and multi-region Twilio failover.
- Integrate OpenTelemetry collectors, Prometheus, Grafana, and Loki for full observability.
- Conduct security reviews, penetration testing, and finalize compliance (privacy notices, data retention).

## Key Design Decisions
- **FastAPI** is used for all Python services to keep the stack consistent and lightweight.
- **Twilio Programmable Voice** offers reliable PSTN coverage in Mexico and mature webhook support.
- **Amazon Transcribe Streaming** and **Amazon Polly Neural** provide industry-leading quality for Spanish speech interfaces tailored to Mexican Spanish.
- **OpenAI GPT-4o** is leveraged for high-quality bilingual reasoning with support for function-calling.
- **PostgreSQL + Qdrant** give structured + semantic storage for conversational memory and RAG.
- **Redis** acts as both the transient state store and Celery broker, simplifying early deployments.
- **Docker Compose** accelerates local development; production will target Terraform-provisioned Kubernetes clusters.

## Next Steps
- Flesh out webhook handlers with Twilio signature validation and media streaming bridge.
- Implement Redis-backed session manager and Celery worker scaffolding.
- Add integration tests covering telephony event ingestion and conversation orchestration pathways.
- Provide Terraform modules for core infrastructure (VPC, EKS/GKE, secrets, observability stack).

## Contributing
1. Create a feature branch from `main`.
2. Implement changes with tests and documentation updates.
3. Run `make lint` and `make format` before submitting a PR.
4. Open a GitHub Pull Request describing your changes and referencing relevant Jira tickets.

## License
Distributed under the MIT License. See `LICENSE` (to be added) for more information.
