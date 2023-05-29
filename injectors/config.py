import os

KAFKA_URL = os.environ.get("KAFKA_URL") or "localhost:9092"
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC") or "github_events"
DEBUG = os.environ.get("DEBUG") == "true"
