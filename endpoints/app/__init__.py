from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from apifairy import APIFairy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
apifairy = APIFairy()
ma = Marshmallow()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate = Migrate(app, db)

    apifairy.init_app(app)
    ma.init_app(app)

    # Register blueprints
    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    return app


from app import models
