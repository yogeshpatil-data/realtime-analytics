


<img width="755" height="535" alt="Project_Diagram" src="https://github.com/user-attachments/assets/e59c6b02-c36c-42f8-8cb8-590af52c82a5" />




# Real-Time Analytics Pipeline  
## Apache Kafka + Spark Structured Streaming (Dockerized)

---

## 1. Project Overview

This project implements a **real-time streaming data pipeline** using:

- Apache Kafka (event streaming)
- Apache Spark Structured Streaming (stream processing)
- Docker & Docker Compose (containerized deployment)
- Python-based ingestion service

The pipeline ingests **live Wikimedia recent-change events** (via Server-Sent Events), publishes them to Kafka, and consumes them using Spark Structured Streaming. All core components run as **Docker containers** on a shared Docker network.

The focus of this project is not only to "make it work", but to demonstrate:

- Realistic streaming architecture design
- Kafka configuration inside Docker (with proper `advertised.listeners`)
- Spark Structured Streaming execution behavior
- Classpath & dependency management for Spark + Kafka
- Debugging real-world runtime failures
- Clean, reproducible setup via Docker

This project can be used as:

- A learning resource for real-time data engineering
- A portfolio / interview discussion project
- A base for extending to Delta Lake / S3 / Data Lakehouse patterns

---

## 2. Architecture

### 2.1 Logical Data Flow

    Wikimedia RecentChange Stream (HTTP SSE)
            |
            v
    Python Ingestion Service (Kafka Producer)
            |
            v
    Kafka Topic: raw_wikimedia_events
            |
            v
    Spark Structured Streaming (Kafka Source)
            |
            v
    Streaming Sink (Console for now)

### 2.2 Physical Deployment (Docker)

All services run inside one Docker host:

    Docker Host
    ├── Zookeeper Container
    ├── Kafka Container
    ├── Ingestion Service Container (Python)
    └── Spark Streaming Container (Spark 3.5.1)

All containers are attached to a common Docker network:

- Network name: `realtime-net`
- Network type: external bridge network

Inside this network:

- Kafka is reachable as `kafka:9092`
- Ingestion service and Spark both use `kafka:9092` as bootstrap

---

## 3. Repository Structure

Root layout:

    realtime-analytics/
    ├── docker/
    │   ├── kafka/
    │   │   └── docker-compose.yml
    │   └── ingestion-spark-compose.yml
    │
    ├── ingestion/
    │   └── wikimedia_to_kafka.py
    │
    ├── spark/
    │   └── spark_streaming.py
    │
    ├── Dockerfile.ingestion
    ├── Dockerfile.spark-runner
    ├── requirements.txt
    └── README.md

**Folders / Files:**

- `docker/kafka/docker-compose.yml`  
  Docker Compose file for **Kafka** and **Zookeeper**.

- `docker/ingestion-spark-compose.yml`  
  Docker Compose file for **ingestion** and **Spark streaming** containers.

- `ingestion/wikimedia_to_kafka.py`  
  Python **producer** that reads Wikimedia SSE and publishes to Kafka.

- `spark/spark_streaming.py`  
  Spark Structured Streaming **consumer** that reads from Kafka and prints to console.

- `Dockerfile.ingestion`  
  Builds the **Python ingestion image**.

- `Dockerfile.spark-runner`  
  Builds the **Spark streaming image**, with all required Kafka-related JARs.

- `requirements.txt`  
  Python dependencies for ingestion.

---

## 4. Docker & Networking

### 4.1 External Docker Network

Create the external network used by all containers:

    docker network create realtime-net

This network is referenced by both Compose files as:

    networks:
      realtime-net:
        external: true

### 4.2 Kafka & Zookeeper Compose (docker/kafka/docker-compose.yml)

Key points:

- Uses Confluent images for Kafka and Zookeeper
- Exposes port `9092` on host
- Attaches to `realtime-net` network
- Correctly sets listeners for use inside Docker

