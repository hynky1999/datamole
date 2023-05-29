import os
import server

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    KAFKA_URL = os.environ.get("KAFKA_URL") or "localhost:9092"
    KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC") or "github_events"
    DEBUG = os.environ.get("DEBUG") == "True"
    HOST = os.environ.get("HOST") or "localhost"
