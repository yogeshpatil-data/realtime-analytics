import json
import time
import uuid
import random
from kafka import KafkaProducer

# Create Kafka producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

event_types = ["click", "view", "purchase"]
devices = ["web", "mobile"]
countries = ["IN", "US", "US", "UK"]  # weighted on purpose

print("Kafka Producer started... sending events")

while True:
    event = {
        "event_id": str(uuid.uuid4()),
        "user_id": f"user_{random.randint(1, 100)}",
        "session_id": str(uuid.uuid4()),
        "event_type": random.choice(event_types),
        "page_url": random.choice(["/home", "/product", "/cart"]),
        "event_timestamp": time.time(),
        "device": random.choice(devices),
        "country": random.choice(countries)
    }

    producer.send("click_events", event)
    print("Sent:", event)

    time.sleep(1)
