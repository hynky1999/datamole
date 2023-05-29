import json
import logging
import time
from app.models import Event
from kafka import KafkaConsumer
from sqlalchemy import exc

from app import db


def init_kafka(app, exit_event):
    consumer = None
    while exit_event.is_set() is False:
        try:
            consumer = KafkaConsumer(
                app.config["KAFKA_TOPIC"],
                bootstrap_servers=[app.config["KAFKA_URL"]],
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                auto_offset_reset="earliest",
                consumer_timeout_ms=5000,
            )
            logging.info("Kafka consumer initialized")
            break
        except Exception as e:
            logging.error("Error initializing Kafka consumer: {}".format(e))
            time.sleep(5)
    return consumer


def listen_to_gh_events(app, exit_event):
    """
    Background process that listens to the Kafka topic providing github events
    """
    consumer = init_kafka(app, exit_event)
    if consumer is None:
        logging.error("Kafka consumer could not be initialized")
        return

    while True:
        for message in consumer:
            process_message(app, message)

        if exit_event.is_set():
            logging.info("Exiting background process")
            break

    consumer.close()


def process_message(app, message):
    with app.app_context():
        try:
            event = Event.from_dict(message.value)
            db.session.add(event)
            db.session.commit()
            logging.info("Event saved")
        except exc.IntegrityError:
            logging.debug("Event already exists")
            db.session.rollback()
        except Exception as e:
            logging.error("Error processing message: {}".format(e))
            db.session.rollback()