Important environment variables:

    KAFKA_BROKER_ID=1
    KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
    KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092
    KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1

**Why `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092`?**

- Inside the Docker network, other containers reach Kafka using hostname `kafka`
- If this were set to `localhost:9092`, clients inside containers would try to reconnect to themselves, not the Kafka container
- This is a common and critical networking bug; it is correctly handled here

---

## 5. Ingestion Service (Python → Kafka)

### 5.1 Purpose

The ingestion service:

- Connects to Wikimedia's **RecentChange SSE API**
- Parses JSON events
- Publishes them into Kafka topic `raw_wikimedia_events` using `kafka-python`

### 5.2 Python Code: `ingestion/wikimedia_to_kafka.py`

Key behavior:

- Streams from:
  - `https://stream.wikimedia.org/v2/stream/recentchange`
- Uses a custom `User-Agent` header (best practice for public APIs)
- Connects to Kafka using Bootstrap servers: `kafka:9092`
- Publishes JSON messages to topic: `raw_wikimedia_events`

Key concepts:

- Filters out non-`"message"` SSE events
- Skips empty payloads
- Uses `json.loads` to deserialize event data
- Produces messages with `value_serializer` that JSON-encodes Python objects

---

## 6. Spark Streaming Service (Kafka → Spark)

### 6.1 Purpose

The Spark streaming container runs a Spark Structured Streaming job that:

- Reads from Kafka topic `raw_wikimedia_events`
- Parses the raw Kafka messages (`key`, `value`, `topic`, `partition`, `offset`)
- Prints them to console (for now)
- Uses checkpointing for reliability and restart capability

### 6.2 Streaming Job: `spark/spark_streaming.py`

Core logic:

- Creates `SparkSession` with:

    appName = "KafkaRawStreamTest"
    master = "local[*]"

- Sets Spark log level to `WARN` to reduce noise
- Reads from Kafka using:

    spark.readStream \
         .format("kafka") \
         .option("kafka.bootstrap.servers", "kafka:9092") \
         .option("subscribe", "raw_wikimedia_events") \
         .option("startingOffsets", "latest") \
         .load()

- Converts binary `key` and `value` to strings via:

    selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)", "topic", "partition", "offset")

- Writes to console:

    writeStream \
        .format("console") \
        .option("truncate", "false") \
        .option("checkpointLocation", "/tmp/spark-checkpoints/raw_wikimedia") \
        .outputMode("append") \
        .start()

- Blocks the driver with `query.awaitTermination()`

### 6.3 Checkpointing

- Checkpoint directory: `/tmp/spark-checkpoints/raw_wikimedia`
- Purpose:
  - Track Kafka offsets
  - Ensure streaming query can be restarted without reprocessing everything
  - Provide exactly-once semantics when combined with idempotent sinks (future work)

---

## 7. Docker Images

### 7.1 Ingestion Image (`Dockerfile.ingestion`)

Key steps:

- Base image: `python:3.11-slim`
- Installs minimal system packages (`ca-certificates`, `curl`, etc.)
- Sets working directory to `/app`
- Copies `requirements.txt` and installs Python dependencies:

    pip install --no-cache-dir -r requirements.txt

- Copies ingestion script:

    COPY ingestion/wikimedia_to_kafka.py /app/wikimedia_to_kafka.py

- Environment variables (optional defaults):

    KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    KAFKA_TOPIC=raw_wikimedia_events

- Entrypoint:

    CMD ["python", "/app/wikimedia_to_kafka.py"]

### 7.2 Spark Runner Image (`Dockerfile.spark-runner`)

Key steps:

- Base image: `apache/spark:3.5.1`
- Installs `curl`
- Sets `SPARK_JARS_DIR=/opt/spark/jars`
- Downloads required JARs for Kafka support into `SPARK_JARS_DIR`:

    - `spark-sql-kafka-0-10_2.12-3.5.1.jar`
    - `spark-token-provider-kafka-0-10_2.12-3.5.1.jar`
    - `kafka-clients-3.5.1.jar`
    - `commons-pool2-2.11.1.jar`

  These are needed because **Spark does not bundle Kafka connectors by default**.

