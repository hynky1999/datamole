import logging
from flask_app import exit_event


def worker_exit(server, worker):
    logging.info("Worker exiting")
    exit_event.set()
