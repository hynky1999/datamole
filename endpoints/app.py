import logging
from app import create_app as create_app
from app.background import listen_to_gh_events


app = create_app()
debug = app.config['DEBUG'] or False
if debug == False:
    logging.basicConfig(level=logging.INFO)
    # Don't run the background process in debug mode because of the reloader
    listen_to_gh_events(app)
else:
    logging.basicConfig(level=logging.DEBUG)
app.run(port=5000, debug=debug)

