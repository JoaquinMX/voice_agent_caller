# System Architecture Overview

## Component Map
- **Telephony Gateway (FastAPI + Twilio Voice)** – Handles PSTN ingress/egress, normalizes webhooks, streams audio through WebSockets, and enforces compliance prompts for Mexican calls.
- **Conversation Orchestrator (FastAPI)** – Maintains dialogue state, coordinates between LLM reasoning (OpenAI GPT-4o) and deterministic flows, and handles Spanish SSML generation.
- **Session Store (Redis + Postgres)** – Redis caches active turn-by-turn context while Postgres stores long-lived transcripts for analytics.
- **Speech Services** – Integrates Amazon Transcribe Streaming for low-latency transcription and Amazon Polly Neural for natural Spanish voices. Audio is piped through the telephony gateway.
- **Backend API (FastAPI + Postgres)** – Persists contacts, call outcomes, transcripts, and integrates with CRM/ERP connectors through REST/GraphQL clients.
- **Knowledge Base (Qdrant + Postgres)** – Hybrid retrieval of factual data with vector and structured storage for RAG.
- **Asynchronous Tasks (Celery + Redis)** – Final transcription cleanup, analytics aggregation, CRM synchronization.
- **Observability (OpenTelemetry + Prometheus + Grafana)** – Distributed traces, metrics, and dashboards for SLA enforcement.

## Data Flow Summary
1. Outbound dial initiated from campaign scheduler triggers Twilio REST API, connecting to telephony gateway.
2. Gateway streams audio to Amazon Transcribe; transcripts are ingested by the conversation orchestrator via Redis pub/sub.
3. Orchestrator queries Qdrant/Postgres for context, crafts prompts for GPT-4o, and returns Spanish responses with SSML cues.
4. Amazon Polly synthesizes speech; telephony gateway feeds audio back to Twilio's <Play> or `<Stream>` instructions.
5. Backend API logs structured conversation data, stores audio/transcripts in object storage (S3-compatible), and issues webhooks to downstream systems.
6. Celery workers process follow-up tasks and emit metrics to Prometheus via OpenTelemetry exporters.

### Dialogue Management
- Slot-filling pipeline gathers `customer_name`, `intent`, and `callback_number` before escalating to LLM reasoning.
- GPT-4o mini model produces empathetic Spanish responses using gathered slots as context, returning SSML hints for the telephony gateway.
- Transcript segments are persisted after each turn for QA and retrieval workflows.

## Scaling Considerations
- Stateless FastAPI services packaged in containers; orchestrated via Kubernetes with HPA based on CPU and queue depth.
- Redis and Postgres deployed as managed services (e.g., AWS ElastiCache and RDS) for high availability.
- Media streaming separated into dedicated pods with autoscaling to manage bandwidth-intensive workloads.
- Multi-region Twilio routing with failover DID numbers to comply with Mexican latency and redundancy requirements.

## Security & Compliance
- Secrets managed through AWS Secrets Manager with per-service IAM roles.
- TLS everywhere; webhook signature validation for Twilio.
- PII encrypted at rest (Postgres pgcrypto) and redacted in logs via OpenTelemetry processors.
- Data residency respected by storing call data in compliant regions (Mexico/US).
