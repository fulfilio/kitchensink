from flask import Flask
from .extensions import fulfil, babel
from .settings import Config


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # register extensions
    fulfil.init_app(app)
    babel.init_app(app)

    # register blueprints
    from kitchensink.shipment import shipment
    app.register_blueprint(shipment)

    return app