- Copies streaming script:

    COPY spark/spark_streaming.py /opt/spark-app/spark_streaming.py

- Environment variables:

    KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    KAFKA_TOPIC=raw_wikimedia_events
    SPARK_CHECKPOINT_DIR=/tmp/spark-checkpoints/raw_wikimedia

- Entrypoint (full path to `spark-submit`):

    CMD ["/opt/spark/bin/spark-submit", "--master", "local[*]", "--conf", "spark.sql.shuffle.partitions=2", "/opt/spark-app/spark_streaming.py"]

**Important lesson captured in this configuration:**

- `spark-submit` is **not** on `PATH` in the base image → must use full path `/opt/spark/bin/spark-submit`
- Kafka-related JARs must be present on the Spark classpath at runtime, otherwise Spark will:
  - Start successfully
  - Fail at the first micro-batch with `ClassNotFoundException` or `NoClassDefFoundError`

This image explicitly solves those problems.

---

## 8. Docker Compose – Services

### 8.1 Kafka & Zookeeper (docker/kafka/docker-compose.yml)

Simplified description:

- `zookeeper` service:
  - Image: `confluentinc/cp-zookeeper:7.5.3`
  - Port: `2181:2181`
  - Network: `realtime-net`

- `kafka` service:
  - Image: `confluentinc/cp-kafka:7.5.3`
  - Depends on: `zookeeper`
  - Port: `9092:9092`
  - Environment:
    - `KAFKA_BROKER_ID=1`
    - `KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181`
    - `KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092`
    - `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092`
    - `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1`
  - Network: `realtime-net`

---

### 8.2 Ingestion & Spark (docker/ingestion-spark-compose.yml)

- `ingestion` service:
  - Image: `realtime_ingestion:latest`
  - Container name: `ingestion_service`
  - Restart policy: `unless-stopped`
  - Network: `realtime-net`
  - Env:
    - `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`
    - `KAFKA_TOPIC=raw_wikimedia_events`

- `spark-runner` service:
  - Image: `realtime_spark_runner:latest`
  - Container name: `spark_stream_service`
  - Restart policy: `unless-stopped`
  - Network: `realtime-net`
  - Volumes:
    - `../:/workspace/project` (optional for development)
    - `/tmp/spark-checkpoints:/tmp/spark-checkpoints`
  - Env:
    - `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`
    - `KAFKA_TOPIC=raw_wikimedia_events`

---

## 9. Step-by-Step Setup & Commands

Below is the complete set of commands used to build and run the project from scratch.

### 9.1 Prerequisites

- Docker installed
- Docker Compose (plugin or standalone)
- Basic terminal access (Linux / WSL recommended)

### 9.2 Create the external network

    docker network create realtime-net

### 9.3 Start Kafka + Zookeeper

From project root (`realtime-analytics/`):

    cd docker/kafka
    docker compose up -d

Verify containers:

    docker ps

You should see `zookeeper` and `kafka`.

### 9.4 Build the ingestion image

From project root:

    cd ~/realtime-analytics
    docker build -f Dockerfile.ingestion -t realtime_ingestion:latest .

### 9.5 Build the Spark runner image

    docker build -f Dockerfile.spark-runner -t realtime_spark_runner:latest .

This step downloads the Kafka connector JARs and bundles them into the Spark image.

### 9.6 Start ingestion service

From project root:

    docker compose -f docker/ingestion-spark-compose.yml up -d ingestion

Check logs:

    docker logs ingestion_service --tail 30

You should see logs indicating that Wikimedia ingestion has started.

### 9.7 Create Kafka topic (explicitly)

Enter Kafka container:

    docker exec -it kafka bash

