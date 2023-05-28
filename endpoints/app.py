import logging
from threading import Thread, Event
from app import create_app as create_app
from app.background import listen_to_gh_events


app = create_app()
exit_event = Event()
if app.config["DEBUG"] == False:
    logging.basicConfig(level=logging.INFO)
    # Don't run the background process in debug mode because of the reloader
    background_task = Thread(
        target=listen_to_gh_events, args=(app, exit_event)
    )
    background_task.start()
else:
    logging.basicConfig(level=logging.DEBUG)
app.run(port=5000, debug=app.config["DEBUG"])

# End the thread when the main process ends
exit_event.set()
