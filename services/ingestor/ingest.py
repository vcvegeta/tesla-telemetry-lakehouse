import json
import os
import time
from datetime import datetime, timezone
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "telemetry_raw")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def build_test_event() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "event_id": f"test-{int(time.time()*1000)}",
        "vehicle_id": os.getenv("SMARTCAR_VEHICLE_ID", "sim-vehicle"),
        "event_time": now,
        "ingest_time": now,
        "source": "bootstrap_test",
        "payload": {
            "battery_percent": 80,
            "speed_mph": 0,
            "odometer_miles": 1234.5
        }
    }

def main():
    print(f"[ingestor] sending to topic={KAFKA_TOPIC} bootstrap={KAFKA_BOOTSTRAP_SERVERS}")
    while True:
        event = build_test_event()
        producer.send(KAFKA_TOPIC, event)
        producer.flush()
        print(f"[ingestor] sent event_id={event['event_id']}")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