Create topic:

    kafka-topics \
      --bootstrap-server kafka:9092 \
      --create \
      --topic raw_wikimedia_events \
      --partitions 3 \
      --replication-factor 1

List topics:

    kafka-topics --bootstrap-server kafka:9092 --list

Consume a few events to verify:

    kafka-console-consumer \
      --bootstrap-server kafka:9092 \
      --topic raw_wikimedia_events \
      --from-beginning \
      --max-messages 5

You should see JSON messages from Wikimedia.

### 9.8 Start Spark streaming service

From project root:

    docker compose -f docker/ingestion-spark-compose.yml up -d spark-runner

Check Spark logs:

    docker logs -f spark_stream_service

You should see:

- Spark starting (`Running Spark version 3.5.1`)
- Streaming query starting
- Batches processing with console output of Kafka messages

---

## 10. Stopping & Restarting

To stop **all** services cleanly:

    docker compose -f docker/ingestion-spark-compose.yml down
    docker compose -f docker/kafka/docker-compose.yml down

This:

- Stops and removes containers
- Preserves images
- Preserves Kafka data (unless volumes are also removed)
- Preserves Spark checkpoints

To restart everything later:

    docker compose -f docker/kafka/docker-compose.yml up -d
    docker compose -f docker/ingestion-spark-compose.yml up -d

---

## 11. Key Learnings & Design Decisions

1. **Kafka in Docker requires correct advertised listeners**

   - Using `localhost:9092` in `KAFKA_ADVERTISED_LISTENERS` breaks container-to-container communication.
   - Correct value: `PLAINTEXT://kafka:9092` (service name on Docker network).

2. **Spark startup vs streaming execution**

   - Spark can start and show UI even if Kafka dependencies are missing.
   - Real failures appear at **first micro-batch** when Kafka consumer is instantiated.
   - This leads to `ClassNotFoundException` / `NoClassDefFoundError` at runtime.

3. **Kafka connector dependencies (Spark 3.5.1)**

   Required JARs:

   - `spark-sql-kafka-0-10_2.12-3.5.1.jar`
   - `spark-token-provider-kafka-0-10_2.12-3.5.1.jar`
   - `kafka-clients-3.5.1.jar`
   - `commons-pool2-2.11.1.jar`

   Without these, Spark fails to use `format("kafka")` as a source.

4. **Checkpointing is mandatory for real streaming jobs**

   - Used to track Kafka offsets
   - Makes streaming job restartable
   - Forms the basis for exactly-once processing when combined with idempotent sinks

5. **Container lifecycle controls process lifecycle**

   - Python and Spark are not run directly on the host.
   - Their lifecycle is managed **entirely** by Docker containers and Compose files.

---

## 12. Possible Extensions

This project is designed to be a foundation you can extend in multiple directions:

- Replace console sink with:
  - Delta Lake tables
  - Parquet on local/S3
  - PostgreSQL or other analytical stores

- Add transformations:
  - Extract useful fields from Wikimedia JSON
  - Filter by namespace / user / operation
  - Aggregate edit counts over windows

- Add orchestration:
  - Use Apache Airflow or other schedulers
  - Define DAGs for starting/stopping streaming jobs

- Move to cloud:
  - Kafka → MSK / Confluent Cloud
  - Spark → EMR / Databricks
  - Keep the same logical architecture

---

## 13. Summary

This project demonstrates an end-to-end real-time analytics pipeline with:

- Kafka + Zookeeper running in Docker
- A Python ingestion service streaming real data from Wikimedia into Kafka
- A Spark Structured Streaming job consuming from Kafka, with proper dependency management
- Fully containerized deployment using Docker Compose
- Clear understanding of Spark–Kafka internals and real-world failure modes

It is suitable as:

- A learning resource
- A portfolio project
- A discussion artifact in data engineering interviews

You can now build on this foundation to explore more advanced topics such as data lakehouse design, streaming joins, stateful aggregations, and production monitoring.

---
