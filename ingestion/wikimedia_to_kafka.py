import os
import json
import logging
from kafka import KafkaProducer
from sseclient import SSEClient

# ---------------------------------------------------
# Logging configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------
WIKIMEDIA_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
)

TOPIC = os.getenv(
    "KAFKA_TOPIC", "raw_wikimedia_events"
)

HEADERS = {
    "User-Agent": "realtime-analytics-pipeline/1.0 (contact: yogesh.patil@example.com)"
}

# ---------------------------------------------------
# Kafka Producer (safe defaults)
# ---------------------------------------------------
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
    retries=5,
    linger_ms=20,
    batch_size=32_768,
    max_in_flight_requests_per_connection=5
)

logging.info("Starting Wikimedia → Kafka ingestion")
logging.info(
    "Kafka=%s | Topic=%s",
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC
)

# ---------------------------------------------------
# SSE Client
# ---------------------------------------------------
client = SSEClient(
    WIKIMEDIA_STREAM_URL,
    headers=HEADERS
)

# ---------------------------------------------------
# Stream events
# ---------------------------------------------------
for event in client:
    # Only process actual message events
    if event.event != "message":
        continue

    if not event.data or not event.data.strip():
        continue

    try:
        data = json.loads(event.data)
    except json.JSONDecodeError:
        continue

    future = producer.send(TOPIC, value=data)

    # Log async errors
    future.add_errback(
        lambda exc: logging.error(
            "Kafka send failed", exc_info=exc
        )
    )
