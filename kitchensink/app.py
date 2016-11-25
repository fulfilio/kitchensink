from flask import Flask
from .extensions import fulfil, babel, toolbar, login_manager
from .settings import Config
from .utils import client_url
from flask_sslify import SSLify


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # register extensions
    fulfil.init_app(app)
    babel.init_app(app)
    toolbar.init_app(app)
    login_manager.init_app(app)

    # Initialize the celery app
    # celery.init_app(app)
    if not app.debug:
        SSLify(app)

    # register blueprints
    from kitchensink.shipment import shipment, move
    app.register_blueprint(shipment)
    app.register_blueprint(move)
    from kitchensink.user import blueprint, public
    app.register_blueprint(blueprint)
    app.register_blueprint(public)

    # Register filters
    app.jinja_env.filters['client_url'] = client_url

    return app