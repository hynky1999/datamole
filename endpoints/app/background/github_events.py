import json
import logging
import time
from app.models import Event
from kafka import KafkaConsumer
from sqlalchemy import exc

from app import db


def listen_to_gh_events(app):
    """
    Background process that listens to the Kafka topic providing github events
    """
    while True:
        try:
            consumer = KafkaConsumer(
                app.config['KAFKA_TOPIC'],
                bootstrap_servers=[app.config['KAFKA_URL']],
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            for message in consumer:
                process_message(app, message)
        except Exception as e:
            logging.error('Error listening to events: {}'.format(e))
            time.sleep(5)


def process_message(app, message):
    with app.app_context():
        try:
            event = Event.from_dict(message.value)
            db.session.add(event)
            db.session.commit()
            logging.info('Event saved')
        except exc.IntegrityError:
            logging.debug('Event already exists')
            db.session.rollback()
        except Exception as e:
            logging.error('Error processing message: {}'.format(e))
            db.session.rollback()