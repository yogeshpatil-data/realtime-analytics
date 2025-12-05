import json
from kafka import KafkaProducer
import sseclient
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

WIKIMEDIA_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "raw_wikimedia_events"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

logging.info("Starting Wikimedia → Kafka ingestion")

client = sseclient.SSEClient(WIKIMEDIA_STREAM_URL)

for event in client:
    if event.event == "message":
        data = json.loads(event.data)
        producer.send(TOPIC, value=data)
        logging.debug("Event produced")

