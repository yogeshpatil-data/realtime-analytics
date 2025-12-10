[readme.md](https://github.com/user-attachments/files/23916828/readme.md)
# Real-Time Clickstream Data Platform on AWS
**Kafka (Amazon MSK) · Spark Structured Streaming · Amazon S3 · Snowflake · CI/CD**

---
## 1. Purpose of This Project

This project implements a **production-style real-time data platform** for processing clickstream events using **distributed streaming primitives** on AWS.

The intent is not to demonstrate tool usage superficially, but to demonstrate:
- correctness guarantees
- fault tolerance and recovery
- system-level design clarity
- production-aligned engineering discipline

---

## 2. Problem Statement

User interaction (clickstream) events arrive:
- continuously
- at high volume
- potentially out of order
- without a predefined end

The platform must:
- ingest events durably
- process them incrementally
- tolerate partial and full system failures
- avoid duplicate results
- scale horizontally
- expose analytics-ready datasets

---

## 3. Design Requirements

### 3.1 Correctness
- Exactly-once processing semantics
- Order preservation within Kafka partitions
- Deterministic recovery after failure

### 3.2 Reliability
- No data loss on failures
- Replay capability from raw storage
- Durable state management

### 3.3 Operability
- Clear operational boundaries
- Observable streaming behavior
- Controlled deployment and execution

### 3.4 Engineering Discipline
- Infrastructure and application separation
- Reproducible environments
- CI/CD-driven deployments

---

## 4. High-Level Architecture

```
Event Producer
     |
     v
Kafka (Amazon MSK)
     |
     v
Spark Structured Streaming (EMR)
     |
     +-------------------+
     |                   |
     v                   v
S3 Raw Layer        S3 Curated Layer
     |
     v
Snowflake Analytics
```

---

## 5. Technology Responsibilities

| Layer | Technology | Responsibility |
|------|-----------|---------------|
| Ingestion | Kafka (MSK) | Durable distributed event log |
| Processing | Spark Structured Streaming | Stateful stream processing |
| Raw Storage | Amazon S3 | Immutable event persistence |
| Curated Storage | Amazon S3 | Optimized analytical datasets |
| Analytics | Snowflake | Query and BI access |
| Automation | GitHub Actions | CI/CD workflows |

Each layer is responsible for a **single concern**.

---

## 6. End-to-End Data Flow

### 6.1 Event Production

Clickstream events are generated as structured JSON messages with a versioned schema.

Producer characteristics:
- idempotent writes
- acknowledgments from all replicas
- no dependency on downstream systems

---

### 6.2 Kafka Ingestion (Amazon MSK)

Kafka acts as a **durable, ordered, partitioned log**.

Key properties:
- Topics are partitioned for parallelism
- Offsets are monotonically increasing per partition
- Replication provides broker-level fault tolerance

Kafka does not track consumers. It only stores data.

---

### 6.3 Spark Structured Streaming Consumption

Spark treats Kafka as an **unbounded data source**.

For every trigger interval:

1. Read last committed offsets from checkpoint
2. Fetch latest offsets from Kafka
3. Define micro-batch boundaries
4. Execute the Spark DAG
5. Write outputs to sinks
6. Atomically commit offsets and state

If a failure occurs before step 6, the entire batch is reprocessed.

---

### 6.4 Checkpointing and State Management

Checkpoints store:
- committed Kafka offsets
- streaming query metadata
- state store references

Checkpoint location:
```
s3://clickstream-checkpoints/spark/job=clickstream
```

Checkpoint integrity is mandatory for exactly-once guarantees.

---

### 6.5 Raw Data Layer (S3)

Raw events are persisted exactly as received.

Characteristics:
- append-only
- immutable
- partitioned by ingestion date

Use cases:
- reprocessing and replay
- auditing
- debugging and validation

---

### 6.6 Stream Processing Logic

Spark applies:
- schema enforcement
- watermarking for late event handling
- session windows
- aggregations

Streaming state is:
- maintained in-memory for active batches
- checkpointed to S3 for recovery

---

### 6.7 Curated Data Layer (S3)

Curated datasets are:
- cleaned and validated
- aggregated for analytics use cases
- partitioned for query efficiency

This layer represents **analytics-ready data**.

---

### 6.8 Analytics Consumption (Snowflake)

Snowflake ingests curated data via:
- external tables, or
- scheduled ingestion pipelines

Snowflake serves strictly as the **analytics and BI layer**.

---

## 7. Exactly-Once Semantics

Exactly-once guarantees are achieved through coordination of:
- Kafka offset tracking
- Spark checkpointing
- idempotent writes to S3
- transactional or merge-based Snowflake ingestion

No individual system provides exactly-once guarantees independently.

---

## 8. Failure Handling Model

| Failure Scenario | System Behavior |
|-----------------|-----------------|
| Executor failure | Task retried |
| Driver failure | Query recovered from checkpoint |
| Kafka outage | Streaming pauses and resumes |
| Partial sink write | Batch re-executed |
| Duplicate events | Resolved through state management |

Failures are expected and explicitly handled.

---

## 9. CI/CD Strategy

### 9.1 Continuous Integration (CI)

Triggered on pull requests and feature branches:
- code linting
- unit tests
- schema validation
- Docker image builds

---

### 9.2 Continuous Deployment (CD)

Triggered on merge to `main`:
1. Build versioned artifacts
2. Push Docker images to Amazon ECR
3. Upload Spark jobs to Amazon S3
4. Prepare EMR execution steps

Execution remains manual to retain operational control.

---

## 10. Environment Strategy

### Python Virtual Environment
- Local development and testing
- IDE integration
- Dependency isolation

### Docker
- Runtime consistency
- CI environment parity
- Linux-native execution

Spark is not executed locally on Windows.

---

## 11. Repository Organization

```
infra/     → Infrastructure definitions (IAM, S3, MSK, EMR)
spark/     → Spark streaming jobs and shared logic
producers/ → Kafka event producers
docker/    → Runtime Docker images
ci-cd/     → CI/CD workflows and scripts
configs/   → Environment-specific configurations
```

Directory boundaries reflect production ownership and responsibilities.

---

## 12. Operational Boundaries

This project intentionally:
- avoids managed streaming abstractions
- exposes Spark internals and failure modes
- prioritizes correctness over convenience
- mirrors real-world production constraints

---

## 13. Learning Outcomes

After completing this project, you should be able to clearly explain:
- Kafka partition and offset semantics
- Spark streaming recovery mechanisms
- State and checkpoint durability
- Cloud-native failure scenarios
- CI/CD for data platforms
- Separation of processing and serving layers

---

## 14. Execution Order

1. IAM configuration
2. S3 bucket setup
3. CI/CD pipeline
4. Kafka (MSK) provisioning
5. Spark (EMR) deployment
6. Snowflake integration

Deviating from this order will compromise system guarantees.

---

## 15. Next Step

Begin with **IAM role and policy design**, followed by S3 bucket layout.

---

✅ This README serves as the **design contract** for the project.  
All implementations must conform to the principles defined here.
