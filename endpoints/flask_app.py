import logging
from threading import Thread, Event
from app import create_app as create_app
from app.background import listen_to_gh_events

exit_event = Event()


def run_background(app):
    logging.info("Starting background process")
    background_task = Thread(
        target=listen_to_gh_events, args=(app, exit_event)
    )
    background_task.start()
    app.background_task = background_task


def run():
    app = create_app()
    run_background(app)
    return app


if __name__ == "__main__":
    app = run()
    # Set logger level
    logging.basicConfig(
        level=logging.DEBUG if app.config["DEBUG"] else logging.INFO,
    )

    app.run(host=app.config["HOST"], debug=app.config["DEBUG"])
    exit_event.set()
